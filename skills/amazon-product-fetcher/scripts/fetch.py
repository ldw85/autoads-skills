#!/usr/bin/env python3
"""
Amazon Product Fetcher — via Decodo API (no direct Amazon scraping)

Uses Decodo's scraper-api to fetch Amazon product data without
being blocked by CAPTCHA or IP blocks.

Usage:
    python fetch.py --asin B0CX44VMKZ
    python fetch.py --asin B0CX44VMKZ --json
"""

import argparse
import json
import os
import re
import sys
import time
import random
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRAPE_URL = "https://scraper-api.decodo.com/v2/scrape"

# Decodo credentials — set via environment variable
# DECODO_AUTH_TOKEN=your_token (base64 encoded "user:password")
# Or use the pre-configured token from decodo-scraper skill
DEFAULT_AUTH = "VTAwMDAzODA1MDQ6UFdfMWI3MjgzMzRmOTE4NjdlMmU3ZDY4ZWVmNzE4ZDEwMzY1"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-integration": "openclaw",
}

# Rate limiting: 0.1-0.3s between calls (~5 req/s)
MIN_DELAY = 0.1
MAX_DELAY = 0.3

_last_call = 0

def rate_limit():
    global _last_call
    now = time.time()
    elapsed = now - _last_call
    if elapsed < MIN_DELAY:
        time.sleep(MIN_DELAY - elapsed + random.uniform(0, 0.05))
    _last_call = time.time()


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
    return f"https://www.amazon.com/dp/{asin}"


# ---------------------------------------------------------------------------
# Decodo API fetch
# ---------------------------------------------------------------------------

def fetch_via_decodo(asin: str, auth_token: str = None) -> dict:
    """
    Fetch Amazon product data via Decodo API.
    
    Tries amazon_pricing first (returns price + seller info),
    falls back to amazon (full page parse).
    """
    token = auth_token or os.environ.get("DECODO_AUTH_TOKEN") or DEFAULT_AUTH
    headers = {**HEADERS, "Authorization": f"Basic {token}"}
    
    # Try amazon_pricing first (cheaper, sufficient for price)
    price_data = _fetch_pricing(asin, headers)
    if price_data:
        return price_data
    
    # Fall back to full amazon parse
    return _fetch_full(asin, headers)


def _fetch_pricing(asin: str, headers: dict) -> dict | None:
    """Use amazon_pricing target — returns price, condition, seller."""
    payload = json.dumps({
        "target": "amazon_pricing",
        "query": asin,
        "headless": "html",
        "page_from": "1",
        "parse": True
    }).encode("utf-8")
    
    req = urllib.request.Request(SCRAPE_URL, data=payload, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
            results = data.get("results", [])
            if not results:
                return None
            
            content = results[0].get("content", {})
            inner = content.get("results", {})
            parse_code = inner.get("parse_status_code", 0)
            pricing = inner.get("pricing", [])
            
            if parse_code == 12000 and pricing:
                first = pricing[0]
                return {
                    "asin": asin,
                    "price": str(first.get("price", "")),
                    "currency": first.get("currency", "USD"),
                    "condition": first.get("condition", ""),
                    "seller": first.get("seller", ""),
                    "availability": first.get("delivery", ""),
                    "rating": "",
                    "reviews": "",
                    "title": inner.get("title", ""),
                    "image_url": "",
                    "product_url": build_url(asin),
                    "source": "decodo_pricing",
                    "parse_status": parse_code,
                }
    except Exception:
        pass
    
    return None


def _fetch_full(asin: str, headers: dict) -> dict | None:
    """Use amazon target — full page parse with title, rating, reviews, image."""
    url = build_url(asin)
    payload = json.dumps({
        "target": "amazon",
        "url": url,
        "parse": True,
    }).encode("utf-8")
    
    req = urllib.request.Request(SCRAPE_URL, data=payload, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
            results = data.get("results", [])
            if not results:
                return None
            
            content = results[0].get("content", {})
            
            # Parse structured fields from content
            title = content.get("title", "") or content.get("name", "")
            price_elem = content.get("price", {})
            if isinstance(price_elem, dict):
                price = price_elem.get("value", price_elem.get("raw", ""))
            else:
                price = price_elem or ""
            
            rating = content.get("rating", "")
            reviews = content.get("review_count", content.get("reviews", ""))
            image = content.get("image", content.get("main_image", ""))
            availability = content.get("availability", content.get("delivery", ""))
            
            return {
                "asin": asin,
                "price": str(price),
                "currency": "USD",
                "condition": "",
                "seller": "",
                "availability": availability,
                "rating": str(rating),
                "reviews": str(reviews),
                "title": title,
                "image_url": image,
                "product_url": url,
                "source": "decodo_full",
                "parse_status": content.get("parse_status_code", ""),
            }
    except Exception as e:
        return {"error": str(e), "asin": asin}


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def fetch_product(asin: str, auth_token: str = None) -> dict:
    rate_limit()
    
    # Try pricing endpoint first
    result = fetch_via_decodo(asin, auth_token)
    
    if result is None or result.get("error"):
        return {
            "asin": asin,
            "title": "",
            "price": "",
            "currency": "",
            "rating": "",
            "reviews": "",
            "availability": "",
            "image_url": "",
            "product_url": build_url(asin),
            "error": result.get("error", "fetch_failed") if result else "no_response",
        }
    
    return result


def print_table(d: dict) -> None:
    title = d.get("title", "")
    rows = [
        ("ASIN",         d.get("asin", "")),
        ("Title",        (title[:80] + "…") if len(title) > 80 else title),
        ("Price",        f"{d.get('currency','')}{d.get('price','')}"),
        ("Rating",       f"{d.get('rating','')} ⭐  ({d.get('reviews','')} reviews)"),
        ("Availability", d.get("availability", "")),
        ("Image",        (d.get("image_url","")[:70] + "…") if d.get("image_url") else ""),
        ("URL",          d.get("product_url", "")),
    ]
    width = max(len(k) for k, _ in rows)
    for k, v in rows:
        if v:
            print(f"  {k:<{width}}  {v}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch Amazon product data via Decodo API — no direct scraping, no CAPTCHA."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--asin", help="Amazon ASIN (e.g. B0CX44VMKZ)")
    group.add_argument("--url",  help="Full Amazon product URL")
    parser.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output as JSON (machine-readable)"
    )
    parser.add_argument(
        "--token", default=None,
        help="Decodo auth token (or set DECODO_AUTH_TOKEN env var)"
    )
    args = parser.parse_args()

    if args.url:
        asin = extract_asin_from_url(args.url)
        if not asin:
            print(f"Error: Could not extract ASIN from URL: {args.url}", file=sys.stderr)
            sys.exit(1)
    else:
        asin = args.asin.strip().upper()

    result = fetch_product(asin, auth_token=args.token)

    if args.as_json:
        # Clean output for JSON
        output = {k: v for k, v in result.items() if v}
        if "error" in output:
            print(json.dumps({"status": "error", "error": output["error"], "asin": asin}))
        else:
            print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if result.get("error"):
            print(f"\n❌ Failed to fetch {asin}: {result['error']}\n", file=sys.stderr)
            sys.exit(1)
        print(f"\n📦 Amazon Product — {asin} (via Decodo)\n")
        print_table(result)
        print()


if __name__ == "__main__":
    main()
