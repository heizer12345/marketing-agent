"""Dynamic HTML artifact generator.

Three modes:
1. generate_dynamic_artifact() — Legacy: agent writes full HTML, tool saves it.
2. assemble_artifact() — Template: deterministic HTML from structured JSON.
3. execute_report_script() — Code-gen: LLM writes Python that uses html_components.py,
   we exec() it to produce custom HTML. Best of both worlds.
"""

import datetime as _datetime_module
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from agents import function_tool

import config
import tools.html_components as _hc


# Directory for saved build scripts (audit trail + debugging)
SCRIPTS_DIR = Path(config.OUTPUT_DIR).parent / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


def _save_script_error(script_filename: str, error_msg: str, tb: str) -> None:
    """Save a sidecar .error.json next to the script for retry lookups."""
    try:
        error_path = SCRIPTS_DIR / f"{script_filename}.error.json"
        error_path.write_text(json.dumps({"error": error_msg, "traceback": tb}), encoding="utf-8")
    except Exception:
        pass  # Non-critical


def _fix_iso_week_labels(html: str) -> str:
    """Convert ISO week strings (e.g. 2026-W12) to human-readable labels (e.g. Mar 18–24).
    Prevents R1 bare-W## violations from ECharts xAxis data using raw ISO weeks."""
    import re as _re

    def _iso_to_label(m):
        s = m.group(0)
        try:
            year_str, w_str = s.split("-W")
            year, wnum = int(year_str), int(w_str)
            monday = datetime.strptime(f"{year}-W{wnum:02d}-1", "%G-W%V-%u")
            sunday = monday + timedelta(days=6)
            # Same-month: "Mar 18–24"; cross-month: "Mar 29–Apr 4"
            if monday.month == sunday.month:
                return f"{monday.strftime('%b')} {monday.day}–{sunday.day}"
            else:
                return f"{monday.strftime('%b')} {monday.day}–{sunday.strftime('%b')} {sunday.day}"
        except Exception:
            return s  # Leave unchanged if parsing fails

    return _re.sub(r'\b20\d\d-W\d{1,2}\b', _iso_to_label, html)


def _save_html(html: str, title: str = "Analysis") -> dict:
    """Save HTML to disk and return result dict."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.html"
    filepath = config.OUTPUT_DIR / filename
    try:
        # Post-process: convert ISO week strings → human-readable labels (R1 compliance)
        html = _fix_iso_week_labels(html)
        filepath.write_text(html, encoding="utf-8")
        return {
            "success": True,
            "filename": filename,
            "filepath": str(filepath),
            "url": f"/reports/{filename}",
            "title": title,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@function_tool
def generate_dynamic_artifact(artifact_html: str, artifact_title: str = "Analysis") -> str:
    """Save a complete HTML artifact to disk. The agent writes the full HTML/JS/CSS
    dynamically based on the analysis data. The HTML should be self-contained with
    CDN-loaded libraries (ECharts, etc.).

    Args:
        artifact_html: Complete HTML document string with inline CSS/JS and CDN libs.
        artifact_title: Title for the artifact (used in filename and display).
    """
    result = _save_html(artifact_html, artifact_title)
    return json.dumps(result)


@function_tool
def execute_report_script(script_code: str, data_json: str = "{}", title: str = "Sourcy Marketing Analysis") -> str:
    """Execute a Python script that builds an HTML report using html_components.py.

    The synthesis agent writes Python code that uses the html_components library
    to build a custom dashboard. This tool exec()'s that code and saves the result.

    The script has access to these pre-injected variables:
    - DATA: dict — all skill results parsed from data_json
    - json: module — for data manipulation
    - All functions from tools.html_components:
        render_sparkline, render_kpi_card, render_kpi_grid,
        render_weekly_line_chart, render_bar_chart, render_funnel_chart,
        render_doughnut_chart, render_heatmap_chart, render_radar_chart,
        render_sortable_table, render_diagnosis_card, render_creative_gallery,
        render_expandable, render_so_what, render_tab_section, render_tab_bar,
        render_full_page, render_before_after, render_action_steps, render_tooltip_label

    The script MUST set a variable called RESULT_HTML to the final HTML string.
    Typically the last line is:
        RESULT_HTML = render_full_page(title, period, tab_bar_html, tab_htmls, chart_js_list)

    Args:
        script_code: Python code string that builds the HTML report.
        data_json: JSON string containing all skill data (parsed into DATA dict).
        title: Report title.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Parse data
    try:
        data = json.loads(data_json) if isinstance(data_json, str) else data_json
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps({"success": False, "error": f"Invalid data_json: {e}"})

    # 2. Save script for debugging / audit trail
    script_filename = f"build_{timestamp}.py"
    script_path = SCRIPTS_DIR / script_filename
    try:
        script_path.write_text(script_code, encoding="utf-8")
    except Exception:
        pass  # Non-critical — continue even if save fails

    # 3. Build exec namespace with all html_components functions + DATA
    # Also ensure tools/ is importable so `from html_components import ...` works if LLM writes it
    import sys as _sys
    _tools_dir = str(Path(__file__).parent)
    if _tools_dir not in _sys.path:
        _sys.path.insert(0, _tools_dir)

    namespace = {
        "DATA": data,
        "json": json,
        "datetime": _datetime_module,   # full module so datetime.timedelta works
        "timedelta": timedelta,         # also available directly
        "title": title,                 # report title available in script scope
        # Inject all public functions from html_components
        "render_sparkline": _hc.render_sparkline,
        "render_kpi_card": _hc.render_kpi_card,
        "render_kpi_grid": _hc.render_kpi_grid,
        "render_weekly_line_chart": _hc.render_weekly_line_chart,
        "render_bar_chart": _hc.render_bar_chart,
        "render_funnel_chart": _hc.render_funnel_chart,
        "render_doughnut_chart": _hc.render_doughnut_chart,
        "render_heatmap_chart": _hc.render_heatmap_chart,
        "render_radar_chart": _hc.render_radar_chart,
        "render_sortable_table": _hc.render_sortable_table,
        "render_diagnosis_card": _hc.render_diagnosis_card,
        "render_creative_gallery": _hc.render_creative_gallery,
        "render_expandable": _hc.render_expandable,
        "render_so_what": _hc.render_so_what,
        "render_tab_section": _hc.render_tab_section,
        "render_tab_bar": _hc.render_tab_bar,
        "render_full_page": _hc.render_full_page,
        "render_decision_summary": _hc.render_decision_summary,
        "render_comparison_header": _hc.render_comparison_header,
        # Recommendation components
        "render_before_after": _hc.render_before_after,
        "render_action_steps": _hc.render_action_steps,
        "render_action_item": _hc.render_action_item,
        "render_tooltip_label": _hc.render_tooltip_label,
        # Additional components
        "render_score_breakdown": _hc.render_score_breakdown,
        "render_message_alignment_card": _hc.render_message_alignment_card,
        "render_conversion_funnel": _hc.render_conversion_funnel,
        "render_reasoning_chain": _hc.render_reasoning_chain,
        # R9/R18/R19 compliance components (frequently used by synthesis agent)
        "render_tracking_banner": _hc.render_tracking_banner,
        "render_exec_summary_table": _hc.render_exec_summary_table,
        "render_decision_table": _hc.render_decision_table,
        # Result placeholder
        "RESULT_HTML": None,
    }

    # 3b. Sanitize common unicode characters that cause SyntaxErrors in Python
    # LLMs sometimes emit → ≥ ≤ — inside Python code (not string literals)
    _unicode_subs = {
        "\u2192": "->",   # →
        "\u2190": "<-",   # ←
        "\u2265": ">=",   # ≥
        "\u2264": "<=",   # ≤
        "\u2260": "!=",   # ≠
        "\u2013": "-",    # – (en dash)
        "\u2014": "-",    # — (em dash, outside strings)
    }
    for bad, good in _unicode_subs.items():
        script_code = script_code.replace(bad, good)

    # 4a. Pre-compile to catch SyntaxErrors with actionable hints
    try:
        compile(script_code, "<script>", "exec")
    except SyntaxError as e:
        hint = (
            "SyntaxError — most common causes:\n"
            "1. Unescaped quotes inside strings: use triple-quotes (\"\"\"...\"\"\") for text with quotes.\n"
            "2. Variable name starts with '.': remove the leading dot.\n"
            f"Line {e.lineno}: {(e.text or '').strip()[:120]}"
        )
        error_msg = f"Script syntax error: {e}"
        tb = f"SyntaxError at line {e.lineno}: {e.msg}\n  {(e.text or '').strip()}"
        _save_script_error(script_filename, error_msg, tb)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "hint": hint,
            "script_saved": script_filename,
        })

    # 4b. Execute the script
    try:
        exec(script_code, namespace)
    except Exception as e:
        tb = traceback.format_exc()
        error_msg = f"Script execution failed: {e}"
        _save_script_error(script_filename, error_msg, tb)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "traceback": tb,
            "script_saved": script_filename,
            "hint": "Check the saved script at public/scripts/ for debugging.",
        })

    # 5. Extract RESULT_HTML
    result_html = namespace.get("RESULT_HTML")
    if not result_html or not isinstance(result_html, str):
        error_msg = "Script did not set RESULT_HTML to an HTML string."
        _save_script_error(script_filename, error_msg, "")
        return json.dumps({
            "success": False,
            "error": error_msg,
            "script_saved": script_filename,
            "hint": "The script must set RESULT_HTML = render_full_page(...) at the end.",
        })

    # 6. Save HTML to disk
    result = _save_html(result_html, title)
    result["script_saved"] = script_filename
    return json.dumps(result)
