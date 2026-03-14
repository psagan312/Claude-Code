"""
Formats the Claude recommendations dict into a human-readable terminal report
and an optional JSON file.
"""

from __future__ import annotations
import json
from datetime import datetime


# ── ANSI colour helpers ────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
DIM    = "\033[2m"


def _colour(text: str, colour: str) -> str:
    return f"{colour}{text}{RESET}"

def _status_colour(status: str) -> str:
    return {
        "good":     GREEN,
        "warning":  YELLOW,
        "critical": RED,
    }.get(status, WHITE)

def _health_bar(score: int, width: int = 20) -> str:
    filled = int(score / 10 * width)
    colour = GREEN if score >= 7 else (YELLOW if score >= 4 else RED)
    bar = "█" * filled + "░" * (width - filled)
    return f"{colour}[{bar}]{RESET} {score}/10"

def _section(title: str) -> str:
    line = "═" * 70
    return f"\n{CYAN}{BOLD}{line}\n  {title}\n{line}{RESET}\n"

def _subsection(title: str) -> str:
    return f"\n{WHITE}{BOLD}▶ {title}{RESET}\n"

def _bullet(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    return f"{prefix}{DIM}•{RESET} {text}"


# ── main formatter ─────────────────────────────────────────────────────────

def format_report(recs: dict, account_name: str = "", currency: str = "USD") -> str:
    lines: list[str] = []

    # Header
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(_colour(f"\n{'━'*70}", CYAN))
    lines.append(_colour(f"  META ADS PERFORMANCE ANALYSIS  ·  {ts}", BOLD))
    if account_name:
        lines.append(_colour(f"  Account: {account_name}", DIM))
    lines.append(_colour(f"{'━'*70}\n", CYAN))

    # Executive summary
    lines.append(_section("EXECUTIVE SUMMARY"))
    lines.append(recs.get("executive_summary", ""))
    score = recs.get("overall_health_score", 0)
    lines.append(f"\n  Account Health: {_health_bar(score)}\n")

    # Key metrics
    lines.append(_section("KEY METRICS ASSESSMENT"))
    metrics = recs.get("key_metrics_assessment", {})
    metric_labels = {
        "roas": "ROAS", "cpa": f"CPA ({currency})", "ctr": "CTR (%)",
        "frequency": "Frequency", "cpm": f"CPM ({currency})", "nca_rate": "NCA Rate (%)",
    }
    for key, label in metric_labels.items():
        m = metrics.get(key, {})
        val    = m.get("value", "N/A")
        status = m.get("status", "")
        comment = m.get("comment", "")
        colour = _status_colour(status)
        val_str = f"{val:.2f}" if isinstance(val, (int, float)) else str(val)
        lines.append(f"  {label:<18} {_colour(val_str, colour):<30}  {DIM}{comment}{RESET}")

    # Quick wins
    lines.append(_section("QUICK WINS  (< 1 week)"))
    for item in recs.get("quick_wins", []):
        p = item.get("priority", "")
        lines.append(_subsection(f"#{p} · {item.get('action', '')}"))
        lines.append(_bullet(f"Why:    {item.get('rationale', '')}"))
        lines.append(_bullet(f"Impact: {item.get('expected_impact', '')}"))
        lines.append(_bullet(f"Effort: {item.get('effort', '')}  ·  Timeline: {item.get('timeframe', '')}"))

    # Strategic recommendations
    lines.append(_section("STRATEGIC RECOMMENDATIONS"))
    for item in recs.get("strategic_recommendations", []):
        p   = item.get("priority", "")
        cat = item.get("category", "")
        lines.append(_subsection(f"#{p} [{cat}] · {item.get('action', '')}"))
        lines.append(_bullet(f"Why:    {item.get('rationale', '')}"))
        lines.append(_bullet(f"Impact: {item.get('expected_impact', '')}"))
        lines.append(_bullet(f"Effort: {item.get('effort', '')}  ·  Timeline: {item.get('timeframe', '')}"))

    # NCA plan
    lines.append(_section("NEW CUSTOMER ACQUISITION PLAN"))
    nca = recs.get("new_customer_acquisition_plan", {})
    lines.append(f"  Current State: {nca.get('current_state', '')}\n")
    lines.append(_subsection("Recommended Tactics"))
    for t in nca.get("recommended_tactics", []):
        lines.append(_bullet(t))
    lines.append(_subsection("Budget Allocation"))
    lines.append(f"  {nca.get('budget_allocation_suggestion', '')}")
    lines.append(_subsection("Audience Strategy"))
    lines.append(f"  {nca.get('audience_strategy', '')}")

    # Scale / fix campaigns
    lines.append(_section("CAMPAIGNS TO SCALE"))
    for c in recs.get("campaigns_to_scale", []):
        pct = c.get("suggested_budget_increase_pct", "")
        lines.append(_bullet(f"{_colour(c.get('name',''), GREEN)} (+{pct}% budget)  —  {c.get('reason','')}"))

    lines.append(_section("CAMPAIGNS TO PAUSE OR FIX"))
    for c in recs.get("campaigns_to_pause_or_fix", []):
        lines.append(_bullet(f"{_colour(c.get('name',''), RED)}"))
        lines.append(_bullet(f"Issue:  {c.get('issue','')}", indent=6))
        lines.append(_bullet(f"Action: {c.get('recommended_action','')}", indent=6))

    # Creative
    lines.append(_section("CREATIVE RECOMMENDATIONS"))
    cr = recs.get("creative_recommendations", {})
    if cr.get("fatigue_warnings"):
        lines.append(_subsection("Fatigue Warnings"))
        for w in cr["fatigue_warnings"]:
            lines.append(_bullet(w, indent=4))
    if cr.get("format_recommendations"):
        lines.append(_subsection("Format Recommendations"))
        for f in cr["format_recommendations"]:
            lines.append(_bullet(f, indent=4))
    if cr.get("testing_priorities"):
        lines.append(_subsection("Testing Priorities"))
        for t in cr["testing_priorities"]:
            lines.append(_bullet(t, indent=4))

    # 30-day plan
    lines.append(_section("30-DAY ACTION PLAN"))
    for week in recs.get("30_day_action_plan", []):
        lines.append(_subsection(f"Week {week.get('week','')}"))
        for action in week.get("actions", []):
            lines.append(_bullet(action, indent=4))

    lines.append(_colour(f"\n{'━'*70}\n", CYAN))
    return "\n".join(lines)


def save_report(recs: dict, payload: dict, output_prefix: str = "meta_ads_report") -> tuple[str, str]:
    """Save JSON report and return file paths."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"{output_prefix}_{ts}.json"
    full = {"analysis_payload": payload, "recommendations": recs, "generated_at": ts}
    with open(json_path, "w") as f:
        json.dump(full, f, indent=2)
    return json_path
