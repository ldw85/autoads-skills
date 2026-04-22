#!/usr/bin/env python3
"""
Amazon Inventory Monitor for Google Ads

Checks all enabled Google Ads campaigns for Amazon product URLs
and verifies if products are still in stock and purchasable.
"""

import sys
import os
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse

# Add autoads to path - use absolute path
autoads_path = "/root/.openclaw/workspace/autoads"
if autoads_path not in sys.path:
    sys.path.insert(0, autoads_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProductCheck:
    """Result of checking a single product."""
    url: str
    asin: str
    title: str
    status: str  # "in_stock", "out_of_stock", "unavailable", "error"
    price: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class CampaignInventoryReport:
    """Inventory report for a single campaign."""
    campaign_id: str
    campaign_name: str
    status: str
    products: List[ProductCheck] = field(default_factory=list)
    
    @property
    def in_stock_count(self) -> int:
        return sum(1 for p in self.products if p.status == "in_stock")
    
    @property
    def out_of_stock_count(self) -> int:
        return sum(1 for p in self.products if p.status in ("out_of_stock", "unavailable"))


def extract_asin_from_url(url: str) -> Optional[str]:
    """Extract ASIN from Amazon URL.
    
    Supports formats:
    - https://www.amazon.com/dp/ASIN
    - https://www.amazon.com/dp/ASIN?tag=...
    - https://www.amazon.com/gp/product/ASIN
    """
    # Match /dp/ASIN pattern
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    # Match /gp/product/ASIN pattern
    match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    return None


def is_amazon_url(url: str) -> bool:
    """Check if URL is an Amazon product URL."""
    if not url:
        return False
    parsed = urlparse(url)
    return "amazon.com" in parsed.netloc and ("/dp/" in url or "/gp/product/" in url)


def get_google_ads_campaigns_with_urls(customer_id: str, require_spend: bool = True, spend_days: int = 7) -> List[Dict[str, Any]]:
    """Get all enabled campaigns with their ad destination URLs.
    
    Args:
        customer_id: Google Ads customer ID
        require_spend: If True, only return campaigns with spend in the last 7 days
        spend_days: Number of days to look back for spend data (default: 7)
    
    Returns list of dicts with campaign info and URLs.
    """
    try:
        from src.google_ads_client import GoogleAdsClientWrapper
        from src.config import load_config
        
        config = load_config()
        google_ads = GoogleAdsClientWrapper(config.google_ads)
        
        if not google_ads.client:
            logger.error("Google Ads client not available")
            return []
        
        campaigns_data = []
        
        # Determine date filter string
        date_str = f"LAST_{spend_days}_DAYS"
        
        # Query for all enabled campaigns
        # We query with segments.date to get daily data, then aggregate
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group_ad.ad.id,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls,
                ad_group_ad.ad.final_url_suffix,
                ad_group_ad.ad.tracking_url_template,
                ad_group_ad.status,
                metrics.cost_micros,
                metrics.clicks,
                segments.date
            FROM ad_group_ad
            WHERE campaign.status = 'ENABLED'
            AND ad_group.status = 'ENABLED'
            AND ad_group_ad.status = 'ENABLED'
            AND segments.date DURING {date_str}
        """
        
        ga_service = google_ads.client.get_service("GoogleAdsService")
        search_request = google_ads.client.get_type("SearchGoogleAdsRequest")
        search_request.query = query
        search_request.customer_id = customer_id
        
        results = ga_service.search(request=search_request)
        
        # Aggregate results by ad_id, summing clicks/cost across dates
        ad_data = {}
        for row in results:
            campaign = row.campaign
            ad_group = row.ad_group
            ad = row.ad_group_ad.ad
            
            ad_key = str(ad.id)
            if ad_key not in ad_data:
                ad_data[ad_key] = {
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "campaign_status": campaign.status.name,
                    "ad_id": ad_key,
                    "total_clicks": 0,
                    "total_cost": 0,
                    "final_urls": [],
                    "headlines": [h.text for h in ad.responsive_search_ad.headlines] if ad.responsive_search_ad else [],
                }
            
            # Accumulate metrics
            ad_data[ad_key]["total_clicks"] += row.metrics.clicks or 0
            ad_data[ad_key]["total_cost"] += (row.metrics.cost_micros or 0) / 1000000
            
            # Extract URLs (only once per ad)
            if not ad_data[ad_key]["final_urls"]:
                final_urls = []
                if ad.final_urls:
                    url_suffix = ad.final_url_suffix or ""
                    for base_url in ad.final_urls:
                        if url_suffix and "?" not in base_url:
                            final_url = f"{base_url}?{url_suffix}"
                        else:
                            final_url = base_url
                        final_urls.append(final_url)
                
                ad_data[ad_key]["final_urls"] = [u for u in final_urls if is_amazon_url(u)]
        
        # Filter for ads with recent spend and build final list
        for ad_id, data in ad_data.items():
            # Only include if has clicks in last 7 days (indicates recent activity)
            if require_spend and data["total_clicks"] == 0:
                continue
            
            if data["final_urls"]:
                campaigns_data.append({
                    "campaign_id": data["campaign_id"],
                    "campaign_name": data["campaign_name"],
                    "campaign_status": data["campaign_status"],
                    "ad_id": data["ad_id"],
                    "final_urls": data["final_urls"],
                    "headlines": data["headlines"],
                    "total_clicks": data["total_clicks"],
                    "total_cost": data["total_cost"],
                })
        
        return campaigns_data
        
    except Exception as e:
        logger.error(f"Error fetching Google Ads data: {e}")
        return []


def extract_clean_amazon_url(url: str) -> str:
    """Strip tracking parameters from Amazon URL for availability checks.
    
    Removes: &maas=, &tag=, &m=, &aa_campaignid=, &aa_adgroupid=,
             &aa_creativeid=, &ref=, and other affiliate/tracking params.
    Keeps: amazon.com/dp/ASIN or amazon.com/gp/product/ASIN
    """
    if not url:
        return url
    
    # Extract ASIN
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if not asin_match:
        asin_match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
    
    if asin_match:
        asin = asin_match.group(1)
        # Check if URL uses /dp/ or /gp/product/
        if '/dp/' in url:
            return f"https://www.amazon.com/dp/{asin}"
        elif '/gp/product/' in url:
            return f"https://www.amazon.com/gp/product/{asin}"
    
    # Fallback: strip known tracking params via parse_qs
    from urllib.parse import urlparse, parse_qs, urlencode
    parsed = urlparse(url)
    if "amazon.com" not in parsed.netloc:
        return url
    
    # Keep only asin-related params, drop all tracking/attribution params
    tracking_params = {
        'maas', 'tag', 'm', 'aa_campaignid', 'aa_adgroupid', 'aa_creativeid',
        'ref', 'linkCode', 'camp', 'creative', 'pf_rd_p', 'pf_rd_r',
        'gclid', 'fbclid', 'utm_source', 'utm_medium', 'utm_campaign'
    }
    qs = parse_qs(parsed.query)
    clean_qs = {k: v for k, v in qs.items() if k.lower() not in tracking_params}
    clean_query = urlencode(clean_qs, doseq=True) if clean_qs else ""
    
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return f"{base}?{clean_query}" if clean_query else base


def check_amazon_product_with_decodo(url: str) -> ProductCheck:
    """Check Amazon product availability using Decodo scraper.
    
    Uses the decodo scraper skill's scrape.py tool.
    """
    asin = extract_asin_from_url(url)
    if not asin:
        return ProductCheck(
            url=url,
            asin="",
            title="",
            status="error",
            error_message="Could not extract ASIN from URL"
        )
    
    # Strip tracking params before checking - Decodo doesn't need attribution params
    clean_url = extract_clean_amazon_url(url)
    
    try:
        # Use decodo scraper - it's installed at the skill level
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up: amazon-inventory-monitor -> skills -> workspace
        skills_dir = os.path.dirname(script_dir)  # = /root/.openclaw/workspace/skills
        decodo_skill_dir = os.path.join(skills_dir, "decodo-scraper")
        scrape_script = os.path.join(decodo_skill_dir, "tools", "scrape.py")
        
        logger.info(f"Looking for Decodo at: {scrape_script}")
        
        if not os.path.exists(scrape_script):
            logger.error(f"Decodo scrape.py not found at: {scrape_script}")
            return ProductCheck(
                url=url,
                asin=asin,
                title="",
                status="error",
                error_message="Decodo scraper not found"
            )
        
        # Load .env from decodo skill directory
        env_file = os.path.join(decodo_skill_dir, ".env")
        decodo_token = ""
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    if line.strip().startswith("DECODO_AUTH_TOKEN="):
                        decodo_token = line.split("=", 1)[1].strip()
                        break
        
        if not decodo_token:
            logger.error("DECODO_AUTH_TOKEN not found in .env")
            return ProductCheck(
                url=url,
                asin=asin,
                title="",
                status="error",
                error_message="DECODO_AUTH_TOKEN not found"
            )
        
        # Build command with environment - use clean URL for Decodo
        cmd = f'''cd "{decodo_skill_dir}" && DECODO_AUTH_TOKEN="{decodo_token}" python3 tools/scrape.py --target amazon --url "{clean_url}" 2>&1'''
        
        result = os.popen(cmd).read()
        
        if not result:
            return ProductCheck(
                url=url,
                asin=asin,
                title="",
                status="error",
                error_message="No response from Decodo"
            )
        
        # Parse JSON response
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            return ProductCheck(
                url=url,
                asin=asin,
                title="",
                status="error",
                error_message=f"Failed to parse Decodo response: {result[:200]}"
            )
        
        # Check stock status
        stock = data.get("stock", "")
        price = data.get("price", 0)
        title = data.get("title", "")
        
        if "in stock" in stock.lower() or "instock" in stock.lower():
            status = "in_stock"
        elif "out of stock" in stock.lower() or "unavailable" in stock.lower():
            status = "out_of_stock"
        elif "currently unavailable" in stock.lower():
            status = "unavailable"
        else:
            # Default based on presence of price
            if price and price > 0:
                status = "in_stock"
            else:
                status = "unknown"
        
        return ProductCheck(
            url=url,
            asin=asin,
            title=title,
            status=status,
            price=price,
            error_message=None
        )
        
    except Exception as e:
        logger.error(f"Error checking {url}: {e}")
        return ProductCheck(
            url=url,
            asin=asin,
            title="",
            status="error",
            error_message=str(e)
        )


def check_all_campaigns(customer_id: str, max_workers: int = 10, require_spend: bool = True) -> List[CampaignInventoryReport]:
    """Check inventory for all enabled campaigns using parallel Decodo calls.
    
    Args:
        customer_id: Google Ads customer ID
        max_workers: Maximum number of parallel Decodo calls (default: 10)
        require_spend: If True, only check ASINs with spend/clicks in last 7 days (default: True)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # Get all campaigns with URLs
    campaigns = get_google_ads_campaigns_with_urls(customer_id, require_spend=require_spend)
    
    if not campaigns:
        logger.info("No enabled campaigns with Amazon URLs found")
        return []
    
    logger.info(f"Found {len(campaigns)} campaigns with Amazon URLs")
    logger.info(f"Using {max_workers} parallel workers for Decodo calls")
    
    # Deduplicate URLs per campaign
    reports = []
    for camp in campaigns:
        camp_id = camp["campaign_id"]
        camp_name = camp["campaign_name"]
        camp_status = camp["campaign_status"]
        
        # Deduplicate URLs
        unique_urls = list(set(camp["final_urls"]))
        
        logger.info(f"Processing campaign {camp_id}: {camp_name} ({len(unique_urls)} URLs)")
        
        report = CampaignInventoryReport(
            campaign_id=camp_id,
            campaign_name=camp_name,
            status=camp_status,
            products=[]
        )
        
        # Use ThreadPoolExecutor for parallel Decodo calls
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all URL checks
            future_to_url = {executor.submit(check_amazon_product_with_decodo, url): url for url in unique_urls}
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    product = future.result()
                    report.products.append(product)
                    status_str = "✅" if product.status == "in_stock" else "❌"
                    logger.info(f"  {status_str} {product.asin}: {product.status}")
                except Exception as e:
                    logger.error(f"Error checking {url}: {e}")
                    report.products.append(ProductCheck(
                        url=url,
                        asin=extract_asin_from_url(url) or "unknown",
                        title="",
                        status="error",
                        error_message=str(e)
                    ))
        
        reports.append(report)
    
    return reports


def generate_report(reports: List[CampaignInventoryReport]) -> str:
    """Generate formatted report for Feishu."""
    
    if not reports:
        return "✅ **Amazon Inventory Check Complete**\n\nNo enabled campaigns with Amazon URLs found."
    
    # Summary
    total_campaigns = len(reports)
    total_products = sum(len(r.products) for r in reports)
    in_stock = sum(r.in_stock_count for r in reports)
    out_of_stock = sum(r.out_of_stock_count for r in reports)
    
    lines = []
    lines.append("📊 **Amazon Inventory Check Report**")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("**Summary:**")
    lines.append(f"- Total Campaigns: {total_campaigns}")
    lines.append(f"- Total Products: {total_products}")
    lines.append(f"- ✅ In Stock: {in_stock}")
    lines.append(f"- ❌ Out of Stock / Unavailable: {out_of_stock}")
    lines.append("")
    
    # Detailed per campaign
    for report in reports:
        lines.append("---")
        lines.append(f"**Campaign:** {report.campaign_name}")
        lines.append(f"ID: `{report.campaign_id}` | Status: {report.status}")
        lines.append(f"Products: {report.in_stock_count} ✅ | {report.out_of_stock_count} ❌")
        lines.append("")
        
        for product in report.products:
            if product.status == "in_stock":
                status_icon = "✅"
                status_text = f"${product.price}" if product.price else "In Stock"
            elif product.status in ("out_of_stock", "unavailable"):
                status_icon = "❌"
                status_text = "Out of Stock"
            else:
                status_icon = "⚠️"
                status_text = product.error_message or "Unknown"
            
            # Truncate title
            title = product.title[:60] + "..." if len(product.title) > 60 else product.title
            
            lines.append(f"{status_icon} **{title}**")
            lines.append(f"   ASIN: `{product.asin}` | {status_text}")
            lines.append(f"   URL: {product.url}")
            lines.append("")
    
    # Add recommendations
    if out_of_stock > 0:
        lines.append("---")
        lines.append("⚡ **Recommendations:**")
        lines.append(f"1. {out_of_stock} product(s) are out of stock - consider pausing these ads")
        lines.append("2. Review the destination URLs and update if products are discontinued")
        lines.append("3. Look for alternative products to replace out-of-stock items")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Amazon inventory for Google Ads")
    parser.add_argument(
        "--customer-id",
        required=True,
        help="Google Ads Customer ID (without dashes)"
    )
    parser.add_argument(
        "--output",
        help="Output file path (optional)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=10,
        help="Number of parallel Decodo calls (default: 10)"
    )
    parser.add_argument(
        "--no-spend-filter",
        action="store_true",
        help="Don't filter by recent spend (check all Amazon URLs, even with no recent spend)"
    )
    
    args = parser.parse_args()
    
    require_spend = not args.no_spend_filter
    
    logger.info(f"Starting inventory check for customer {args.customer_id}")
    if require_spend:
        logger.info("Filtering to ASINs with spend/clicks in last 7 days")
    else:
        logger.info("Checking all ASINs (no spend filter)")
    
    reports = check_all_campaigns(args.customer_id, max_workers=args.parallel, require_spend=require_spend)
    
    if args.json:
        # Output as JSON
        output = []
        for r in reports:
            output.append({
                "campaign_id": r.campaign_id,
                "campaign_name": r.campaign_name,
                "status": r.status,
                "products": [
                    {
                        "url": p.url,
                        "asin": p.asin,
                        "title": p.title,
                        "status": p.status,
                        "price": p.price,
                        "error": p.error_message
                    }
                    for p in r.products
                ]
            })
        print(json.dumps(output, indent=2))
    else:
        # Generate formatted report
        report_text = generate_report(reports)
        print(report_text)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(report_text)
            logger.info(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
