"""
Generates realistic synthetic Meta Ads account data for demo/testing purposes.
Mimics a mid-sized DTC e-commerce brand spending ~$15k/month across multiple campaigns.
"""

from __future__ import annotations
import random
from datetime import date, timedelta


def _make_actions(purchases: float, revenue: float, leads: float,
                  atc: float, vc: float, new_cust: float) -> tuple[list, list]:
    actions = []
    action_values = []
    if purchases > 0:
        for at in ["purchase", "omni_purchase"]:
            actions.append({"action_type": at, "value": str(purchases)})
            action_values.append({"action_type": at, "value": str(revenue)})
    if leads > 0:
        actions.append({"action_type": "lead", "value": str(leads)})
    if atc > 0:
        actions.append({"action_type": "add_to_cart", "value": str(atc)})
    if vc > 0:
        actions.append({"action_type": "view_content", "value": str(vc)})
    if new_cust > 0:
        actions.append({"action_type": "new_customer_purchase", "value": str(new_cust)})
    return actions, action_values


CAMPAIGNS = [
    {
        "id": "camp_001", "name": "Prospecting — Lookalike 1-3%",
        "status": "ACTIVE", "objective": "OUTCOME_SALES",
        "daily_budget": "15000",
        # Performance profile: solid ROAS, moderate frequency
        "_profile": {"spend": 4200, "roas": 3.1, "frequency": 2.8, "ctr": 1.4, "cpm": 12.5,
                     "purchase_rate": 0.018, "lead_rate": 0.0, "atc_mult": 8, "vc_mult": 20,
                     "nca_rate": 0.72},
    },
    {
        "id": "camp_002", "name": "Retargeting — Website Visitors 30d",
        "status": "ACTIVE", "objective": "OUTCOME_SALES",
        "daily_budget": "8000",
        # High ROAS (warm audience), but high frequency — creative fatigue risk
        "_profile": {"spend": 2800, "roas": 5.2, "frequency": 4.8, "ctr": 2.1, "cpm": 9.8,
                     "purchase_rate": 0.042, "lead_rate": 0.0, "atc_mult": 5, "vc_mult": 12,
                     "nca_rate": 0.08},
    },
    {
        "id": "camp_003", "name": "Prospecting — Broad / Interest Stack",
        "status": "ACTIVE", "objective": "OUTCOME_SALES",
        "daily_budget": "12000",
        # Below target ROAS — needs work
        "_profile": {"spend": 3100, "roas": 1.4, "frequency": 2.1, "ctr": 0.7, "cpm": 16.2,
                     "purchase_rate": 0.006, "lead_rate": 0.0, "atc_mult": 9, "vc_mult": 25,
                     "nca_rate": 0.68},
    },
    {
        "id": "camp_004", "name": "Lead Gen — Email Capture",
        "status": "ACTIVE", "objective": "OUTCOME_LEADS",
        "daily_budget": "5000",
        # Lead gen — no purchases expected
        "_profile": {"spend": 1400, "roas": 0.0, "frequency": 1.9, "ctr": 1.8, "cpm": 8.4,
                     "purchase_rate": 0.0, "lead_rate": 0.085, "atc_mult": 0, "vc_mult": 0,
                     "nca_rate": 0.0},
    },
    {
        "id": "camp_005", "name": "Retention — Past Purchasers 90d",
        "status": "ACTIVE", "objective": "OUTCOME_SALES",
        "daily_budget": "4000",
        # Very high ROAS (existing customers), low NCA
        "_profile": {"spend": 980, "roas": 7.8, "frequency": 3.1, "ctr": 2.8, "cpm": 7.6,
                     "purchase_rate": 0.058, "lead_rate": 0.0, "atc_mult": 4, "vc_mult": 8,
                     "nca_rate": 0.04},
    },
    {
        "id": "camp_006", "name": "TOF — Video Views / Awareness",
        "status": "ACTIVE", "objective": "OUTCOME_AWARENESS",
        "daily_budget": "3000",
        # Brand awareness — spend with low direct conversion, new customers
        "_profile": {"spend": 820, "roas": 0.9, "frequency": 1.5, "ctr": 0.4, "cpm": 5.8,
                     "purchase_rate": 0.002, "lead_rate": 0.0, "atc_mult": 3, "vc_mult": 40,
                     "nca_rate": 0.90},
    },
    {
        "id": "camp_007", "name": "Dynamic Product Ads — Cart Abandoners",
        "status": "ACTIVE", "objective": "OUTCOME_SALES",
        "daily_budget": "6000",
        # DPA — good ROAS, high checkout rate
        "_profile": {"spend": 1650, "roas": 4.3, "frequency": 5.2, "ctr": 3.1, "cpm": 10.1,
                     "purchase_rate": 0.038, "lead_rate": 0.0, "atc_mult": 3, "vc_mult": 6,
                     "nca_rate": 0.06},
    },
    {
        "id": "camp_008", "name": "Prospecting — Competitor Interest",
        "status": "PAUSED", "objective": "OUTCOME_SALES",
        "daily_budget": "5000",
        # Paused — low historical spend, poor performance
        "_profile": {"spend": 420, "roas": 0.6, "frequency": 2.3, "ctr": 0.5, "cpm": 19.5,
                     "purchase_rate": 0.003, "lead_rate": 0.0, "atc_mult": 7, "vc_mult": 18,
                     "nca_rate": 0.75},
    },
]


def _campaign_insight(camp: dict) -> dict:
    p = camp["_profile"]
    spend = p["spend"]
    impressions = int(spend / p["cpm"] * 1000)
    reach = int(impressions / p["frequency"])
    clicks = int(impressions * p["ctr"] / 100)
    purchases = round(clicks * p["purchase_rate"], 1)
    revenue = round(purchases * spend * p["roas"] / max(purchases, 0.001), 2) if purchases > 0 else 0.0
    leads = round(clicks * p["lead_rate"], 1)
    atc = round(purchases * p["atc_mult"], 1)
    vc = round(atc * p["vc_mult"], 1) if atc > 0 else 0.0
    new_cust = round(purchases * p["nca_rate"], 1)
    actions, action_values = _make_actions(purchases, revenue, leads, atc, vc, new_cust)
    initiate_checkout = [{"action_type": "initiate_checkout", "value": str(round(atc * 0.6, 1))}] if atc > 0 else []

    return {
        "campaign_id": camp["id"],
        "campaign_name": camp["name"],
        "spend": str(spend),
        "impressions": str(impressions),
        "reach": str(reach),
        "frequency": str(round(p["frequency"], 2)),
        "clicks": str(clicks),
        "unique_clicks": str(int(clicks * 0.85)),
        "ctr": str(round(p["ctr"], 2)),
        "cpc": str(round(spend / max(clicks, 1), 2)),
        "cpm": str(round(p["cpm"], 2)),
        "actions": actions + initiate_checkout,
        "action_values": action_values,
        "date_start": str(date.today() - timedelta(days=29)),
        "date_stop": str(date.today()),
    }


def _adset_insights(camp: dict, n: int = 2) -> list[dict]:
    p = camp["_profile"]
    results = []
    for i in range(1, n + 1):
        spend = p["spend"] / n * random.uniform(0.7, 1.3)
        impr = int(spend / p["cpm"] * 1000)
        clicks = int(impr * p["ctr"] / 100 * random.uniform(0.8, 1.2))
        purchases = round(clicks * p["purchase_rate"] * random.uniform(0.5, 1.5), 1)
        revenue = round(purchases * (p["roas"] * spend / max(p["spend"], 1)) / max(purchases, 0.001) * spend, 2)
        actions, action_values = _make_actions(purchases, revenue, 0, round(purchases * p["atc_mult"], 1), 0, 0)
        results.append({
            "campaign_id": camp["id"],
            "campaign_name": camp["name"],
            "adset_id": f"{camp['id']}_as{i}",
            "adset_name": f"{camp['name']} · Ad Set {i}",
            "spend": str(round(spend, 2)),
            "impressions": str(impr),
            "reach": str(int(impr / p["frequency"])),
            "frequency": str(round(p["frequency"] * random.uniform(0.8, 1.2), 2)),
            "clicks": str(clicks),
            "ctr": str(round(p["ctr"] * random.uniform(0.7, 1.3), 2)),
            "cpc": str(round(spend / max(clicks, 1), 2)),
            "cpm": str(round(p["cpm"] * random.uniform(0.9, 1.1), 2)),
            "actions": actions,
            "action_values": action_values,
            "date_start": str(date.today() - timedelta(days=29)),
            "date_stop": str(date.today()),
        })
    return results


def _ad_insights(camp: dict, n: int = 3) -> list[dict]:
    p = camp["_profile"]
    results = []
    ad_names = [
        "UGC — Testimonial v1", "Static — Product Hero v2", "Video — 15s Hook v3",
        "Carousel — Benefits", "DPA Auto", "Reels — Unboxing"
    ]
    for i in range(1, n + 1):
        spend = p["spend"] / n * random.uniform(0.5, 1.5)
        impr = int(spend / p["cpm"] * 1000)
        clicks = int(impr * p["ctr"] / 100 * random.uniform(0.6, 1.4))
        purchases = round(clicks * p["purchase_rate"] * random.uniform(0.3, 2.0), 1)
        revenue = round(purchases * p["roas"] * random.uniform(0.8, 1.2) * spend / max(purchases * p["roas"], 0.001), 2) if purchases > 0 else 0
        actions, action_values = _make_actions(purchases, revenue, 0, 0, 0, 0)
        results.append({
            "campaign_id": camp["id"],
            "campaign_name": camp["name"],
            "adset_id": f"{camp['id']}_as1",
            "adset_name": f"{camp['name']} · Ad Set 1",
            "ad_id": f"{camp['id']}_ad{i}",
            "ad_name": ad_names[(i - 1) % len(ad_names)],
            "spend": str(round(spend, 2)),
            "impressions": str(impr),
            "frequency": str(round(p["frequency"] * random.uniform(0.7, 1.3), 2)),
            "clicks": str(clicks),
            "ctr": str(round(p["ctr"] * random.uniform(0.5, 1.8), 2)),
            "cpc": str(round(spend / max(clicks, 1), 2)),
            "cpm": str(round(p["cpm"] * random.uniform(0.85, 1.15), 2)),
            "actions": actions,
            "action_values": action_values,
            "date_start": str(date.today() - timedelta(days=29)),
            "date_stop": str(date.today()),
        })
    return results


def _daily_trend(days: int = 30) -> list[dict]:
    daily = []
    base_spend = 500
    for d in range(days):
        day_date = date.today() - timedelta(days=days - 1 - d)
        # Simulate weekend uplift and a mid-period dip
        weekday_mult = 1.15 if day_date.weekday() >= 5 else 1.0
        mid_dip = 0.85 if 10 <= d <= 14 else 1.0
        spend = base_spend * weekday_mult * mid_dip * random.uniform(0.85, 1.15)
        impr = int(spend / 11 * 1000)
        clicks = int(impr * 0.012)
        purchases = round(clicks * 0.02 * random.uniform(0.7, 1.3), 1)
        revenue = round(purchases * random.uniform(55, 85), 2)
        actions, action_values = _make_actions(purchases, revenue, 0, 0, 0, 0)
        daily.append({
            "spend": str(round(spend, 2)),
            "impressions": str(impr),
            "clicks": str(clicks),
            "ctr": str(round(clicks / max(impr, 1) * 100, 2)),
            "cpm": str(round(spend / max(impr, 1) * 1000, 2)),
            "cpc": str(round(spend / max(clicks, 1), 2)),
            "actions": actions,
            "action_values": action_values,
            "date_start": str(day_date),
            "date_stop": str(day_date),
        })
    return daily


def generate_demo_data(days_back: int = 30) -> dict:
    random.seed(42)  # reproducible
    campaign_insights = [_campaign_insight(c) for c in CAMPAIGNS]
    adset_insights = []
    ad_insights = []
    for c in CAMPAIGNS:
        adset_insights.extend(_adset_insights(c, n=2))
        ad_insights.extend(_ad_insights(c, n=3))

    return {
        "account": {
            "id": "act_123456789",
            "name": "DTC Brand — Main Account (DEMO)",
            "currency": "USD",
            "timezone_name": "America/New_York",
            "account_status": 1,
        },
        "campaigns": [
            {k: v for k, v in c.items() if not k.startswith("_")}
            for c in CAMPAIGNS
        ],
        "campaign_insights": campaign_insights,
        "adset_insights": adset_insights,
        "ad_insights": ad_insights,
        "daily_trend": _daily_trend(days_back),
        "fetched_at": str(date.today()),
        "days_back": days_back,
    }
