---
name: amazon-inventory-monitor
description: Check Amazon product availability for Google Ads campaigns. Monitors enabled campaigns and verifies if linked Amazon products are in stock. Use when asked to check ad inventory, verify product availability, or audit Amazon product links in Google Ads.
credentials:
  - Google Ads API credentials (via autoads config)
  - Decodo API token (via decodo-scraper .env)
env:
  required:
    - DECODO_AUTH_TOKEN
  autoads_config: true
---

# Amazon Inventory Monitor Skill

Checks all **enabled** Google Ads campaigns for Amazon product URLs and verifies if products are still in stock and purchasable using Decodo scraper.

## What It Does

1. **Fetches all enabled campaigns** from Google Ads API
2. **Extracts Amazon destination URLs** from responsive search ads
3. **Checks each product** using Decodo Amazon scraper for:
   - Stock status (In Stock / Out of Stock / Unavailable)
   - Current price
   - Product title
4. **Generates a report** with recommendations

## Usage

```bash
cd /root/.openclaw/workspace/skills/amazon-inventory-monitor
python3 check_inventory.py --customer-id "CUSTOMER_ID"
```

### Options

| Option | Description |
|--------|-------------|
| `--customer-id` | Google Ads Customer ID (required, no dashes) |
| `--output FILE` | Save report to file |
| `--json` | Output raw JSON instead of formatted text |

## Example Output

```
📊 **Amazon Inventory Check Report**
Generated: 2026-03-29 20:00:00

---
**Summary:**
- Total Campaigns: 3
- Total Products: 12
- ✅ In Stock: 10
- ❌ Out of Stock / Unavailable: 2

---
**Campaign:** Brand Dash Cam Sale
ID: `1234567890` | Status: ENABLED
Products: 8 ✅ | 1 ❌

✅ **ROVE R2-4K DUAL Dash Cam Front and Rear...**
   ASIN: `B0D6J5B98H` | $109.98
   URL: https://www.amazon.com/dp/B0D6J5B98H

❌ **OLD PRODUCT - Discontinued**
   ASIN: `B0XXXXXXX` | Out of Stock
   URL: https://www.amazon.com/dp/B0XXXXXXX

⚡ **Recommendations:**
1. 2 product(s) are out of stock - consider pausing these ads
2. Review the destination URLs and update if products are discontinued
```

## Cron Job

Runs daily at 8:00 PM (Asia/Shanghai):

```
Cron ID: amazon-inventory-monitor-daily
Event: systemEvent: "amazon_inventory_check"
Time: 20:00 Asia/Shanghai
```

## Notes

- Only checks **enabled** campaigns, ad groups, and ads
- Deduplicates URLs within each campaign
- Uses Decodo for reliable Amazon scraping (no blocking)
- Report is sent to Feishu after completion
