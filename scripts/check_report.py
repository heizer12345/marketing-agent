#!/usr/bin/env python3
"""Rule compliance checker for Sourcy Marketing Analyst reports."""
import re, pathlib, sys, json

BASE = pathlib.Path(__file__).parent.parent

def check_report(html_path, label=""):
    p = pathlib.Path(html_path)
    if not p.exists():
        return {"error": f"FILE NOT FOUND: {html_path}"}
    html = p.read_text()
    results = {}

    # R1: No bare W## labels in prose (exclude W3C)
    w_matches = re.findall(r'\bW\d{1,2}\b', html)
    w_in_prose = [m for m in w_matches if m not in ['W3C']]
    results['R1_no_bare_week'] = ('PASS' if len(w_in_prose) == 0
                                  else f'FAIL ({len(w_in_prose)} W## found: {list(set(w_in_prose))[:5]})')

    # R9: Exec summary table (render_exec_summary_table output)
    results['R9_exec_summary'] = ('PASS' if 'exec-summary' in html
                                   or 'Exec Summary' in html
                                   or 'Executive Summary' in html else 'FAIL')

    # R18: Tracking banner — mandatory every report
    # render_tracking_banner generates: "DATA GAP" (error), "TRACKING ISSUE" (warning), "NOTE" (info)
    # Structural inject (html_components.py) uses "warning" → "TRACKING ISSUE" when LLM omits it
    results['R18_tracking_banner'] = ('PASS' if 'DATA GAP' in html
                                       or 'TRACKING ISSUE' in html
                                       or '>NOTE<' in html
                                       or 'tracking-banner' in html
                                       or 'tracking-gap' in html else 'FAIL')

    # R19: Decision table — only required if there's a country or campaign breakdown table
    # Be specific: country table or campaign performance table, not generic "breakdown"
    has_country_or_campaign = any(kw in html for kw in [
        'by country', 'by Country', 'By Country', 'country-table',
        'Country | ', '| Country', 'per country',
        'Campaign Performance', 'campaign performance',
        'by campaign', 'By Campaign'
    ])
    has_decision_table = ('decision-table' in html or
                          ('Observation' in html and 'Interpretation' in html and 'Decision' in html))
    if has_country_or_campaign:
        results['R19_decision_table'] = 'PASS' if has_decision_table else 'FAIL'
    else:
        results['R19_decision_table'] = 'N/A'

    # G3: Positive signals — [POSITIVE] render_so_what label or positive content keywords
    has_positive_label = '[positive]' in html.lower()
    has_positive_content = ('positive' in html.lower() and
                             any(kw in html.lower() for kw in [
                                 'signal', 'winning', 'performing', 'what this means',
                                 'working well', 'above benchmark', 'outperform']))
    results['G3_positive_signals'] = 'PASS' if (has_positive_label or has_positive_content) else 'FAIL'

    # UX basics
    results['tooltip_present'] = 'PASS' if 'tooltip' in html.lower() else 'FAIL'
    results['charts_present'] = 'PASS' if ('chart' in html.lower() or 'canvas' in html.lower()) else 'FAIL'
    results['tabs_present'] = 'PASS' if 'tab' in html.lower() else 'FAIL'

    size_kb = p.stat().st_size // 1024
    pass_vals = [v for v in results.values()]
    passes = sum(1 for v in pass_vals if v == 'PASS')
    total = sum(1 for v in pass_vals if v not in ('N/A',))

    tag = label or p.name
    print(f"\n=== {tag}: {p.name} ({size_kb}KB) ===")
    print(f"Score: {passes}/{total}")
    for k, v in results.items():
        icon = '✅' if v == 'PASS' else ('⚪' if v == 'N/A' else '❌')
        print(f"  {icon} {k}: {v}")
    return {"score": passes, "total": total, "results": results, "size_kb": size_kb}


def check_ticket(ticket_id, label=""):
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://localhost:8000/api/tickets/{ticket_id}") as r:
            d = json.loads(r.read())
    except Exception as e:
        print(f"\n  Error fetching {ticket_id}: {e}")
        return None
    artifacts = d.get("artifacts", [])
    if not artifacts:
        print(f"\n=== {label or ticket_id}: NO ARTIFACT (status={d.get('status')}) ===")
        return None
    fp = artifacts[0].get("file_path", "") if isinstance(artifacts[0], dict) else ""
    if fp.startswith("/reports/"):
        path = BASE / "public" / "reports" / fp[len("/reports/"):]
    elif fp.startswith("/content/"):
        path = BASE / "public" / "content" / fp[len("/content/"):]
    else:
        path = BASE / "public" / fp.lstrip("/")
    return check_report(path, label or ticket_id)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if pathlib.Path(arg).exists():
                check_report(arg)
            else:
                check_ticket(arg)
