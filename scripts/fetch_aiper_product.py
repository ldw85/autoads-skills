#!/usr/bin/env python3
import subprocess
import json
import time

url = "https://www.amazon.com/dp/B0FJ818NNZ"

print("⏳ 正在调用 Decodo API 获取商品信息...")
time.sleep(2)  # Rate limit mitigation

result = subprocess.run(
    ["python3", "/root/.openclaw/workspace/skills/amazon-product-fetcher/scripts/fetch.py", "--url", url, "--json"],
    capture_output=True,
    text=True,
    timeout=30
)

if result.returncode == 0:
    try:
        data = json.loads(result.stdout)
        print("\n✅ 商品信息获取成功!")
        print("\n📋 商品详情:")
        print(f"   ASIN: {data.get('asin', 'N/A')}")
        print(f"   标题: {data.get('title', 'N/A')}")
        print(f"   价格: {data.get('currency', 'USD')} {data.get('price', 'N/A')}")
        print(f"   评分: {data.get('rating', 'N/A')} ⭐")
        print(f"   评论数: {data.get('reviews', 'N/A')}")
        print(f"   库存: {data.get('availability', 'N/A')}")
        print(f"   图片: {data.get('image_url', 'N/A')[:80]}...")
    except:
        print(result.stdout)
else:
    print(f"❌ 错误: {result.stderr}")
    print("\n尝试备用方案...")
    
    # Try direct curl
    import os
    token = os.environ.get("DECODO_AUTH_TOKEN", "")
    if token:
        import urllib.request
        import urllib.parse
        
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }
        
        payload = json.dumps({
            "url": url,
            "country": "US",
            "source": "amazon_pricing"
        }).encode()
        
        req = urllib.request.Request(
            "https://scraper-api.decodo.com/v2/scrape",
            data=payload,
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                print("\n✅ 备用方案成功!")
                print(f"   价格: {data.get('price', {}).get('value', 'N/A')}")
                print(f"   Currency: {data.get('price', {}).get('currency', 'USD')}")
        except Exception as e:
            print(f"备用方案也失败: {e}")