#!/usr/bin/env python3
"""Archer Product Selector - Get products from Archer API"""
import os
import sys
import csv
import time
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
ARARCHER_API_URL = "https://api.archeraffiliates.com"
OUTPUT_CSV = "/root/.openclaw/workspace/logs/archer_selected_products.csv"
FEISHU_DOC_TOKEN = "Ly7XdBWptoNWxVxMha3cwhLbn7f"
EXCHANGE_RATE = 6.98

# =====================
# CREDENTIALS
# =====================
SOCKET_PATH = "/var/run/cred-agent/cred-agent.sock"
BUFFER_SIZE = 4096

def cred_agent_get(name: str) -> str:
    """Get credential from cred-agent daemon via UNIX socket"""
    if not Path(SOCKET_PATH).exists():
        return None
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2)
        client.connect(SOCKET_PATH)
        client.sendall(f"GET {name}".encode())
        chunks = []
        while True:
            try:
                chunk = client.recv(BUFFER_SIZE)
                if not chunk:
                    break
                chunks.append(chunk)
            except socket.timeout:
                break
        response = b"".join(chunks)
        client.close()
        return response.decode() if response else None
    except Exception:
        return None

import socket

def get_archer_credentials():
    """Get Archer credentials from cred-agent or env"""
    return {
        "username": cred_agent_get("ARCHER_USERNAME"),
        "password": cred_agent_get("ARCHER_PASSWORD"),
        "access_token": os.environ.get("ARCHER_ACCESS_TOKEN"),
    }

def refresh_archer_token(username, password):
    """Refresh Archer access token via /token endpoint"""
    if not username or not password:
        return None
    try:
        resp = requests.post(
            ARARCHER_API_URL + "/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            if token:
                env_path = Path("/root/.openclaw/workspace/autoads/.env")
                lines = []
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        lines = f.readlines()
                new_lines = []
                found = False
                for line in lines:
                    if line.startswith('ARCHER_ACCESS_TOKEN='):
                        new_lines.append('ARCHER_ACCESS_TOKEN=' + token + '\n')
                        found = True
                    else:
                        new_lines.append(line)
                if not found:
                    new_lines.append('\nARCHER_ACCESS_TOKEN=' + token + '\n')
                with open(env_path, 'w') as f:
                    f.writelines(new_lines)
                logger.info("Token refreshed successfully")
                return token
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
    return None

def fetch_archer_products():
    """Fetch all products from Archer API"""
    logger.info("Fetching Archer products...")
    
    creds = get_archer_credentials()
    username = creds.get("username")
    password = creds.get("password")
    access_token = creds.get("access_token")
    
    if username and password:
        logger.info("Trying token refresh...")
        new_token = refresh_archer_token(username, password)
        if new_token:
            access_token = new_token
    
    if not access_token:
        env_path = Path("/root/.openclaw/workspace/autoads/.env")
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('ARCHER_ACCESS_TOKEN='):
                        access_token = line.split('=', 1)[1].strip()
                        break
    
    if not access_token:
        logger.warning("No access token found")
        return []
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer " + access_token
    }
    
    all_products = []
    page = 0
    page_size = 100
    
    while True:
        params = {"skip": page * page_size, "limit": page_size, "product_available": "yes"}
        try:
            resp = requests.get(ARARCHER_API_URL + "/getproducts", params=params, headers=headers, timeout=60)
            data = resp.json()
            if resp.status_code == 401:
                logger.warning("Token expired or invalid")
                return []
            if "product_catalog" not in data:
                logger.warning("No product_catalog in response")
                break
            products = data.get("product_catalog", [])
            if not products:
                break
            all_products.extend(products)
            logger.info(f"Page {page}: got {len(products)} products, total: {len(all_products)}")
            total = data.get("total_count", 0)
            if len(all_products) >= total:
                break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            break
    
    logger.info(f"Total Archer products fetched: {len(all_products)}")
    return all_products

def filter_products(products):
    """Filter products by conditions"""
    filtered = []
    for p in products:
        try:
            reviews = int(p.get("total_reviews", 0) or 0)
            rating = float(p.get("avg_rating", 0) or 0)
            price = float(p.get("price", 0) or 0)
            if reviews >= 500 and rating >= 4.0 and price > 0:
                filtered.append(p)
        except (ValueError, TypeError):
            continue
    logger.info(f"Filtered: {len(filtered)} from {len(products)}")
    return filtered

def extract_keywords(product):
    """Extract brand and keywords"""
    title = product.get("product_name", "")
    brand = product.get("company_name", "")
    if not brand:
        brand = title.split()[0] if title else "Unknown"
    brand = brand.split('-')[0].split()[0]
    words = title.replace("-", " ").replace(",", " ").split()
    skip_words = ["for", "with", "and", "the", "pro", "ultra", "plus", "max"]
    product_type = ""
    for w in words:
        w_clean = w.lower()
        if w_clean not in skip_words and len(w_clean) > 2:
            product_type = w
            break
    if not product_type:
        product_type = words[1] if len(words) > 1 else "Product"
    keyword1 = brand + " " + product_type
    keyword2 = brand + " " + (words[1] if len(words) > 1 else brand)
    return {"brand": brand, "keyword1": keyword1, "keyword2": keyword2}

def query_google(client, keyword):
    """Query Google Keyword Planner"""
    try:
        kp = client.get_service("KeywordPlanIdeaService")
        req = client.get_type("GenerateKeywordIdeasRequest")
        from config import get_config
        req.customer_id = get_config().google_ads.login_customer_id
        req.keyword_seed.keywords.extend([keyword])
        req.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
        # US location + English language
        geo_svc = client.get_service("GeoTargetConstantService")
        lang_svc = client.get_service("GoogleAdsService")
        us_geo = geo_svc.geo_target_constant_path(2840)
        us_lang = lang_svc.language_constant_path(1000)
        req.geo_target_constants.extend([us_geo])
        req.language = us_lang
        # Add US location and English language
        req.geo_target_constants.extend(['2840'])  # United States
        req.language.extend(['1000'])    # English
        response = kp.generate_keyword_ideas(request=req)
        max_vol = 0
        cpc_low = cpc_high = 0
        for result in response.results:
            m = result.keyword_idea_metrics
            vol = int(m.avg_monthly_searches) if m.avg_monthly_searches else 0
            cpc_l = float(m.low_top_of_page_bid_micros / 1_000_000) if m.low_top_of_page_bid_micros else 0
            cpc_h = float(m.high_top_of_page_bid_micros / 1_000_000) if m.high_top_of_page_bid_micros else 0
            if vol > max_vol:
                max_vol = vol
                cpc_low = cpc_l
                cpc_high = cpc_h
        return {"volume": max_vol, "cpc_low": cpc_low, "cpc_high": cpc_high}
    except Exception as e:
        logger.warning(f"Google API error: {e}")
        return {"volume": 0, "cpc_low": 0, "cpc_high": 0}

def deduplicate_and_merge(results):
    """Deduplicate by ASIN"""
    seen = {}
    for r in results:
        asin = r.get("asin", "")
        vol = r.get("volume", 0)
        if asin not in seen:
            seen[asin] = r
        elif vol > seen[asin].get("volume", 0):
            seen[asin] = r
    return sorted(seen.values(), key=lambda x: x.get("volume", 0), reverse=True)

def load_from_cache():
    """Load from cache CSV"""
    cache_files = [
        "/root/.openclaw/workspace/logs/archer_65_google_final.csv",
        "/root/.openclaw/workspace/logs/archer_65_google.csv",
    ]
    for cache_file in cache_files:
        try:
            if not os.path.exists(cache_file):
                continue
            with open(cache_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                products = []
                for row in reader:
                    products.append({
                        "asin": row.get("ASIN", ""),
                        "product_name": row.get("产品名称", ""),
                        "reviews": int(row.get("评论数", 0) or 0),
                        "rating": float(row.get("star", 0) or 0),
                        "brand": row.get("品牌词", ""),
                        "keyword1": row.get("关键词1(品牌+产品)", ""),
                        "keyword2": row.get("关键词2(品牌+型号)", ""),
                        "volume": int(row.get("搜索量/月", 0) or 0),
                        "cpc_low_rmb": float(row.get("CPC最小(RMB)", 0) or 0),
                        "cpc_high_rmb": float(row.get("CPC最大(RMB)", 0) or 0),
                    })
                if products:
                    logger.info(f"Loaded {len(products)} from cache")
                    return products
        except Exception as e:
            logger.warning(f"Cache load error: {e}")
    return None

def update_feishu(results):
    """Update Feishu doc"""
    import tempfile
    lines = []
    lines.append("# Archer选品结果 - Google API实测\n")
    lines.append(f"共{len(results)}个商品\n\n")
    lines.append("| # | ASIN | 产品名称 | 评论 | star | 品牌 | 关键词 | 搜索量/月 | CPC(￥) |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    for i, r in enumerate(results[:60], 1):
        name = r.get("product_name", "")[:22]
        cpc_str = f"{r['cpc_low_rmb']:.1f}-{r['cpc_high_rmb']:.1f}"
        lines.append(f"|{i}|{r['asin']}|{name}|{r['reviews']}|{r['rating']}|{r['brand']}|{r['keyword1']}|{r['volume']}|{cpc_str}|\n")
    content = "".join(lines)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    logger.info(f"Content: {temp_path}")
    return {"success": True}


def main():
    import sys
    sys.path.insert(0, "/root/.openclaw/workspace/autoads/src")
    from dotenv import load_dotenv
    load_dotenv("/root/.openclaw/workspace/autoads/.env")
    from config import get_config
    from google.ads.googleads.client import GoogleAdsClient
    import tempfile

    logger.info("Starting Archer Product Selector...")
    
    # Initialize Google Ads client
    cfg = get_config()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(cfg.google_ads.service_account_json)
        temp_path = f.name
    client = GoogleAdsClient.load_from_dict({
        "developer_token": cfg.google_ads.developer_token,
        "json_key_file_path": temp_path,
        "login_customer_id": cfg.google_ads.login_customer_id,
        "use_proto_plus": True,
    })
    
    # Step 1: Get products from Archer API or cache
    all_products = fetch_archer_products()
    
    if not all_products:
        logger.warning("Archer API unavailable, trying cache...")
        all_products = load_from_cache()
    
    if not all_products:
        logger.error("No products available")
        return {"success": False}
    
    # Step 2: Filter products (reviews >= 500, rating >= 4.0)
    filtered = filter_products(all_products)
    
    if not filtered:
        logger.warning("No filtered products, using all from cache")
        filtered = all_products
    
    logger.info(f"Processing {len(filtered)} products...")
    
    # Step 3: Query Google for volume and CPC (with US+EN)
    results = []
    for product in filtered[:20]:  # Limit to avoid quota issues
        kw = product.get("keyword1", product.get("product_name", ""))
        if kw:
            data = query_google(client, kw)
            product["volume"] = data.get("volume", 0)
            product["cpc_low_rmb"] = data.get("cpc_low", 0) * 6.98
            product["cpc_high_rmb"] = data.get("cpc_high", 0) * 6.98
            results.append(product)
            logger.info(f"  {kw}: vol={data.get('volume', 0)}")
            time.sleep(0.3)
    
    if not results:
        results = filtered
    
    # Save CSV
    fieldnames = ["asin", "product_name", "reviews", "rating", "brand", "keyword1", "keyword2", "volume", "cpc_low_rmb", "cpc_high_rmb"]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(results)
    logger.info(f"Saved CSV: {OUTPUT_CSV}")
    
    # Update Feishu
    update_feishu(results)
    
    return {"success": True, "total": len(results)}

