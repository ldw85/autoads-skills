#!/usr/bin/env python3
"""PartnerBoost Product Selector - Get products from PartnerBoost API"""
import os
import sys
import csv
import time
import json
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
PARTNERBOOST_API_URL = "https://app.partnerboost.com"
OUTPUT_CSV = "/root/.openclaw/workspace/logs/partnerboost_selected_products.csv"
FEISHU_DOC_TOKEN = ""  # To be configured
EXCHANGE_RATE = 7.0

# =====================
# CONFIG FROM ENV
# =====================
def load_partnerboost_config():
    """Load PartnerBoost config from .env file"""
    env_path = "/root/.openclaw/workspace/autoads/.env"
    config = {"token": "", "uid": ""}
    
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#"): continue
                if "=" not in line: continue
                key, val = line.split("=", 1)
                if key == "PARTNERBOOST_TOKEN":
                    config["token"] = val
                elif key == "PARTNERBOOST_UID":
                    config["uid"] = val
    
    return config

# =====================
# CREDENTIALS (Env File Fallback)
# =====================
def get_partnerboost_creds():
    """Get PartnerBoost credentials from .env"""
    config = load_partnerboost_config()
    if config["token"]:
        return config["token"], config.get("uid", "")
    return None, None

# =====================
# API CLIENT
# =====================
class PartnerBoostClient:
    def __init__(self, token: str = None, uid: str = None):
        self.token = token or ""
        self.uid = uid or ""
        self.base_url = PARTNERBOOST_API_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_products(self, page: int = 1, page_size: int = 20, country_code: str = "US", 
                  brand_id: int = None, sort: str = "", asins: str = "",
                  relationship: int = 1, has_promo_code: int = 0, has_acc: int = 0) -> dict:
        """Get FBA products from PartnerBoost API
        
        Args:
            page: Page number (starts from 1)
            page_size: Items per page (max 100)
            country_code: Country filter (US, UK, etc.)
            brand_id: Brand ID filter
            sort: Sort order (price_desc, price_asc, discount_desc, etc.)
            asins: Specific ASINs to fetch (comma-separated)
            relationship: 1 = affiliate products only
            has_promo_code: Filter by promo code availability
            has_acc: Filter by accelerator commission
            
        Returns:
            dict with 'list' and 'has_more' keys
        """
        payload = {
            "token": self.token,
            "page_size": page_size,
            "page": page,
            "default_filter": 0,
            "country_code": country_code,
            "brand_id": brand_id,
            "sort": sort,
            "asins": asins,
            "relationship": relationship,
            "is_original_currency": 0,
            "has_promo_code": has_promo_code,
            "has_acc": has_acc,
            "filter_sexual_wellness": 0,
            "uid": self.uid,
            "return_link": 0
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None and v != ""}
        
        # Use explicit URL
        url = "https://app.partnerboost.com/api/datafeed/get_fba_products"
        
        try:
            resp = self.session.post(
                url,
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("status", {}).get("code") == 0:
                return data.get("data", {})
            else:
                logger.error(f"API error: {data.get('status', {})}")
                return {"list": [], "has_more": False}
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            return {"list": [], "has_more": False}
    
    def get_all_products(self, page_size: int = 50, max_pages: int = 100, delay: float = 1.0) -> list:
        """Fetch all products across multiple pages
        
        Args:
            page_size: Items per page
            max_pages: Maximum pages to fetch
            delay: Delay between requests (seconds)
            
        Returns:
            List of all products
        """
        all_products = []
        page = 1
        
        while page <= max_pages:
            logger.info(f"Fetching page {page}...")
            result = self.get_products(page=page, page_size=page_size)
            
            products = result.get("list", [])
            if not products:
                break
                
            all_products.extend(products)
            logger.info(f"  Total: {len(all_products)}")
            
            if not result.get("has_more", False):
                break
                
            page += 1
            time.sleep(delay)
        
        return all_products
    
    def extract_asin(self, url: str) -> str:
        """Extract ASIN from Amazon URL"""
        if not url:
            return ""
        # Match patterns like /dp/ASIN or /gp/product/ASIN
        import re
        match = re.search(r'/dp/([A-Z0-9]{10})', url) or re.search(r'/gp/product/([A-Z0-9]{10})', url)
        return match.group(1) if match else ""
    
    def parse_price(self, price_str: str) -> float:
        """Parse price string like '$269.99' to float"""
        if not price_str:
            return 0.0
        import re
        match = re.search(r'[\d.]+', price_str.replace(',', ''))
        return float(match.group(0)) if match else 0.0
    
    def get_link(self, product: dict, tracking_id: str = "", ad_id: str = "") -> str:
        """Generate affiliate link with custom tracking
        
        Args:
            product: Product dict from API
            tracking_id: Custom tracking ID
            ad_id: Ad group ID
            
        Returns:
            Affiliate link with tracking params
        """
        link = product.get("link", "")
        if not link or ("?" not in link):
            return link
            
        # Add custom tracking params
        separator = "&" if "&" in link else "?"
        base, suffix = link.split("?", 1)
        
        params = []
        for param in suffix.split("&"):
            if param.startswith("maas="):
                # Replace maas with custom tracking
                if tracking_id:
                    params.append(f"maas={tracking_id}")
                else:
                    params.append(param)
            elif param.startswith("aa_campaignid="):
                if tracking_id:
                    params.append(f"aa_campaignid=PB{tracking_id[:8]}")
                else:
                    params.append(param)
            elif param.startswith("aa_adgroupid="):
                if ad_id:
                    params.append(f"aa_adgroupid={ad_id}")
                else:
                    params.append(param)
            else:
                params.append(param)
        
        return f"{base}?{'&'.join(params)}"


# =====================
# FILTERS
# =====================
def filter_products(products: list, min_price: float = 0, max_price: float = 99999,
                   min_reviews: int = 0, min_rating: float = 0,
                   min_discount: float = 0, has_promo: bool = False,
                   has_acc: bool = False) -> list:
    """Filter products by criteria
    
    Args:
        products: Raw product list
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        min_reviews: Minimum review count
        min_rating: Minimum rating (0-5)
        min_discount: Minimum discount percentage
        has_promo: Must have promo code
        has_acc: Must have accelerator commission
        
    Returns:
        Filtered product list
    """
    client = PartnerBoostClient()
    filtered = []
    
    for p in products:
        # Price filter
        price = client.parse_price(p.get("discount_price") or p.get("original_price", ""))
        if price < min_price or price > max_price:
            continue
        
        # Reviews filter
        reviews_str = p.get("reviews", "0")
        reviews = int(reviews_str.replace(",", "")) if reviews_str else 0
        if reviews < min_reviews:
            continue
        
        # Rating filter
        rating_str = p.get("rating", "0")
        try:
            rating = float(rating_str)
        except:
            rating = 0.0
        if rating < min_rating:
            continue
        
        # Discount filter
        discount_str = p.get("discount", "0%").replace("%", "")
        try:
            discount = float(discount_str)
        except:
            discount = 0.0
        if discount < min_discount:
            continue
        
        # Promo code filter
        if has_promo:
            promo_codes = p.get("promo_code_list", [])
            if not promo_codes:
                continue
        
        # Accelerator filter
        if has_acc:
            acc_comm = p.get("acc_commission", "")
            if not acc_comm or acc_comm == "0%":
                continue
        
        filtered.append(p)
    
    return filtered


def export_to_csv(products: list, output_path: str):
    """Export products to CSV
    
    Args:
        products: Product list
        output_path: Output CSV file path
    """
    if not products:
        logger.warning("No products to export")
        return
    
    client = PartnerBoostClient()
    fieldnames = [
        "ASIN",
        "product_name",
        "brand_name",
        "original_price",
        "discount_price", 
        "discount",
        "rating",
        "reviews",
        "commission",
        "acc_commission",
        "category",
        "subcategory",
        "availability",
        "country_code",
        "url",
        "link",
        "has_promo",
        "has_acc"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for p in products:
            row = {
                "ASIN": client.extract_asin(p.get("url", "")),
                "product_name": p.get("product_name", ""),
                "brand_name": p.get("brand_name", ""),
                "original_price": p.get("original_price", ""),
                "discount_price": p.get("discount_price", ""),
                "discount": p.get("discount", ""),
                "rating": p.get("rating", ""),
                "reviews": p.get("reviews", ""),
                "commission": p.get("commission", ""),
                "acc_commission": p.get("acc_commission", ""),
                "category": p.get("category", ""),
                "subcategory": p.get("subcategory", ""),
                "availability": p.get("availability", ""),
                "country_code": p.get("country_code", ""),
                "url": p.get("url", ""),
                "link": p.get("link", ""),
                "has_promo": "Yes" if p.get("promo_code_list") else "No",
                "has_acc": "Yes" if p.get("acc_commission") else "No"
            }
            writer.writerow(row)
    
    logger.info(f"Exported {len(products)} products to {output_path}")


def export_to_markdown(products: list, output_path: str):
    """Export products to Markdown table
    
    Args:
        products: Product list  
        output_path: Output MD file path
    """
    if not products:
        return
    
    client = PartnerBoostClient()
    lines = ["# PartnerBoost选品结果\n"]
    lines.append(f"共{len(products)}个商品\n")
    lines.append("---\n")
    lines.append("| # | ASIN | 产品 | 品牌 | 价格 | 折扣 | 评论 | 评分 | 佣金 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    
    for i, p in enumerate(products[:50], 1):  # Max 50 for display
        asin = client.extract_asin(p.get("url", ""))
        name = p.get("product_name", "")[:25]
        brand = p.get("brand_name", "")
        price = p.get("discount_price", "-")
        disc = p.get("discount", "-")
        rev = p.get("reviews", "0")
        rat = p.get("rating", "-")
        comm = p.get("acc_commission", p.get("commission", "-"))
        
        lines.append(f"|{i}|{asin}|{name}|{brand}|{price}|{disc}|{rev}|{rat}|{comm}|")
    
    lines.append("\n---\n")
    lines.append(f"*共{len(products)}个商品*")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Exported markdown to {output_path}")


# =====================
# MAIN
# =====================
def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PartnerBoost Product Selector")
    parser.add_argument("--token", "-t", help="PartnerBoost API token")
    parser.add_argument("--uid", "-u", help="PartnerBoost UID")
    parser.add_argument("--country", "-c", default="US", help="Country code (default: US)")
    parser.add_argument("--page-size", "-ps", type=int, default=50, help="Page size (default: 50)")
    parser.add_argument("--max-pages", "-mp", type=int, default=50, help="Max pages (default: 50)")
    parser.add_argument("--min-price", type=float, default=0, help="Minimum price")
    parser.add_argument("--max-price", type=float, default=9999, help="Maximum price")
    parser.add_argument("--min-reviews", type=int, default=20, help="Minimum reviews (default: 20)")
    parser.add_argument("--min-rating", type=float, default=4.0, help="Minimum rating (default: 4.0)")
    parser.add_argument("--min-discount", type=float, default=0, help="Minimum discount %%")
    parser.add_argument("--has-promo", action="store_true", help="Must have promo code")
    parser.add_argument("--has-acc", action="store_true", help="Must have accelerator")
    parser.add_argument("--output", "-o", default=OUTPUT_CSV, help="Output CSV path")
    parser.add_argument("--export-md", "-m", help="Export to markdown file")
    
    args = parser.parse_args()
    
    # Get credentials from .env if not provided
    if not args.token:
        args.token, args.uid = get_partnerboost_creds()
    
    if not args.token:
        logger.error("No PARTNERBOOST_TOKEN found in .env")
        sys.exit(1)
    
    # Create client
    client = PartnerBoostClient(token=args.token, uid=args.uid)
    
    # Fetch products
    logger.info(f"Fetching products from {args.country}...")
    products = client.get_all_products(
        page_size=args.page_size,
        max_pages=args.max_pages,
        delay=1.0
    )
    
    logger.info(f"Total products fetched: {len(products)}")
    
    if not products:
        logger.error("No products fetched")
        sys.exit(1)
    
    # Filter
    logger.info("Applying filters...")
    filtered = filter_products(
        products,
        min_price=args.min_price,
        max_price=args.max_price,
        min_reviews=args.min_reviews,
        min_rating=args.min_rating,
        min_discount=args.min_discount,
        has_promo=args.has_promo,
        has_acc=args.has_acc
    )
    
    logger.info(f"Products after filtering: {len(filtered)}")
    
    # Export
    export_to_csv(filtered, args.output)
    
    if args.export_md:
        export_to_markdown(filtered, args.export_md)
    
    logger.info("Done!")


if __name__ == "__main__":
    main()