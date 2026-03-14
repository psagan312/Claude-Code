"""
Claude-powered recommendation engine for Meta Ads performance analysis.
Sends structured account data to Claude and returns actionable recommendations.
"""

import json
import anthropic

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior performance marketing strategist specializing in Meta (Facebook/Instagram) advertising.
You analyse paid social account data and produce structured, actionable recommendations.

Your analysis must:
1. Be grounded strictly in the provided data — cite specific numbers
2. Prioritise actions by expected revenue/profit impact
3. Distinguish between quick wins (< 1 week to implement) and strategic changes (1-4 weeks)
4. Address both ROAS optimisation AND new customer acquisition (NCA) separately
5. Flag creative fatigue, audience overlap, and budget inefficiency
6. Provide specific targeting, bidding, budget, and creative recommendations

Format your response as valid JSON with this structure:
{
  "executive_summary": "2-3 sentence overview of account health",
  "overall_health_score": <1-10>,
  "key_metrics_assessment": {
    "roas": { "value": <float>, "status": "good|warning|critical", "comment": "..." },
    "cpa": { "value": <float>, "status": "good|warning|critical", "comment": "..." },
    "ctr": { "value": <float>, "status": "good|warning|critical", "comment": "..." },
    "frequency": { "value": <float>, "status": "good|warning|critical", "comment": "..." },
    "cpm": { "value": <float>, "status": "good|warning|critical", "comment": "..." },
    "nca_rate": { "value": <float>, "status": "good|warning|critical", "comment": "..." }
  },
  "quick_wins": [
    {
      "priority": 1,
      "action": "...",
      "rationale": "...",
      "expected_impact": "...",
      "effort": "low|medium|high",
      "timeframe": "..."
    }
  ],
  "strategic_recommendations": [
    {
      "priority": 1,
      "category": "Budget|Bidding|Creative|Audience|Structure|Tracking",
      "action": "...",
      "rationale": "...",
      "expected_impact": "...",
      "effort": "low|medium|high",
      "timeframe": "..."
    }
  ],
  "new_customer_acquisition_plan": {
    "current_state": "...",
    "recommended_tactics": ["...", "..."],
    "budget_allocation_suggestion": "...",
    "audience_strategy": "..."
  },
  "campaigns_to_scale": [
    { "name": "...", "reason": "...", "suggested_budget_increase_pct": <int> }
  ],
  "campaigns_to_pause_or_fix": [
    { "name": "...", "issue": "...", "recommended_action": "..." }
  ],
  "creative_recommendations": {
    "fatigue_warnings": ["..."],
    "format_recommendations": ["..."],
    "testing_priorities": ["..."]
  },
  "30_day_action_plan": [
    { "week": 1, "actions": ["..."] },
    { "week": 2, "actions": ["..."] },
    { "week": 3, "actions": ["..."] },
    { "week": 4, "actions": ["..."] }
  ]
}"""

USER_PROMPT_TEMPLATE = """Analyse this Meta Ads account performance data and provide comprehensive recommendations
to drive profitable revenue growth and new customer acquisition.

Account Performance Data (last {days} days):
```json
{data}
```

Provide your full analysis and recommendations in the JSON format specified."""


def get_recommendations(analysis_payload: dict) -> dict:
    """
    Send the structured analytics payload to Claude and return parsed recommendations.

    Args:
        analysis_payload: Output of PerformanceAnalyzer.full_analysis_payload()

    Returns:
        dict with Claude's structured recommendations
    """
    client = anthropic.Anthropic()

    days = analysis_payload.get("days_analyzed", 30)
    user_msg = USER_PROMPT_TEMPLATE.format(
        days=days,
        data=json.dumps(analysis_payload, indent=2)
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw_text = response.content[0].text.strip()

    # Extract JSON even if Claude wraps it in markdown fences
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1])

    return json.loads(raw_text)


def stream_recommendations(analysis_payload: dict) -> dict:
    """
    Same as get_recommendations but streams the response and prints progress.
    Returns the final parsed recommendations dict.
    """
    client = anthropic.Anthropic()
    days = analysis_payload.get("days_analyzed", 30)
    user_msg = USER_PROMPT_TEMPLATE.format(
        days=days,
        data=json.dumps(analysis_payload, indent=2)
    )

    print("\nGenerating AI recommendations...\n" + "─" * 60)
    full_text = ""

    with client.messages.stream(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_text += text

    print("\n" + "─" * 60)

    raw_text = full_text.strip()
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1])

    return json.loads(raw_text)
