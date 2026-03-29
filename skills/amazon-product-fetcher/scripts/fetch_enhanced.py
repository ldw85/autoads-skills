#!/usr/bin/env python3
"""
Amazon Product Fetcher Enhanced — stdlib only, no pip dependencies.
Fetches comprehensive product data from Amazon public pages.

新增字段:
- title: 商品标题
- about_this_item: About this item (商品特性)
- first_5star_review: 评分最高的评论(第一条)
- carousel_images: 商品轮播图URL列表
- main_image: 主图(同原版)

Usage:
    python fetch_enhanced.py --url "https://www.amazon.com/dp/B0CX44VMKZ"
    python fetch_enhanced.py --asin B0CX44VMKZ --json
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MARKETPLACE = os.environ.get("AMAZON_MARKETPLACE", "www.amazon.com")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ---------------------------------------------------------------------------
# URL / ASIN helpers
# ---------------------------------------------------------------------------

def extract_asin_from_url(url: str) -> str | None:
    for pattern in [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/ASIN/([A-Z0-9]{10})",
        r"[?&]asin=([A-Z0-9]{10})",
    ]:
        m = re.search(pattern, url, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return None

def build_url(asin: str) -> str:
    return f"https://{MARKETPLACE}/dp/{asin}"

# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------

def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except Exception as e:
        print(f"Error fetching page: {e}", file=sys.stderr)
        sys.exit(1)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first(patterns: list, text: str) -> str:
    for p in patterns:
        m = re.search(p, text, re.DOTALL | re.IGNORECASE)
        if m:
            val = html.unescape(m.group(1)).strip()
            val = re.sub(r"<[^>]+>", "", val).strip()
            if val:
                return val
    return ""

def _all(patterns: list, text: str) -> list:
    results = []
    for p in patterns:
        matches = re.findall(p, text, re.DOTALL | re.IGNORECASE)
        for m in matches:
            val = html.unescape(m).strip()
            val = re.sub(r"<[^>]+>", "", val).strip()
            if val and val not in results:
                results.append(val)
    return results

# ---------------------------------------------------------------------------
# Original field parsers
# ---------------------------------------------------------------------------

def parse_title(page: str) -> str:
    return _first([
        r'id="productTitle"[^>]*>\s*(.*?)\s*</span>',
        r'"title"\s*:\s*"([^"]{10,})"',
    ], page)

def parse_price(page: str) -> tuple:
    raw = _first([
        r'class="a-price[^"]*"[^>]*>.*?<span\s+class="a-offscreen">([^<]+)</span>',
        r'id="priceblock_ourprice"[^>]*>\s*([^<\n]+)',
        r'id="priceblock_dealprice"[^>]*>\s*([^<\n]+)',
        r'class="priceToPay[^"]*"[^>]*>.*?<span[^>]*>\s*([0-9][0-9,\.]*)\s*</span>',
    ], page)
    if not raw:
        return ("", "")
    raw = raw.strip()
    m = re.match(r'^([^\d]*)([\d,\.]+)', raw)
    if m:
        return (m.group(2).strip(), m.group(1).strip())
    return (raw, "")

def parse_rating(page: str) -> str:
    return _first([
        r'class="a-icon-alt">\s*([\d\.]+)\s+out of',
        r'aria-label="([\d\.]+) out of 5',
        r'"ratingScore"\s*:\s*"?([\d\.]+)"?',
    ], page)

def parse_reviews(page: str) -> str:
    return _first([
        r'id="acrCustomerReviewText"[^>]*>\s*([\d,]+)\s+rating',
        r'"reviewCount"\s*:\s*"?([\d,]+)"?',
        r'([\d,]+)\s+(?:global\s+)?ratings?\b',
    ], page)

def parse_availability(page: str) -> str:
    return _first([
        r'id="availability"[^>]*>.*?<span[^>]*>\s*(.*?)\s*</span>',
        r'"availability"\s*:\s*"([^"]+)"',
    ], page)

def parse_image(page: str) -> str:
    return _first([
        r'"hiRes"\s*:\s*"(https://[^"]+\.jpg[^"]*)"',
        r'"large"\s*:\s*"(https://[^"]+\.jpg[^"]*)"',
        r'id="landingImage"[^>]+src="([^"]+)"',
        r'id="imgBlkFront"[^>]+src="([^"]+)"',
    ], page)

# ---------------------------------------------------------------------------
# NEW: Enhanced field parsers
# ---------------------------------------------------------------------------

def parse_about_this_item(page: str) -> list:
    """
    Parse 'About this item' section (also known as product features).
    Returns a list of feature strings.
    """
    # Try different selectors Amazon uses
    patterns = [
        # Standard feature bullets
        r'<ul[^>]*class="[^"]*a-list[^"]*"[^>]*>(.*?)</ul>',
        # Feature bullets in detail page
        r'"featurebullets"\s*:\s*\[(.*?)\]',
        # Amazon choice / product info table
        r'<div[^>]+id="productOverview[^"]*"[^>]*>(.*?)</div>',
        # Post-purchase features
        r'<div[^>]+id="poExpander"[^>]*>(.*?)</div>',
        # Generic feature list
        r'<li[^>]*class="[^"]*a-spacing[^"]*mini[^"]*"[^>]*>\s*<span[^>]*>(.*?)</span>',
    ]
    
    results = []
    section = _first(patterns, page)
    
    if section:
        # Extract individual bullet points
        bullet_patterns = [
            r'<li[^>]*>\s*<span[^>]*>(.*?)</span>',
            r'<li[^>]*>(.*?)</li>',
            r'"keyFeature"\s*:\s*"(.*?)"',
        ]
        for p in bullet_patterns:
            matches = re.findall(p, section, re.DOTALL | re.IGNORECASE)
            for m in matches:
                val = html.unescape(m).strip()
                val = re.sub(r"<[^>]+>", "", val).strip()
                if val and len(val) > 3 and val not in results:
                    results.append(val)
    
    # Fallback: search for feature text directly
    if not results:
        patterns2 = [
            r'feature-bullets[^>]*>.*?<ul[^>]*>(.*?)</ul>',
            r'product-overview[^>]*>.*?<ul[^>]*>(.*?)</ul>',
        ]
        for p in patterns2:
            m = re.search(p, page, re.DOTALL | re.IGNORECASE)
            if m:
                items = re.findall(r'<li[^>]*>(.*?)</li>', m.group(1), re.DOTALL)
                for item in items:
                    val = html.unescape(item).strip()
                    val = re.sub(r"<[^>]+>", "", val).strip()
                    if val and len(val) > 3 and val not in results:
                        results.append(val)
    
    return results[:10]  # Limit to 10 features

def parse_first_5star_review(page: str) -> dict:
    """
    Find the top positive review (5-star).
    Returns dict with review text, author, date, helpful votes.
    """
    result = {
        "rating": "",
        "text": "",
        "author": "",
        "date": "",
        "helpful_votes": 0,
        "verified": False
    }
    
    # Find reviews section - look for 5-star reviews first
    # Amazon stores reviews in JSON data often
    review_patterns = [
        # JSON format reviews
        r'"reviews"\s*:\s*\[(.*?)\]',
        r'"reviewBody"\s*:\s*"([^"]{50,})"',
        r'"reviewText"\s*:\s*"([^"]{50,})"',
        # HTML review items
        r'<div[^>]+class="[^"]*review[^"]*"[^>]*>.*?<span[^>]+class="[^"]*review-text[^"]*"[^>]*>(.*?)</span>',
    ]
    
    review_text = ""
    for p in review_patterns:
        m = re.search(p, page, re.DOTALL | re.IGNORECASE)
        if m:
            review_text = html.unescape(m.group(1)).strip()
            review_text = re.sub(r"<[^>]+>", "", review_text).strip()
            if len(review_text) > 50:
                break
    
    # Try to find star rating near the review
    star_patterns = [
        r'<span[^>]+class="[^"]*a-icon-alt[^"]*"[^>]*>\s*([\d\.]+)\s*out\s*of',
        r'"rating"\s*:\s*([\d\.]+)',
        r'<span[^>]+aria-label="([^"]*5[^"]*star[^"]*)"',
    ]
    
    for p in star_patterns:
        m = re.search(p, page, re.IGNORECASE)
        if m:
            result["rating"] = m.group(1).strip()
            break
    
    # If no 5-star found, look for top positive review
    if not result["rating"]:
        # Look for "Most helpful" or top review marker
        top_patterns = [
            r'class="[^"]*cr-original-review-text[^"]*"[^>]*>(.*?)</[^>]+>',
            r'<span[^>]+class="[^"]*review-text[^"]*"[^>]*>(.*?)</span>',
        ]
        for p in top_patterns:
            m = re.search(p, page, re.DOTALL | re.IGNORECASE)
            if m:
                text = html.unescape(m.group(1)).strip()
                text = re.sub(r"<[^>]+>", "", text).strip()
                if len(text) > 50:
                    review_text = text
                    result["rating"] = "5.0"
                    break
    
    result["text"] = review_text[:2000]  # Limit review length
    
    # Try to extract author
    author_patterns = [
        r'<span[^>]+class="[^"]*author[^"]*"[^>]*>(.*?)</span>',
        r'"author"\s*:\s*"([^"]+)"',
        r'By\s+<[^>]*>([^<]+)<',
    ]
    for p in author_patterns:
        m = re.search(p, page, re.IGNORECASE)
        if m:
            result["author"] = html.unescape(m.group(1)).strip()
            break
    
    # Try to extract date
    date_patterns = [
        r'<span[^>]+class="[^"]*review-date[^"]*"[^>]*>(.*?)</span>',
        r'"reviewDate"\s*:\s*"([^"]+)"',
        r'on\s+([A-Z][a-z]+\s+\d+,\s+\d{4})',
    ]
    for p in date_patterns:
        m = re.search(p, page, re.IGNORECASE)
        if m:
            result["date"] = html.unescape(m.group(1)).strip()
            break
    
    # Try to find helpful votes
    helpful_patterns = [
        r'(\d+)\s*(?:people|found|voted)\s*(?:this\s*)?helpful',
        r'"helpfulVoteCount"\s*:\s*(\d+)',
        r'class="[^"]*cr-helpful[^"]*"[^>]*>\s*(\d+)',
    ]
    for p in helpful_patterns:
        m = re.search(p, page, re.IGNORECASE)
        if m:
            result["helpful_votes"] = int(m.group(1))
            break
    
    # Check verified purchase
    if re.search(r'Verified\s*Purchase', page, re.IGNORECASE):
        result["verified"] = True
    
    return result

def parse_carousel_images(page: str) -> list:
    """
    Extract product carousel/alternative images.
    Returns list of image URLs.
    """
    images = []
    
    # Pattern 1: Amazon's new image gallery JSON
    json_patterns = [
        r'"entrenchedPremiumImageBelt"\s*:\s*\[(.*?)\]',
        r'"imageGalleryData"\s*:\s*\[(.*?)\]',
        r'"colorImages"\s*:\s*\{[^}]*"initial"\s*:\s*\[(.*?)\]',
    ]
    
    for p in json_patterns:
        m = re.search(p, page, re.DOTALL | re.IGNORECASE)
        if m:
            # Extract URLs from JSON array
            urls = re.findall(r'"https://[^"]+\.jpg[^"]*"', m.group(1))
            for url in urls:
                url = html.unescape(url).strip('"')
                if url and url not in images:
                    images.append(url)
    
    # Pattern 2: Legacy image arrays
    img_patterns = [
        r'"thumbImage"\s*:\s*\[(.*?)\]',
        r'"largeImage"\s*:\s*\[(.*?)\]',
    ]
    
    for p in img_patterns:
        m = re.search(p, page, re.DOTALL | re.IGNORECASE)
        if m:
            urls = re.findall(r'https://[^"]+\.jpg[^"]*', m.group(1))
            for url in urls:
                if url and url not in images:
                    images.append(url)
    
    # Pattern 3: Image blob data
    blob_patterns = [
        r'"hiRes"\s*:\s*\[(.*?)\]',
        r'"large"\s*:\s*\[(.*?)\]',
    ]
    
    for p in blob_patterns:
        m = re.search(p, page, re.DOTALL | re.IGNORECASE)
        if m:
            urls = re.findall(r'https://[^"]+(?:\.jpg|\.png|\.jpeg)[^"]*', m.group(1))
            for url in urls:
                if url and url not in images:
                    images.append(url)
    
    # Pattern 4: Data-asin images
    asin_img_patterns = [
        r'"ASIN"\s*:\s*"[^"]+"\s*,\s*"assigned_to_hover[^"]*"\s*,\s*\[(.*?)\]',
    ]
    
    for p in asin_img_patterns:
        m = re.search(p, page, re.DOTALL | re.IGNORECASE)
        if m:
            urls = re.findall(r'https://[^"]+(?:\.jpg|\.png|\.jpeg)[^"]*', m.group(1))
            for url in urls:
                if url and url not in images:
                    images.append(url)
    
    # Remove duplicates and clean
    seen = set()
    unique_images = []
    for url in images:
        # Skip icons and tiny images
        if any(x in url.lower() for x in ['icon', 'sprite', 'pixel', 'blank', 'data:']):
            continue
        if url not in seen and len(url) > 50:
            seen.add(url)
            unique_images.append(url)
    
    return unique_images[:20]  # Limit to 20 images

def parse_brand(page: str) -> str:
    """Parse brand name."""
    patterns = [
        r'<a[^>]+id="bylineInfo"[^>]*>([^<]+)</a>',
        r'<a[^>]+class="[^"]*brand[^"]*"[^>]*>([^<]+)</a>',
        r'"brand"\s*:\s*"([^"]+)"',
        r'Brand\s*:</[^>]+>\s*<[^>]+>([^<]+)<',
    ]
    return _first(patterns, page)

def parse_bullet_features(page: str) -> list:
    """Alias for parse_about_this_item for clarity."""
    return parse_about_this_item(page)

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def fetch_product_enhanced(asin: str) -> dict:
    url = build_url(asin)
    page = fetch_page(url)
    
    about_item = parse_about_this_item(page)
    first_review = parse_first_5star_review(page)
    carousel = parse_carousel_images(page)
    
    # Only use first carousel image as main image if no hiRes found
    main_image = parse_image(page)
    if not main_image and carousel:
        main_image = carousel[0]
    
    price, currency = parse_price(page)
    
    return {
        "asin": asin,
        "title": parse_title(page),
        "brand": parse_brand(page),
        "price": price,
        "currency": currency,
        "rating": parse_rating(page),
        "reviews": parse_reviews(page),
        "availability": parse_availability(page),
        "main_image": main_image,
        "carousel_images": carousel,
        "about_this_item": about_item,
        "first_5star_review": first_review if first_review.get("text") else None,
        "product_url": url,
    }

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_enhanced_report(d: dict) -> None:
    print(f"\n📦 Amazon Product Report — {d.get('asin', '')}\n")
    print("=" * 70)
    
    title = d.get("title", "N/A")
    print(f"🏷️  Title: {title}")
    print()
    
    if d.get("brand"):
        print(f"🏪 Brand: {d.get('brand')}")
    
    print(f"💰 Price: {d.get('currency', '')}{d.get('price', 'N/A')}")
    print(f"⭐ Rating: {d.get('rating', 'N/A')} ({d.get('reviews', 'N/A')} reviews)")
    print(f"📦 Availability: {d.get('availability', 'N/A')}")
    print()
    
    print("-" * 70)
    print("📸 Main Image:")
    print(f"   {d.get('main_image', 'N/A')}")
    print()
    
    if d.get("carousel_images"):
        print(f"🎠 Carousel Images ({len(d.get('carousel_images', []))} total):")
        for i, img in enumerate(d.get('carousel_images', [])[:5], 1):
            print(f"   {i}. {img}")
        if len(d.get('carousel_images', [])) > 5:
            print(f"   ... and {len(d.get('carousel_images', [])) - 5} more")
        print()
    
    print("-" * 70)
    print("📋 About This Item:")
    features = d.get("about_this_item", [])
    if features:
        for i, feat in enumerate(features, 1):
            print(f"   {i}. {feat}")
    else:
        print("   (Not found)")
    print()
    
    print("-" * 70)
    print("⭐ First 5-Star Review:")
    review = d.get("first_5star_review")
    if review and review.get("text"):
        print(f"   Rating: {review.get('rating', 'N/A')} ⭐")
        if review.get("author"):
            print(f"   Author: {review.get('author')}")
        if review.get("date"):
            print(f"   Date: {review.get('date')}")
        if review.get("verified"):
            print(f"   ✅ Verified Purchase")
        if review.get("helpful_votes"):
            print(f"   👍 Helpful: {review.get('helpful_votes')} votes")
        print(f"   Review:\n   {review.get('text', 'N/A')[:500]}")
        if len(review.get('text', '')) > 500:
            print(f"   ... [truncated, full review in JSON output]")
    else:
        print("   (Not found)")
    print()
    
    print("=" * 70)
    print(f"🔗 Product URL: {d.get('product_url', '')}")

def main():
    parser = argparse.ArgumentParser(
        description="Amazon Product Fetcher Enhanced — fetches title, About This Item, "
                   "first 5-star review, carousel images, and more."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--asin", help="Amazon ASIN (e.g. B0CX44VMKZ)")
    group.add_argument("--url",  help="Full Amazon product URL")
    parser.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output as JSON (machine-readable)"
    )
    parser.add_argument(
        "--marketplace", default=None,
        help="Amazon domain (default: www.amazon.com)"
    )
    args = parser.parse_args()
    
    if args.marketplace:
        global MARKETPLACE
        MARKETPLACE = args.marketplace
    
    if args.url:
        asin = extract_asin_from_url(args.url)
        if not asin:
            print(f"Error: Could not extract ASIN from URL: {args.url}", file=sys.stderr)
            sys.exit(1)
    else:
        asin = args.asin.strip().upper()
    
    result = fetch_product_enhanced(asin)
    
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_enhanced_report(result)

if __name__ == "__main__":
    main()
