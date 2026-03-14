#!/usr/bin/env python3
"""
Meta Ads Performance Analyzer — CLI entry point.

Usage:
    python analyze.py \
        --token YOUR_META_ACCESS_TOKEN \
        --account 123456789 \
        [--days 30] \
        [--target-roas 2.5] \
        [--target-cpa 45] \
        [--max-frequency 3.5] \
        [--output report] \
        [--demo]

Environment variables (alternative to flags):
    META_ACCESS_TOKEN   — Meta long-lived user access token
    META_AD_ACCOUNT_ID  — Ad account ID (without 'act_' prefix)
    ANTHROPIC_API_KEY   — Anthropic API key (required)

Demo mode:
    Pass --demo to run with realistic synthetic data (no Meta credentials needed).
    Useful for testing the analysis pipeline and Claude integration.
"""

import argparse
import json
import os
import sys
from demo_data import generate_demo_data


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Meta Ads Performance Analyzer powered by Claude")
    p.add_argument("--token",         default=os.getenv("META_ACCESS_TOKEN"),      help="Meta access token")
    p.add_argument("--account",       default=os.getenv("META_AD_ACCOUNT_ID"),     help="Ad account ID")
    p.add_argument("--days",          type=int, default=30,                         help="Lookback window in days (default: 30)")
    p.add_argument("--target-roas",   type=float, default=2.0,                      help="Target ROAS threshold (default: 2.0)")
    p.add_argument("--target-cpa",    type=float, default=50.0,                     help="Target CPA in account currency (default: 50)")
    p.add_argument("--max-frequency", type=float, default=3.5,                      help="Max acceptable frequency before creative fatigue flag (default: 3.5)")
    p.add_argument("--output",        default="meta_ads_report",                    help="Output file prefix for saved JSON report")
    p.add_argument("--demo",          action="store_true",                          help="Run with synthetic demo data (no Meta credentials needed)")
    p.add_argument("--no-stream",     action="store_true",                          help="Don't stream Claude output (return all at once)")
    p.add_argument("--save-payload",  action="store_true",                          help="Save the raw analysis payload to JSON before calling Claude")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # ── Validate environment ────────────────────────────────────────────────
    try:
        import anthropic as _anthropic
        _anthropic.Anthropic()  # raises if no key is found anywhere
    except Exception:
        print(
            "ERROR: Anthropic API key not found. Set ANTHROPIC_API_KEY or configure ~/.anthropic/config.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.demo and (not args.token or not args.account):
        print(
            "ERROR: --token and --account are required unless running with --demo.\n"
            "       Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID env vars or pass the flags.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Fetch / generate data ───────────────────────────────────────────────
    if args.demo:
        print("Running in DEMO mode with synthetic data…")
        raw_data = generate_demo_data(days_back=args.days)
    else:
        from meta_ads_client import MetaAdsClient
        client = MetaAdsClient(
            access_token=args.token,
            ad_account_id=args.account,
        )
        raw_data = client.collect_all(days_back=args.days)

    # ── Analyse ─────────────────────────────────────────────────────────────
    from performance_analyzer import PerformanceAnalyzer
    analyzer = PerformanceAnalyzer(
        raw_data,
        target_roas=args.target_roas,
        target_cpa=args.target_cpa,
        max_frequency=args.max_frequency,
    )
    payload = analyzer.full_analysis_payload()

    if args.save_payload:
        payload_file = f"{args.output}_payload.json"
        with open(payload_file, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"Analysis payload saved to: {payload_file}")

    # ── Get Claude recommendations ──────────────────────────────────────────
    from ai_recommendations import get_recommendations, stream_recommendations
    if args.no_stream:
        recs = get_recommendations(payload)
    else:
        recs = stream_recommendations(payload)

    # ── Format & display ────────────────────────────────────────────────────
    from report_formatter import format_report, save_report
    account_name = payload["account_summary"].get("name", "")
    currency     = payload["account_summary"].get("currency", "USD")
    report_text  = format_report(recs, account_name=account_name, currency=currency)
    print(report_text)

    # ── Save JSON report ─────────────────────────────────────────────────────
    json_path = save_report(recs, payload, output_prefix=args.output)
    print(f"Full JSON report saved to: {json_path}\n")


if __name__ == "__main__":
    main()
