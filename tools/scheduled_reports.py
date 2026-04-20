"""Scheduled reports and alerts — BACKLOG stubs (not yet implemented)."""

from agents import function_tool


@function_tool
def schedule_report(report_type: str, frequency: str, recipients: str) -> str:
    """[NOT YET IMPLEMENTED] Schedule recurring report generation.

    Args:
        report_type: Report type — 'weekly_overview', 'monthly_seo', 'competitor_update'
        frequency: How often — 'weekly', 'monthly'
        recipients: Comma-separated email addresses
    """
    return (
        "Scheduled reports feature is planned but not yet implemented. "
        "For now, ask me to generate a report manually and I'll create it immediately."
    )


@function_tool
def set_alert(alert_type: str, threshold: str, channel: str = "email") -> str:
    """[NOT YET IMPLEMENTED] Set up monitoring alerts for traffic or rank changes.

    Args:
        alert_type: Alert trigger — 'traffic_drop', 'rank_drop', 'competitor_overtake'
        threshold: Alert threshold (e.g., '-20%' for 20% traffic drop)
        channel: Notification channel — 'email' or 'slack'
    """
    return (
        "Alert system feature is planned but not yet implemented. "
        "For now, I can analyze your current data on demand."
    )
