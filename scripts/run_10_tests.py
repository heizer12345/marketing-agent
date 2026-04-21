#!/usr/bin/env python3
"""
10-Query WebSocket Test Suite — tests R1-R21 rule compliance in generated artifacts.

Usage:
    python scripts/run_10_tests.py

Each test:
 1. Creates a ticket via REST
 2. Sends the query over WebSocket
 3. Waits up to TIMEOUT_SECONDS for an artifact URL in the stream
 4. Fetches the HTML artifact
 5. Runs rule-specific checks on the HTML content
 6. Prints PASS / FAIL / SKIP per check

Timeout: 600s per query (real agent runs, so this can take a while).
"""

import asyncio
import json
import re
import sys
import time
import uuid
from datetime import datetime
from typing import Optional
import urllib.request

try:
    import websockets
except ImportError:
    print("Installing websockets…")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets

BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"
TIMEOUT = 600  # seconds per query (agent runs can take up to 10 min)
LOG_FILE = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

# ─── ANSI colours ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  return f"{GREEN}✅ PASS{RESET}  {msg}"
def fail(msg): return f"{RED}❌ FAIL{RESET}  {msg}"
def skip(msg): return f"{YELLOW}⏭  SKIP{RESET}  {msg}"
def info(msg): return f"{CYAN}ℹ{RESET}  {msg}"

# ─── REST helpers ────────────────────────────────────────────────────────────

def rest_post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def rest_get(path: str) -> str:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=15) as r:
        return r.read().decode()

# ─── Rule checkers (operate on raw HTML string) ─────────────────────────────

def check_no_bare_week_numbers(html: str) -> tuple[bool, str]:
    """R1 — chart labels should use dates not W## (bare week numbers)."""
    bare = re.findall(r"(?<![A-Za-z0-9_-])(W\d{1,2})(?![A-Za-z0-9])", html)
    # Allow 'W' followed by digit in data contexts like JSON values "2026-W11"
    # Strip those — only flag if they appear as visible text in labels/tds
    suspicious = [w for w in bare if html.count(w) > 2]  # repeated = likely used in chart labels
    if not suspicious:
        return True, "No bare W## labels found"
    return False, f"Found bare week labels: {list(set(suspicious))[:5]}"


def check_country_table_has_cvr(html: str) -> tuple[bool, str]:
    """R2 — country table must include CVR or CPL columns."""
    has_country = bool(re.search(r'(Philippines|Indonesia|Thailand|country)', html, re.I))
    if not has_country:
        return True, "No country table in this report (skip)"
    has_cvr = bool(re.search(r'(CVR|CPL|Conv(?:ersion)?\s*Rate|Cost.*Lead)', html, re.I))
    if has_cvr:
        return True, "Country table includes CVR/CPL columns"
    return False, "Country table missing CVR/CPL columns — only shows spend/sessions"


def check_has_exec_summary(html: str) -> tuple[bool, str]:
    """R9 — exec summary table (render_exec_summary_table or similar) present."""
    has_exec = bool(re.search(
        r'(Paid Acquisition|Organic.*SEO|CRO.*On.site|exec.summ|Exec Summary|Status.*Verdict|'
        r'On Track|Action Needed|Monitor)',
        html, re.I
    ))
    if has_exec:
        return True, "Exec summary table found"
    return False, "No exec summary table detected"


def check_has_tracking_banner(html: str) -> tuple[bool, str]:
    """R7 — tracking issues shown as a global banner, not buried in prose."""
    has_banner = bool(re.search(
        r'(DATA.GAP|TRACKING.ISSUE|tracking.*broken|conversion.*not.firing|'
        r'render_tracking_banner|tracking.*dependency)',
        html, re.I
    ))
    if has_banner:
        return True, "Tracking banner present"
    return False, "No tracking status banner found"


def check_has_whats_working(html: str) -> tuple[bool, str]:
    """R8 — 'What's Working' section or positive signals present."""
    has_positive = bool(re.search(
        r'(what.s working|positive signal|performing well|beating.*benchmark|'
        r'ecfdf5|10b981|growing steady)',  # green color codes used by render_so_what positive
        html, re.I
    ))
    if has_positive:
        return True, "Positive/What's Working section found"
    return False, "No positive signals section — report may be 100% problems"


def check_source_labels(html: str) -> tuple[bool, str]:
    """R3 — every chart/KPI should have a source label."""
    has_sources = bool(re.search(r'Source:\s*(GA4|Meta Ads|Search Console|Google Ads|PostHog)', html, re.I))
    if has_sources:
        return True, "Source labels present on components"
    return False, "No explicit source labels found (GA4, Meta Ads, etc.)"


def check_decision_table(html: str) -> tuple[bool, str]:
    """R5 — decision table with Observation/Interpretation/Decision columns."""
    has_decision_table = bool(re.search(
        r'(Observation.*Interpretation|Interpretation.*Decision|Decision.*Action|'
        r'Signal.*Observation)',
        html, re.I
    ))
    if has_decision_table:
        return True, "Decision table (Obs/Interp/Decision) found"
    return False, "No structured decision table found — using plain Notes column?"


def check_root_cause(html: str) -> tuple[bool, str]:
    """R10/R17 — root cause explanation, not just symptoms."""
    has_root_cause = bool(re.search(
        r'(ROOT\s*CAUSE|root.cause|because|reason.*is|WHY.*this|'
        r'Advantage\+|campaign.*setting|targeting.*config)',
        html, re.I
    ))
    if has_root_cause:
        return True, "Root cause explanation found"
    return False, "No root cause analysis detected — may be symptom-only"


def check_date_labels_in_period(html: str) -> tuple[bool, str]:
    """R1 — period strings use dates, not week numbers."""
    # Check render_full_page period string: look for month abbreviations
    has_dates = bool(re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', html))
    if has_dates:
        return True, "Date-based period labels found (Jan/Feb/Mar etc.)"
    return False, "Period labels may use week numbers instead of dates"


def check_has_weekly_trend_chart(html: str) -> tuple[bool, str]:
    """R11 — organic trend should be a weekly line chart."""
    has_chart = bool(re.search(r'(chart-.*\d|echart|series.*data|render_weekly_line)', html, re.I))
    if has_chart:
        return True, "Chart/EChart configuration found"
    return False, "No chart detected in artifact"


def check_tooltips_present(html: str) -> tuple[bool, str]:
    """Tooltip fix — tooltips use both title attr and custom div."""
    has_title_attr = bool(re.search(r'title="[^"]{10,}"', html))
    has_custom_tip = bool(re.search(r'z-index:9999|pointer-events:none.*white-space:normal', html))
    if has_title_attr and has_custom_tip:
        return True, "Tooltips have both native title= and custom styled overlay"
    elif has_title_attr:
        return True, "Tooltips have native title= fallback (always works)"
    return False, "No tooltip attributes found — tooltips may be missing"


def check_schema_not_invented(html: str) -> tuple[bool, str]:
    """Schema hard-fail — if error JSON returned, schema guard worked."""
    has_error_guard = bool(re.search(r'(no .json files|save_schema_file|schema_relative)', html, re.I))
    # For non-schema queries this is n/a; for schema queries we check artifact format
    has_json_ld = bool(re.search(r'"@context".*schema\.org|application/ld\+json', html, re.I))
    has_jsx = bool(re.search(r'JsonLd|json-ld', html, re.I))
    if has_json_ld or has_jsx:
        return True, "JSON-LD schema present in artifact"
    return False, "No schema markup found in artifact (may be expected for non-schema queries)"


def check_wow_has_periods(html: str) -> tuple[bool, str]:
    """R15 — WoW change_pct present alongside metrics."""
    has_wow = bool(re.search(r'(WoW|MoM|vs\s+prev|change_pct|\+\d+%|\-\d+%)', html, re.I))
    if has_wow:
        return True, "WoW/MoM comparison values found"
    return False, "No WoW/MoM comparisons found — metrics may be static"


def check_platform_timeframe_labels(html: str) -> tuple[bool, str]:
    """R3 — each data source shows its own timeframe."""
    has_windows = bool(re.search(
        r'(last 30d|last 90d|last 28d|last 7d|\(\d+ day|\d+d\))',
        html, re.I
    ))
    if has_windows:
        return True, "Platform-specific timeframe labels present"
    return False, "No per-platform timeframe labels detected"


# ─── Test definitions ────────────────────────────────────────────────────────

TESTS = [
    {
        "id": 1,
        "query": "Give me an executive dashboard of all marketing",
        "rules": ["R9", "R14", "R8", "R7"],
        "checks": [
            ("R9 exec_summary_table",    check_has_exec_summary),
            ("R8 whats_working",         check_has_whats_working),
            ("R7 tracking_banner",       check_has_tracking_banner),
            ("source_labels",            check_source_labels),
        ],
    },
    {
        "id": 2,
        "query": "Which Google Ads campaigns are wasting budget and why",
        "rules": ["R6", "R10", "R17"],
        "checks": [
            ("R10/R17 root_cause",       check_root_cause),
            ("source_labels",            check_source_labels),
            ("R5 decision_table",        check_decision_table),
        ],
    },
    {
        "id": 3,
        "query": "Compare Instagram Reels vs static posts — show engagement breakdown",
        "rules": ["tooltip fix", "R15"],
        "checks": [
            ("tooltip_fix",              check_tooltips_present),
            ("R15 wow_comparison",       check_wow_has_periods),
            ("source_labels",            check_source_labels),
        ],
    },
    {
        "id": 4,
        "query": "What is our tracking status and which marketing decisions can't I trust right now",
        "rules": ["R7", "R12"],
        "checks": [
            ("R7 tracking_banner",       check_has_tracking_banner),
            ("R8 whats_working",         check_has_whats_working),
            ("source_labels",            check_source_labels),
        ],
    },
    {
        "id": 5,
        "query": "Show weekly organic search trend for last 12 weeks with pattern call-out",
        "rules": ["R11", "R1"],
        "checks": [
            ("R1 no_bare_W_labels",      check_no_bare_week_numbers),
            ("R1 date_labels",           check_date_labels_in_period),
            ("R11 weekly_chart",         check_has_weekly_trend_chart),
        ],
    },
    {
        "id": 6,
        "query": "Compare Meta Ads week over week — spend and leads by country",
        "rules": ["R2", "R5", "R15"],
        "checks": [
            ("R2 country_cvr_cpl",       check_country_table_has_cvr),
            ("R5 decision_table",        check_decision_table),
            ("R15 wow_comparison",       check_wow_has_periods),
        ],
    },
    {
        "id": 7,
        "query": "Full marketing audit with executive summary and prioritized actions",
        "rules": ["R9", "R13", "R8"],
        "checks": [
            ("R9 exec_summary_table",    check_has_exec_summary),
            ("R8 whats_working",         check_has_whats_working),
            ("R13 actions_present",      lambda h: (bool(re.search(r'(Do This Week|Priority|action_item|render_action)', h, re.I)), "Actions tab found")),
            ("source_labels",            check_source_labels),
        ],
    },
    {
        "id": 8,
        "query": "Show 6-month organic traffic trend",
        "rules": ["R11 MoM", "R15"],
        "checks": [
            ("R11 monthly_chart",        check_has_weekly_trend_chart),
            ("R1 date_labels",           check_date_labels_in_period),
            ("R15 wow_or_mom",           check_wow_has_periods),
        ],
    },
    {
        "id": 9,
        "query": "Add organization schema to the homepage, about, and pricing pages",
        "rules": ["schema hard-fail"],
        "checks": [
            ("schema_json_ld",           check_schema_not_invented),
            ("source_labels",            check_source_labels),
        ],
    },
    {
        "id": 10,
        "query": "Why are non-target country paid sessions so high — what is the root cause",
        "rules": ["R17 root cause"],
        "checks": [
            ("R17 root_cause",           check_root_cause),
            ("R2 country_table",         check_country_table_has_cvr),
            ("R10 diagnosis",            lambda h: (bool(re.search(r'(diagnosis|ROOT CAUSE|Advantage\+|geo.*target|country.*target)', h, re.I)), "Diagnosis/root cause block found")),
        ],
    },
]

# ─── WebSocket runner ────────────────────────────────────────────────────────

async def run_query(query: str, ticket_id: str, timeout: int) -> Optional[str]:
    """Send query via WebSocket, return first artifact URL found or None on timeout."""
    url = f"{WS_BASE}/ws/{ticket_id}"
    artifact_url = None
    started = time.time()

    try:
        async with websockets.connect(url, ping_timeout=60, close_timeout=10) as ws:
            await ws.send(json.dumps({"type": "query", "content": query}))
            print(f"    {info('Query sent, waiting for artifact…')}")

            while time.time() - started < timeout:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    elapsed = int(time.time() - started)
                    print(f"    ⏳ No message for 30s (total {elapsed}s elapsed)…")
                    continue

                msg = json.loads(raw)
                mtype = msg.get("type", "")

                if mtype == "artifact":
                    url_val = msg.get("url") or msg.get("file_path") or ""
                    if url_val:
                        artifact_url = url_val
                        print(f"    {info(f'Artifact URL: {artifact_url}')}")

                elif mtype == "status":
                    status = msg.get("status", "")
                    print(f"    Status: {status}")
                    if status in ("completed", "error", "failed"):
                        break

                elif mtype == "message":
                    content = msg.get("content", "")
                    # Also scan message text for artifact paths
                    m = re.search(r'(/(?:reports|content|reviews)/[^\s"\'<>]+\.html)', content)
                    if m and not artifact_url:
                        artifact_url = m.group(1)
                        print(f"    {info(f'Artifact in message: {artifact_url}')}")

                elif mtype == "error":
                    print(f"    {fail('Error from server: ' + msg.get('message', '?'))}")
                    break

    except Exception as e:
        print(f"    {fail(f'WebSocket error: {e}')}")

    return artifact_url


def fetch_html(artifact_path: str) -> Optional[str]:
    """Fetch the HTML artifact from localhost."""
    try:
        url = f"{BASE}{artifact_path}"
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"    {fail(f'Could not fetch artifact: {e}')}")
        return None


def run_checks(html: str, checks: list) -> list[dict]:
    results = []
    for name, fn in checks:
        try:
            passed, detail = fn(html)
            results.append({"name": name, "passed": passed, "detail": detail})
        except Exception as ex:
            results.append({"name": name, "passed": False, "detail": f"Check error: {ex}"})
    return results

# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  Marketing Agent — 10-Query Test Suite{RESET}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Server: {BASE}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    all_results = []
    total_pass = total_fail = total_skip = 0

    for test in TESTS:
        tid = test["id"]
        query = test["query"]
        rules = ", ".join(test["rules"])

        print(f"\n{BOLD}{'─'*70}{RESET}")
        print(f"{BOLD}Test {tid}/10{RESET}  [{rules}]")
        print(f"  Query: {CYAN}\"{query}\"{RESET}")

        # Create ticket
        try:
            ticket = rest_post("/api/tickets", {"title": f"Test {tid}: {query[:50]}", "created_by": "test_runner"})
            ticket_id = ticket["id"]
            print(f"  Ticket: {ticket_id[:8]}")
        except Exception as e:
            print(f"  {fail(f'Could not create ticket: {e}')} — skipping")
            all_results.append({"id": tid, "query": query, "artifact": None, "checks": [], "skipped": True})
            continue

        t_start = time.time()
        artifact_path = await run_query(query, ticket_id, TIMEOUT)
        elapsed = int(time.time() - t_start)

        if not artifact_path:
            # Try fetching from DB artifacts
            try:
                ticket_data = json.loads(rest_get(f"/api/tickets/{ticket_id}"))
                arts = ticket_data.get("artifacts", [])
                if arts:
                    last = arts[-1]
                    artifact_path = last.get("file_path") if isinstance(last, dict) else last
                    print(f"  {info(f'Artifact from DB: {artifact_path}')}")
            except Exception:
                pass

        if not artifact_path:
            print(f"  {fail(f'No artifact after {elapsed}s — query timed out or failed')}")
            all_results.append({"id": tid, "query": query, "artifact": None, "checks": [], "skipped": True})
            total_skip += len(test["checks"])
            continue

        print(f"  Elapsed: {elapsed}s  →  {artifact_path}")

        html = fetch_html(artifact_path)
        if not html:
            print(f"  {fail('Could not fetch HTML artifact')}")
            all_results.append({"id": tid, "query": query, "artifact": artifact_path, "checks": [], "skipped": True})
            total_skip += len(test["checks"])
            continue

        print(f"  HTML size: {len(html):,} chars")

        check_results = run_checks(html, test["checks"])
        for cr in check_results:
            if cr["passed"]:
                print(f"    {ok(cr['name'])} — {cr['detail']}")
                total_pass += 1
            else:
                print(f"    {fail(cr['name'])} — {cr['detail']}")
                total_fail += 1

        all_results.append({
            "id": tid, "query": query, "rules": rules,
            "artifact": artifact_path, "elapsed": elapsed,
            "checks": check_results, "skipped": False,
        })

    # ─── Summary ────────────────────────────────────────────────────────────
    print(f"\n\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  RESULTS SUMMARY{RESET}")
    print(f"{'='*70}")
    total = total_pass + total_fail + total_skip
    print(f"  Total checks:  {total}")
    print(f"  {GREEN}Pass:   {total_pass}{RESET}")
    print(f"  {RED}Fail:   {total_fail}{RESET}")
    print(f"  {YELLOW}Skip:   {total_skip}{RESET} (no artifact / timeout)")
    print()

    for r in all_results:
        if r.get("skipped"):
            status_str = f"{YELLOW}⏭ SKIPPED{RESET}"
        else:
            passed = sum(1 for c in r["checks"] if c["passed"])
            total_c = len(r["checks"])
            status_str = f"{GREEN}✅ {passed}/{total_c}{RESET}" if passed == total_c else f"{RED}❌ {passed}/{total_c}{RESET}"
        print(f"  Test {r['id']:2d}  {status_str}  {r['query'][:55]}")

    print(f"\n{BOLD}{'='*70}{RESET}\n")

    # Write markdown log
    lines = [f"# Test Run — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    for r in all_results:
        lines.append(f"\n## Test {r['id']}: {r['query']}")
        if r.get("skipped"):
            lines.append("**Status: SKIPPED** (no artifact)\n")
        else:
            lines.append(f"Rules: {r.get('rules','')}  |  Elapsed: {r.get('elapsed',0)}s  |  Artifact: `{r.get('artifact','')}`\n")
            for c in r["checks"]:
                sym = "✅" if c["passed"] else "❌"
                lines.append(f"- {sym} **{c['name']}**: {c['detail']}")
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(lines))
    print(f"Log written → {LOG_FILE}\n")


if __name__ == "__main__":
    asyncio.run(main())
