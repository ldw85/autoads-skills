#!/usr/bin/env python3
"""Direct Decodo API call for Aiper Scuba S1"""

import urllib.request
import urllib.parse
import json
import os

url = "https://www.amazon.com/dp/B0FJ818NNZ"
token = os.environ.get("DECODO_AUTH_TOKEN", "")

print("⏳ 获取 Aiper Scuba S1 商品信息...")
print(f"   URL: {url}")

if not token:
    print("❌ DECODO_AUTH_TOKEN 环境变量未设置")
    print("\n使用备用方案 - 直接抓取 Amazon...")
    
    # Fallback: try direct HTTP request
    import urllib.error
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
            # Simple price extraction
            import re
            price_match = re.search(r'<span class="a-price-whole">(\d+)</span><span class="a-price-decimal">\.(\d+)</span>', html)
            if price_match:
                whole = price_match.group(1)
                decimal = price_match.group(2)
                print(f"\n✅ 价格获取成功: ${whole}.{decimal}")
            else:
                print("   无法提取价格")
                
            # Extract title
            title_match = re.search(r'<span id="productTitle"[^>]*>([^<]+)</span>', html)
            if title_match:
                title = title_match.group(1).strip()
                print(f"   标题: {title[:80]}...")
                
    except Exception as e:
        print(f"❌ 错误: {e}")
else:
    # Use Decodo API
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }
    
    payload = json.dumps({
        "url": url,
        "country": "US",
        "source": "amazon"
    }).encode()
    
    req = urllib.request.Request(
        "https://scraper-api.decodo.com/v2/scrape",
        data=payload,
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            
            print("\n✅ Decodo API 返回:")
            print(f"   状态: {data.get('status', 'unknown')}")
            
            if 'title' in data:
                print(f"   标题: {data['title'][:80]}...")
            
            price_info = data.get('price', {})
            if price_info:
                print(f"   价格: {price_info.get('currency', 'USD')} {price_info.get('value', 'N/A')}")
            
            if 'rating' in data:
                print(f"   评分: {data['rating']} ⭐")
                
            if 'review_count' in data:
                print(f"   评论数: {data['review_count']}")
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误: {e.code}")
        if e.code == 429:
            print("   Decodo API 速率限制，请稍后再试")
    except Exception as e:
        print(f"❌ 错误: {e}")