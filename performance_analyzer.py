"""
Performance analysis engine for Meta Ads data.
Computes KPIs, flags issues, and structures data for Claude recommendations.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ── helpers ────────────────────────────────────────────────────────────────

def _sum_actions(actions: list[dict], action_types: list[str]) -> float:
    if not actions:
        return 0.0
    return sum(
        float(a.get("value", 0))
        for a in actions
        if a.get("action_type") in action_types
    )

def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator else default


# ── purchase conversion action types ───────────────────────────────────────
PURCHASE_ACTIONS = ["purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"]
LEAD_ACTIONS     = ["lead", "omni_lead", "offsite_conversion.fb_pixel_lead"]
ATC_ACTIONS      = ["add_to_cart", "omni_add_to_cart"]
INITIATE_CHECKOUT_ACTIONS = ["initiate_checkout", "omni_initiated_checkout"]
VIEW_CONTENT_ACTIONS = ["view_content", "omni_view_content"]
NEW_CUSTOMER_ACTIONS = ["new_customer_purchase"]  # requires Meta NCA solution


@dataclass
class CampaignMetrics:
    id: str
    name: str
    objective: str
    status: str
    spend: float
    impressions: float
    reach: float
    frequency: float
    clicks: float
    ctr: float
    cpc: float
    cpm: float
    purchases: float
    purchase_value: float
    leads: float
    atc: float
    initiate_checkout: float
    view_content: float
    new_customer_purchases: float
    roas: float
    cpa: float          # cost per purchase
    cpl: float          # cost per lead
    conversion_rate: float  # purchases / clicks
    checkout_rate: float    # checkouts / atc
    atc_rate: float         # atc / view_content

    # derived flags
    flags: list[str] = field(default_factory=list)

    @classmethod
    def from_insight(cls, insight: dict, campaign_meta: dict | None = None) -> "CampaignMetrics":
        spend       = float(insight.get("spend", 0))
        impressions = float(insight.get("impressions", 0))
        reach       = float(insight.get("reach", 0))
        clicks      = float(insight.get("clicks", 0))
        ctr         = float(insight.get("ctr", 0))
        cpc         = float(insight.get("cpc", 0))
        cpm         = float(insight.get("cpm", 0))
        frequency   = float(insight.get("frequency", 0))

        actions       = insight.get("actions", []) or []
        action_values = insight.get("action_values", []) or []

        purchases         = _sum_actions(actions, PURCHASE_ACTIONS)
        purchase_value    = _sum_actions(action_values, PURCHASE_ACTIONS)
        leads             = _sum_actions(actions, LEAD_ACTIONS)
        atc               = _sum_actions(actions, ATC_ACTIONS)
        initiate_checkout = _sum_actions(actions, INITIATE_CHECKOUT_ACTIONS)
        view_content      = _sum_actions(actions, VIEW_CONTENT_ACTIONS)
        new_customers     = _sum_actions(actions, NEW_CUSTOMER_ACTIONS)

        roas              = _safe_div(purchase_value, spend)
        cpa               = _safe_div(spend, purchases)
        cpl               = _safe_div(spend, leads)
        conversion_rate   = _safe_div(purchases, clicks) * 100
        checkout_rate     = _safe_div(initiate_checkout, atc) * 100
        atc_rate          = _safe_div(atc, view_content) * 100

        meta = campaign_meta or {}
        return cls(
            id=insight.get("campaign_id", insight.get("id", "")),
            name=insight.get("campaign_name", insight.get("name", "Unknown")),
            objective=meta.get("objective", insight.get("objective", "UNKNOWN")),
            status=meta.get("status", "UNKNOWN"),
            spend=spend, impressions=impressions, reach=reach,
            frequency=frequency, clicks=clicks, ctr=ctr, cpc=cpc, cpm=cpm,
            purchases=purchases, purchase_value=purchase_value,
            leads=leads, atc=atc, initiate_checkout=initiate_checkout,
            view_content=view_content, new_customer_purchases=new_customers,
            roas=roas, cpa=cpa, cpl=cpl,
            conversion_rate=conversion_rate,
            checkout_rate=checkout_rate, atc_rate=atc_rate,
        )

    def detect_flags(self, target_roas: float = 2.0, target_cpa: float = 50.0,
                     max_frequency: float = 3.5) -> list[str]:
        flags = []
        if self.spend > 100 and self.roas < target_roas and self.purchases > 0:
            flags.append(f"LOW_ROAS ({self.roas:.2f}x vs target {target_roas}x)")
        if self.spend > 100 and self.cpa > target_cpa * 2 and self.purchases > 0:
            flags.append(f"HIGH_CPA (${self.cpa:.2f} vs target ${target_cpa})")
        if self.frequency > max_frequency:
            flags.append(f"HIGH_FREQUENCY ({self.frequency:.1f}x — creative fatigue risk)")
        if self.ctr < 0.5 and self.impressions > 5000:
            flags.append(f"LOW_CTR ({self.ctr:.2f}% — weak creative/audience)")
        if self.spend > 50 and self.purchases == 0 and self.leads == 0:
            flags.append("ZERO_CONVERSIONS — potential tracking or audience issue")
        if self.checkout_rate < 20 and self.atc > 10:
            flags.append(f"LOW_CHECKOUT_RATE ({self.checkout_rate:.1f}%) — cart abandonment issue")
        if self.atc_rate < 5 and self.view_content > 50:
            flags.append(f"LOW_ATC_RATE ({self.atc_rate:.1f}%) — product page/offer issue")
        self.flags = flags
        return flags


@dataclass
class AccountSummary:
    name: str
    currency: str
    timezone: str
    total_spend: float
    total_revenue: float
    total_purchases: float
    total_leads: float
    total_new_customer_purchases: float
    overall_roas: float
    overall_cpa: float
    overall_cpl: float
    avg_cpm: float
    avg_ctr: float
    avg_frequency: float
    top_campaigns_by_roas: list[dict]
    top_campaigns_by_spend: list[dict]
    bottom_campaigns_by_roas: list[dict]
    campaign_count: int
    active_campaign_count: int
    daily_trend: list[dict]
    nca_rate: float  # new customer acquisition rate (new purchases / total purchases)


class PerformanceAnalyzer:
    """Transforms raw Meta API data into structured analytics."""

    def __init__(self, raw_data: dict, target_roas: float = 2.0,
                 target_cpa: float = 50.0, max_frequency: float = 3.5):
        self.raw = raw_data
        self.target_roas = target_roas
        self.target_cpa = target_cpa
        self.max_frequency = max_frequency

    def _campaign_meta_map(self) -> dict[str, dict]:
        return {c["id"]: c for c in self.raw.get("campaigns", [])}

    def _parse_campaign_metrics(self) -> list[CampaignMetrics]:
        meta_map = self._campaign_meta_map()
        metrics = []
        for insight in self.raw.get("campaign_insights", []):
            cid = insight.get("campaign_id", insight.get("id", ""))
            m = CampaignMetrics.from_insight(insight, meta_map.get(cid))
            m.detect_flags(self.target_roas, self.target_cpa, self.max_frequency)
            metrics.append(m)
        return metrics

    def _parse_adset_metrics(self) -> list[dict]:
        results = []
        for i in self.raw.get("adset_insights", []):
            spend = float(i.get("spend", 0))
            purchases = _sum_actions(i.get("actions", []) or [], PURCHASE_ACTIONS)
            purchase_value = _sum_actions(i.get("action_values", []) or [], PURCHASE_ACTIONS)
            results.append({
                "id": i.get("adset_id"), "name": i.get("adset_name"),
                "campaign_name": i.get("campaign_name"),
                "spend": spend,
                "purchases": purchases,
                "roas": _safe_div(purchase_value, spend),
                "cpa": _safe_div(spend, purchases),
                "ctr": float(i.get("ctr", 0)),
                "frequency": float(i.get("frequency", 0)),
                "cpm": float(i.get("cpm", 0)),
            })
        return results

    def _parse_ad_metrics(self) -> list[dict]:
        results = []
        for i in self.raw.get("ad_insights", []):
            spend = float(i.get("spend", 0))
            purchases = _sum_actions(i.get("actions", []) or [], PURCHASE_ACTIONS)
            purchase_value = _sum_actions(i.get("action_values", []) or [], PURCHASE_ACTIONS)
            results.append({
                "id": i.get("ad_id"), "name": i.get("ad_name"),
                "adset_name": i.get("adset_name"),
                "campaign_name": i.get("campaign_name"),
                "spend": spend,
                "impressions": float(i.get("impressions", 0)),
                "purchases": purchases,
                "roas": _safe_div(purchase_value, spend),
                "cpa": _safe_div(spend, purchases),
                "ctr": float(i.get("ctr", 0)),
                "frequency": float(i.get("frequency", 0)),
                "cpm": float(i.get("cpm", 0)),
            })
        return results

    def _summarize_daily(self) -> tuple[list[dict], dict]:
        daily = []
        for d in self.raw.get("daily_trend", []):
            spend = float(d.get("spend", 0))
            actions = d.get("actions", []) or []
            purchases = _sum_actions(actions, PURCHASE_ACTIONS)
            action_values = d.get("action_values", []) or []
            revenue = _sum_actions(action_values, PURCHASE_ACTIONS)
            daily.append({
                "date": d.get("date_start"),
                "spend": spend,
                "revenue": revenue,
                "purchases": purchases,
                "roas": _safe_div(revenue, spend),
                "ctr": float(d.get("ctr", 0)),
                "cpm": float(d.get("cpm", 0)),
            })
        # week-over-week comparison (last 7 vs prior 7)
        daily_sorted = sorted(daily, key=lambda x: x.get("date", ""))
        wow = {}
        if len(daily_sorted) >= 14:
            last7  = daily_sorted[-7:]
            prior7 = daily_sorted[-14:-7]
            def _avg(lst, key): return sum(r[key] for r in lst) / max(len(lst), 1)
            wow = {
                "spend_change_pct":   _safe_div(_avg(last7, "spend") - _avg(prior7, "spend"), _avg(prior7, "spend")) * 100,
                "roas_change_pct":    _safe_div(_avg(last7, "roas")  - _avg(prior7, "roas"),  _avg(prior7, "roas"))  * 100,
                "cpm_change_pct":     _safe_div(_avg(last7, "cpm")   - _avg(prior7, "cpm"),   _avg(prior7, "cpm"))   * 100,
            }
        return daily, wow

    def build_summary(self) -> AccountSummary:
        account   = self.raw.get("account", {})
        campaigns = self._parse_campaign_metrics()

        total_spend    = sum(c.spend for c in campaigns)
        total_revenue  = sum(c.purchase_value for c in campaigns)
        total_purchases = sum(c.purchases for c in campaigns)
        total_leads    = sum(c.leads for c in campaigns)
        total_new_cust = sum(c.new_customer_purchases for c in campaigns)
        total_impr     = sum(c.impressions for c in campaigns)
        total_clicks   = sum(c.clicks for c in campaigns)

        by_roas  = sorted([c for c in campaigns if c.spend > 10], key=lambda x: x.roas, reverse=True)
        by_spend = sorted(campaigns, key=lambda x: x.spend, reverse=True)

        daily, wow = self._summarize_daily()

        def _campaign_dict(c: CampaignMetrics) -> dict:
            return {
                "name": c.name, "objective": c.objective, "status": c.status,
                "spend": c.spend, "roas": c.roas, "cpa": c.cpa,
                "purchases": c.purchases, "revenue": c.purchase_value,
                "ctr": c.ctr, "frequency": c.frequency, "flags": c.flags,
            }

        return AccountSummary(
            name=account.get("name", "Unknown Account"),
            currency=account.get("currency", "USD"),
            timezone=account.get("timezone_name", ""),
            total_spend=total_spend,
            total_revenue=total_revenue,
            total_purchases=total_purchases,
            total_leads=total_leads,
            total_new_customer_purchases=total_new_cust,
            overall_roas=_safe_div(total_revenue, total_spend),
            overall_cpa=_safe_div(total_spend, total_purchases),
            overall_cpl=_safe_div(total_spend, total_leads),
            avg_cpm=_safe_div(total_spend * 1000, total_impr),
            avg_ctr=_safe_div(total_clicks, total_impr) * 100,
            avg_frequency=sum(c.frequency for c in campaigns) / max(len(campaigns), 1),
            top_campaigns_by_roas=[_campaign_dict(c) for c in by_roas[:5]],
            top_campaigns_by_spend=[_campaign_dict(c) for c in by_spend[:5]],
            bottom_campaigns_by_roas=[_campaign_dict(c) for c in by_roas[-5:] if c.roas < self.target_roas],
            campaign_count=len(campaigns),
            active_campaign_count=sum(1 for c in campaigns if c.status == "ACTIVE"),
            daily_trend=daily,
            nca_rate=_safe_div(total_new_cust, total_purchases) * 100,
        )

    def full_analysis_payload(self) -> dict:
        """Returns a JSON-serialisable dict ready to pass to Claude."""
        summary   = self.build_summary()
        adsets    = self._parse_adset_metrics()
        ads       = self._parse_ad_metrics()
        _, wow    = self._summarize_daily()
        campaigns = self._parse_campaign_metrics()

        flagged = [
            {"name": c.name, "spend": c.spend, "flags": c.flags}
            for c in campaigns if c.flags
        ]

        top_ads_by_roas = sorted(
            [a for a in ads if a["spend"] > 10],
            key=lambda x: x["roas"], reverse=True
        )[:10]
        bottom_ads_by_roas = sorted(
            [a for a in ads if a["spend"] > 10 and a["roas"] < self.target_roas],
            key=lambda x: x["roas"]
        )[:10]

        return {
            "account_summary": {
                "name": summary.name,
                "currency": summary.currency,
                "timezone": summary.timezone,
                "total_spend": round(summary.total_spend, 2),
                "total_revenue": round(summary.total_revenue, 2),
                "total_purchases": int(summary.total_purchases),
                "total_leads": int(summary.total_leads),
                "overall_roas": round(summary.overall_roas, 2),
                "overall_cpa": round(summary.overall_cpa, 2),
                "overall_cpl": round(summary.overall_cpl, 2),
                "avg_cpm": round(summary.avg_cpm, 2),
                "avg_ctr": round(summary.avg_ctr, 3),
                "avg_frequency": round(summary.avg_frequency, 2),
                "campaign_count": summary.campaign_count,
                "active_campaign_count": summary.active_campaign_count,
                "nca_rate_pct": round(summary.nca_rate, 1),
            },
            "week_over_week": wow,
            "top_campaigns_by_roas": summary.top_campaigns_by_roas,
            "top_campaigns_by_spend": summary.top_campaigns_by_spend,
            "underperforming_campaigns": summary.bottom_campaigns_by_roas,
            "flagged_campaigns": flagged,
            "top_ads_by_roas": top_ads_by_roas,
            "bottom_ads_by_roas": bottom_ads_by_roas,
            "top_adsets": sorted(adsets, key=lambda x: x["roas"], reverse=True)[:10],
            "target_roas": self.target_roas,
            "target_cpa": self.target_cpa,
            "days_analyzed": self.raw.get("days_back", 30),
        }
