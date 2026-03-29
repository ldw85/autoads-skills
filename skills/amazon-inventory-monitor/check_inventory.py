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


def get_google_ads_campaigns_with_urls(customer_id: str) -> List[Dict[str, Any]]:
    """Get all enabled campaigns with their ad destination URLs.
    
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
        
        # Query for all enabled campaigns
        query = """
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
                ad_group_ad.status
            FROM ad_group_ad
            WHERE campaign.status = 'ENABLED'
            AND ad_group.status = 'ENABLED'
            AND ad_group_ad.status = 'ENABLED'
        """
        
        ga_service = google_ads.client.get_service("GoogleAdsService")
        search_request = google_ads.client.get_type("SearchGoogleAdsRequest")
        search_request.query = query
        search_request.customer_id = customer_id
        
        results = ga_service.search(request=search_request)
        
        for row in results:
            campaign = row.campaign
            ad_group = row.ad_group
            ad = row.ad_group_ad.ad
            
            # Extract final URLs (apply suffix if present)
            final_urls = []
            if ad.final_urls:
                url_suffix = ad.final_url_suffix or ""
                for base_url in ad.final_urls:
                    if url_suffix and "?" not in base_url:
                        final_url = f"{base_url}?{url_suffix}"
                    else:
                        final_url = base_url
                    final_urls.append(final_url)
            
            # Only keep Amazon URLs
            amazon_urls = [u for u in final_urls if is_amazon_url(u)]
            
            if amazon_urls:
                campaigns_data.append({
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "campaign_status": campaign.status.name,
                    "ad_id": str(ad.id),
                    "final_urls": amazon_urls,
                    "headlines": [h.text for h in ad.responsive_search_ad.headlines] if ad.responsive_search_ad else [],
                })
        
        return campaigns_data
        
    except Exception as e:
        logger.error(f"Error fetching Google Ads data: {e}")
        return []


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
        
        # Build command with environment
        cmd = f'''cd "{decodo_skill_dir}" && DECODO_AUTH_TOKEN="{decodo_token}" python3 tools/scrape.py --target amazon --url "{url}" 2>&1'''
        
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


def check_all_campaigns(customer_id: str) -> List[CampaignInventoryReport]:
    """Check inventory for all enabled campaigns."""
    
    # Get all campaigns with URLs
    campaigns = get_google_ads_campaigns_with_urls(customer_id)
    
    if not campaigns:
        logger.info("No enabled campaigns with Amazon URLs found")
        return []
    
    logger.info(f"Found {len(campaigns)} campaigns with Amazon URLs")
    
    # Deduplicate URLs per campaign
    reports = []
    for camp in campaigns:
        camp_id = camp["campaign_id"]
        camp_name = camp["campaign_name"]
        camp_status = camp["campaign_status"]
        
        # Deduplicate URLs
        unique_urls = list(set(camp["final_urls"]))
        
        report = CampaignInventoryReport(
            campaign_id=camp_id,
            campaign_name=camp_name,
            status=camp_status,
            products=[]
        )
        
        for url in unique_urls:
            logger.info(f"Checking {url}...")
            product = check_amazon_product_with_decodo(url)
            report.products.append(product)
        
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
    
    args = parser.parse_args()
    
    logger.info(f"Starting inventory check for customer {args.customer_id}")
    
    reports = check_all_campaigns(args.customer_id)
    
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
