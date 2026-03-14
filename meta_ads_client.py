"""
Meta Ads API client for fetching account performance data.
Uses the Facebook Marketing API via facebook-business SDK.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad


class MetaAdsClient:
    """Client for pulling Meta Ads performance data."""

    # Core metrics for performance analysis
    CAMPAIGN_FIELDS = [
        "id", "name", "status", "objective", "daily_budget", "lifetime_budget",
    ]

    INSIGHTS_FIELDS = [
        "campaign_id", "campaign_name",
        "adset_id", "adset_name",
        "ad_id", "ad_name",
        "impressions", "reach", "frequency",
        "clicks", "unique_clicks",
        "spend", "cpm", "cpc", "ctr",
        "actions", "action_values",
        "cost_per_action_type",
        "video_p25_watched_actions", "video_p50_watched_actions",
        "video_p75_watched_actions", "video_p100_watched_actions",
        "date_start", "date_stop",
    ]

    def __init__(self, access_token: str, ad_account_id: str, app_id: str = "", app_secret: str = ""):
        self.ad_account_id = ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"
        FacebookAdsApi.init(app_id or "stub", app_secret or "stub", access_token)
        self.account = AdAccount(self.ad_account_id)

    def _date_range(self, days_back: int = 30) -> dict:
        end = datetime.now().date()
        start = end - timedelta(days=days_back - 1)
        return {"since": str(start), "until": str(end)}

    def get_account_info(self) -> dict:
        fields = ["id", "name", "currency", "timezone_name", "account_status"]
        return self.account.api_get(fields=fields).export_all_data()

    def get_campaigns(self) -> list[dict]:
        campaigns = self.account.get_campaigns(fields=self.CAMPAIGN_FIELDS)
        return [c.export_all_data() for c in campaigns]

    def get_campaign_insights(self, days_back: int = 30, level: str = "campaign") -> list[dict]:
        """Fetch insights at campaign / adset / ad level."""
        params = {
            "level": level,
            "date_preset": "last_30d" if days_back == 30 else "custom",
            "time_range": self._date_range(days_back),
            "breakdowns": [],
        }
        insights = self.account.get_insights(fields=self.INSIGHTS_FIELDS, params=params)
        return [i.export_all_data() for i in insights]

    def get_adset_insights(self, days_back: int = 30) -> list[dict]:
        return self.get_campaign_insights(days_back, level="adset")

    def get_ad_insights(self, days_back: int = 30) -> list[dict]:
        return self.get_campaign_insights(days_back, level="ad")

    def get_daily_breakdown(self, days_back: int = 30) -> list[dict]:
        """Day-by-day account-level spend and conversions."""
        params = {
            "level": "account",
            "time_increment": 1,
            "time_range": self._date_range(days_back),
        }
        fields = [
            "spend", "impressions", "clicks", "actions", "action_values",
            "cpm", "cpc", "ctr", "date_start",
        ]
        insights = self.account.get_insights(fields=fields, params=params)
        return [i.export_all_data() for i in insights]

    def collect_all(self, days_back: int = 30) -> dict:
        """Collect all data needed for a full analysis."""
        print(f"Fetching Meta Ads data for the last {days_back} days...")
        return {
            "account": self.get_account_info(),
            "campaigns": self.get_campaigns(),
            "campaign_insights": self.get_campaign_insights(days_back),
            "adset_insights": self.get_adset_insights(days_back),
            "ad_insights": self.get_ad_insights(days_back),
            "daily_trend": self.get_daily_breakdown(days_back),
            "fetched_at": datetime.now().isoformat(),
            "days_back": days_back,
        }
