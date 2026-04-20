"""Generate the Google Ads API Basic Access design documentation PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

OUTPUT_PATH = "output/Sourcy_Global_Google_Ads_API_Design_Document.pdf"

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=22, spaceAfter=6, textColor=HexColor('#1a1a2e'),
        fontName='Helvetica-Bold',
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontSize=16, spaceAfter=8, spaceBefore=16,
        textColor=HexColor('#1a1a2e'), fontName='Helvetica-Bold',
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=13, spaceAfter=6, spaceBefore=12,
        textColor=HexColor('#16213e'), fontName='Helvetica-Bold',
    )
    body_style = ParagraphStyle(
        'CustomBody', parent=styles['Normal'],
        fontSize=10, spaceAfter=6, leading=14,
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=body_style,
        leftIndent=20, bulletIndent=10,
        spaceBefore=2, spaceAfter=2,
    )

    elements = []

    # --- Title Page ---
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("Google Ads API Tool", title_style))
    elements.append(Paragraph("Design Documentation", ParagraphStyle(
        'Subtitle', parent=styles['Title'], fontSize=16,
        textColor=HexColor('#666666'), spaceAfter=20,
    )))
    elements.append(HRFlowable(width="100%", thickness=2, color=HexColor('#1a1a2e')))
    elements.append(Spacer(1, 30))

    info_data = [
        ["Company:", "Sourcy Global Pte Ltd"],
        ["Website:", "https://sourcy.ai"],
        ["Contact:", "eugeneclarance@sourcyglobal.com"],
        ["Date:", "April 2026"],
        ["Version:", "1.0"],
        ["Document Type:", "API Basic Access Application - Design Document"],
    ]
    info_table = Table(info_data, colWidths=[120, 350])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#374151')),
    ]))
    elements.append(info_table)
    elements.append(PageBreak())

    # --- Section 1: Company Overview ---
    elements.append(Paragraph("1. Company Overview", h1_style))
    elements.append(Paragraph(
        "Sourcy Global is a B2B sourcing platform (sourcy.ai) that connects buyers with "
        "verified suppliers across Southeast Asia and Latin America. We use Google Ads to "
        "drive qualified traffic to our platform and generate business leads across our "
        "target markets: Indonesia, Philippines, Thailand, Brazil, United States, and Mexico.",
        body_style
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "We only advertise for our own website (sourcy.ai) and do not manage ads for any "
        "third-party clients. All advertising is managed by our internal marketing team.",
        body_style
    ))

    # --- Section 2: Tool Purpose ---
    elements.append(Paragraph("2. Tool Purpose & Scope", h1_style))
    elements.append(Paragraph(
        "We are building an internal marketing analytics tool that connects to the Google Ads "
        "API to automate campaign performance reporting. The tool serves two primary functions:",
        body_style
    ))
    elements.append(Paragraph("1. <b>Performance Reporting Dashboard</b> - An interactive HTML dashboard "
        "that displays campaign metrics including impressions, clicks, CTR, CPC, conversions, "
        "ROAS, and cost breakdowns by geography and audience segment.", bullet_style))
    elements.append(Paragraph("2. <b>Automated Weekly Reports</b> - Generate HTML reports with charts "
        "and tables summarizing weekly campaign performance, geographic distribution, and "
        "actionable optimization recommendations.", bullet_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "<b>Important:</b> The tool is <b>read-only</b>. It only pulls performance metrics "
        "from the API for reporting purposes. It does not create, modify, pause, or delete "
        "any campaigns, ad groups, ads, or other Google Ads entities.",
        body_style
    ))

    # --- Section 3: Tool Access ---
    elements.append(Paragraph("3. Tool Access", h1_style))
    elements.append(Paragraph(
        "The tool is strictly for <b>internal use only</b>. Only employees and authorized "
        "team members of Sourcy Global will have access to the tool. No external users, "
        "clients, or third parties will have direct access.",
        body_style
    ))
    elements.append(Spacer(1, 6))

    access_data = [
        ["Role", "Access Level", "Description"],
        ["Marketing Team", "Full Dashboard", "View all reports and generate new ones"],
        ["Management", "Report Viewer", "View generated reports and KPI summaries"],
        ["Engineering", "Admin", "Tool maintenance and API credential management"],
    ]
    access_table = Table(access_data, colWidths=[120, 120, 230])
    access_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fb')]),
    ]))
    elements.append(access_table)

    # --- Section 4: Architecture ---
    elements.append(Paragraph("4. Technical Architecture", h1_style))
    elements.append(Paragraph("4.1 System Components", h2_style))

    arch_data = [
        ["Component", "Technology", "Purpose"],
        ["Agent Framework", "OpenAI Agents SDK (Python)", "Orchestrates data collection and analysis"],
        ["Google Ads Integration", "google-ads Python client", "Pulls campaign performance data via API"],
        ["Google Analytics Integration", "google-analytics-data", "Pulls website traffic and conversion data"],
        ["Search Console Integration", "google-api-python-client", "Pulls organic search performance data"],
        ["Report Generator", "Jinja2 + Chart.js", "Generates interactive HTML reports with charts"],
        ["Authentication", "OAuth 2.0", "Secure API access with refresh tokens"],
    ]
    arch_table = Table(arch_data, colWidths=[130, 150, 190])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fb')]),
    ]))
    elements.append(arch_table)

    elements.append(Paragraph("4.2 Data Flow", h2_style))
    elements.append(Paragraph(
        "The system follows a simple read-only data flow:", body_style
    ))
    elements.append(Paragraph("1. User requests a report via the chat interface", bullet_style))
    elements.append(Paragraph("2. The Data Analyst agent determines which API calls are needed", bullet_style))
    elements.append(Paragraph("3. API tools fetch data from Google Ads, GA4, and Search Console", bullet_style))
    elements.append(Paragraph("4. The agent analyzes the data and identifies insights", bullet_style))
    elements.append(Paragraph("5. The report generator creates an HTML report with charts", bullet_style))
    elements.append(Paragraph("6. The report is saved locally and presented to the user", bullet_style))

    # --- Section 5: API Services Used ---
    elements.append(Paragraph("5. Google Ads API Services Used", h1_style))
    elements.append(Paragraph(
        "The tool uses the Google Ads API in <b>read-only mode</b>. The following services "
        "and resources are accessed:", body_style
    ))

    api_data = [
        ["API Service / Resource", "Method", "Purpose"],
        ["GoogleAdsService", "SearchStream", "Query campaign, ad group, and keyword metrics"],
        ["Campaign resource", "Read", "Get campaign names, status, channel type"],
        ["AdGroup resource", "Read", "Get ad group performance breakdown"],
        ["KeywordView resource", "Read", "Get keyword-level performance metrics"],
        ["SearchTermView resource", "Read", "View actual search queries triggering ads"],
        ["GeographicView resource", "Read", "Get country/region performance data"],
        ["AdGroupAudienceView", "Read", "Get audience segment performance"],
    ]
    api_table = Table(api_data, colWidths=[150, 80, 240])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fb')]),
    ]))
    elements.append(api_table)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "<b>No mutate/write operations are performed.</b> The tool does not create, update, "
        "pause, or delete any campaigns, ads, keywords, or other Google Ads entities.",
        body_style
    ))

    # --- Section 6: Tool Mockup ---
    elements.append(PageBreak())
    elements.append(Paragraph("6. Tool Mockup - Report Dashboard", h1_style))
    elements.append(Paragraph(
        "Below is a mockup of the HTML report generated by the tool. The report includes "
        "KPI summary cards, campaign performance tables, geographic breakdown charts, "
        "and actionable insights.", body_style
    ))
    elements.append(Spacer(1, 10))

    # Mockup: KPI Cards
    elements.append(Paragraph("6.1 KPI Summary Cards", h2_style))
    kpi_data = [
        ["Total Spend", "Conversions", "ROAS", "Avg. CTR", "Sessions (GA4)"],
        ["$5,230.45", "142", "3.8x", "4.2%", "2,971"],
        ["+12% vs last week", "+23% vs last week", "+0.5x vs last week", "-0.3% vs last week", "+8% vs last week"],
    ]
    kpi_table = Table(kpi_data, colWidths=[94] * 5)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f0f9ff')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('FONTSIZE', (0, 2), (-1, 2), 7),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#666666')),
        ('TEXTCOLOR', (0, 2), (2, 2), HexColor('#10b981')),
        ('TEXTCOLOR', (3, 2), (3, 2), HexColor('#ef4444')),
        ('TEXTCOLOR', (4, 2), (4, 2), HexColor('#10b981')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), white),
    ]))
    elements.append(kpi_table)

    # Mockup: Campaign Table
    elements.append(Paragraph("6.2 Campaign Performance Table", h2_style))
    camp_data = [
        ["Campaign", "Impressions", "Clicks", "CTR", "Cost", "Conv.", "ROAS"],
        ["Brand - SEA Markets", "45,230", "3,120", "6.9%", "$1,890", "67", "4.2x"],
        ["Product - Indonesia", "23,450", "1,456", "6.2%", "$1,230", "38", "3.9x"],
        ["Brand - LatAm", "18,900", "890", "4.7%", "$980", "22", "3.1x"],
        ["Remarketing - Global", "12,340", "567", "4.6%", "$650", "15", "2.8x"],
    ]
    camp_table = Table(camp_data, colWidths=[130, 70, 55, 45, 55, 45, 45])
    camp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fb')]),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ]))
    elements.append(camp_table)

    # Mockup: Geo Table
    elements.append(Paragraph("6.3 Geographic Performance (Blindspot Detection)", h2_style))
    geo_data = [
        ["Country", "Status", "Impressions", "Clicks", "Cost", "Conv.", "Flag"],
        ["Indonesia", "TARGET", "18,450", "1,230", "$890", "32", "OK"],
        ["Philippines", "TARGET", "12,300", "780", "$620", "18", "OK"],
        ["United States", "TARGET", "8,900", "456", "$780", "12", "OK"],
        ["Thailand", "TARGET", "6,700", "345", "$410", "8", "LOW CTR"],
        ["Nigeria", "NON-TARGET", "3,200", "89", "$120", "0", "WASTED SPEND"],
        ["India", "NON-TARGET", "2,800", "67", "$95", "0", "WASTED SPEND"],
    ]
    geo_table = Table(geo_data, colWidths=[80, 75, 70, 50, 50, 45, 90])
    geo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fb')]),
        ('BACKGROUND', (6, 5), (6, 6), HexColor('#fee2e2')),
        ('TEXTCOLOR', (6, 5), (6, 6), HexColor('#991b1b')),
        ('FONTNAME', (6, 5), (6, 6), 'Helvetica-Bold'),
        ('BACKGROUND', (6, 4), (6, 4), HexColor('#fef3c7')),
        ('TEXTCOLOR', (6, 4), (6, 4), HexColor('#92400e')),
        ('BACKGROUND', (1, 1), (1, 4), HexColor('#d1fae5')),
        ('TEXTCOLOR', (1, 1), (1, 4), HexColor('#065f46')),
        ('BACKGROUND', (1, 5), (1, 6), HexColor('#fee2e2')),
        ('TEXTCOLOR', (1, 5), (1, 6), HexColor('#991b1b')),
    ]))
    elements.append(geo_table)

    # Mockup: Insights
    elements.append(Paragraph("6.4 Insights & Recommendations", h2_style))

    insight_data = [
        ["WASTED SPEND ALERT: 4.5% of total budget ($215) is going to non-target countries "
         "(Nigeria, India). Recommend adding negative geo targeting to exclude these regions."],
        ["LOW CTR: Thailand campaigns show 3.1% CTR vs 6.5% average for other target markets. "
         "Investigate ad copy relevance and keyword match types for Thai market."],
        ["OPPORTUNITY: 12 high-volume organic keywords from Search Console have no paid coverage. "
         "Consider creating campaigns for these keywords to capture additional traffic."],
    ]
    for i, row in enumerate(insight_data):
        colors = [HexColor('#fee2e2'), HexColor('#fef3c7'), HexColor('#d1fae5')]
        borders = [HexColor('#ef4444'), HexColor('#f59e0b'), HexColor('#10b981')]
        t = Table([[row[0]]], colWidths=[440])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors[i]),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('LINEBEFOREDECOR', (0, 0), (0, -1)),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4))

    # --- Section 7: Security ---
    elements.append(PageBreak())
    elements.append(Paragraph("7. Security & Compliance", h1_style))
    elements.append(Paragraph("- OAuth 2.0 credentials stored securely in environment variables", bullet_style))
    elements.append(Paragraph("- Refresh tokens stored in .env file, excluded from version control via .gitignore", bullet_style))
    elements.append(Paragraph("- Service account JSON key stored in credentials/ directory, excluded from version control", bullet_style))
    elements.append(Paragraph("- All API access is read-only - no write/mutate operations", bullet_style))
    elements.append(Paragraph("- Tool runs locally on company machines - no cloud hosting or external access", bullet_style))
    elements.append(Paragraph("- Only authorized internal team members can access the tool", bullet_style))

    # --- Section 8: Summary ---
    elements.append(Paragraph("8. Summary", h1_style))
    elements.append(Paragraph(
        "This tool is a simple, internal-only, read-only marketing analytics tool built for "
        "Sourcy Global's marketing team. It pulls campaign performance metrics from the Google "
        "Ads API to generate visual reports that help our team optimize ad spend across our "
        "target markets. No campaign modifications are made through the API.",
        body_style
    ))

    doc.build(elements)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
