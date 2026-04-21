"""Meta (Facebook) Marketing API tools — READ-ONLY ad analysis.

Provides campaign performance, targeting diagnostics, creative details,
and spend-by-country analysis. All tools gracefully degrade if API keys
are not configured.

Requires: pip install facebook-business
Auth: System User token via META_ACCESS_TOKEN + META_AD_ACCOUNT_ID env vars.
"""

import json
import time as _time
from datetime import datetime, timedelta
from typing import Optional
from agents import function_tool

import config

_API_INITIALIZED = False
_ad_account = None


def _init_api():
    """Lazily initialize the Facebook Ads API."""
    global _API_INITIALIZED, _ad_account
    if _API_INITIALIZED:
        return _ad_account

    if not config.META_ACCESS_TOKEN or not config.META_AD_ACCOUNT_ID:
        return None

    try:
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.adaccount import AdAccount

        FacebookAdsApi.init(
            app_id=config.META_APP_ID or None,
            app_secret=config.META_APP_SECRET or None,
            access_token=config.META_ACCESS_TOKEN,
        )
        _ad_account = AdAccount(f"act_{config.META_AD_ACCOUNT_ID}")
        _API_INITIALIZED = True
        return _ad_account
    except Exception as e:
        _API_INITIALIZED = True
        return None


def _missing_key():
    return json.dumps({
        "error": "Meta Ads API not configured. Add META_ACCESS_TOKEN and META_AD_ACCOUNT_ID to .env",
        "skipped": True,
    })


def _parse_date_range(date_range: str) -> dict:
    """Convert our standard date_range strings to Meta's time_range format."""
    today = datetime.now()
    if date_range == "last_7_days":
        since = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif date_range == "last_30_days":
        since = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    elif date_range == "last_90_days":
        since = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    elif date_range == "last_120_days":
        since = (today - timedelta(days=120)).strftime("%Y-%m-%d")
    elif ":" in date_range:
        parts = date_range.split(":")
        return {"since": parts[0], "until": parts[1]}
    else:
        since = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    until = today.strftime("%Y-%m-%d")
    return {"since": since, "until": until}


def _is_target_country(code: str) -> bool:
    """Check if a country code is in Sourcy's target markets."""
    return code.upper() in [c.upper() for c in config.ALL_VALID_CODES]


def _extract_funnel_actions(actions: Optional[list]) -> dict:
    """Extract full funnel metrics from Meta's actions array.

    Returns dict with link_clicks, landing_page_views, leads, messaging_replies,
    and total conversions (leads + messaging).
    """
    result = {
        "link_clicks": 0,
        "landing_page_views": 0,
        "leads": 0,
        "messaging_replies": 0,
        "conversions": 0,
    }
    if not actions:
        return result
    for a in actions:
        atype = a.get("action_type", "")
        value = int(a.get("value", 0))
        if atype == "link_click":
            result["link_clicks"] += value
        elif atype == "landing_page_view":
            result["landing_page_views"] += value
        elif atype in ("lead", "offsite_conversion.fb_pixel_lead"):
            result["leads"] += value
        elif atype == "onsite_conversion.messaging_first_reply":
            result["messaging_replies"] += value
    result["conversions"] = result["leads"] + result["messaging_replies"]
    return result


# ─── Tool 1: Campaign Overview ─────────────────────────────────────────

@function_tool
def get_meta_campaigns(date_range: str = "last_30_days") -> str:
    """Get all Meta (Facebook/Instagram) ad campaigns with performance metrics.
    Shows campaign name, status, objective, budget, spend, CTR, CPC, conversions.

    Args:
        date_range: Time period — 'last_7_days', 'last_30_days', 'last_90_days',
                    or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        from facebook_business.adobjects.campaign import Campaign

        time_range = _parse_date_range(date_range)
        campaigns_raw = account.get_campaigns(
            fields=[
                Campaign.Field.name,
                Campaign.Field.status,
                Campaign.Field.objective,
                Campaign.Field.daily_budget,
                Campaign.Field.lifetime_budget,
                Campaign.Field.start_time,
                Campaign.Field.stop_time,
                Campaign.Field.created_time,
                Campaign.Field.effective_status,
            ],
        )

        campaigns = []
        for camp in campaigns_raw:
            camp_id = camp["id"]
            # Get insights for this campaign
            try:
                insights = camp.get_insights(
                    fields=[
                        "spend", "impressions", "reach", "frequency",
                        "clicks", "unique_clicks", "ctr", "unique_ctr",
                        "cpc", "cpm", "outbound_clicks",
                        "quality_ranking", "engagement_rate_ranking",
                        "conversion_rate_ranking",
                        "actions", "cost_per_action_type",
                    ],
                    params={"time_range": time_range},
                )
                _time.sleep(0.3)  # Rate limit
                ins = insights[0] if insights else {}
            except Exception:
                ins = {}

            # Extract full funnel from actions
            funnel = _extract_funnel_actions(ins.get("actions"))

            # Compute campaign duration
            start_time = camp.get("start_time", "")
            days_running = None
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    stop_time = camp.get("stop_time", "")
                    if stop_time:
                        end_dt = datetime.fromisoformat(stop_time.replace("Z", "+00:00"))
                    else:
                        end_dt = datetime.now(start_dt.tzinfo) if start_dt.tzinfo else datetime.now()
                    days_running = (end_dt - start_dt).days
                except Exception:
                    pass

            effective_status = camp.get("effective_status", "")
            is_learning = "LEARNING" in effective_status.upper() if effective_status else False

            # Extract outbound clicks
            outbound_clicks = 0
            outbound_data = ins.get("outbound_clicks", [])
            if isinstance(outbound_data, list):
                for oc in outbound_data:
                    if oc.get("action_type") == "outbound_click":
                        outbound_clicks = int(oc.get("value", 0))

            campaigns.append({
                "campaign_id": camp_id,
                "name": camp.get("name", ""),
                "status": camp.get("status", ""),
                "effective_status": effective_status,
                "objective": camp.get("objective", ""),
                "daily_budget": camp.get("daily_budget", "N/A"),
                "lifetime_budget": camp.get("lifetime_budget", "N/A"),
                "spend": ins.get("spend", "0"),
                "impressions": ins.get("impressions", "0"),
                "reach": ins.get("reach", "0"),
                "frequency": ins.get("frequency", "0"),
                "clicks": ins.get("clicks", "0"),
                "unique_clicks": ins.get("unique_clicks", "0"),
                "ctr": ins.get("ctr", "0"),
                "unique_ctr": ins.get("unique_ctr", "0"),
                "cpc": ins.get("cpc", "0"),
                "cpm": ins.get("cpm", "0"),
                "outbound_clicks": outbound_clicks,
                "quality_ranking": ins.get("quality_ranking", "N/A"),
                "engagement_rate_ranking": ins.get("engagement_rate_ranking", "N/A"),
                "conversion_rate_ranking": ins.get("conversion_rate_ranking", "N/A"),
                "link_clicks": funnel["link_clicks"],
                "landing_page_views": funnel["landing_page_views"],
                "leads": funnel["leads"],
                "messaging_replies": funnel["messaging_replies"],
                "conversions": funnel["conversions"],
                "start_time": start_time or "N/A",
                "stop_time": camp.get("stop_time", "N/A"),
                "created_time": camp.get("created_time", "N/A"),
                "days_running": days_running,
                "is_learning_phase": is_learning,
            })

        return json.dumps({
            "date_range": time_range,
            "campaigns_found": len(campaigns),
            "campaigns": campaigns,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 2: Ad Set Targeting ───────────────────────────────────────────

@function_tool
def get_meta_adset_targeting(campaign_id: str) -> str:
    """Get targeting configuration for all ad sets in a campaign.
    Shows countries, demographics, interests, audiences, and flags NON-TARGET countries.

    Args:
        campaign_id: Meta campaign ID to inspect (e.g., '23851234567890')
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.adobjects.adset import AdSet

        campaign = Campaign(campaign_id)
        adsets = campaign.get_ad_sets(
            fields=[
                AdSet.Field.name,
                AdSet.Field.status,
                AdSet.Field.targeting,
                AdSet.Field.daily_budget,
                AdSet.Field.effective_status,
                AdSet.Field.start_time,
                AdSet.Field.created_time,
            ],
        )

        results = []
        for adset in adsets:
            targeting = adset.get("targeting", {})
            # Handle targeting as dict or object
            if hasattr(targeting, 'export_all_data'):
                targeting = targeting.export_all_data()
            elif isinstance(targeting, str):
                import ast
                try:
                    targeting = ast.literal_eval(str(targeting).replace("<Targeting> ", ""))
                except Exception:
                    targeting = {}

            geo = targeting.get("geo_locations", {})
            countries = geo.get("countries", [])
            cities = geo.get("cities", [])
            regions = geo.get("regions", [])

            # Extract country codes from cities/regions too
            city_countries = list(set(c.get("country", "") for c in cities if c.get("country")))
            all_geo_countries = list(set(countries + city_countries))

            # Flag non-target countries
            non_target = [c for c in all_geo_countries if not _is_target_country(c)]
            target = [c for c in all_geo_countries if _is_target_country(c)]

            # Extract ALL audience details from flexible_spec
            interests = []
            behaviors = []
            work_positions = []
            work_employers = []
            for spec in targeting.get("flexible_spec", []):
                for interest in spec.get("interests", []):
                    interests.append(interest.get("name", ""))
                for behavior in spec.get("behaviors", []):
                    behaviors.append(behavior.get("name", ""))
                for wp in spec.get("work_positions", []):
                    work_positions.append(wp.get("name", ""))
                for we in spec.get("work_employers", []):
                    work_employers.append(we.get("name", ""))

            # Advantage audience / auto-expansion
            targeting_auto = targeting.get("targeting_automation", {})
            advantage_audience = targeting_auto.get("advantage_audience", 0)

            adset_effective = adset.get("effective_status", "")
            adset_learning = "LEARNING" in adset_effective.upper() if adset_effective else False

            results.append({
                "adset_id": adset["id"],
                "name": adset.get("name", ""),
                "status": adset.get("status", ""),
                "effective_status": adset_effective,
                "is_in_learning_phase": adset_learning,
                "start_time": adset.get("start_time", "N/A"),
                "created_time": adset.get("created_time", "N/A"),
                "daily_budget": adset.get("daily_budget", "N/A"),
                "optimization_goal": adset.get("optimization_goal", "N/A"),
                "targeting": {
                    "countries": countries,
                    "cities": [{"name": c.get("name"), "country": c.get("country"),
                                "radius": c.get("radius")} for c in cities],
                    "regions": regions,
                    "all_geo_countries": all_geo_countries,
                    "target_countries": target,
                    "non_target_countries": non_target,
                    "has_non_target_issue": len(non_target) > 0,
                    "age_min": targeting.get("age_min", "N/A"),
                    "age_max": targeting.get("age_max", "N/A"),
                    "genders": targeting.get("genders", []),
                    "device_platforms": targeting.get("device_platforms", []),
                    "publisher_platforms": targeting.get("publisher_platforms", []),
                    "facebook_positions": targeting.get("facebook_positions", []),
                    "instagram_positions": targeting.get("instagram_positions", []),
                    "interests": interests,
                    "behaviors": behaviors,
                    "work_positions": work_positions,
                    "work_employers": work_employers,
                    "custom_audiences": [
                        {"id": ca.get("id"), "name": ca.get("name")}
                        for ca in targeting.get("custom_audiences", [])
                    ],
                    "excluded_custom_audiences": [
                        {"id": ca.get("id"), "name": ca.get("name")}
                        for ca in targeting.get("excluded_custom_audiences", [])
                    ],
                    "advantage_audience_enabled": advantage_audience == 1,
                    "location_types": geo.get("location_types", []),
                },
            })

        return json.dumps({
            "campaign_id": campaign_id,
            "adsets_found": len(results),
            "adsets": results,
            "warning": "Non-target countries detected in targeting!" if any(
                r["targeting"]["has_non_target_issue"] for r in results
            ) else None,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 3: Ad Performance by Breakdown ────────────────────────────────

@function_tool
def get_meta_ad_performance(date_range: str = "last_30_days", breakdown: str = "country") -> str:
    """Get Meta ad performance broken down by a dimension.
    Use to see which countries, age groups, genders, or devices perform best/worst.

    Args:
        date_range: Time period — 'last_7_days', 'last_30_days', 'last_90_days'
        breakdown: Dimension — 'country', 'age', 'gender', 'device_platform', 'publisher_platform'
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        time_range = _parse_date_range(date_range)
        insights = account.get_insights(
            fields=[
                "spend", "impressions", "clicks", "ctr", "cpc",
                "actions", "cost_per_action_type",
            ],
            params={
                "time_range": time_range,
                "breakdowns": [breakdown],
                "level": "account",
                "limit": 50,
            },
        )

        rows = []
        for ins in insights:
            funnel = _extract_funnel_actions(ins.get("actions"))

            row = {
                breakdown: ins.get(breakdown, "N/A"),
                "spend": ins.get("spend", "0"),
                "impressions": ins.get("impressions", "0"),
                "clicks": ins.get("clicks", "0"),
                "ctr": ins.get("ctr", "0"),
                "cpc": ins.get("cpc", "0"),
                "link_clicks": funnel["link_clicks"],
                "landing_page_views": funnel["landing_page_views"],
                "leads": funnel["leads"],
                "messaging_replies": funnel["messaging_replies"],
                "conversions": funnel["conversions"],
            }

            # Annotate countries with target flag
            if breakdown == "country":
                country_code = ins.get("country", "")
                row["is_target"] = _is_target_country(country_code)

            rows.append(row)

        # Sort by spend descending
        rows.sort(key=lambda x: float(x.get("spend", 0)), reverse=True)

        return json.dumps({
            "date_range": time_range,
            "breakdown": breakdown,
            "rows_found": len(rows),
            "rows": rows,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 4: Ad Creatives ──────────────────────────────────────────────

@function_tool
def get_meta_ad_creatives(campaign_id: str) -> str:
    """Get creative details (headlines, body text, images, CTAs) for ads in a campaign.
    Returns image URLs that can be embedded in artifacts for visual review.

    Args:
        campaign_id: Meta campaign ID to inspect
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.adobjects.ad import Ad
        from facebook_business.adobjects.adcreative import AdCreative

        campaign = Campaign(campaign_id)
        ads = campaign.get_ads(
            fields=[
                Ad.Field.name,
                Ad.Field.status,
                Ad.Field.creative,
            ],
        )

        creatives = []
        for ad in ads[:20]:  # Limit to 20 ads
            creative_id = ad.get("creative", {}).get("id")
            if not creative_id:
                continue

            try:
                creative = AdCreative(creative_id).api_get(fields=[
                    AdCreative.Field.title,
                    AdCreative.Field.body,
                    AdCreative.Field.link_url,
                    AdCreative.Field.call_to_action_type,
                    AdCreative.Field.image_url,
                    AdCreative.Field.thumbnail_url,
                    AdCreative.Field.object_story_spec,
                    AdCreative.Field.asset_feed_spec,
                ])
                _time.sleep(0.3)

                # Extract from object_story_spec if available
                story = creative.get("object_story_spec", {})
                if hasattr(story, 'export_all_data'):
                    story = story.export_all_data()
                link_data = story.get("link_data", {})
                video_data = story.get("video_data", {})

                # Extract from asset_feed_spec (multiple headlines/descriptions)
                asset_feed = creative.get("asset_feed_spec", {})
                if hasattr(asset_feed, 'export_all_data'):
                    asset_feed = asset_feed.export_all_data()

                headline_variants = [t.get("text", "") for t in asset_feed.get("titles", [])]
                body_variants = [b.get("text", "") for b in asset_feed.get("bodies", [])]
                description_variants = [d.get("text", "") for d in asset_feed.get("descriptions", [])]

                # Get CTA from video_data if present
                cta_type = creative.get("call_to_action_type", "")
                if not cta_type and video_data:
                    cta_info = video_data.get("call_to_action", {})
                    cta_type = cta_info.get("type", "")
                    cta_destination = cta_info.get("value", {}).get("app_destination", "")
                else:
                    cta_destination = ""

                # WhatsApp welcome message
                welcome_msg = ""
                if video_data.get("page_welcome_message"):
                    try:
                        wm = json.loads(video_data["page_welcome_message"])
                        welcome_msg = wm.get("text_format", {}).get("message", {}).get("text", "")
                        ice_breakers = [ib.get("title", "") for ib in
                                        wm.get("text_format", {}).get("message", {}).get("ice_breakers", [])]
                    except Exception:
                        ice_breakers = []
                else:
                    ice_breakers = []

                creatives.append({
                    "ad_id": ad["id"],
                    "ad_name": ad.get("name", ""),
                    "ad_status": ad.get("status", ""),
                    "headline": creative.get("title", ""),
                    "headline_variants": headline_variants,
                    "body": creative.get("body", ""),
                    "body_variants": body_variants,
                    "description": link_data.get("description", ""),
                    "description_variants": description_variants,
                    "link_url": creative.get("link_url", link_data.get("link", video_data.get("call_to_action", {}).get("value", {}).get("link", ""))),
                    "cta_type": cta_type,
                    "cta_destination": cta_destination,
                    "image_url": creative.get("image_url", video_data.get("image_url", "")),
                    "thumbnail_url": creative.get("thumbnail_url", ""),
                    "has_video": bool(video_data.get("video_id")),
                    "whatsapp_welcome_message": welcome_msg,
                    "whatsapp_ice_breakers": ice_breakers,
                    "optimization_type": asset_feed.get("optimization_type", ""),
                })
            except Exception as ex:
                creatives.append({
                    "ad_id": ad["id"],
                    "ad_name": ad.get("name", ""),
                    "error": str(ex),
                })
                continue

        return json.dumps({
            "campaign_id": campaign_id,
            "creatives_found": len(creatives),
            "creatives": creatives,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 5: Spend by Country ──────────────────────────────────────────

@function_tool
def get_meta_spend_by_country(date_range: str = "last_30_days") -> str:
    """Get Meta ad spend broken down by country, with target market flagging.
    Calculates total wasted spend on non-target countries.

    Args:
        date_range: Time period — 'last_7_days', 'last_30_days', 'last_90_days'
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        time_range = _parse_date_range(date_range)
        insights = account.get_insights(
            fields=[
                "spend", "impressions", "clicks", "ctr", "cpc",
                "actions", "cost_per_action_type",
            ],
            params={
                "time_range": time_range,
                "breakdowns": ["country"],
                "level": "account",
                "limit": 100,
            },
        )

        countries = []
        total_spend = 0
        wasted_spend = 0

        for ins in insights:
            code = ins.get("country", "")
            spend = float(ins.get("spend", 0))
            is_target = _is_target_country(code)
            total_spend += spend
            if not is_target:
                wasted_spend += spend

            funnel = _extract_funnel_actions(ins.get("actions"))

            countries.append({
                "country_code": code,
                "is_target": is_target,
                "spend": f"{spend:.2f}",
                "impressions": ins.get("impressions", "0"),
                "clicks": ins.get("clicks", "0"),
                "ctr": ins.get("ctr", "0"),
                "cpc": ins.get("cpc", "0"),
                "link_clicks": funnel["link_clicks"],
                "landing_page_views": funnel["landing_page_views"],
                "leads": funnel["leads"],
                "conversions": funnel["conversions"],
            })

        countries.sort(key=lambda x: float(x["spend"]), reverse=True)

        return json.dumps({
            "date_range": time_range,
            "total_spend": f"{total_spend:.2f}",
            "wasted_spend_non_target": f"{wasted_spend:.2f}",
            "wasted_percentage": f"{(wasted_spend / total_spend * 100):.1f}%" if total_spend > 0 else "0%",
            "countries_found": len(countries),
            "countries": countries,
            "alert": f"${wasted_spend:.0f} spent on non-target countries!" if wasted_spend > 50 else None,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 6: Audience Configuration ────────────────────────────────────

@function_tool
def get_meta_audience_overlap(campaign_id: str) -> str:
    """Get audience configuration for all ad sets in a campaign.
    Shows custom audiences, lookalike audiences, and interest targeting.

    Args:
        campaign_id: Meta campaign ID to inspect
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.adobjects.adset import AdSet

        campaign = Campaign(campaign_id)
        adsets = campaign.get_ad_sets(
            fields=[
                AdSet.Field.name,
                AdSet.Field.targeting,
                AdSet.Field.promoted_object,
            ],
        )

        results = []
        for adset in adsets:
            targeting = adset.get("targeting", {})
            if hasattr(targeting, 'export_all_data'):
                targeting = targeting.export_all_data()

            # Custom audiences
            custom = targeting.get("custom_audiences", [])
            excluded = targeting.get("excluded_custom_audiences", [])

            # ALL flexible_spec data
            interests = []
            behaviors = []
            work_positions = []
            work_employers = []
            for spec in targeting.get("flexible_spec", []):
                interests.extend(spec.get("interests", []))
                behaviors.extend(spec.get("behaviors", []))
                work_positions.extend(spec.get("work_positions", []))
                work_employers.extend(spec.get("work_employers", []))

            results.append({
                "adset_id": adset["id"],
                "name": adset.get("name", ""),
                "custom_audiences": [
                    {"id": ca.get("id"), "name": ca.get("name")} for ca in custom
                ],
                "excluded_audiences": [
                    {"id": ca.get("id"), "name": ca.get("name")} for ca in excluded
                ],
                "interests": [i.get("name", "") for i in interests],
                "behaviors": [b.get("name", "") for b in behaviors],
                "work_positions": [wp.get("name", "") for wp in work_positions],
                "work_employers": [we.get("name", "") for we in work_employers],
                "has_custom_audience": len(custom) > 0,
                "has_lookalike": any("lookalike" in ca.get("name", "").lower() for ca in custom),
                "audience_breadth": "narrow" if len(custom) > 0 else ("medium" if work_positions else "broad"),
                "audience_assessment": {
                    "has_b2b_signals": len(work_positions) > 0,
                    "has_competitor_targeting": any("alibaba" in i.get("name", "").lower() for i in interests),
                    "has_behavioral_targeting": len(behaviors) > 0,
                    "missing": [
                        x for x in [
                            "custom_audiences" if not custom else None,
                            "lookalike_audiences" if not any("lookalike" in ca.get("name", "").lower() for ca in custom) else None,
                            "work_position_targeting" if not work_positions else None,
                        ] if x
                    ],
                },
            })

        return json.dumps({
            "campaign_id": campaign_id,
            "adsets_found": len(results),
            "adsets": results,
            "recommendation": "Consider adding custom audiences (website visitors, email lists) for better targeting"
            if not any(r["has_custom_audience"] for r in results) else None,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 7: Campaign Trend (Time-Series) ────────────────────────────

@function_tool
def get_meta_campaign_trend(
    campaign_id: str = "",
    date_range: str = "last_30_days",
    time_increment: str = "7",
) -> str:
    """Get Meta campaign performance over time with daily or weekly breakdown.
    Shows how metrics changed over the date range to identify trends, spikes, and declines.

    Args:
        campaign_id: Optional campaign ID. If empty, returns account-level trend.
        date_range: Time period — 'last_7_days', 'last_30_days', 'last_90_days', or 'YYYY-MM-DD:YYYY-MM-DD'
        time_increment: '1' for daily, '7' for weekly breakdown. Default '7' (weekly).
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        time_range = _parse_date_range(date_range)
        params = {
            "time_range": time_range,
            "time_increment": int(time_increment),
            "limit": 200,
        }

        if campaign_id:
            from facebook_business.adobjects.campaign import Campaign
            source = Campaign(campaign_id)
        else:
            source = account
            params["level"] = "account"

        insights = source.get_insights(
            fields=[
                "spend", "impressions", "clicks", "ctr", "cpc",
                "actions", "cost_per_action_type",
            ],
            params=params,
        )

        periods = []
        prev_spend = None
        for ins in insights:
            funnel = _extract_funnel_actions(ins.get("actions"))
            spend = float(ins.get("spend", 0))

            # Compute period-over-period change
            spend_change = None
            if prev_spend is not None and prev_spend > 0:
                spend_change = round((spend - prev_spend) / prev_spend * 100, 1)

            # Build human-readable period label from date_start / date_stop
            ds = ins.get("date_start", "")
            de = ins.get("date_stop", "")
            try:
                _ds = datetime.strptime(ds, "%Y-%m-%d")
                _de = datetime.strptime(de, "%Y-%m-%d")
                week_label = f"{_ds.strftime('%b %d')}–{_de.strftime('%b %d')}"
                week_start = _ds.strftime("%b %d")
                week_end = _de.strftime("%b %d")
            except Exception:
                week_label = ds
                week_start = ds
                week_end = de

            periods.append({
                "date_start": ds,
                "date_stop": de,
                "week_label": week_label,   # e.g. "Mar 17–23" — use in charts/tables (NOT W## labels)
                "week_start": week_start,   # e.g. "Mar 17"
                "week_end": week_end,       # e.g. "Mar 23"
                "spend": f"{spend:.2f}",
                "impressions": ins.get("impressions", "0"),
                "clicks": ins.get("clicks", "0"),
                "ctr": ins.get("ctr", "0"),
                "cpc": ins.get("cpc", "0"),
                "link_clicks": funnel["link_clicks"],
                "landing_page_views": funnel["landing_page_views"],
                "leads": funnel["leads"],
                "messaging_replies": funnel["messaging_replies"],
                "conversions": funnel["conversions"],
                "spend_change_pct": spend_change,
            })
            prev_spend = spend

        # Identify best/worst periods
        if periods:
            best = max(periods, key=lambda p: float(p["ctr"] or 0))
            worst = min(periods, key=lambda p: float(p["ctr"] or 0))
        else:
            best = worst = None

        week_labels = [p["week_label"] for p in periods]
        return json.dumps({
            "campaign_id": campaign_id or "account_level",
            "date_range": time_range,
            "time_increment_days": int(time_increment),
            "periods_found": len(periods),
            "week_labels": week_labels,   # ["Mar 17–23", "Mar 24–30", …] — use for chart X-axis
            "periods": periods,
            "best_period": best,
            "worst_period": worst,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 7b: Week-over-Week Comparison ───────────────────────────────

@function_tool
def get_meta_wow_comparison(campaign_id: str = "") -> str:
    """Get Week-over-Week comparison for a Meta campaign or account.
    Returns this week vs last week metrics with % change for every key metric.
    Designed for the WoW funnel table in the artifact.

    Args:
        campaign_id: Optional campaign ID. If empty, returns account-level WoW.
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        from datetime import datetime, timedelta

        today = datetime.now()
        # This week: last 7 days
        tw_end = today.strftime("%Y-%m-%d")
        tw_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        # Last week: 8-14 days ago
        lw_end = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        lw_start = (today - timedelta(days=14)).strftime("%Y-%m-%d")

        def _fetch_period(since, until):
            params = {
                "time_range": {"since": since, "until": until},
                "limit": 1,
            }
            if campaign_id:
                from facebook_business.adobjects.campaign import Campaign
                source = Campaign(campaign_id)
            else:
                source = account
                params["level"] = "account"

            insights = source.get_insights(
                fields=[
                    "spend", "impressions", "clicks", "ctr", "cpc",
                    "actions", "cost_per_action_type",
                ],
                params=params,
            )
            for ins in insights:
                funnel = _extract_funnel_actions(ins.get("actions"))
                spend = float(ins.get("spend", 0))
                clicks = int(ins.get("clicks", 0))
                impressions = int(ins.get("impressions", 0))
                ctr = float(ins.get("ctr", 0))
                cpc = float(ins.get("cpc", 0))
                cpl = spend / funnel["conversions"] if funnel["conversions"] > 0 else 0
                return {
                    "spend": round(spend, 2),
                    "impressions": impressions,
                    "clicks": clicks,
                    "ctr": round(ctr, 4),
                    "cpc": round(cpc, 2),
                    "link_clicks": funnel["link_clicks"],
                    "landing_page_views": funnel["landing_page_views"],
                    "leads": funnel["leads"],
                    "messaging_replies": funnel["messaging_replies"],
                    "conversions": funnel["conversions"],
                    "cost_per_lead": round(cpl, 2),
                }
            return None

        this_week = _fetch_period(tw_start, tw_end)
        last_week = _fetch_period(lw_start, lw_end)

        def _pct_change(curr, prev):
            if prev and prev > 0:
                return round((curr - prev) / prev * 100, 1)
            return None

        changes = {}
        if this_week and last_week:
            for key in this_week:
                tw_val = this_week[key]
                lw_val = last_week[key]
                if isinstance(tw_val, (int, float)) and isinstance(lw_val, (int, float)):
                    changes[f"{key}_change_pct"] = _pct_change(tw_val, lw_val)

        return json.dumps({
            "campaign_id": campaign_id or "account_level",
            "this_week": {"period": f"{tw_start} to {tw_end}", "metrics": this_week},
            "last_week": {"period": f"{lw_start} to {lw_end}", "metrics": last_week},
            "changes": changes,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 8: Ad-Level Performance with Creatives ─────────────────────

@function_tool
def get_meta_ad_level_performance(campaign_id: str, date_range: str = "last_30_days") -> str:
    """Get per-ad performance with linked creative data for a campaign.
    Shows which specific ads (headlines, images, CTAs) performed best/worst by spend, CTR, conversions.

    Args:
        campaign_id: Meta campaign ID to analyze
        date_range: Time period — 'last_7_days', 'last_30_days', 'last_90_days'
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.adobjects.ad import Ad
        from facebook_business.adobjects.adcreative import AdCreative

        time_range = _parse_date_range(date_range)

        # Get per-ad insights in a single efficient call
        campaign = Campaign(campaign_id)
        ad_insights = campaign.get_insights(
            fields=[
                "ad_id", "ad_name", "spend", "impressions", "clicks",
                "ctr", "cpc", "actions", "cost_per_action_type",
            ],
            params={
                "time_range": time_range,
                "level": "ad",
                "limit": 50,
            },
        )

        # Build insights lookup by ad_id
        insights_by_ad = {}
        for ins in ad_insights:
            insights_by_ad[ins.get("ad_id", "")] = ins

        # Get ads with creative references
        ads = campaign.get_ads(
            fields=[Ad.Field.name, Ad.Field.status, Ad.Field.creative],
        )

        results = []
        for ad in ads[:30]:  # Limit to 30 ads
            ad_id = ad["id"]
            ins = insights_by_ad.get(ad_id, {})
            funnel = _extract_funnel_actions(ins.get("actions"))

            # Fetch creative details
            creative_id = ad.get("creative", {}).get("id")
            creative_info = {}
            if creative_id:
                try:
                    creative = AdCreative(creative_id).api_get(fields=[
                        AdCreative.Field.title,
                        AdCreative.Field.body,
                        AdCreative.Field.image_url,
                        AdCreative.Field.thumbnail_url,
                        AdCreative.Field.call_to_action_type,
                        AdCreative.Field.asset_feed_spec,
                    ])
                    _time.sleep(0.2)

                    asset_feed = creative.get("asset_feed_spec", {})
                    if hasattr(asset_feed, 'export_all_data'):
                        asset_feed = asset_feed.export_all_data()

                    creative_info = {
                        "headline": creative.get("title", ""),
                        "headline_variants": [t.get("text", "") for t in asset_feed.get("titles", [])],
                        "body": creative.get("body", ""),
                        "image_url": creative.get("image_url", ""),
                        "thumbnail_url": creative.get("thumbnail_url", ""),
                        "cta_type": creative.get("call_to_action_type", ""),
                    }
                except Exception:
                    creative_info = {"error": "Could not fetch creative"}

            spend = float(ins.get("spend", 0))
            results.append({
                "ad_id": ad_id,
                "ad_name": ad.get("name", ""),
                "status": ad.get("status", ""),
                "spend": f"{spend:.2f}",
                "impressions": ins.get("impressions", "0"),
                "clicks": ins.get("clicks", "0"),
                "ctr": ins.get("ctr", "0"),
                "cpc": ins.get("cpc", "0"),
                "link_clicks": funnel["link_clicks"],
                "landing_page_views": funnel["landing_page_views"],
                "leads": funnel["leads"],
                "conversions": funnel["conversions"],
                **creative_info,
            })

        # Sort by spend descending
        results.sort(key=lambda x: float(x.get("spend", 0)), reverse=True)

        # Identify best/worst performers
        with_spend = [r for r in results if float(r.get("spend", 0)) > 0]
        best_ctr = max(with_spend, key=lambda r: float(r.get("ctr", 0))) if with_spend else None
        best_conv = max(with_spend, key=lambda r: r.get("conversions", 0)) if with_spend else None
        worst_ctr = min(with_spend, key=lambda r: float(r.get("ctr", 0))) if with_spend else None

        return json.dumps({
            "campaign_id": campaign_id,
            "date_range": time_range,
            "ads_found": len(results),
            "ads": results,
            "best_ctr_ad": best_ctr.get("ad_name") if best_ctr else None,
            "best_converting_ad": best_conv.get("ad_name") if best_conv else None,
            "worst_ctr_ad": worst_ctr.get("ad_name") if worst_ctr else None,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 9: Multi-Week Trend (5 weeks) ─────────────────────────────

@function_tool
def get_meta_multi_week_trend(campaign_id: str = "", weeks: int = 5) -> str:
    """Get 5-week performance trend for a campaign or the whole account.
    Returns weekly breakdown with reach, frequency, quality rankings, and full funnel.
    Essential for spotting creative fatigue, audience saturation, and budget trends.

    Args:
        campaign_id: Optional campaign ID. If empty, returns account-level trend.
        weeks: Number of weeks to analyze (default 5, max 12).
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        days = weeks * 7
        today = datetime.now()
        since = (today - timedelta(days=days)).strftime("%Y-%m-%d")
        until = today.strftime("%Y-%m-%d")

        params = {
            "time_range": {"since": since, "until": until},
            "time_increment": 7,
            "limit": 200,
        }

        if campaign_id:
            from facebook_business.adobjects.campaign import Campaign
            source = Campaign(campaign_id)
        else:
            source = account
            params["level"] = "account"

        insights = source.get_insights(
            fields=[
                "spend", "impressions", "reach", "frequency",
                "clicks", "unique_clicks", "ctr", "unique_ctr",
                "cpc", "cpm", "outbound_clicks",
                "quality_ranking", "engagement_rate_ranking",
                "conversion_rate_ranking",
                "actions", "cost_per_action_type",
            ],
            params=params,
        )

        periods = []
        prev_spend = None
        for ins in insights:
            funnel = _extract_funnel_actions(ins.get("actions"))
            spend = float(ins.get("spend", 0))

            spend_change = None
            if prev_spend is not None and prev_spend > 0:
                spend_change = round((spend - prev_spend) / prev_spend * 100, 1)

            # Extract outbound clicks
            outbound = 0
            ob_data = ins.get("outbound_clicks", [])
            if isinstance(ob_data, list):
                for oc in ob_data:
                    if oc.get("action_type") == "outbound_click":
                        outbound = int(oc.get("value", 0))

            # Build human-readable week label from date_start / date_stop
            ds = ins.get("date_start", "")
            de = ins.get("date_stop", "")
            try:
                _ds = datetime.strptime(ds, "%Y-%m-%d")
                _de = datetime.strptime(de, "%Y-%m-%d")
                week_label = f"{_ds.strftime('%b %d')}–{_de.strftime('%b %d')}"
                week_start = _ds.strftime("%b %d")
                week_end = _de.strftime("%b %d")
            except Exception:
                week_label = ds
                week_start = ds
                week_end = de

            periods.append({
                "date_start": ds,
                "date_stop": de,
                "week_label": week_label,   # e.g. "Mar 17–23" — use this in charts/tables (NOT W## labels)
                "week_start": week_start,   # e.g. "Mar 17"
                "week_end": week_end,       # e.g. "Mar 23"
                "spend": f"{spend:.2f}",
                "impressions": ins.get("impressions", "0"),
                "reach": ins.get("reach", "0"),
                "frequency": ins.get("frequency", "0"),
                "clicks": ins.get("clicks", "0"),
                "unique_clicks": ins.get("unique_clicks", "0"),
                "ctr": ins.get("ctr", "0"),
                "unique_ctr": ins.get("unique_ctr", "0"),
                "cpc": ins.get("cpc", "0"),
                "cpm": ins.get("cpm", "0"),
                "outbound_clicks": outbound,
                "quality_ranking": ins.get("quality_ranking", "N/A"),
                "engagement_rate_ranking": ins.get("engagement_rate_ranking", "N/A"),
                "conversion_rate_ranking": ins.get("conversion_rate_ranking", "N/A"),
                "link_clicks": funnel["link_clicks"],
                "landing_page_views": funnel["landing_page_views"],
                "leads": funnel["leads"],
                "messaging_replies": funnel["messaging_replies"],
                "conversions": funnel["conversions"],
                "spend_change_pct": spend_change,
            })
            prev_spend = spend

        week_labels = [p["week_label"] for p in periods]
        return json.dumps({
            "campaign_id": campaign_id or "account_level",
            "weeks_requested": weeks,
            "periods_found": len(periods),
            "week_labels": week_labels,   # ["Mar 17–23", "Mar 24–30", …] — use for chart X-axis
            "periods": periods,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})


# ─── Tool 10: Demographic Breakdown ─────────────────────────────────

@function_tool
def get_meta_demographic_breakdown(date_range: str = "last_30_days") -> str:
    """Get Meta ad performance broken down by demographics (age + gender)
    and by platform (Facebook vs Instagram vs Audience Network).
    Shows which demographics and platforms convert best for Sourcy.

    Args:
        date_range: Time period — 'last_7_days', 'last_30_days', 'last_90_days'
    """
    account = _init_api()
    if not account:
        return _missing_key()

    try:
        time_range = _parse_date_range(date_range)
        fields = [
            "spend", "impressions", "reach", "clicks", "ctr", "cpc",
            "actions", "cost_per_action_type",
        ]

        # Age + Gender breakdown
        age_gender_insights = account.get_insights(
            fields=fields,
            params={
                "time_range": time_range,
                "breakdowns": ["age", "gender"],
                "level": "account",
                "limit": 100,
            },
        )

        by_age_gender = []
        for ins in age_gender_insights:
            funnel = _extract_funnel_actions(ins.get("actions"))
            by_age_gender.append({
                "age": ins.get("age", ""),
                "gender": ins.get("gender", ""),
                "spend": ins.get("spend", "0"),
                "impressions": ins.get("impressions", "0"),
                "reach": ins.get("reach", "0"),
                "clicks": ins.get("clicks", "0"),
                "ctr": ins.get("ctr", "0"),
                "cpc": ins.get("cpc", "0"),
                "conversions": funnel["conversions"],
                "leads": funnel["leads"],
            })
        by_age_gender.sort(key=lambda x: float(x.get("spend", 0)), reverse=True)

        _time.sleep(0.5)  # Rate limit

        # Publisher platform breakdown
        platform_insights = account.get_insights(
            fields=fields + ["reach", "frequency"],
            params={
                "time_range": time_range,
                "breakdowns": ["publisher_platform"],
                "level": "account",
                "limit": 10,
            },
        )

        by_platform = []
        for ins in platform_insights:
            funnel = _extract_funnel_actions(ins.get("actions"))
            by_platform.append({
                "platform": ins.get("publisher_platform", ""),
                "spend": ins.get("spend", "0"),
                "impressions": ins.get("impressions", "0"),
                "reach": ins.get("reach", "0"),
                "frequency": ins.get("frequency", "0"),
                "clicks": ins.get("clicks", "0"),
                "ctr": ins.get("ctr", "0"),
                "cpc": ins.get("cpc", "0"),
                "conversions": funnel["conversions"],
                "leads": funnel["leads"],
            })
        by_platform.sort(key=lambda x: float(x.get("spend", 0)), reverse=True)

        return json.dumps({
            "date_range": time_range,
            "by_age_gender": by_age_gender,
            "by_platform": by_platform,
            "top_demographic": by_age_gender[0] if by_age_gender else None,
            "top_platform": by_platform[0] if by_platform else None,
        })
    except Exception as e:
        return json.dumps({"error": f"Meta Ads API error: {str(e)}"})
