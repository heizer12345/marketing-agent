"""HTML Report Generator with Chart.js visualizations."""

import json
from datetime import datetime
from pathlib import Path
from agents import function_tool
from jinja2 import Template

import config

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
        .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 32px; border-radius: 12px; margin-bottom: 24px; }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header .subtitle { opacity: 0.8; font-size: 14px; }
        .header .date { opacity: 0.6; font-size: 13px; margin-top: 4px; }
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .kpi-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .kpi-card .label { font-size: 12px; text-transform: uppercase; color: #666; letter-spacing: 0.5px; }
        .kpi-card .value { font-size: 28px; font-weight: 700; margin: 4px 0; }
        .kpi-card .change { font-size: 13px; }
        .kpi-card .change.positive { color: #10b981; }
        .kpi-card .change.negative { color: #ef4444; }
        .kpi-card .change.neutral { color: #6b7280; }
        .section { background: white; border-radius: 10px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .section h2 { font-size: 18px; margin-bottom: 16px; color: #1a1a2e; }
        .section h3 { font-size: 15px; margin: 16px 0 8px; color: #374151; }
        .chart-container { position: relative; height: 350px; margin: 16px 0; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { text-align: left; padding: 10px 12px; background: #f8f9fb; border-bottom: 2px solid #e5e7eb; font-weight: 600; color: #374151; }
        td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }
        tr:hover { background: #f8f9fb; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
        .badge-green { background: #d1fae5; color: #065f46; }
        .badge-red { background: #fee2e2; color: #991b1b; }
        .badge-yellow { background: #fef3c7; color: #92400e; }
        .badge-blue { background: #dbeafe; color: #1e40af; }
        .insight-box { background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 16px; margin: 12px 0; border-radius: 0 8px 8px 0; }
        .insight-box.warning { background: #fef3c7; border-left-color: #f59e0b; }
        .insight-box.danger { background: #fee2e2; border-left-color: #ef4444; }
        .insight-box.success { background: #d1fae5; border-left-color: #10b981; }
        .insight-box h4 { font-size: 14px; margin-bottom: 4px; }
        .insight-box p { font-size: 13px; color: #4b5563; }
        .footer { text-align: center; padding: 24px; color: #9ca3af; font-size: 12px; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{{ title }}</h1>
        <div class="subtitle">{{ subtitle }}</div>
        <div class="date">Generated: {{ generated_at }} | Period: {{ date_range }}</div>
    </div>

    {% if kpis %}
    <div class="kpi-grid">
        {% for kpi in kpis %}
        <div class="kpi-card">
            <div class="label">{{ kpi.label }}</div>
            <div class="value">{{ kpi.value }}</div>
            {% if kpi.change is defined %}
            <div class="change {{ kpi.change_class }}">{{ kpi.change }}</div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% for section in sections %}
    <div class="section">
        <h2>{{ section.title }}</h2>

        {% if section.insights %}
        {% for insight in section.insights %}
        <div class="insight-box {{ insight.type }}">
            <h4>{{ insight.title }}</h4>
            <p>{{ insight.message }}</p>
        </div>
        {% endfor %}
        {% endif %}

        {% if section.chart_id %}
        <div class="chart-container">
            <canvas id="{{ section.chart_id }}"></canvas>
        </div>
        {% endif %}

        {% if section.table %}
        <table>
            <thead>
                <tr>
                    {% for col in section.table.columns %}
                    <th>{{ col }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for row in section.table.rows %}
                <tr>
                    {% for cell in row %}
                    <td>{{ cell }}</td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}

        {% if section.html %}
        {{ section.html }}
        {% endif %}
    </div>
    {% endfor %}

    <div class="footer">
        Marketing Data Analyst Agent | Auto-generated report
    </div>
</div>

{% if charts_js %}
<script>
{{ charts_js }}
</script>
{% endif %}

</body>
</html>"""


@function_tool
def generate_html_report(report_data_json: str) -> str:
    """Generate an HTML report with charts and tables from structured data.

    Args:
        report_data_json: JSON string with report structure. Expected format:
            {
                "title": "Weekly Marketing Report",
                "subtitle": "Campaign Performance Analysis",
                "date_range": "2026-04-01 to 2026-04-08",
                "kpis": [
                    {"label": "Total Spend", "value": "$5,230", "change": "+12% vs last week", "change_class": "negative"},
                    {"label": "Conversions", "value": "142", "change": "+23%", "change_class": "positive"}
                ],
                "sections": [
                    {
                        "title": "Campaign Performance",
                        "insights": [
                            {"type": "warning", "title": "High spend in Nigeria", "message": "15% of budget going to non-target country"}
                        ],
                        "chart_id": "campaignChart",
                        "table": {
                            "columns": ["Campaign", "Impressions", "Clicks", "CTR", "Cost", "Conv"],
                            "rows": [["Brand Campaign", "12,340", "890", "7.2%", "$450", "45"]]
                        }
                    }
                ],
                "charts_js": "new Chart(document.getElementById('campaignChart'), {...});"
            }
    """
    try:
        data = json.loads(report_data_json)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON - {str(e)}"

    data.setdefault("title", "Marketing Report")
    data.setdefault("subtitle", "")
    data.setdefault("date_range", "")
    data.setdefault("kpis", [])
    data.setdefault("sections", [])
    data.setdefault("charts_js", "")
    data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    template = Template(REPORT_TEMPLATE)
    html = template.render(**data)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.html"
    filepath = config.OUTPUT_DIR / filename

    with open(filepath, "w") as f:
        f.write(html)

    return str({
        "status": "success",
        "filepath": str(filepath),
        "filename": filename,
        "message": f"Report generated and saved to {filepath}"
    })
