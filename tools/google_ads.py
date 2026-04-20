"""Google Ads API tools for the Data Analyst agent."""

import json
from datetime import datetime, timedelta
from agents import function_tool

import config

# Lazy import — Google Ads SDK is only needed if credentials are configured
_GoogleAdsClient = None
_GoogleAdsException = None


def _ensure_imports():
    global _GoogleAdsClient, _GoogleAdsException
    if _GoogleAdsClient is None:
        from google.ads.googleads.client import GoogleAdsClient as GAC
        from google.ads.googleads.errors import GoogleAdsException as GAE
        _GoogleAdsClient = GAC
        _GoogleAdsException = GAE

def _missing_key():
    return json.dumps({
        "error": "Google Ads API not configured. Run setup_google_ads_auth.py to complete OAuth setup.",
        "skipped": True,
    })


def _get_client():
    """Create a Google Ads API client using OAuth2 credentials.

    Note: We do NOT use login_customer_id here because the authenticated user
    has direct access to the ad account. The MCC (863-528-9239) doesn't have
    the ad account (102-851-7956) linked as a client, but direct access works.
    """
    _ensure_imports()
    credentials = {
        "developer_token": config.GOOGLE_ADS_DEVELOPER_TOKEN,
        "client_id": config.GOOGLE_ADS_CLIENT_ID,
        "client_secret": config.GOOGLE_ADS_CLIENT_SECRET,
        "refresh_token": config.GOOGLE_ADS_REFRESH_TOKEN,
        "use_proto_plus": True,
    }
    # Don't use login_customer_id — direct access to ad account works without MCC
    return _GoogleAdsClient.load_from_dict(credentials)


def _parse_date_range(date_range: str) -> tuple[str, str]:
    """Parse a date range string into start/end dates.

    Supports: 'last_7_days', 'last_30_days', 'this_month', 'last_month',
              or 'YYYY-MM-DD:YYYY-MM-DD' format.
    """
    today = datetime.now()
    if date_range == "last_7_days":
        start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    elif date_range == "last_30_days":
        start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    elif date_range == "this_month":
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    elif date_range == "last_month":
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
        end = last_month_end.strftime("%Y-%m-%d")
    elif ":" in date_range:
        start, end = date_range.split(":")
    else:
        start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    return start, end


def _run_query(query: str) -> list[dict]:
    """Execute a GAQL query and return results as dicts."""
    if not config.GOOGLE_ADS_REFRESH_TOKEN:
        return [{"error": "Google Ads not configured", "skipped": True}]

    try:
        client = _get_client()
    except Exception as e:
        return [{"error": f"Google Ads client init failed: {e}", "skipped": True}]

    service = client.get_service("GoogleAdsService")
    customer_id = config.GOOGLE_ADS_CUSTOMER_ID

    rows = []
    try:
        response = service.search_stream(customer_id=customer_id, query=query)
        for batch in response:
            for row in batch.results:
                rows.append(row)
    except Exception as ex:
        error_msg = str(ex)
        if "USER_PERMISSION_DENIED" in error_msg:
            return [{"error": "Google Ads: Permission denied. The ad account may not be linked to the MCC. Check Google Ads UI > Settings > Account access.", "skipped": True}]
        return [{"error": f"Google Ads API error: {error_msg}", "skipped": True}]
    return rows


@function_tool
def get_active_campaigns(date_range: str = "last_7_days") -> str:
    """Get all active campaigns with key performance metrics.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    start, end = _parse_date_range(date_range)
    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.all_conversions,
            metrics.conversions_value,
            metrics.cost_per_conversion,
            metrics.search_impression_share
        FROM campaign
        WHERE campaign.status = 'ENABLED'
            AND segments.date BETWEEN '{start}' AND '{end}'
        ORDER BY metrics.cost_micros DESC
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    results = []
    for row in rows:
        cost = row.metrics.cost_micros / 1_000_000
        conv_value = row.metrics.conversions_value
        roas = conv_value / cost if cost > 0 else 0
        # Impression share metric (may be None if not Search campaign)
        search_imp_share = None
        try:
            if row.metrics.search_impression_share:
                search_imp_share = round(row.metrics.search_impression_share * 100, 1)
        except Exception:
            pass

        results.append({
            "campaign_id": str(row.campaign.id),
            "name": row.campaign.name,
            "channel": str(row.campaign.advertising_channel_type.name),
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "ctr": round(row.metrics.ctr * 100, 2),
            "avg_cpc": round(row.metrics.average_cpc / 1_000_000, 2),
            "cost": round(cost, 2),
            "conversions": round(row.metrics.conversions, 1),
            "all_conversions": round(row.metrics.all_conversions, 1) if row.metrics.all_conversions else 0,
            "conversion_value": round(conv_value, 2),
            "cost_per_conversion": round(row.metrics.cost_per_conversion / 1_000_000, 2) if row.metrics.cost_per_conversion else 0,
            "roas": round(roas, 2),
            "search_impression_share_pct": search_imp_share,
        })

    return str({"date_range": f"{start} to {end}", "campaigns": results, "total_campaigns": len(results)})


@function_tool
def get_campaign_detail(campaign_id: str, date_range: str = "last_7_days") -> str:
    """Get detailed ad group breakdown for a specific campaign.

    Args:
        campaign_id: The Google Ads campaign ID.
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    start, end = _parse_date_range(date_range)
    query = f"""
        SELECT
            ad_group.id,
            ad_group.name,
            ad_group.status,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM ad_group
        WHERE campaign.id = {campaign_id}
            AND ad_group.status = 'ENABLED'
            AND segments.date BETWEEN '{start}' AND '{end}'
        ORDER BY metrics.cost_micros DESC
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    results = []
    for row in rows:
        cost = row.metrics.cost_micros / 1_000_000
        results.append({
            "ad_group_id": str(row.ad_group.id),
            "name": row.ad_group.name,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "ctr": round(row.metrics.ctr * 100, 2),
            "avg_cpc": round(row.metrics.average_cpc / 1_000_000, 2),
            "cost": round(cost, 2),
            "conversions": round(row.metrics.conversions, 1),
            "conversion_value": round(row.metrics.conversions_value, 2),
        })

    return str({"campaign_id": campaign_id, "date_range": f"{start} to {end}", "ad_groups": results})


@function_tool
def get_geo_performance(date_range: str = "last_7_days") -> str:
    """Get campaign performance broken down by country/region.
    Important for identifying wasted spend in non-target countries.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    start, end = _parse_date_range(date_range)
    query = f"""
        SELECT
            geographic_view.country_criterion_id,
            geographic_view.location_type,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM geographic_view
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND metrics.impressions > 0
        ORDER BY metrics.cost_micros DESC
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    # Aggregate by country
    country_data = {}
    for row in rows:
        country_id = str(row.geographic_view.country_criterion_id)
        if country_id not in country_data:
            country_data[country_id] = {
                "country_criterion_id": country_id,
                "impressions": 0, "clicks": 0, "cost": 0,
                "conversions": 0, "conversion_value": 0,
            }
        d = country_data[country_id]
        d["impressions"] += row.metrics.impressions
        d["clicks"] += row.metrics.clicks
        d["cost"] += row.metrics.cost_micros / 1_000_000
        d["conversions"] += row.metrics.conversions
        d["conversion_value"] += row.metrics.conversions_value

    results = []
    for d in sorted(country_data.values(), key=lambda x: x["cost"], reverse=True):
        d["ctr"] = round((d["clicks"] / d["impressions"] * 100) if d["impressions"] > 0 else 0, 2)
        d["cost"] = round(d["cost"], 2)
        d["conversions"] = round(d["conversions"], 1)
        d["conversion_value"] = round(d["conversion_value"], 2)
        d["roas"] = round(d["conversion_value"] / d["cost"], 2) if d["cost"] > 0 else 0
        results.append(d)

    target_codes = config.TARGET_COUNTRY_CODES
    return str({
        "date_range": f"{start} to {end}",
        "target_countries": target_codes,
        "countries": results,
        "note": "country_criterion_id maps to Google's geo target constants. Cross-reference with target_countries to find wasted spend."
    })


@function_tool
def get_keyword_performance(campaign_id: str, date_range: str = "last_7_days") -> str:
    """Get keyword-level performance metrics for a campaign.

    Args:
        campaign_id: The Google Ads campaign ID.
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    start, end = _parse_date_range(date_range)
    query = f"""
        SELECT
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM keyword_view
        WHERE campaign.id = {campaign_id}
            AND segments.date BETWEEN '{start}' AND '{end}'
            AND metrics.impressions > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 50
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    results = []
    for row in rows:
        cost = row.metrics.cost_micros / 1_000_000
        results.append({
            "keyword": row.ad_group_criterion.keyword.text,
            "match_type": str(row.ad_group_criterion.keyword.match_type.name),
            "quality_score": row.ad_group_criterion.quality_info.quality_score if row.ad_group_criterion.quality_info.quality_score else None,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "ctr": round(row.metrics.ctr * 100, 2),
            "avg_cpc": round(row.metrics.average_cpc / 1_000_000, 2),
            "cost": round(cost, 2),
            "conversions": round(row.metrics.conversions, 1),
        })

    return str({"campaign_id": campaign_id, "date_range": f"{start} to {end}", "keywords": results})


@function_tool
def get_search_terms(campaign_id: str, date_range: str = "last_7_days") -> str:
    """Get actual search queries that triggered ads for a campaign.
    Useful for finding irrelevant queries and new keyword opportunities.

    Args:
        campaign_id: The Google Ads campaign ID.
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    start, end = _parse_date_range(date_range)
    query = f"""
        SELECT
            search_term_view.search_term,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE campaign.id = {campaign_id}
            AND segments.date BETWEEN '{start}' AND '{end}'
            AND metrics.impressions > 0
        ORDER BY metrics.impressions DESC
        LIMIT 50
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    results = []
    for row in rows:
        results.append({
            "search_term": row.search_term_view.search_term,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "ctr": round(row.metrics.ctr * 100, 2),
            "cost": round(row.metrics.cost_micros / 1_000_000, 2),
            "conversions": round(row.metrics.conversions, 1),
        })

    return str({"campaign_id": campaign_id, "date_range": f"{start} to {end}", "search_terms": results})


@function_tool
def get_audience_performance(date_range: str = "last_7_days") -> str:
    """Get performance metrics by audience segment across all campaigns.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    start, end = _parse_date_range(date_range)
    query = f"""
        SELECT
            campaign.name,
            ad_group_audience_view.resource_name,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM ad_group_audience_view
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND metrics.impressions > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 30
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    results = []
    for row in rows:
        cost = row.metrics.cost_micros / 1_000_000
        results.append({
            "campaign": row.campaign.name,
            "audience_resource": row.ad_group_audience_view.resource_name,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "ctr": round(row.metrics.ctr * 100, 2),
            "cost": round(cost, 2),
            "conversions": round(row.metrics.conversions, 1),
            "conversion_value": round(row.metrics.conversions_value, 2),
        })

    return str({"date_range": f"{start} to {end}", "audiences": results})


# ─── Tool 6b: Ad Copy / Creative Assets ───────────────────────────────

@function_tool
def get_ad_copy(campaign_id: str = "", date_range: str = "last_30_days") -> str:
    """Get ad copy (headlines, descriptions) and performance for responsive search ads.
    Shows which headline/description variants are performing best.

    Args:
        campaign_id: Optional campaign ID. If empty, returns all enabled ads.
        date_range: 'last_7_days', 'last_30_days', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    if not config.GOOGLE_ADS_REFRESH_TOKEN:
        return _missing_key()

    start, end = _parse_date_range(date_range)
    campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""

    query = f"""
        SELECT
            campaign.name,
            ad_group.name,
            ad_group_ad.ad.id,
            ad_group_ad.ad.type,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions
        FROM ad_group_ad
        WHERE campaign.status = 'ENABLED'
            AND ad_group_ad.status = 'ENABLED'
            {campaign_filter}
            AND segments.date BETWEEN '{start}' AND '{end}'
            AND metrics.impressions > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 30
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return json.dumps(rows[0])

    results = []
    for row in rows:
        ad = row.ad_group_ad.ad
        headlines = [h.text for h in ad.responsive_search_ad.headlines] if ad.responsive_search_ad.headlines else []
        descriptions = [d.text for d in ad.responsive_search_ad.descriptions] if ad.responsive_search_ad.descriptions else []
        final_urls = list(ad.final_urls) if ad.final_urls else []
        cost = row.metrics.cost_micros / 1_000_000

        results.append({
            "campaign": row.campaign.name,
            "ad_group": row.ad_group.name,
            "ad_id": str(ad.id),
            "ad_type": str(ad.type_.name),
            "headlines": headlines,
            "descriptions": descriptions,
            "final_urls": final_urls,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "ctr": round(row.metrics.ctr * 100, 2),
            "cost": round(cost, 2),
            "conversions": round(row.metrics.conversions, 1),
        })

    return json.dumps({
        "date_range": f"{start} to {end}",
        "ads": results,
        "total_ads": len(results),
    })


# ─── Tool 7: Campaign Trend (Daily/Weekly Time Series) ────────────────

@function_tool
def get_google_ads_campaign_trend(
    campaign_id: str = "",
    date_range: str = "last_30_days",
) -> str:
    """Get Google Ads campaign performance over time with daily breakdown.
    Shows how metrics changed over the date range to identify trends, spikes, and declines.

    Args:
        campaign_id: Optional campaign ID. If empty, returns account-level daily trends.
        date_range: 'last_7_days', 'last_30_days', 'this_month', 'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    if not config.GOOGLE_ADS_REFRESH_TOKEN:
        return _missing_key()

    start, end = _parse_date_range(date_range)

    campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT
            segments.date,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.cost_per_conversion
        FROM campaign
        WHERE campaign.status = 'ENABLED'
            AND segments.date BETWEEN '{start}' AND '{end}'
            {campaign_filter}
        ORDER BY segments.date ASC
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return json.dumps({"error": rows[0]["error"], "skipped": True})

    # Aggregate by date
    daily = {}
    for row in rows:
        date_str = str(row.segments.date)
        if date_str not in daily:
            daily[date_str] = {
                "date": date_str, "impressions": 0, "clicks": 0,
                "cost": 0, "conversions": 0, "conversion_value": 0,
            }
        d = daily[date_str]
        d["impressions"] += row.metrics.impressions
        d["clicks"] += row.metrics.clicks
        d["cost"] += row.metrics.cost_micros / 1_000_000
        d["conversions"] += row.metrics.conversions
        d["conversion_value"] += row.metrics.conversions_value

    periods = []
    prev_spend = None
    for date_str in sorted(daily.keys()):
        d = daily[date_str]
        d["cost"] = round(d["cost"], 2)
        d["ctr"] = round((d["clicks"] / d["impressions"] * 100), 2) if d["impressions"] > 0 else 0
        d["avg_cpc"] = round(d["cost"] / d["clicks"], 2) if d["clicks"] > 0 else 0
        d["conversions"] = round(d["conversions"], 1)
        d["conversion_value"] = round(d["conversion_value"], 2)
        d["roas"] = round(d["conversion_value"] / d["cost"], 2) if d["cost"] > 0 else 0

        spend_change = None
        if prev_spend is not None and prev_spend > 0:
            spend_change = round((d["cost"] - prev_spend) / prev_spend * 100, 1)
        d["spend_change_pct"] = spend_change
        prev_spend = d["cost"]

        periods.append(d)

    return json.dumps({
        "campaign_id": campaign_id or "account_level",
        "date_range": f"{start} to {end}",
        "periods": periods,
        "period_count": len(periods),
    })


# ─── Tool 8: Week-over-Week Comparison ────────────────────────────────

@function_tool
def get_google_ads_wow(date_range: str = "last_14_days") -> str:
    """Get Week-over-Week comparison for Google Ads — this week vs last week.
    Returns all campaigns with WoW change for every metric.

    Args:
        date_range: Should be 'last_14_days' to cover two full weeks. Default is 'last_14_days'.
    """
    if not config.GOOGLE_ADS_REFRESH_TOKEN:
        return _missing_key()

    today = datetime.now()
    tw_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    tw_end = today.strftime("%Y-%m-%d")
    lw_start = (today - timedelta(days=14)).strftime("%Y-%m-%d")
    lw_end = (today - timedelta(days=7)).strftime("%Y-%m-%d")

    def _fetch_period(start, end):
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.advertising_channel_type,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE campaign.status = 'ENABLED'
                AND segments.date BETWEEN '{start}' AND '{end}'
            ORDER BY metrics.cost_micros DESC
        """
        rows = _run_query(query)
        if rows and isinstance(rows[0], dict) and "error" in rows[0]:
            return None
        campaigns = {}
        for row in rows:
            cid = str(row.campaign.id)
            if cid not in campaigns:
                campaigns[cid] = {
                    "campaign_id": cid, "name": row.campaign.name,
                    "channel": str(row.campaign.advertising_channel_type.name),
                    "impressions": 0, "clicks": 0, "cost": 0,
                    "conversions": 0, "conversion_value": 0,
                }
            c = campaigns[cid]
            c["impressions"] += row.metrics.impressions
            c["clicks"] += row.metrics.clicks
            c["cost"] += row.metrics.cost_micros / 1_000_000
            c["conversions"] += row.metrics.conversions
            c["conversion_value"] += row.metrics.conversions_value
        for c in campaigns.values():
            c["cost"] = round(c["cost"], 2)
            c["ctr"] = round((c["clicks"] / c["impressions"] * 100), 2) if c["impressions"] > 0 else 0
            c["avg_cpc"] = round(c["cost"] / c["clicks"], 2) if c["clicks"] > 0 else 0
            c["roas"] = round(c["conversion_value"] / c["cost"], 2) if c["cost"] > 0 else 0
        return campaigns

    this_week = _fetch_period(tw_start, tw_end)
    last_week = _fetch_period(lw_start, lw_end)

    if this_week is None:
        return _missing_key()

    # Compute WoW changes per campaign
    comparisons = []
    all_ids = set(list((this_week or {}).keys()) + list((last_week or {}).keys()))
    for cid in all_ids:
        tw = (this_week or {}).get(cid, {})
        lw = (last_week or {}).get(cid, {})

        def pct(curr_val, prev_val):
            if prev_val and prev_val > 0:
                return round((curr_val - prev_val) / prev_val * 100, 1)
            return None

        comparisons.append({
            "campaign_id": cid,
            "name": tw.get("name") or lw.get("name", ""),
            "channel": tw.get("channel") or lw.get("channel", ""),
            "this_week": tw,
            "last_week": lw,
            "changes": {
                "impressions_pct": pct(tw.get("impressions", 0), lw.get("impressions", 0)),
                "clicks_pct": pct(tw.get("clicks", 0), lw.get("clicks", 0)),
                "cost_pct": pct(tw.get("cost", 0), lw.get("cost", 0)),
                "ctr_pct": pct(tw.get("ctr", 0), lw.get("ctr", 0)),
                "conversions_pct": pct(tw.get("conversions", 0), lw.get("conversions", 0)),
                "roas_pct": pct(tw.get("roas", 0), lw.get("roas", 0)),
            },
        })

    comparisons.sort(key=lambda x: x.get("this_week", {}).get("cost", 0), reverse=True)

    return json.dumps({
        "this_week_period": f"{tw_start} to {tw_end}",
        "last_week_period": f"{lw_start} to {lw_end}",
        "campaigns": comparisons,
        "total_campaigns": len(comparisons),
    })


# ─── Tool 9: Budget Overview ──────────────────────────────────────────

@function_tool
def get_google_ads_budget_overview() -> str:
    """Get budget details for all active campaigns — total budget, daily budget, spend.
    Shows how budget is distributed across campaigns."""
    if not config.GOOGLE_ADS_REFRESH_TOKEN:
        return _missing_key()

    # Get campaign budgets + recent spend
    today = datetime.now()
    start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign_budget.amount_micros,
            campaign_budget.total_amount_micros,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM campaign
        WHERE campaign.status = 'ENABLED'
            AND segments.date BETWEEN '{start}' AND '{end}'
        ORDER BY metrics.cost_micros DESC
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return json.dumps({"error": rows[0]["error"], "skipped": True})

    campaigns = {}
    for row in rows:
        cid = str(row.campaign.id)
        if cid not in campaigns:
            daily_budget = row.campaign_budget.amount_micros / 1_000_000 if row.campaign_budget.amount_micros else 0
            total_budget = row.campaign_budget.total_amount_micros / 1_000_000 if row.campaign_budget.total_amount_micros else None
            campaigns[cid] = {
                "campaign_id": cid,
                "name": row.campaign.name,
                "channel": str(row.campaign.advertising_channel_type.name),
                "daily_budget": round(daily_budget, 2),
                "total_budget": round(total_budget, 2) if total_budget else "unlimited",
                "spend_last_7d": 0,
                "conversions_7d": 0,
                "conversion_value_7d": 0,
            }
        c = campaigns[cid]
        c["spend_last_7d"] += row.metrics.cost_micros / 1_000_000
        c["conversions_7d"] += row.metrics.conversions
        c["conversion_value_7d"] += row.metrics.conversions_value

    results = []
    total_daily = 0
    total_spend = 0
    for c in sorted(campaigns.values(), key=lambda x: x["spend_last_7d"], reverse=True):
        c["spend_last_7d"] = round(c["spend_last_7d"], 2)
        c["conversions_7d"] = round(c["conversions_7d"], 1)
        c["conversion_value_7d"] = round(c["conversion_value_7d"], 2)
        c["budget_utilization_pct"] = round(
            (c["spend_last_7d"] / (c["daily_budget"] * 7) * 100), 1
        ) if c["daily_budget"] > 0 else 0
        total_daily += c["daily_budget"]
        total_spend += c["spend_last_7d"]
        results.append(c)

    return json.dumps({
        "period": f"{start} to {end}",
        "campaigns": results,
        "total_daily_budget": round(total_daily, 2),
        "total_spend_last_7d": round(total_spend, 2),
        "total_campaigns": len(results),
    })


# ─── Tool 10: Multi-Week Trend (5 weeks) ────────────────────────────

@function_tool
def get_google_ads_weekly_trend(campaign_id: str = "", weeks: int = 5) -> str:
    """Get 5-week campaign performance trend with impression share.
    Returns weekly aggregated data with WoW changes for trend analysis.

    Args:
        campaign_id: Optional campaign ID. If empty, returns account-level weekly trends.
        weeks: Number of weeks (default 5).
    """
    if not config.GOOGLE_ADS_REFRESH_TOKEN:
        return _missing_key()

    today = datetime.now()
    start = (today - timedelta(days=weeks * 7)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT
            segments.date,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM campaign
        WHERE campaign.status = 'ENABLED'
            AND segments.date BETWEEN '{start}' AND '{end}'
            {campaign_filter}
        ORDER BY segments.date ASC
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return json.dumps({"error": rows[0]["error"], "skipped": True})

    # Aggregate by ISO week
    weekly = {}
    for row in rows:
        date_str = str(row.segments.date)
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            iso_week = dt.strftime("%Y-W%V")
        except Exception:
            continue

        if iso_week not in weekly:
            weekly[iso_week] = {
                "week": iso_week, "impressions": 0, "clicks": 0,
                "cost": 0, "conversions": 0, "conversion_value": 0,
            }
        w = weekly[iso_week]
        w["impressions"] += row.metrics.impressions
        w["clicks"] += row.metrics.clicks
        w["cost"] += row.metrics.cost_micros / 1_000_000
        w["conversions"] += row.metrics.conversions
        w["conversion_value"] += row.metrics.conversions_value

    # Build weekly list with WoW changes
    periods = []
    prev_spend = None
    for week_key in sorted(weekly.keys()):
        w = weekly[week_key]
        w["cost"] = round(w["cost"], 2)
        w["ctr"] = round((w["clicks"] / w["impressions"] * 100), 2) if w["impressions"] > 0 else 0
        w["avg_cpc"] = round(w["cost"] / w["clicks"], 2) if w["clicks"] > 0 else 0
        w["conversions"] = round(w["conversions"], 1)
        w["roas"] = round(w["conversion_value"] / w["cost"], 2) if w["cost"] > 0 else 0
        wow_pct = None
        if prev_spend is not None and prev_spend > 0:
            wow_pct = round((w["cost"] - prev_spend) / prev_spend * 100, 1)
        w["spend_change_pct"] = wow_pct
        prev_spend = w["cost"]

        # Clean up temp fields
        del w["conversion_value"]
        periods.append(w)

    return json.dumps({
        "campaign_id": campaign_id or "account_level",
        "weeks_requested": weeks,
        "periods": periods,
    })


# ─── Tool 11: Search Terms Extended (with weekly trends) ────────────

@function_tool
def get_search_terms_extended(campaign_id: str, weeks: int = 5) -> str:
    """Get actual search queries that triggered ads, with weekly trend data.
    Shows which search terms are growing, declining, or stable over time.
    Essential for finding new keyword opportunities and negative keyword candidates.

    Args:
        campaign_id: The Google Ads campaign ID.
        weeks: Number of weeks to analyze (default 5).
    """
    if not config.GOOGLE_ADS_REFRESH_TOKEN:
        return _missing_key()

    today = datetime.now()
    start = (today - timedelta(days=weeks * 7)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    query = f"""
        SELECT
            search_term_view.search_term,
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE campaign.id = {campaign_id}
            AND segments.date BETWEEN '{start}' AND '{end}'
            AND metrics.impressions > 0
        ORDER BY metrics.impressions DESC
        LIMIT 500
    """
    rows = _run_query(query)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return json.dumps({"error": rows[0]["error"], "skipped": True})

    # Group by search term + week
    terms = {}
    for row in rows:
        term = row.search_term_view.search_term
        date_str = str(row.segments.date)
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            iso_week = dt.strftime("%Y-W%V")
        except Exception:
            continue

        if term not in terms:
            terms[term] = {"term": term, "total_impressions": 0, "total_clicks": 0,
                           "total_cost": 0, "total_conversions": 0, "weekly": {}}
        t = terms[term]
        t["total_impressions"] += row.metrics.impressions
        t["total_clicks"] += row.metrics.clicks
        t["total_cost"] += row.metrics.cost_micros / 1_000_000
        t["total_conversions"] += row.metrics.conversions

        if iso_week not in t["weekly"]:
            t["weekly"][iso_week] = {"impressions": 0, "clicks": 0, "cost": 0, "conversions": 0}
        w = t["weekly"][iso_week]
        w["impressions"] += row.metrics.impressions
        w["clicks"] += row.metrics.clicks
        w["cost"] += row.metrics.cost_micros / 1_000_000
        w["conversions"] += row.metrics.conversions

    # Determine trends and format
    results = []
    for term_data in sorted(terms.values(), key=lambda x: x["total_impressions"], reverse=True)[:100]:
        weekly_sorted = sorted(term_data["weekly"].items())
        weekly_list = [{"week": w, **d} for w, d in weekly_sorted]
        for w in weekly_list:
            w["cost"] = round(w["cost"], 2)
            w["conversions"] = round(w["conversions"], 1)

        # Trend detection: compare first vs last week impressions
        if len(weekly_list) >= 2:
            first_imp = weekly_list[0]["impressions"]
            last_imp = weekly_list[-1]["impressions"]
            if first_imp > 0:
                change = (last_imp - first_imp) / first_imp * 100
                trend = "growing" if change > 20 else "declining" if change < -20 else "stable"
            else:
                trend = "new" if last_imp > 0 else "stable"
        else:
            trend = "insufficient_data"

        results.append({
            "search_term": term_data["term"],
            "total_impressions": term_data["total_impressions"],
            "total_clicks": term_data["total_clicks"],
            "total_cost": round(term_data["total_cost"], 2),
            "total_conversions": round(term_data["total_conversions"], 1),
            "ctr": round((term_data["total_clicks"] / term_data["total_impressions"] * 100), 2) if term_data["total_impressions"] > 0 else 0,
            "trend": trend,
            "weekly": weekly_list,
        })

    return json.dumps({
        "campaign_id": campaign_id,
        "weeks_analyzed": weeks,
        "search_terms": results,
        "growing_terms": [t["search_term"] for t in results if t["trend"] == "growing"][:10],
        "declining_terms": [t["search_term"] for t in results if t["trend"] == "declining"][:10],
    })
