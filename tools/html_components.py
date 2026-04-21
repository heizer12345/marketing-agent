"""Deterministic HTML component builders for marketing dashboards.

Pure Python functions that generate HTML/CSS/JS fragments for:
- KPI cards with sparklines
- ECharts configurations (line, bar, funnel, heatmap, radar)
- Sortable data tables with inline sparklines
- Diagnosis cards with severity colors
- Creative gallery (Meta ad images with performance badges)
- Expandable accordion sections
- Tab containers

All functions return HTML strings. No LLM needed.
"""

import json
from datetime import datetime
from typing import Any, Optional

# ─── Color Palette ────────────────────────────────────────────────────

COLORS = {
    "primary": "#3b82f6",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#6366f1",
    "muted": "#94a3b8",
    "bg_dark": "#0f172a",
    "bg_card": "#ffffff",
    "bg_page": "#f8fafc",
    "text": "#1e293b",
    "text_light": "#64748b",
    "border": "#e2e8f0",
    # Chart series colors
    "series": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#6366f1", "#ec4899", "#14b8a6", "#f97316"],
}

SEVERITY_COLORS = {
    "urgent": {"bg": "#fef2f2", "border": "#ef4444", "text": "#991b1b"},
    "important": {"bg": "#fffbeb", "border": "#f59e0b", "text": "#92400e"},
    "nice_to_have": {"bg": "#eff6ff", "border": "#3b82f6", "text": "#1e40af"},
    "positive": {"bg": "#ecfdf5", "border": "#10b981", "text": "#065f46"},
    "cross_skill": {"bg": "#f0f9ff", "border": "#0ea5e9", "text": "#0c4a6e"},
}


# ─── Inline SVG Sparkline ────────────────────────────────────────────

def render_sparkline(values: list, color: str = "#3b82f6", width: int = 80, height: int = 24) -> str:
    """Render a tiny inline SVG sparkline for table cells.

    Args:
        values: List of 3-8 numeric values (e.g., weekly metrics)
        color: Stroke color (hex)
        width: SVG width in pixels
        height: SVG height in pixels
    """
    if not values or len(values) < 2:
        return '<span style="color:#94a3b8">—</span>'

    # Normalize values to SVG coordinates
    min_v = min(values)
    max_v = max(values)
    span = max_v - min_v if max_v != min_v else 1
    padding = 2

    points = []
    for i, v in enumerate(values):
        x = padding + (i / (len(values) - 1)) * (width - 2 * padding)
        y = height - padding - ((v - min_v) / span) * (height - 2 * padding)
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)

    # Determine trend color
    trend_color = color
    if values[-1] > values[0]:
        trend_color = COLORS["success"]
    elif values[-1] < values[0]:
        trend_color = COLORS["danger"]

    return (
        f'<svg width="{width}" height="{height}" style="vertical-align:middle">'
        f'<polyline points="{polyline}" fill="none" stroke="{trend_color}" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{points[-1].split(",")[0]}" cy="{points[-1].split(",")[1]}" '
        f'r="2" fill="{trend_color}"/>'
        f'</svg>'
    )


# ─── KPI Card ────────────────────────────────────────────────────────

def render_kpi_card(
    label: str,
    value: Any,
    change_pct: Optional[float] = None,
    benchmark: Optional[str] = None,
    sparkline_values: Optional[list] = None,
    prefix: str = "",
    suffix: str = "",
    source: str = "",
    tooltip: str = "",
    drilldown: Optional[dict] = None,
    mom_change_pct: Optional[float] = None,
) -> str:
    """Render a KPI metric card with optional WoW/MoM change, sparkline, source, tooltip, and drilldown.

    Args:
        source: Data source label (e.g., "GA4", "Search Console", "Meta Ads API").
        tooltip: Plain-language explanation of what this metric means (shown on hover).
        drilldown: Dict with "headers" (list) and "rows" (list of lists) for expand-in-place detail.
    """
    # Format value
    if isinstance(value, float):
        display_value = f"{prefix}{value:,.2f}{suffix}"
    elif isinstance(value, int):
        display_value = f"{prefix}{value:,}{suffix}"
    else:
        display_value = f"{prefix}{value}{suffix}"

    # Change badge — WoW + optional MoM
    change_html = ""
    if change_pct is not None:
        arrow = "&#9650;" if change_pct > 0 else "&#9660;" if change_pct < 0 else "&#8212;"
        color = COLORS["success"] if change_pct > 0 else COLORS["danger"] if change_pct < 0 else COLORS["muted"]
        change_html = f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:5px">'
        change_html += (
            f'<span style="font-size:11px;font-weight:600;color:{color};'
            f'background:{color}12;border-radius:4px;padding:1px 6px">'
            f'{arrow} {abs(change_pct):.1f}% WoW</span>'
        )
        if mom_change_pct is not None:
            m_arrow = "&#9650;" if mom_change_pct > 0 else "&#9660;" if mom_change_pct < 0 else "&#8212;"
            m_color = COLORS["success"] if mom_change_pct > 0 else COLORS["danger"] if mom_change_pct < 0 else COLORS["muted"]
            change_html += (
                f'<span style="font-size:11px;font-weight:600;color:{m_color};'
                f'background:{m_color}12;border-radius:4px;padding:1px 6px">'
                f'{m_arrow} {abs(mom_change_pct):.1f}% MoM</span>'
            )
        change_html += '</div>'

    # Benchmark badge
    bench_html = ""
    if benchmark:
        bench_html = f'<div style="font-size:11px;color:{COLORS["text_light"]};margin-top:2px">vs {benchmark}</div>'

    # Sparkline
    spark_html = ""
    if sparkline_values:
        spark_html = f'<div style="margin-top:6px">{render_sparkline(sparkline_values)}</div>'

    # Source label
    source_html = ""
    if source:
        source_html = f'<div style="font-size:10px;color:{COLORS["muted"]};margin-top:6px;border-top:1px solid {COLORS["border"]};padding-top:4px">📊 {source}</div>'

    # Tooltip on label
    label_html = label
    if tooltip:
        label_html = render_tooltip_label(label, tooltip)

    # Drilldown (expand-in-place table on click)
    drilldown_html = ""
    click_attrs = ""
    expand_icon = ""
    if drilldown and isinstance(drilldown, dict) and "headers" in drilldown and "rows" in drilldown:
        uid = f"dd_{abs(hash(label + str(value))) % 100000}"
        click_attrs = (
            f'onclick="var d=document.getElementById(\'{uid}\');'
            f'd.style.display=d.style.display===\'none\'?\'block\':\'none\'"'
            f' style="cursor:pointer"'
        )
        expand_icon = f'<span style="font-size:10px;color:{COLORS["muted"]};float:right">▾ click to expand</span>'
        # Build mini-table
        th = "".join(f'<th style="padding:5px 8px;text-align:left;font-size:11px;font-weight:600;'
                     f'background:{COLORS["bg_page"]};border-bottom:1px solid {COLORS["border"]}">'
                     f'{h}</th>' for h in drilldown["headers"])
        rows_html = ""
        for row in drilldown["rows"][:20]:
            cells = "".join(f'<td style="padding:4px 8px;font-size:11px;border-bottom:1px solid {COLORS["border"]}20">'
                           f'{c}</td>' for c in row)
            rows_html += f'<tr>{cells}</tr>'
        if len(drilldown["rows"]) > 20:
            rows_html += (f'<tr><td colspan="{len(drilldown["headers"])}" style="padding:6px 8px;'
                         f'font-size:11px;color:{COLORS["muted"]};text-align:center">'
                         f'...and {len(drilldown["rows"]) - 20} more rows</td></tr>')
        drilldown_html = (
            f'<div id="{uid}" style="display:none;margin-top:8px;border-top:1px solid {COLORS["border"]};'
            f'padding-top:8px;max-height:300px;overflow-y:auto">'
            f'<table style="width:100%;border-collapse:collapse"><thead><tr>{th}</tr></thead>'
            f'<tbody>{rows_html}</tbody></table></div>'
        )

    return f"""<div {click_attrs or ''} style="background:{COLORS['bg_card']};border-radius:8px;padding:16px;
        box-shadow:0 1px 3px rgba(0,0,0,.08);min-width:160px;{'cursor:pointer' if drilldown else ''}">
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.04em;
            color:{COLORS['text_light']};margin-bottom:6px">{label_html}{expand_icon}</div>
        <div style="font-size:22px;font-weight:700;color:{COLORS['text']}">{display_value}</div>
        {change_html}{bench_html}{spark_html}{source_html}{drilldown_html}
    </div>"""


def render_kpi_grid(cards: list) -> str:
    """Render a grid of KPI cards.

    Args:
        cards: List of dicts with keys matching render_kpi_card params,
               OR list of already-rendered HTML strings.
    """
    parts = []
    for c in cards:
        if isinstance(c, str):
            parts.append(c)   # already rendered HTML
        elif isinstance(c, dict):
            parts.append(render_kpi_card(**c))
    cards_html = "\n".join(parts)
    return f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px">{cards_html}</div>'


# ─── ECharts Configuration Builders ──────────────────────────────────

def _echart_container(chart_id: str, height: int = 340, title: str = "") -> str:
    """Wrap an ECharts container div."""
    title_html = f'<h3 style="font-size:15px;font-weight:600;margin:0 0 12px 0;color:{COLORS["text"]}">{title}</h3>' if title else ""
    return f"""{title_html}<div id="{chart_id}" style="width:100%;height:{height}px;margin-bottom:24px"></div>"""


def render_weekly_line_chart(
    chart_id: str,
    weeks: list[str],
    series: list[dict],
    title: str = "",
    height: int = 340,
) -> tuple[str, str]:
    """Render a multi-series line chart for weekly trends.

    Args:
        chart_id: Unique DOM ID for the chart
        weeks: List of week labels (e.g., ["W10", "W11", "W12", "W13", "W14"])
        series: List of dicts with {name, data, color?} (e.g., [{"name": "Sessions", "data": [100, 120, ...]}])
        title: Chart title
        height: Chart height in pixels

    Returns:
        Tuple of (container_html, init_js)
    """
    container = _echart_container(chart_id, height, title)

    echart_series = []
    for i, s in enumerate(series):
        color = s.get("color", COLORS["series"][i % len(COLORS["series"])])
        echart_series.append({
            "name": s["name"],
            "type": "line",
            "smooth": True,
            "data": s["data"],
            "itemStyle": {"color": color},
            "lineStyle": {"width": 2},
            "symbol": "circle",
            "symbolSize": 6,
        })

    option = {
        "tooltip": {"trigger": "axis"},
        "legend": {"bottom": 0, "textStyle": {"fontSize": 11}},
        "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "5%", "containLabel": True},
        "xAxis": {"type": "category", "data": weeks, "axisLabel": {"fontSize": 11}},
        "yAxis": {"type": "value", "axisLabel": {"fontSize": 11}},
        "series": echart_series,
    }

    init_js = f"echarts.init(document.getElementById('{chart_id}')).setOption({json.dumps(option)});"
    return container, init_js


def render_bar_chart(
    chart_id: str,
    categories: list[str],
    series: list[dict],
    title: str = "",
    horizontal: bool = False,
    height: int = 340,
) -> tuple[str, str]:
    """Render a bar chart (vertical or horizontal)."""
    container = _echart_container(chart_id, height, title)

    echart_series = []
    for i, s in enumerate(series):
        color = s.get("color", COLORS["series"][i % len(COLORS["series"])])
        echart_series.append({
            "name": s["name"],
            "type": "bar",
            "data": s["data"],
            "itemStyle": {"color": color, "borderRadius": [4, 4, 0, 0] if not horizontal else [0, 4, 4, 0]},
            "barMaxWidth": 40,
        })

    if horizontal:
        x_axis = {"type": "value", "axisLabel": {"fontSize": 11}}
        y_axis = {"type": "category", "data": categories, "axisLabel": {"fontSize": 11}}
    else:
        x_axis = {"type": "category", "data": categories, "axisLabel": {"fontSize": 11, "rotate": 30}}
        y_axis = {"type": "value", "axisLabel": {"fontSize": 11}}

    option = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"bottom": 0, "textStyle": {"fontSize": 11}},
        "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "5%", "containLabel": True},
        "xAxis": x_axis,
        "yAxis": y_axis,
        "series": echart_series,
    }

    init_js = f"echarts.init(document.getElementById('{chart_id}')).setOption({json.dumps(option)});"
    return container, init_js


def render_funnel_chart(
    chart_id: str,
    stages: list[dict],
    title: str = "",
    height: int = 300,
) -> tuple[str, str]:
    """Render a funnel chart.

    Args:
        stages: List of {name, value} dicts, ordered from largest to smallest.
    """
    container = _echart_container(chart_id, height, title)

    # Normalize stages: accept strings, tuples, or dicts with value/count keys
    norm_stages = []
    for s in stages:
        if isinstance(s, str):
            norm_stages.append({"name": s, "value": 0})
        elif isinstance(s, (list, tuple)) and len(s) >= 2:
            norm_stages.append({"name": str(s[0]), "value": s[1]})
        elif isinstance(s, dict):
            name = s.get("name") or s.get("label") or s.get("stage") or str(s)
            value = s.get("value") or s.get("count") or s.get("total") or 0
            norm_stages.append({"name": name, "value": value})
        else:
            norm_stages.append({"name": str(s), "value": 0})

    option = {
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "series": [{
            "type": "funnel",
            "left": "10%",
            "top": 10,
            "bottom": 10,
            "width": "80%",
            "sort": "descending",
            "gap": 2,
            "label": {"show": True, "position": "inside", "fontSize": 12},
            "itemStyle": {"borderColor": "#fff", "borderWidth": 1},
            "data": [{"name": s["name"], "value": s["value"]} for s in norm_stages],
        }],
    }

    init_js = f"echarts.init(document.getElementById('{chart_id}')).setOption({json.dumps(option)});"
    return container, init_js


def render_doughnut_chart(
    chart_id: str,
    data: list[dict],
    title: str = "",
    height: int = 300,
) -> tuple[str, str]:
    """Render a doughnut/pie chart.

    Args:
        data: List of {name, value} dicts, OR a plain {name: value} dict.
    """
    # Accept plain dict {name: value}, list of {name/label, value} dicts, or list of tuples
    if isinstance(data, dict):
        data = [{"name": k, "value": v} for k, v in data.items()]
    elif isinstance(data, list):
        norm = []
        for d in data:
            if isinstance(d, dict):
                name = d.get("name") or d.get("label") or str(d)
                norm.append({"name": name, "value": d.get("value", 0)})
            elif isinstance(d, (list, tuple)) and len(d) >= 2:
                norm.append({"name": str(d[0]), "value": d[1]})
            else:
                norm.append({"name": str(d), "value": 0})
        data = norm

    container = _echart_container(chart_id, height, title)

    option = {
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"bottom": 0, "textStyle": {"fontSize": 11}},
        "series": [{
            "type": "pie",
            "radius": ["40%", "70%"],
            "center": ["50%", "45%"],
            "avoidLabelOverlap": True,
            "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": True, "fontSize": 11},
            "data": [{"name": d["name"], "value": d["value"]} for d in data],
        }],
    }

    init_js = f"echarts.init(document.getElementById('{chart_id}')).setOption({json.dumps(option)});"
    return container, init_js


def render_heatmap_chart(
    chart_id: str,
    x_labels: list[str],
    y_labels: list[str],
    data: list[list],
    title: str = "",
    height: int = 400,
    value_label: str = "Position",
    invert_color: bool = False,
) -> tuple[str, str]:
    """Render a heatmap chart (e.g., keyword position changes over weeks).

    Args:
        x_labels: Column labels (e.g., week names)
        y_labels: Row labels (e.g., keyword names)
        data: List of [x_index, y_index, value] triples
        invert_color: If True, lower values are green (good for position rankings)
    """
    container = _echart_container(chart_id, height, title)

    min_val = min(d[2] for d in data) if data else 0
    max_val = max(d[2] for d in data) if data else 100

    if invert_color:
        # Lower = better (green), higher = worse (red) — for position rankings
        visual_map_colors = [COLORS["success"], "#fbbf24", COLORS["danger"]]
    else:
        visual_map_colors = [COLORS["danger"], "#fbbf24", COLORS["success"]]

    option = {
        "tooltip": {
            "position": "top",
            "formatter": f"{{b}}<br>{{c[1]}}: {{c[2]}} {value_label}",
        },
        "grid": {"left": "15%", "right": "5%", "top": "5%", "bottom": "15%"},
        "xAxis": {"type": "category", "data": x_labels, "splitArea": {"show": True}, "axisLabel": {"fontSize": 11}},
        "yAxis": {"type": "category", "data": y_labels, "splitArea": {"show": True}, "axisLabel": {"fontSize": 10}},
        "visualMap": {
            "min": min_val,
            "max": max_val,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": 0,
            "inRange": {"color": visual_map_colors},
        },
        "series": [{
            "type": "heatmap",
            "data": data,
            "label": {"show": True, "fontSize": 10},
            "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)"}},
        }],
    }

    init_js = f"echarts.init(document.getElementById('{chart_id}')).setOption({json.dumps(option)});"
    return container, init_js


def render_radar_chart(
    chart_id: str,
    indicators: list[dict],
    series: list[dict],
    title: str = "",
    height: int = 340,
) -> tuple[str, str]:
    """Render a radar chart for competitive comparison.

    Args:
        indicators: List of {name, max} dicts, OR plain strings (max defaults to 100).
        series: List of {name, data} dicts with values matching indicator order.
    """
    # Normalise indicators: accept plain strings or dicts missing 'max'
    norm_indicators = []
    for ind in indicators:
        if isinstance(ind, str):
            norm_indicators.append({"name": ind, "max": 100})
        elif isinstance(ind, dict):
            norm_indicators.append({"name": ind.get("name", str(ind)), "max": ind.get("max", 100)})
        else:
            norm_indicators.append({"name": str(ind), "max": 100})

    container = _echart_container(chart_id, height, title)

    option = {
        "tooltip": {"trigger": "item"},
        "legend": {"bottom": 0, "textStyle": {"fontSize": 11}},
        "radar": {"indicator": [{"name": i["name"], "max": i["max"]} for i in norm_indicators]},
        "series": [{
            "type": "radar",
            "data": [{"value": s["data"], "name": s["name"]} for s in series],
        }],
    }

    init_js = f"echarts.init(document.getElementById('{chart_id}')).setOption({json.dumps(option)});"
    return container, init_js


# ─── Sortable Data Table ─────────────────────────────────────────────

def render_sortable_table(
    headers: list[str],
    rows: list[list],
    table_id: str = "",
    sparkline_col: Optional[int] = None,
    highlight_col: Optional[int] = None,
    max_rows: Optional[int] = None,
    source: str = "",
    period: str = "",
    header_tooltips: Optional[list] = None,
) -> str:
    """Render a sortable HTML table with optional sparkline column and source footer.

    Args:
        headers: Column header labels
        rows: List of row data (each row is a list matching headers)
        table_id: Unique ID for the table
        sparkline_col: Column index that contains sparkline values (list of numbers)
        highlight_col: Column index to highlight with color-coded badges
        max_rows: If set, show only this many rows with an expandable "Show more" button
        source: Data source label (e.g., "GA4", "Search Console") — shown as footer
        period: Date period (e.g., "Mar 14 - Apr 14") — shown in footer
        header_tooltips: List of tooltip strings matching headers (same length as headers).
                         Each header gets an info icon with hover explanation.
    """
    tid = table_id or f"tbl_{id(rows)}"

    # Normalise header_tooltips: accept dict {header: tooltip} or list
    if isinstance(header_tooltips, dict):
        header_tooltips = [header_tooltips.get(h, "") for h in headers]

    # Normalise rows: accept list of dicts (use values in order)
    if rows and isinstance(rows[0], dict):
        rows = [list(r.values()) for r in rows]

    # Build header with optional tooltips
    _header_cells = []
    for i, h in enumerate(headers):
        tip = ""
        if header_tooltips and i < len(header_tooltips) and header_tooltips[i]:
            tip = render_tooltip_label(h, header_tooltips[i])
        else:
            tip = h
        _header_cells.append(
            f'<th onclick="sortTable(\'{tid}\',{i})" style="cursor:pointer;position:sticky;top:0;'
            f'background:{COLORS["bg_dark"]};color:#fff;padding:10px 12px;font-size:11px;'
            f'text-transform:uppercase;letter-spacing:0.04em;text-align:left;white-space:nowrap">'
            f'{tip} <span style="opacity:0.5">&#8597;</span></th>'
        )
    header_cells = "".join(_header_cells)

    # Build body rows
    visible_rows = rows[:max_rows] if max_rows else rows
    hidden_rows = rows[max_rows:] if max_rows else []

    def _format_cell(val, col_idx):
        if col_idx == sparkline_col and isinstance(val, list):
            return render_sparkline(val)
        if col_idx == highlight_col and isinstance(val, (int, float)):
            if val > 0:
                return f'<span style="color:{COLORS["success"]};font-weight:600">&#9650; {val:+.1f}%</span>'
            elif val < 0:
                return f'<span style="color:{COLORS["danger"]};font-weight:600">&#9660; {val:+.1f}%</span>'
            return f'<span style="color:{COLORS["muted"]}">0%</span>'
        if isinstance(val, float):
            return f"{val:,.2f}"
        if isinstance(val, int):
            return f"{val:,}"
        return str(val) if val is not None else "—"

    def _build_rows(row_list, hidden=False):
        style = ' style="display:none"' if hidden else ""
        cls = f' class="{tid}-hidden"' if hidden else ""
        result = ""
        for ri, row in enumerate(row_list):
            bg = "#f8fafc" if ri % 2 == 0 else "#fff"
            cells = "".join(
                f'<td style="padding:8px 12px;font-size:13px;border-bottom:1px solid {COLORS["border"]}">'
                f'{_format_cell(cell, ci)}</td>'
                for ci, cell in enumerate(row)
            )
            result += f'<tr{cls}{style} style="background:{bg}">{cells}</tr>\n'
        return result

    body_html = _build_rows(visible_rows)
    hidden_html = _build_rows(hidden_rows, hidden=True) if hidden_rows else ""

    show_more = ""
    if hidden_rows:
        show_more = (
            f'<tr id="{tid}-toggle"><td colspan="{len(headers)}" style="text-align:center;padding:10px;'
            f'cursor:pointer;color:{COLORS["primary"]};font-size:13px;font-weight:500" '
            f'onclick="document.querySelectorAll(\'.{tid}-hidden\').forEach(r=>r.style.display=\'\');'
            f'document.getElementById(\'{tid}-toggle\').style.display=\'none\'">'
            f'Show {len(hidden_rows)} more rows &#9660;</td></tr>'
        )

    # Source/period footer
    source_footer = ""
    if source or period:
        parts = []
        if source:
            parts.append(f"📊 Source: {source}")
        if period:
            parts.append(f"📅 {period}")
        source_footer = (
            f'<div style="padding:6px 12px;font-size:10px;color:{COLORS["muted"]};'
            f'background:{COLORS["bg_page"]};border-top:1px solid {COLORS["border"]}">'
            f'{" &middot; ".join(parts)}</div>'
        )

    return f"""<div style="overflow-x:auto;border-radius:8px;border:1px solid {COLORS['border']};margin-bottom:24px">
    <table id="{tid}" style="width:100%;border-collapse:collapse;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{body_html}{hidden_html}{show_more}</tbody>
    </table>{source_footer}</div>"""


# ─── Diagnosis Card ──────────────────────────────────────────────────

def render_diagnosis_card(
    observation: str,
    evidence: str,
    diagnosis: str,
    confidence: str = "Medium",
    action_chain: str = "",
    severity: str = "important",
    source: str = "",
) -> str:
    """Render a diagnosis finding card.

    Args:
        severity: "urgent", "important", "nice_to_have", "positive", "cross_skill"
        source: Data sources used (e.g., "GA4 + Meta Ads API")
    """
    colors = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["important"])
    severity_label = severity.replace("_", " ").upper()

    action_html = ""
    if action_chain:
        action_html = f"""<div style="margin-top:10px;padding-top:10px;border-top:1px solid {colors['border']}30">
            <strong style="font-size:12px">Action Chain:</strong>
            <div style="font-size:13px;margin-top:4px;line-height:1.6">{action_chain}</div>
        </div>"""

    return f"""<div style="border-left:4px solid {colors['border']};padding:16px;margin:12px 0;
        background:{colors['bg']};border-radius:0 8px 8px 0">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;
                color:{colors['text']};background:{colors['border']}20;padding:2px 8px;border-radius:4px">
                {severity_label}</span>
            <span style="font-size:11px;color:{COLORS['text_light']}">Confidence: {confidence}{f' &middot; 📊 {source}' if source else ''}</span>
        </div>
        <div style="font-size:14px;font-weight:600;color:{colors['text']};margin-bottom:6px">
            {diagnosis}</div>
        <div style="font-size:13px;color:{COLORS['text']};margin-bottom:4px">
            <strong>What happened:</strong> {observation}</div>
        <div style="font-size:13px;color:{COLORS['text_light']}">
            <strong>Evidence:</strong> {evidence}</div>
        {action_html}
    </div>"""


# ─── Creative Gallery ────────────────────────────────────────────────

def render_creative_gallery(creatives: list[dict]) -> str:
    """Render a grid of Meta ad creatives with images and performance badges.

    Args:
        creatives: List of dicts with keys: ad_name, headline, body, image_url,
                   spend, ctr, conversions, quality_ranking, status (best/ok/worst)
    """
    cards = []
    for c in creatives:
        image_url = c.get("image_url", "")
        image_html = (
            f'<img src="{image_url}" style="width:100%;height:180px;object-fit:cover;border-radius:6px 6px 0 0">'
            if image_url
            else f'<div style="width:100%;height:180px;background:{COLORS["bg_page"]};border-radius:6px 6px 0 0;'
                 f'display:flex;align-items:center;justify-content:center;color:{COLORS["muted"]}">No image</div>'
        )

        # Performance badge
        status = c.get("status", "ok")
        badge_color = COLORS["success"] if status == "best" else COLORS["danger"] if status == "worst" else COLORS["muted"]
        badge_label = "Top Performer" if status == "best" else "Underperformer" if status == "worst" else ""

        badge_html = ""
        if badge_label:
            badge_html = (
                f'<div style="position:absolute;top:8px;right:8px;background:{badge_color};color:#fff;'
                f'padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700">{badge_label}</div>'
            )

        # Quality ranking
        quality = c.get("quality_ranking", "")
        quality_html = ""
        if quality:
            qcolor = COLORS["success"] if "ABOVE" in str(quality) else COLORS["danger"] if "BELOW" in str(quality) else COLORS["muted"]
            quality_html = f'<div style="font-size:11px;color:{qcolor}">Quality: {quality}</div>'

        ctr = c.get("ctr", 0)
        spend = c.get("spend", 0)
        conversions = c.get("conversions", 0)

        cards.append(f"""<div style="background:{COLORS['bg_card']};border-radius:8px;
            box-shadow:0 1px 3px rgba(0,0,0,.08);overflow:hidden;position:relative">
            {badge_html}{image_html}
            <div style="padding:12px">
                <div style="font-size:13px;font-weight:600;margin-bottom:4px;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{c.get('headline', c.get('ad_name', ''))}</div>
                <div style="font-size:12px;color:{COLORS['text_light']};margin-bottom:8px;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{c.get('body', '')[:60]}</div>
                <div style="display:flex;gap:12px;font-size:12px">
                    <span><strong>CTR</strong> {float(ctr):.2f}%</span>
                    <span><strong>Spend</strong> ${float(spend):,.0f}</span>
                    <span><strong>Conv</strong> {conversions}</span>
                </div>
                {quality_html}
            </div>
        </div>""")

    return f"""<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;margin-bottom:24px">
        {"".join(cards)}
    </div>"""


# ─── Expandable Section ──────────────────────────────────────────────

# ─── Tooltip Label ──────────────────────────────────────────────────

def render_tooltip_label(text: str, tooltip: str) -> str:
    """Wrap a text label with an info icon and hover tooltip.

    Uses BOTH native `title` attribute (always works, never clipped) AND a custom styled
    tooltip (richer styling, may get clipped in tables/overflow contexts). Native title
    is the reliability guarantee.

    Args:
        text: The visible label text
        tooltip: Plain-language explanation shown on hover
    """
    if not tooltip:
        return text
    # Escape tooltip for use as HTML attribute value
    safe_tooltip = (tooltip.replace("&", "&amp;").replace('"', "&quot;")
                    .replace("<", "&lt;").replace(">", "&gt;"))
    uid = f"tip_{abs(hash(text + tooltip)) % 100000}"
    return (
        f'<span title="{safe_tooltip}" style="position:relative;cursor:help" '
        f'onmouseenter="var t=document.getElementById(\'{uid}\');if(t){{t.style.display=\'block\'}}" '
        f'onmouseleave="var t=document.getElementById(\'{uid}\');if(t){{t.style.display=\'none\'}}">'
        f'{text} <span style="font-size:10px;color:{COLORS["muted"]};vertical-align:super">ⓘ</span>'
        f'<div id="{uid}" style="display:none;position:absolute;bottom:calc(100% + 6px);left:0;'
        f'width:280px;max-width:90vw;padding:10px 14px;background:{COLORS["bg_dark"]};color:#e2e8f0;'
        f'border-radius:8px;font-size:12px;line-height:1.5;font-weight:400;'
        f'box-shadow:0 4px 12px rgba(0,0,0,.3);z-index:9999;text-transform:none;'
        f'letter-spacing:normal;pointer-events:none;white-space:normal">{tooltip}</div>'
        f'</span>'
    )


# ─── Score Breakdown (GEO / EEAT / SEO factor visualization) ───────

def render_score_breakdown(
    title: str,
    total_score: float,
    max_score: float,
    factors: list[dict],
    benchmark: str = "",
    benchmark_score: Optional[float] = None,
    source: str = "",
    impact_chain: str = "",
) -> str:
    """Render a visual score card with per-factor breakdown bars.

    Makes composite scores like GEO: 56/100 or EEAT: 50.6/100 transparent
    by showing each contributing factor as a horizontal progress bar.

    Args:
        title: Score name (e.g., "GEO Score", "E-E-A-T Score")
        total_score: Overall score value
        max_score: Maximum possible score
        factors: List of dicts with 'name', 'score', 'max', 'note' (optional)
                 Example: [{"name": "Citability", "score": 15, "max": 25, "note": "Missing answer blocks"}]
        benchmark: Benchmark description (e.g., "B2B SaaS industry avg")
        benchmark_score: Benchmark score value for visual comparison
        source: Data source label
        impact_chain: Plain-text impact explanation (why this score matters)
    """
    pct = round(total_score / max_score * 100) if max_score else 0
    score_color = (COLORS["danger"] if pct < 40 else
                   COLORS["warning"] if pct < 65 else
                   COLORS["success"])

    # Benchmark comparison badge
    bench_html = ""
    if benchmark and benchmark_score is not None:
        bench_pct = round(benchmark_score / max_score * 100)
        gap = round(total_score - benchmark_score, 1)
        gap_color = COLORS["success"] if gap >= 0 else COLORS["danger"]
        gap_sign = "+" if gap >= 0 else ""
        bench_html = (
            f'<div style="display:flex;align-items:center;gap:8px;margin-top:6px;flex-wrap:wrap">'
            f'<span style="font-size:11px;color:{COLORS["text_light"]}">Benchmark: '
            f'<strong>{benchmark}</strong> — {bench_pct}%</span>'
            f'<span style="font-size:11px;font-weight:600;color:{gap_color};'
            f'background:{gap_color}12;border-radius:4px;padding:1px 6px">'
            f'{gap_sign}{gap} pts vs benchmark</span>'
            f'</div>'
        )

    # Factor bars
    factor_rows = ""
    for f in factors:
        f_pct = round(f["score"] / f["max"] * 100) if f["max"] else 0
        f_color = (COLORS["danger"] if f_pct < 40 else
                   COLORS["warning"] if f_pct < 65 else
                   COLORS["success"])
        note_html = (
            f'<div style="font-size:10px;color:{COLORS["text_light"]};margin-top:1px">'
            f'{f.get("note", "")}</div>'
        ) if f.get("note") else ""

        factor_rows += f"""
        <div style="margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px">
                <span style="font-size:12px;color:{COLORS['text']};font-weight:500">{f['name']}</span>
                <span style="font-size:11px;font-weight:700;color:{f_color}">{f['score']}/{f['max']} ({f_pct}%)</span>
            </div>
            <div style="height:6px;background:{COLORS['border']};border-radius:3px;overflow:hidden">
                <div style="height:100%;width:{f_pct}%;background:{f_color};border-radius:3px;
                    transition:width .4s ease"></div>
            </div>
            {note_html}
        </div>"""

    impact_html = ""
    if impact_chain:
        impact_html = (
            f'<div style="margin-top:12px;padding:10px 14px;background:{COLORS["bg_page"]};'
            f'border-radius:6px;border-left:3px solid {score_color}">'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'color:{score_color};letter-spacing:0.06em;margin-bottom:4px">Why This Matters</div>'
            f'<div style="font-size:12px;color:{COLORS["text"]};line-height:1.5">{impact_chain}</div>'
            f'</div>'
        )

    source_html = (
        f'<div style="font-size:10px;color:{COLORS["muted"]};margin-top:8px">📊 {source}</div>'
    ) if source else ""

    return f"""<div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
        border-radius:12px;padding:18px;margin:12px 0">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:8px">
            <div style="font-size:14px;font-weight:700;color:{COLORS['text']}">{title}</div>
            <div style="display:flex;align-items:center;gap:10px">
                <div style="width:52px;height:52px;border-radius:50%;
                    background:conic-gradient({score_color} {pct * 3.6}deg, {COLORS['border']} 0deg);
                    display:flex;align-items:center;justify-content:center;
                    box-shadow:inset 0 0 0 8px {COLORS['bg_card']}">
                    <span style="font-size:13px;font-weight:700;color:{score_color}">{pct}%</span>
                </div>
                <div>
                    <div style="font-size:20px;font-weight:700;color:{COLORS['text']}">{total_score}/{int(max_score)}</div>
                    <div style="font-size:10px;color:{COLORS['text_light']}">out of {int(max_score)} pts</div>
                </div>
            </div>
        </div>
        {bench_html}
        <div style="margin-top:14px">{factor_rows}</div>
        {impact_html}
        {source_html}
    </div>"""


# ─── Message Alignment Card ─────────────────────────────────────────

def render_message_alignment_card(
    campaign: str,
    ad_promise: str,
    landing_page: str,
    audience_intent: str,
    alignment: str,
    gap: str = "",
    fix: str = "",
) -> str:
    """Render a message alignment card showing 3-way alignment for a campaign.

    Args:
        campaign: Campaign name
        ad_promise: Ad headline/promise text
        landing_page: Landing page H1 or above-fold text
        audience_intent: Targeting description (job titles / interests / etc.)
        alignment: "ALIGNED", "PARTIAL", or "MISALIGNED"
        gap: Description of the specific mismatch (if not ALIGNED)
        fix: Specific action to achieve ALIGNED status
    """
    al_map = {
        "ALIGNED": (COLORS["success"], "✅", "#ecfdf5", "#a7f3d0"),
        "PARTIAL": (COLORS["warning"], "🟡", "#fffbeb", "#fde68a"),
        "MISALIGNED": (COLORS["danger"], "🔴", "#fef2f2", "#fecaca"),
    }
    color, icon, bg, border = al_map.get(alignment.upper(), (COLORS["muted"], "⬜", COLORS["bg_page"], COLORS["border"]))

    gap_html = ""
    if gap:
        gap_html = (
            f'<div style="margin-top:10px;padding:8px 12px;background:{COLORS["bg_page"]};'
            f'border-radius:6px;border-left:3px solid {color}">'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'color:{color};letter-spacing:0.06em;margin-bottom:3px">Gap</div>'
            f'<div style="font-size:12px;color:{COLORS["text"]}">{gap}</div>'
            f'</div>'
        )
    fix_html = ""
    if fix:
        fix_html = (
            f'<div style="margin-top:6px;padding:8px 12px;background:{COLORS["success"]}08;'
            f'border-radius:6px;border-left:3px solid {COLORS["success"]}">'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'color:{COLORS["success"]};letter-spacing:0.06em;margin-bottom:3px">Fix</div>'
            f'<div style="font-size:12px;color:{COLORS["text"]}">{fix}</div>'
            f'</div>'
        )

    rows = [
        ("Ad Promise", ad_promise, "📢"),
        ("Landing Page", landing_page, "🌐"),
        ("Audience Intent", audience_intent, "🎯"),
    ]
    rows_html = ""
    for label, content, em in rows:
        rows_html += f"""
        <div style="display:grid;grid-template-columns:110px 1fr;gap:8px;
            padding:7px 0;border-bottom:1px solid {COLORS['border']}">
            <div style="font-size:11px;font-weight:600;color:{COLORS['text_light']}">{em} {label}</div>
            <div style="font-size:12px;color:{COLORS['text']};line-height:1.4">{content}</div>
        </div>"""

    return f"""<div style="background:{bg};border:1px solid {border};border-radius:10px;
        padding:14px;margin:8px 0">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
            <div style="font-size:13px;font-weight:600;color:{COLORS['text']}">{campaign}</div>
            <div style="font-size:12px;font-weight:700;color:{color};
                background:{color}20;border-radius:6px;padding:3px 10px">{icon} {alignment}</div>
        </div>
        {rows_html}
        {gap_html}
        {fix_html}
    </div>"""


# ─── Conversion Funnel with Inter-Stage Rates ──────────────────────

def render_conversion_funnel(stages: list[dict]) -> str:
    """Render a horizontal conversion funnel with inter-stage conversion rates.

    Calculates conversion rates between each consecutive stage deterministically.
    Shows: Stage (count) --[X%]--> Stage (count) chain.

    Args:
        stages: List of dicts with 'name' and 'value' keys.
                Optional 'sub' for a subtitle/source label per stage.
                Example: [
                    {"name": "Impressions", "value": 45000, "sub": "Meta Ads"},
                    {"name": "Link Clicks", "value": 945, "sub": "Meta Ads"},
                    {"name": "Landing Page Views", "value": 737, "sub": "GA4"},
                    {"name": "Leads", "value": 26, "sub": "Sourcy DB"},
                ]
    """
    if not stages:
        return '<div style="color:#94a3b8;font-size:13px;padding:12px">No funnel data available</div>'

    # Calculate inter-stage conversion rates
    enriched = []
    for i, s in enumerate(stages):
        rate = None
        if i > 0 and stages[i - 1]["value"] and stages[i - 1]["value"] > 0:
            rate = round(s["value"] / stages[i - 1]["value"] * 100, 1)
        enriched.append({"name": s["name"], "value": s.get("value", 0),
                          "sub": s.get("sub", ""), "rate": rate})

    # Width proportions (first stage = 100%, rest scaled)
    max_val = max(s["value"] for s in enriched) or 1

    html = '<div style="overflow-x:auto;padding:4px 0">'
    html += '<div style="display:flex;align-items:flex-start;gap:0;min-width:max-content">'

    for i, s in enumerate(enriched):
        width_pct = max(20, int(s["value"] / max_val * 100))
        bar_color = COLORS["series"][i % len(COLORS["series"])]

        sub_html = (
            f'<div style="font-size:10px;color:{COLORS["text_light"]};margin-top:2px">'
            f'{s["sub"]}</div>'
        ) if s["sub"] else ""

        stage_html = f"""
        <div style="display:flex;flex-direction:column;align-items:center;min-width:120px">
            <div style="font-size:12px;font-weight:600;color:{COLORS['text']};
                text-align:center;margin-bottom:6px;line-height:1.3">{s['name']}</div>
            <div style="width:100%;background:{bar_color}18;border-radius:6px;
                border:2px solid {bar_color};padding:10px 8px;text-align:center">
                <div style="font-size:18px;font-weight:700;color:{bar_color}">
                    {s['value']:,}</div>
                {sub_html}
            </div>
        </div>"""

        html += stage_html

        # Arrow + conversion rate connector
        if i < len(enriched) - 1:
            next_rate = enriched[i + 1]["rate"]
            rate_color = COLORS["danger"] if (next_rate and next_rate < 5) else \
                         COLORS["warning"] if (next_rate and next_rate < 20) else \
                         COLORS["success"]
            rate_label = f"{next_rate}%" if next_rate is not None else "—"

            html += f"""
            <div style="display:flex;flex-direction:column;align-items:center;
                justify-content:center;padding:0 6px;min-width:64px;padding-top:36px">
                <div style="font-size:12px;font-weight:700;color:{rate_color};
                    background:{rate_color}15;border:1px solid {rate_color}40;
                    border-radius:10px;padding:2px 8px;white-space:nowrap;margin-bottom:4px">
                    {rate_label}</div>
                <div style="font-size:18px;color:{COLORS['muted']}">→</div>
            </div>"""

    html += '</div></div>'

    # Summary row: overall funnel conversion
    if len(enriched) >= 2 and enriched[0]["value"] and enriched[-1]["value"]:
        overall = round(enriched[-1]["value"] / enriched[0]["value"] * 100, 2)
        html += (
            f'<div style="margin-top:10px;padding:8px 12px;background:{COLORS["bg_page"]};'
            f'border-radius:6px;font-size:12px;color:{COLORS["text_light"]}">'
            f'Overall funnel: <strong style="color:{COLORS["text"]}">{enriched[0]["name"]}</strong> → '
            f'<strong style="color:{COLORS["text"]}">{enriched[-1]["name"]}</strong>: '
            f'<strong style="color:{COLORS["primary"]}">{overall}%</strong> end-to-end conversion'
            f'</div>'
        )

    return html


# ─── Reasoning Chain Block ─────────────────────────────────────────

def render_reasoning_chain(
    issue: str,
    what_happened: str,
    why_it_matters: str,
    root_cause: str,
    action: str,
    confidence: str = "High",
    priority_score: str = "",
) -> str:
    """Render a 5-step reasoning chain card for recommendations.

    Shows: Issue → What Happened → Why It Matters → Root Cause → Action
    as a vertically connected flow, color-coded by severity.

    Args:
        issue: What is wrong with numbers (Step 1)
        what_happened: The change/state with timeline (Step 2)
        why_it_matters: Business impact in $ or leads (Step 3)
        root_cause: The mechanism/underlying cause (Step 4)
        action: Specific executable action with IDs/URLs (Step 5)
        confidence: High / Medium / Low
        priority_score: Priority score string e.g. "8 × 9 × 10 = 720"
    """
    conf_color = {
        "High": COLORS["success"],
        "Medium": COLORS["warning"],
        "Low": COLORS["danger"],
    }.get(confidence, COLORS["muted"])

    priority_badge = ""
    if priority_score:
        priority_badge = (
            f'<span style="font-size:11px;font-weight:600;padding:3px 10px;'
            f'border-radius:12px;background:{COLORS["primary"]}15;color:{COLORS["primary"]};'
            f'border:1px solid {COLORS["primary"]}30">Priority: {priority_score}</span>'
        )

    conf_badge = (
        f'<span style="font-size:11px;font-weight:600;padding:3px 10px;'
        f'border-radius:12px;background:{conf_color}15;color:{conf_color};'
        f'border:1px solid {conf_color}30">Confidence: {confidence}</span>'
    )

    steps = [
        ("1", "ISSUE", issue, COLORS["danger"], "#fef2f2", "#fecaca"),
        ("2", "WHAT HAPPENED", what_happened, "#7c3aed", "#f5f3ff", "#ddd6fe"),
        ("3", "WHY IT MATTERS", why_it_matters, COLORS["warning"], "#fffbeb", "#fde68a"),
        ("4", "ROOT CAUSE", root_cause, COLORS["info"], "#eef2ff", "#c7d2fe"),
        ("5", "ACTION", action, COLORS["success"], "#ecfdf5", "#a7f3d0"),
    ]

    steps_html = ""
    for i, (num, label, content, color, bg, border) in enumerate(steps):
        connector = ""
        if i < len(steps) - 1:
            connector = (
                f'<div style="display:flex;justify-content:center;margin:0">'
                f'<div style="width:2px;height:16px;background:{COLORS["border"]}"></div>'
                f'</div>'
                f'<div style="display:flex;justify-content:center;margin:0 0 0">'
                f'<svg width="16" height="10" viewBox="0 0 16 10" fill="none" style="display:block">'
                f'<path d="M8 10 L0 0 L16 0 Z" fill="{COLORS["border"]}"/></svg>'
                f'</div>'
            )

        steps_html += f"""
        <div style="border:1px solid {border};border-radius:8px;padding:12px 14px;background:{bg}">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                <div style="width:22px;height:22px;border-radius:50%;background:{color};
                    color:#fff;font-size:11px;font-weight:700;display:flex;align-items:center;
                    justify-content:center;flex-shrink:0">{num}</div>
                <div style="font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.08em;color:{color}">{label}</div>
            </div>
            <div style="font-size:13px;color:{COLORS['text']};line-height:1.6;
                padding-left:30px">{content}</div>
        </div>{connector}"""

    return f"""<div style="border:1px solid {COLORS['border']};border-radius:12px;
        padding:18px;margin:14px 0;background:{COLORS['bg_card']};
        box-shadow:0 1px 4px rgba(0,0,0,.05)">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap">
            <div style="font-size:13px;font-weight:600;color:{COLORS['text']}">Reasoning Chain</div>
            {priority_badge}
            {conf_badge}
        </div>
        {steps_html}
    </div>"""


# ─── Before → After Block ──────────────────────────────────────────

def render_before_after(
    before: str,
    after: str,
    reasoning: str,
    context: str = "",
    expected_impact: str = "",
) -> str:
    """Render a visual before/after comparison block for recommendations.

    Args:
        before: Current text/setting (quoted verbatim)
        after: Proposed replacement (actual new text)
        reasoning: Why this change improves things
        context: What element this refers to (e.g., "Page title on /sourcing/scams")
        expected_impact: Expected metric improvement (e.g., "+15-25% CTR")
    """
    impact_badge = ""
    if expected_impact:
        impact_badge = (
            f'<span style="background:{COLORS["success"]}20;color:{COLORS["success"]};'
            f'font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;'
            f'position:absolute;top:12px;right:12px">{expected_impact}</span>'
        )

    context_html = ""
    if context:
        context_html = (
            f'<div style="font-size:11px;color:{COLORS["text_light"]};margin-bottom:10px;'
            f'font-weight:500">{context}</div>'
        )

    return f"""<div style="position:relative;border:1px solid {COLORS['border']};
        border-radius:10px;padding:16px;margin:12px 0;background:{COLORS['bg_card']}">
        {impact_badge}{context_html}
        <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:start">
            <!-- BEFORE -->
            <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:12px">
                <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#991b1b;
                    letter-spacing:0.05em;margin-bottom:6px">BEFORE</div>
                <div style="font-size:13px;color:#1e293b;text-decoration:line-through;
                    text-decoration-color:#ef4444;line-height:1.5">{before}</div>
            </div>
            <!-- Arrow -->
            <div style="display:flex;align-items:center;padding-top:24px;font-size:20px;
                color:{COLORS['muted']}">→</div>
            <!-- AFTER -->
            <div style="background:#ecfdf5;border:1px solid #a7f3d0;border-radius:8px;padding:12px">
                <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#065f46;
                    letter-spacing:0.05em;margin-bottom:6px">AFTER</div>
                <div style="font-size:13px;color:#1e293b;font-weight:500;line-height:1.5">{after}</div>
            </div>
        </div>
        <!-- WHY -->
        <div style="margin-top:12px;padding:10px 14px;background:{COLORS['bg_page']};
            border-radius:6px;border-left:3px solid {COLORS['primary']}">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:{COLORS['primary']};
                letter-spacing:0.05em;margin-bottom:3px">WHY THIS IS BETTER</div>
            <div style="font-size:12px;color:{COLORS['text']};line-height:1.5">{reasoning}</div>
        </div>
    </div>"""


# ─── Action Steps Block ─────────────────────────────────────────────

def render_action_steps(
    title: str,
    platform: str,
    time_estimate: str,
    steps: list[str],
    skill_level: str = "Anyone",
    definitions: Optional[dict] = None,
    done_state: str = "",
    verification: str = "",
) -> str:
    """Render a step-by-step action card that a non-expert can follow.

    Args:
        title: Action title
        platform: Where to do it (e.g., "Google Ads", "Meta Ads Manager")
        time_estimate: How long (e.g., "~10 minutes")
        steps: Numbered step instructions
        skill_level: Required expertise (e.g., "Anyone", "Needs ad account access")
        definitions: Dict of term → plain-language definition
        done_state: What the screen looks like when done
        verification: How to verify the action worked + expected metric change
    """
    # Header badges
    platform_icon = {"Google Ads": "🔍", "Meta Ads Manager": "📘", "GA4": "📊",
                     "Search Console": "🔎", "sourcy.ai CMS": "🌐"}.get(platform, "⚙️")
    skill_color = {"Anyone": COLORS["success"], "Needs ad account access": COLORS["warning"],
                   "Needs developer": COLORS["danger"]}.get(skill_level, COLORS["muted"])

    header = (
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:14px">'
        f'<span style="font-size:14px;font-weight:600;color:{COLORS["text"]}">{title}</span>'
        f'<span style="font-size:11px;padding:3px 8px;border-radius:4px;background:{COLORS["bg_page"]};'
        f'border:1px solid {COLORS["border"]}">{platform_icon} {platform}</span>'
        f'<span style="font-size:11px;padding:3px 8px;border-radius:4px;background:{COLORS["bg_page"]};'
        f'border:1px solid {COLORS["border"]}">⏱ {time_estimate}</span>'
        f'<span style="font-size:11px;padding:3px 8px;border-radius:4px;background:{skill_color}15;'
        f'color:{skill_color};border:1px solid {skill_color}30">{skill_level}</span>'
        f'</div>'
    )

    # Steps
    steps_html = ""
    for i, step in enumerate(steps, 1):
        steps_html += (
            f'<div style="display:flex;gap:10px;margin-bottom:8px">'
            f'<div style="width:24px;height:24px;border-radius:50%;background:{COLORS["primary"]};'
            f'color:#fff;display:flex;align-items:center;justify-content:center;'
            f'font-size:12px;font-weight:600;flex-shrink:0">{i}</div>'
            f'<div style="font-size:13px;line-height:1.6;padding-top:2px">{step}</div>'
            f'</div>'
        )

    # Definitions (collapsible)
    defs_html = ""
    if definitions:
        # Accept list of {term, definition} dicts OR a plain dict
        if isinstance(definitions, list):
            pairs = [(d.get("term", d.get("name", str(d))), d.get("definition", d.get("desc", ""))) for d in definitions if isinstance(d, dict)]
        else:
            pairs = list(definitions.items())
        defs_items = "".join(
            f'<div style="margin-bottom:6px"><strong style="color:{COLORS["text"]}">{term}</strong>: '
            f'<span style="color:{COLORS["text_light"]}">{defn}</span></div>'
            for term, defn in pairs
        )
        uid = f"defs_{abs(hash(title)) % 100000}"
        defs_html = (
            f'<div style="margin-top:12px;border-top:1px solid {COLORS["border"]};padding-top:10px">'
            f'<div onclick="var d=document.getElementById(\'{uid}\');d.style.display=d.style.display===\'none\'?\'block\':\'none\'"'
            f' style="cursor:pointer;font-size:12px;font-weight:600;color:{COLORS["primary"]}">'
            f'📖 Key terms explained ▾</div>'
            f'<div id="{uid}" style="display:none;margin-top:8px;font-size:12px;line-height:1.6">'
            f'{defs_items}</div></div>'
        )

    # Done state
    done_html = ""
    if done_state:
        done_html = (
            f'<div style="margin-top:12px;padding:10px 14px;background:#ecfdf5;'
            f'border-radius:6px;border-left:3px solid {COLORS["success"]}">'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'color:{COLORS["success"]};letter-spacing:0.05em;margin-bottom:3px">WHAT "DONE" LOOKS LIKE</div>'
            f'<div style="font-size:12px;color:{COLORS["text"]}">{done_state}</div>'
            f'</div>'
        )

    # Verification
    verify_html = ""
    if verification:
        verify_html = (
            f'<div style="margin-top:8px;padding:10px 14px;background:#eff6ff;'
            f'border-radius:6px;border-left:3px solid {COLORS["primary"]}">'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'color:{COLORS["primary"]};letter-spacing:0.05em;margin-bottom:3px">HOW TO VERIFY</div>'
            f'<div style="font-size:12px;color:{COLORS["text"]}">{verification}</div>'
            f'</div>'
        )

    return f"""<div style="border:1px solid {COLORS['border']};border-radius:10px;
        padding:16px;margin:12px 0;background:{COLORS['bg_card']}">
        {header}{steps_html}{defs_html}{done_html}{verify_html}
    </div>"""


# ─── Action Item with Ownership ────────────────────────────────────

def render_action_item(
    title: str,
    priority_score: float,
    owner: str,
    timeline: str,
    expected_outcome: str,
    platform: str,
    steps: list[str],
    status: str = "Not Started",
    skill_level: str = "Anyone",
    definitions: Optional[dict] = None,
    done_state: str = "",
    verification: str = "",
    time_estimate: str = "",
) -> str:
    """Render an action item with ownership metadata + step-by-step instructions.

    Wraps render_action_steps with a header row showing priority, owner, timeline,
    expected outcome, and status — making recommendations immediately executable
    with clear accountability.

    Args:
        title: Action title
        priority_score: Numeric priority score (higher = more urgent)
        owner: Who should do this (e.g., "Marketing Lead", "Developer", "Anyone")
        timeline: When to do it (e.g., "This week", "By April 30", "This month")
        expected_outcome: Specific metric improvement (e.g., "Save ~$900/month")
        platform: Where to do it (e.g., "Meta Ads Manager", "GA4")
        steps: Step-by-step instructions
        status: Current status ("Not Started", "In Progress", "Done")
        skill_level: Required expertise level
        definitions: Dict of term → definition
        done_state: What done looks like
        verification: How to verify it worked
        time_estimate: Time to complete (e.g., "~10 minutes")
    """
    # Priority badge color
    if priority_score >= 500:
        pri_color, pri_label = COLORS["danger"], "⚡ High Priority"
    elif priority_score >= 200:
        pri_color, pri_label = COLORS["warning"], "📅 Medium Priority"
    else:
        pri_color, pri_label = COLORS["muted"], "🎯 Long-term"

    # Status badge
    status_colors = {
        "Not Started": (COLORS["muted"], "#f8fafc"),
        "In Progress": (COLORS["warning"], "#fffbeb"),
        "Done": (COLORS["success"], "#ecfdf5"),
    }
    st_color, st_bg = status_colors.get(status, (COLORS["muted"], "#f8fafc"))

    header = f"""<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
        gap:8px;padding:12px 14px;background:{COLORS['bg_page']};border-radius:8px;
        border:1px solid {COLORS['border']};margin-bottom:12px">
        <div>
            <div style="font-size:10px;text-transform:uppercase;font-weight:600;
                color:{COLORS['text_light']};letter-spacing:0.06em;margin-bottom:3px">Priority</div>
            <div style="font-size:12px;font-weight:700;color:{pri_color}">{pri_label} ({priority_score})</div>
        </div>
        <div>
            <div style="font-size:10px;text-transform:uppercase;font-weight:600;
                color:{COLORS['text_light']};letter-spacing:0.06em;margin-bottom:3px">Owner</div>
            <div style="font-size:12px;font-weight:600;color:{COLORS['text']}">{owner}</div>
        </div>
        <div>
            <div style="font-size:10px;text-transform:uppercase;font-weight:600;
                color:{COLORS['text_light']};letter-spacing:0.06em;margin-bottom:3px">Timeline</div>
            <div style="font-size:12px;font-weight:600;color:{COLORS['text']}">{timeline}</div>
        </div>
        <div>
            <div style="font-size:10px;text-transform:uppercase;font-weight:600;
                color:{COLORS['text_light']};letter-spacing:0.06em;margin-bottom:3px">Expected Outcome</div>
            <div style="font-size:12px;font-weight:600;color:{COLORS['success']}">{expected_outcome}</div>
        </div>
        <div>
            <div style="font-size:10px;text-transform:uppercase;font-weight:600;
                color:{COLORS['text_light']};letter-spacing:0.06em;margin-bottom:3px">Status</div>
            <div style="font-size:12px;font-weight:600;color:{st_color};
                background:{st_bg};border-radius:4px;padding:1px 8px;
                display:inline-block">{status}</div>
        </div>
    </div>"""

    steps_card = render_action_steps(
        title=title,
        platform=platform,
        time_estimate=time_estimate or "~15 minutes",
        steps=steps,
        skill_level=skill_level,
        definitions=definitions,
        done_state=done_state,
        verification=verification,
    )

    return f"""<div style="border:1px solid {pri_color}40;border-radius:12px;
        padding:16px;margin:14px 0;background:{COLORS['bg_card']};
        border-left:4px solid {pri_color}">
        {header}
        {steps_card}
    </div>"""


# ─── Expandable Section ─────────────────────────────────────────────

def render_expandable(summary: str, detail_html: str, expanded: bool = False) -> str:
    """Render a click-to-expand accordion section."""
    uid = f"exp_{id(summary)}"
    display = "block" if expanded else "none"
    arrow = "&#9660;" if expanded else "&#9654;"

    return f"""<div style="border:1px solid {COLORS['border']};border-radius:8px;margin-bottom:12px;overflow:hidden">
        <div onclick="var d=document.getElementById('{uid}');d.style.display=d.style.display==='none'?'block':'none';
            this.querySelector('.arrow').innerHTML=d.style.display==='none'?'&#9654;':'&#9660;'"
            style="padding:12px 16px;cursor:pointer;background:{COLORS['bg_page']};
            display:flex;align-items:center;gap:8px;font-size:14px;font-weight:500">
            <span class="arrow" style="font-size:10px">{arrow}</span>{summary}
        </div>
        <div id="{uid}" style="display:{display};padding:16px;border-top:1px solid {COLORS['border']}">
            {detail_html}
        </div>
    </div>"""


# ─── So What Section ────────────────────────────────────────────────

def render_so_what(urgency: str, message: str, actions: list[str]) -> str:
    """Render a 'What This Means for Sourcy' insight box.

    Args:
        urgency: "urgent", "important", "nice_to_have"
        message: Plain English explanation
        actions: List of specific action items
    """
    colors = SEVERITY_COLORS.get(urgency, SEVERITY_COLORS["important"])
    label = urgency.replace("_", " ").upper()

    actions_html = ""
    if actions:
        items = "".join(f'<li style="margin-bottom:4px">{a}</li>' for a in actions)
        actions_html = f'<ol style="margin:8px 0 0 0;padding-left:20px;font-size:13px">{items}</ol>'

    return f"""<div style="background:{colors['bg']};border:1px solid {colors['border']}30;
        border-radius:8px;padding:16px;margin:16px 0">
        <div style="font-size:14px;font-weight:600;color:{colors['text']};margin-bottom:6px">
            [{label}] What This Means for Sourcy</div>
        <div style="font-size:13px;color:{COLORS['text']};line-height:1.6">{message}</div>
        {actions_html}
    </div>"""


# ─── Decision Summary (Semrush-style "Biggest Problem" box) ─────────

def render_decision_summary(
    title: str,
    root_cause: str,
    action: str,
    confidence: str = "High",
    severity: str = "urgent",
    source: str = "",
) -> str:
    """Render a prominent 'Biggest Problem' decision summary card.
    Appears at the top of the Overview tab, Semrush-style.

    Args:
        title: Short problem title (e.g., "Conversion rate dropped 22% this week")
        root_cause: Why it happened (specific, not vague)
        action: What to do about it (specific campaign/page/action)
        confidence: "High", "Medium", "Low"
        severity: "urgent", "important", etc.
        source: Data sources (e.g., "GA4 + Google Ads")
    """
    colors = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["urgent"])
    severity_label = severity.replace("_", " ").upper()

    return f"""<div style="border:2px solid {colors['border']};border-radius:12px;padding:20px;
        margin-bottom:24px;background:{colors['bg']};display:flex;gap:20px">
        <div style="flex:1">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <span style="font-size:11px;font-weight:700;text-transform:uppercase;
                    background:{colors['border']};color:#fff;padding:3px 10px;border-radius:4px">
                    {severity_label}</span>
                <span style="font-size:11px;color:{COLORS['text_light']}">Confidence: {confidence}</span>
            </div>
            <h3 style="font-size:16px;font-weight:700;color:{colors['text']};margin:0 0 10px">{title}</h3>
            <div style="margin-bottom:8px">
                <div style="font-size:11px;font-weight:600;text-transform:uppercase;color:{COLORS['text_light']};
                    letter-spacing:0.04em;margin-bottom:3px">ROOT CAUSE</div>
                <div style="font-size:13px;color:{COLORS['text']};line-height:1.5">{root_cause}</div>
            </div>
            <div style="margin-bottom:8px">
                <div style="font-size:11px;font-weight:600;text-transform:uppercase;color:{COLORS['text_light']};
                    letter-spacing:0.04em;margin-bottom:3px">RECOMMENDED ACTION</div>
                <div style="font-size:13px;color:{COLORS['text']};line-height:1.5">{action}</div>
            </div>
            {'<div style="font-size:10px;color:' + COLORS["muted"] + ';margin-top:8px">📊 Based on: ' + source + '</div>' if source else ''}
        </div>
    </div>"""


# ─── G4: Tracking Status Banner ──────────────────────────────────────

def render_tracking_banner(
    severity: str,
    message: str,
    affected_metrics: list[str] | None = None,
) -> str:
    """Render a sticky data-quality warning at the top of any tab.

    Use this whenever tracking gaps mean a metric is unreliable or missing.
    Satisfies R7 — tracking issues must be visible, not buried in footnotes.

    Args:
        severity: "error" (data missing) | "warning" (partial data) | "info" (minor gap)
        message: Plain-English description of the tracking issue
        affected_metrics: List of metric names impacted (e.g. ["CVR", "CPL"])
    """
    style_map = {
        "error":   {"bg": "#fef2f2", "border": "#ef4444", "icon": "🔴", "label": "DATA GAP"},
        "warning": {"bg": "#fffbeb", "border": "#f59e0b", "icon": "⚠️", "label": "TRACKING ISSUE"},
        "info":    {"bg": "#eff6ff", "border": "#3b82f6", "icon": "ℹ️",  "label": "NOTE"},
    }
    s = style_map.get(severity, style_map["warning"])
    affected_html = ""
    if affected_metrics:
        tags = "".join(
            f'<span style="display:inline-block;padding:1px 8px;border-radius:4px;'
            f'background:{s["border"]}22;color:{s["border"]};font-size:11px;'
            f'font-weight:600;margin-right:4px">{m}</span>'
            for m in affected_metrics
        )
        affected_html = f'<div style="margin-top:6px">Affects: {tags}</div>'

    return (
        f'<div style="display:flex;align-items:flex-start;gap:12px;padding:12px 16px;'
        f'background:{s["bg"]};border:1px solid {s["border"]}44;border-left:4px solid {s["border"]};'
        f'border-radius:6px;margin:0 0 16px">'
        f'<span style="font-size:16px;flex-shrink:0;margin-top:1px">{s["icon"]}</span>'
        f'<div style="flex:1">'
        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
        f'color:{s["border"]};letter-spacing:0.06em;margin-bottom:2px">{s["label"]}</div>'
        f'<div style="font-size:13px;color:{COLORS["text"]};line-height:1.5">{message}</div>'
        f'{affected_html}'
        f'</div></div>'
    )


# ─── G5: Decision Table (forced Observation / Interpretation / Decision cols) ─

def render_decision_table(rows: list[dict]) -> str:
    """Render a structured 3-column decision table.

    Each row MUST have: observation, interpretation, decision.
    Optional: severity ("urgent" | "important" | "nice_to_have" | "positive"),
              metric (short name shown as a row badge).

    Satisfies R5 — prevents narrative decisions buried in prose.

    Args:
        rows: List of dicts with keys:
              - metric (str): e.g. "CAC", "Bounce Rate"
              - observation (str): What the data shows
              - interpretation (str): What it means / root cause
              - decision (str): Specific recommended action
              - severity (str, optional): colours the row badge
    """
    if not rows:
        return ""

    header = (
        f'<tr style="background:{COLORS["bg_dark"]};color:#fff">'
        f'<th style="padding:10px 14px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em;width:120px">Signal</th>'
        f'<th style="padding:10px 14px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em">Observation</th>'
        f'<th style="padding:10px 14px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em">Interpretation</th>'
        f'<th style="padding:10px 14px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em">Decision / Action</th>'
        f'</tr>'
    )

    body_rows = []
    for row in rows:
        sev = row.get("severity", "important")
        colors = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["important"])
        metric_badge = ""
        if row.get("metric"):
            metric_badge = (
                f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;'
                f'background:{colors["border"]}22;color:{colors["border"]};'
                f'font-size:11px;font-weight:700">{row["metric"]}</span>'
            )
        body_rows.append(
            f'<tr style="border-bottom:1px solid {COLORS["border"]}">'
            f'<td style="padding:10px 14px;vertical-align:top">{metric_badge}</td>'
            f'<td style="padding:10px 14px;font-size:13px;color:{COLORS["text"]};'
            f'line-height:1.5;vertical-align:top">{row.get("observation","")}</td>'
            f'<td style="padding:10px 14px;font-size:13px;color:{COLORS["text"]};'
            f'line-height:1.5;vertical-align:top">{row.get("interpretation","")}</td>'
            f'<td style="padding:10px 14px;font-size:13px;font-weight:500;'
            f'color:{colors["text"]};line-height:1.5;vertical-align:top">'
            f'{row.get("decision","")}</td>'
            f'</tr>'
        )

    return (
        f'<div style="overflow-x:auto;margin:16px 0;border-radius:8px;'
        f'border:1px solid {COLORS["border"]};box-shadow:0 1px 3px rgba(0,0,0,.06)">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead>{header}</thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        f'</table></div>'
    )


# ─── G6: Exec Summary Table (canonical 5-area overview) ─────────────

_EXEC_SUMMARY_AREAS = ["Paid Acquisition", "Organic / SEO", "CRO / On-site", "Brand & Social", "Product Analytics"]

def render_exec_summary_table(areas: list[dict]) -> str:
    """Render a canonical 5-area executive summary table for the Overview tab.

    Forces consistent structure across every report. Each row maps one strategic
    area to a RAG status, headline number, WoW/MoM delta, and one-line verdict.
    Satisfies R9 — exec summary is a table, not a paragraph.

    Args:
        areas: List of dicts (up to 5, one per canonical area):
               - area (str): matches one of the 5 canonical areas
               - status (str): "green" | "amber" | "red"
               - headline (str): Top-line metric value (e.g. "€42 CPL")
               - delta (str): WoW or MoM change (e.g. "+8% WoW")
               - delta_dir (str): "up_good" | "up_bad" | "down_good" | "down_bad" | "neutral"
               - verdict (str): One-line plain-English assessment
    """
    if not areas:
        return ""

    rag = {
        "green": {"dot": "#10b981", "bg": "#ecfdf5", "label": "On Track"},
        "amber": {"dot": "#f59e0b", "bg": "#fffbeb", "label": "Monitor"},
        "red":   {"dot": "#ef4444", "bg": "#fef2f2", "label": "Action Needed"},
    }
    delta_colors = {
        "up_good":   "#10b981",
        "down_good": "#10b981",
        "up_bad":    "#ef4444",
        "down_bad":  "#ef4444",
        "neutral":   "#94a3b8",
    }

    area_map = {a.get("area", ""): a for a in areas}

    header = (
        f'<tr style="background:{COLORS["bg_dark"]};color:#fff">'
        f'<th style="padding:10px 16px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em;width:180px">Area</th>'
        f'<th style="padding:10px 16px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em;width:90px">Status</th>'
        f'<th style="padding:10px 16px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em;width:120px">Headline</th>'
        f'<th style="padding:10px 16px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em;width:100px">Change</th>'
        f'<th style="padding:10px 16px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em">Verdict</th>'
        f'</tr>'
    )

    body_rows = []
    for area_name in _EXEC_SUMMARY_AREAS:
        row = area_map.get(area_name, {})
        status = row.get("status", "amber")
        r = rag.get(status, rag["amber"])
        delta_dir = row.get("delta_dir", "neutral")
        dc = delta_colors.get(delta_dir, "#94a3b8")
        delta_arrow = {"up_good": "▲", "up_bad": "▲", "down_good": "▼", "down_bad": "▼"}.get(delta_dir, "—")

        body_rows.append(
            f'<tr style="background:{r["bg"]};border-bottom:1px solid {COLORS["border"]}">'
            f'<td style="padding:10px 16px;font-weight:600;font-size:13px;color:{COLORS["text"]}">'
            f'{area_name}</td>'
            f'<td style="padding:10px 16px">'
            f'<span style="display:inline-flex;align-items:center;gap:5px;font-size:12px;'
            f'font-weight:600;color:{r["dot"]}">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{r["dot"]};'
            f'flex-shrink:0;display:inline-block"></span>{r["label"]}</span></td>'
            f'<td style="padding:10px 16px;font-size:14px;font-weight:700;color:{COLORS["text"]}">'
            f'{row.get("headline","—")}</td>'
            f'<td style="padding:10px 16px;font-size:13px;font-weight:600;color:{dc}">'
            f'{delta_arrow} {row.get("delta","—")}</td>'
            f'<td style="padding:10px 16px;font-size:13px;color:{COLORS["text"]};line-height:1.5">'
            f'{row.get("verdict","No data available for this period.")}</td>'
            f'</tr>'
        )

    return (
        f'<div id="exec-summary" style="overflow-x:auto;margin:16px 0;border-radius:8px;'
        f'border:1px solid {COLORS["border"]};box-shadow:0 1px 3px rgba(0,0,0,.06)">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead>{header}</thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        f'</table></div>'
    )


def render_comparison_header(current_period: str, previous_period: str = "") -> str:
    """Render a comparison period badge for the page header.

    Args:
        current_period: Current analysis period (e.g., "Mar 14 - Apr 14, 2026")
        previous_period: Comparison period (e.g., "Feb 14 - Mar 14, 2026")
    """
    if previous_period:
        return (
            f'<div style="display:inline-flex;align-items:center;gap:8px;background:#1e293b;'
            f'padding:6px 14px;border-radius:20px;font-size:12px;color:#e2e8f0;margin-top:8px">'
            f'<span>📅</span>'
            f'<span style="font-weight:600">{current_period}</span>'
            f'<span style="color:#64748b">vs</span>'
            f'<span style="color:#94a3b8">{previous_period}</span>'
            f'</div>'
        )
    return (
        f'<div style="display:inline-flex;align-items:center;gap:8px;background:#1e293b;'
        f'padding:6px 14px;border-radius:20px;font-size:12px;color:#e2e8f0;margin-top:8px">'
        f'<span>📅</span>'
        f'<span style="font-weight:600">{current_period}</span>'
        f'</div>'
    )


# ─── Tab Container ───────────────────────────────────────────────────

def render_tab_section(tab_id: str, content_html: str) -> str:
    """Wrap content in a tab panel div."""
    return f'<div id="tab-{tab_id}" class="tab-content" style="display:none">{content_html}</div>'


def render_tab_bar(tabs: list[dict]) -> str:
    """Render the tab navigation bar.

    Args:
        tabs: List of {id, label, icon?} dicts.
    """
    buttons = []
    for i, tab in enumerate(tabs):
        active = "active" if i == 0 else ""
        icon = tab.get("icon", "")
        icon_html = f'<span style="margin-right:4px">{icon}</span>' if icon else ""
        buttons.append(
            f'<button class="tab-btn {active}" onclick="switchTab(this,\'{tab["id"]}\')"'
            f' style="padding:10px 20px;border:none;background:{COLORS["bg_dark"] if i == 0 else "transparent"};'
            f'color:{"#fff" if i == 0 else COLORS["text_light"]};cursor:pointer;font-size:13px;'
            f'font-weight:500;border-radius:6px;white-space:nowrap">{icon_html}{tab["label"]}</button>'
        )

    return f"""<div style="display:flex;gap:4px;overflow-x:auto;padding:8px;background:{COLORS['bg_page']};
        border-radius:8px;margin-bottom:20px;border:1px solid {COLORS['border']}">{"".join(buttons)}</div>"""


# ─── Full Page Assembly ──────────────────────────────────────────────

def render_full_page(
    title: str,
    period: str,
    tab_bar_html: str,
    tabs_html: list[str],
    chart_init_js: list[str],
    first_tab_id: str = "overview",
) -> str:
    """Assemble a complete self-contained HTML page.

    Args:
        title: Report title
        period: Date range string
        tab_bar_html: Output of render_tab_bar()
        tabs_html: List of tab panel HTML strings (output of render_tab_section())
        chart_init_js: List of ECharts init JavaScript strings
        first_tab_id: ID of the default visible tab
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Make first tab visible
    # Accept both a list of tab HTML strings and a pre-joined string
    all_tabs = tabs_html if isinstance(tabs_html, str) else "\n".join(tabs_html)
    all_tabs = all_tabs.replace(
        f'id="tab-{first_tab_id}" class="tab-content" style="display:none"',
        f'id="tab-{first_tab_id}" class="tab-content" style="display:block"',
    )

    # ── Structural guarantees (G4+G6): inject missing components into every report ──
    # Define tab opener once — used by both R18 and R9 inject logic
    _tab_open = f'id="tab-{first_tab_id}" class="tab-content" style="display:block">'

    # R18 — Tracking banner: inject at the very top of the first tab if missing
    # Check for all three severity labels (DATA GAP, TRACKING ISSUE, NOTE) to avoid double-inject
    _has_tracking = any(kw in all_tabs for kw in ["DATA GAP", "TRACKING ISSUE", "NOTE"])
    _default_banner = ""
    if not _has_tracking:
        _default_banner = render_tracking_banner(
            "warning",
            "GA4 conversion tracking has a known gap — conversion metrics (CVR, CPL, Conversions) "
            "may be 0 or unreliable. Engagement metrics shown in this report are unaffected.",
            ["CVR", "Conversions", "CPL"],
        )
        # Insert banner immediately after the opening div of the first tab
        if _tab_open in all_tabs:
            all_tabs = all_tabs.replace(_tab_open, _tab_open + _default_banner, 1)

    # R9 — Exec summary: inject a minimal amber-filled table if missing
    _has_exec = "exec-summary" in all_tabs
    if not _has_exec:
        _default_exec = render_exec_summary_table([
            {"area": "Paid Acquisition",    "status": "amber", "headline": "See report for details", "delta": "", "delta_dir": "neutral", "verdict": "Check individual tabs"},
            {"area": "Organic / SEO",       "status": "amber", "headline": "See report for details", "delta": "", "delta_dir": "neutral", "verdict": "Check individual tabs"},
            {"area": "CRO / On-site",       "status": "amber", "headline": "See report for details", "delta": "", "delta_dir": "neutral", "verdict": "Check individual tabs"},
            {"area": "Brand & Social",      "status": "amber", "headline": "See report for details", "delta": "", "delta_dir": "neutral", "verdict": "Check individual tabs"},
            {"area": "Product Analytics",   "status": "amber", "headline": "See report for details", "delta": "", "delta_dir": "neutral", "verdict": "Check individual tabs"},
        ])
        # Insert exec summary after the injected banner (if any) or directly after tab open
        # _default_banner is "" when _has_tracking=True (LLM provided banner), so this is always safe
        _insert_marker = _tab_open + _default_banner
        if _insert_marker in all_tabs:
            all_tabs = all_tabs.replace(
                _insert_marker,
                _insert_marker + _default_exec, 1
            )

    # Accept both a list of JS strings and a pre-joined string
    all_chart_js = chart_init_js if isinstance(chart_init_js, str) else "\n".join(chart_init_js)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: {COLORS['bg_page']}; color: {COLORS['text']}; font-size: 14px; line-height: 1.6; }}
.header {{ background: linear-gradient(135deg, {COLORS['bg_dark']}, #1e3a5f);
    color: #fff; padding: 24px 32px; }}
.header h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 4px; }}
.header .period {{ font-size: 13px; opacity: 0.7; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
.tab-btn.active {{ background: {COLORS['bg_dark']} !important; color: #fff !important; }}
h2 {{ font-size: 18px; font-weight: 600; margin: 24px 0 12px; color: {COLORS['text']}; }}
h3 {{ font-size: 15px; font-weight: 600; margin: 18px 0 10px; color: {COLORS['text']}; }}
@media (max-width: 900px) {{
    .container {{ padding: 12px; }}
    .header {{ padding: 16px; }}
}}
</style>
</head>
<body>
<div class="header">
    <h1>{title}</h1>
    <div class="period">{period} &middot; Generated {timestamp}</div>
</div>
<div class="container">
    {tab_bar_html}
    {all_tabs}
</div>
<script>
function switchTab(btn, id) {{
    document.querySelectorAll('.tab-content').forEach(function(t) {{ t.style.display = 'none'; }});
    document.querySelectorAll('.tab-btn').forEach(function(b) {{ b.classList.remove('active');
        b.style.background = 'transparent'; b.style.color = '{COLORS["text_light"]}'; }});
    var el = document.getElementById('tab-' + id);
    if (el) {{ el.style.display = 'block'; }}
    btn.classList.add('active');
    btn.style.background = '{COLORS["bg_dark"]}';
    btn.style.color = '#fff';
    setTimeout(function() {{ window.dispatchEvent(new Event('resize')); }}, 200);
}}
function sortTable(tableId, colIdx) {{
    var table = document.getElementById(tableId);
    if (!table) return;
    var tbody = table.tBodies[0];
    var rows = Array.from(tbody.querySelectorAll('tr:not([id])'));
    var asc = table.getAttribute('data-sort-dir') !== 'asc';
    table.setAttribute('data-sort-dir', asc ? 'asc' : 'desc');
    rows.sort(function(a, b) {{
        var aVal = a.cells[colIdx] ? a.cells[colIdx].textContent.replace(/[,$%]/g, '') : '';
        var bVal = b.cells[colIdx] ? b.cells[colIdx].textContent.replace(/[,$%]/g, '') : '';
        var aNum = parseFloat(aVal), bNum = parseFloat(bVal);
        if (!isNaN(aNum) && !isNaN(bNum)) return asc ? aNum - bNum : bNum - aNum;
        return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }});
    rows.forEach(function(r) {{ tbody.appendChild(r); }});
}}
window.addEventListener('load', function() {{
    {all_chart_js}
}});
window.addEventListener('resize', function() {{
    document.querySelectorAll('[id^="chart-"]').forEach(function(el) {{
        var instance = echarts.getInstanceByDom(el);
        if (instance) instance.resize();
    }});
}});
</script>
</body>
</html>"""
