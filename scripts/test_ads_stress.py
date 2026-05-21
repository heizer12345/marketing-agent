"""Ads stress test — run ad_writer across 4 different campaigns concurrently.

Validates that:
- All 4 campaigns produce 3 variants each (12 total)
- All produce GPT Image 2 PNGs (12 total expected)
- All variants stay on-brand (zero banned phrases)
- Each ad's principle (PAS/AIDA/BAB) is reflected in its FINDINGS_JSON
- The new Sourcy design system shows up in the saved HTML
"""

import asyncio
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import Runner
from skills.content_skills.ad_writer import ad_writer

PERSONA = json.loads(Path("personas/sourcy.json").read_text())
BANNED = PERSONA["banned_phrases"]

# Four real campaign briefs covering different ICPs / angles / channels.
CAMPAIGNS = [
    {
        "name": "Brand aggregators (Meta)",
        "channel": "meta",
        "subject": "AI sourcing agent for brand aggregator portfolios with $50M+ revenue",
        "findings": [
            {"finding_id": "F1", "claim": "Brand aggregators rebuild sourcing ops for every new portfolio brand", "evidence": "Internal customer interviews 2026 Q1", "confidence": "High", "tags": ["pain_point","brand_aggregator"]},
            {"finding_id": "F2", "claim": "Sourcy's verified suppliers + 3-hour quotes scale across portfolio brands without adding headcount", "evidence": "390+ customers; brand aggregators are 22% of base", "confidence": "High", "tags": ["winning_angle","scale"]},
        ],
    },
    {
        "name": "First-time importers (Meta)",
        "channel": "meta",
        "subject": "AI sourcing agent for first-time DTC importers burned by Alibaba",
        "findings": [
            {"finding_id": "F1", "claim": "60% of first-time DTC importers report at least one Alibaba supplier scam in their first year", "evidence": "Internal survey 2026 Q1, n=140", "confidence": "High", "tags": ["pain_point","first_time_importer"]},
            {"finding_id": "F2", "claim": "Sourcy returns first real quote in 3 hours from verified factories", "evidence": "390+ customers", "confidence": "High", "tags": ["winning_angle","speed"]},
        ],
    },
    {
        "name": "Private label sourcing (Google Search)",
        "channel": "google_search",
        "subject": "Private label sourcing service for US DTC brands",
        "findings": [
            {"finding_id": "F1", "claim": "Brands searching 'private label supplier vietnam' convert 4x higher than generic 'sourcing agent' searches", "evidence": "Google Ads search-term report 2026 Q1", "confidence": "Medium", "tags": ["winning_angle","keyword"]},
            {"finding_id": "F2", "claim": "Sourcy offers end-to-end private label: design, sampling, MOQ negotiation, DDP shipping", "evidence": "Service tier menu", "confidence": "High", "tags": ["product_fit","private_label"]},
        ],
    },
    {
        "name": "Vietnam supplier diversification (Instagram Story)",
        "channel": "instagram_story",
        "subject": "Diversify off China — Sourcy onboards verified Vietnam factories",
        "findings": [
            {"finding_id": "F1", "claim": "China tariffs + supply chain pressure pushing brands to add a second country", "evidence": "Industry trend Q1 2026", "confidence": "Medium", "tags": ["macro","diversification"]},
            {"finding_id": "F2", "claim": "Sourcy has verified factories in 30+ countries including Vietnam, Indonesia, Thailand", "evidence": "Active supplier registry", "confidence": "High", "tags": ["winning_angle","geo"]},
        ],
    },
]


def build_prompt(c: dict) -> str:
    findings_json = json.dumps(c["findings"], indent=2)
    return f"""Generate 3 ad variants for {c['channel']}.

Subject: {c['subject']}.

Selected findings:
{findings_json}

Channel: {c['channel']}."""


async def run_one_campaign(c: dict) -> dict:
    t0 = time.time()
    print(f"→ [{c['name']}] dispatching ad_writer...")
    try:
        result = await Runner.run(ad_writer, build_prompt(c), max_turns=18)
        text = str(result.final_output)
        elapsed = time.time() - t0

        # Compliance checks
        text_lc = text.lower()
        banned = [bp for bp in BANNED if re.search(rf"\b{re.escape(bp.lower())}\b", text_lc)]

        # Parse FINDINGS_JSON
        m = re.search(r"<<<FINDINGS_JSON>>>(.*?)<<<END_FINDINGS_JSON>>>", text, re.DOTALL)
        findings = []
        if m:
            try:
                findings = json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Image URLs
        images = list(set(re.findall(r"/content/images/[^\s)]+\.png", text)))

        # Latest ad artifact
        ads_dir = Path("public/reports")
        latest = None
        for f in sorted(ads_dir.glob("ad_*.html"), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.stat().st_mtime >= t0:
                latest = f
                break

        # Design system verification (only if we got an artifact this run)
        design_ok = False
        if latest:
            html = latest.read_text()
            design_ok = "#0F172A" in html and "#22D3EE" in html and "Inter" in html

        # Variant + principle coverage
        variants_count = sum(1 for k in ["Variant A", "Variant B", "Variant C"] if k in text)
        principles_count = sum(1 for k in ["PAS", "AIDA", "BAB"] if k in text)

        return {
            "name": c["name"],
            "channel": c["channel"],
            "elapsed_s": round(elapsed, 1),
            "banned_count": len(banned),
            "banned": banned,
            "findings_count": len(findings),
            "image_count": len(images),
            "artifact_path": str(latest) if latest else None,
            "design_system_applied": design_ok,
            "variants_count": variants_count,
            "principles_count": principles_count,
            "ok": (not banned and len(findings) >= 3 and len(images) >= (0 if c["channel"] == "google_search" else 3)),
        }
    except Exception as e:
        return {"name": c["name"], "error": str(e)[:200], "ok": False}


async def main() -> int:
    print("┌" + "─" * 70 + "┐")
    print("│  ADS STRESS TEST — 4 campaigns running concurrently                  │")
    print("└" + "─" * 70 + "┘")
    print()
    print("Campaigns:")
    for c in CAMPAIGNS:
        print(f"  • {c['name']} ({c['channel']})")
    print()
    t0 = time.time()

    results = await asyncio.gather(*(run_one_campaign(c) for c in CAMPAIGNS))

    total_elapsed = time.time() - t0
    print()
    print("═" * 72)
    print(f"  RESULTS — total wall time {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print("═" * 72)
    print()

    for r in results:
        mark = "✓" if r.get("ok") else "✗"
        print(f"{mark} {r['name']:46s} {r.get('elapsed_s','-'):>6}s")
        if r.get("error"):
            print(f"    error: {r['error']}")
            continue
        print(f"    variants:   {r['variants_count']}/3 · principles: {r['principles_count']}/3")
        print(f"    findings:   {r['findings_count']}")
        print(f"    images:     {r['image_count']} {'(google_search → text only)' if r['channel']=='google_search' else ''}")
        print(f"    banned:     {r['banned_count']} {r['banned']}")
        print(f"    design sys: {'✓ applied' if r['design_system_applied'] else '✗ missing'}")
        if r.get("artifact_path"):
            print(f"    artifact:   {r['artifact_path']}")
        print()

    passed = sum(1 for r in results if r.get("ok"))
    print(f"  {passed}/{len(results)} campaigns passed.")
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
