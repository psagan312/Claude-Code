# Meta Ads Performance Analyzer

AI-powered performance analysis for Meta (Facebook/Instagram) ad accounts.
Fetches real-time data via the Meta Marketing API, runs a structured KPI analysis,
then uses **Claude** to generate actionable recommendations for profitable growth
and new customer acquisition.

---

## What It Does

1. **Pulls live data** — campaigns, ad sets, ads, daily trends via Meta Marketing API
2. **Computes KPIs** — ROAS, CPA, CPL, CTR, frequency, checkout rate, ATC rate, NCA rate
3. **Flags problems** — creative fatigue, low ROAS, zero conversions, high CPA, drop-off funnel issues
4. **AI recommendations** — Claude produces a structured JSON report covering:
   - Executive summary & health score
   - Quick wins (< 1 week)
   - Strategic recommendations (1-4 weeks)
   - New customer acquisition plan
   - Campaigns to scale vs pause/fix
   - Creative fatigue warnings & testing priorities
   - 30-day action plan

---

## Setup

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
export META_ACCESS_TOKEN="EAA..."      # Long-lived Meta user access token
export META_AD_ACCOUNT_ID="123456789"  # Without 'act_' prefix
```

### Getting a Meta Access Token

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create an app (Business type)
3. Add the **Marketing API** product
4. Generate a long-lived user token with these permissions:
   - `ads_read`
   - `ads_management` (for budget fields)
   - `business_management`

---

## Usage

### Live account analysis
```bash
python analyze.py \
    --token "$META_ACCESS_TOKEN" \
    --account "$META_AD_ACCOUNT_ID" \
    --days 30 \
    --target-roas 2.5 \
    --target-cpa 45
```

### Demo mode (no Meta credentials needed)
```bash
python analyze.py --demo
```

### Options
| Flag | Default | Description |
|------|---------|-------------|
| `--token` | `$META_ACCESS_TOKEN` | Meta access token |
| `--account` | `$META_AD_ACCOUNT_ID` | Ad account ID |
| `--days` | 30 | Lookback window |
| `--target-roas` | 2.0 | ROAS below which a campaign is flagged |
| `--target-cpa` | 50 | CPA above which a campaign is flagged |
| `--max-frequency` | 3.5 | Frequency above which creative fatigue is flagged |
| `--output` | `meta_ads_report` | Output JSON file prefix |
| `--demo` | off | Use synthetic demo data |
| `--no-stream` | off | Don't stream Claude output |
| `--save-payload` | off | Save analysis payload JSON before calling Claude |

---

## Architecture

```
analyze.py              ← CLI entry point
├── meta_ads_client.py  ← Meta Marketing API client (real data)
├── demo_data.py        ← Synthetic data generator (demo mode)
├── performance_analyzer.py  ← KPI computation & flag detection
├── ai_recommendations.py    ← Claude integration (prompt + parsing)
└── report_formatter.py      ← Terminal & JSON report formatting
```

## Output

- **Terminal**: Colour-coded report with all recommendations
- **JSON file**: `meta_ads_report_YYYYMMDD_HHMMSS.json` — full structured data for downstream use

---

## Metrics Analysed

| Metric | Description |
|--------|-------------|
| ROAS | Return on ad spend (revenue / spend) |
| CPA | Cost per purchase |
| CPL | Cost per lead |
| CTR | Click-through rate |
| Frequency | Average impressions per unique user |
| CPM | Cost per 1,000 impressions |
| ATC Rate | Add-to-cart rate (ATC / view content) |
| Checkout Rate | Initiate checkout rate (checkouts / ATC) |
| NCA Rate | New customer acquisition rate (new purchases / total purchases) |
