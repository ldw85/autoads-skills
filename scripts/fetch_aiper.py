#!/usr/bin/env python3
import subprocess, json, time, sys

url = "https://www.amazon.com/dp/B0FJ818NNZ"

print("⏳ 获取 Aiper Scuba S1 商品信息...")
print(f"   URL: {url}")

time.sleep(5)

result = subprocess.run(
    [sys.executable, "/root/.openclaw/workspace/skills/amazon-product-fetcher/scripts/fetch.py", "--url", url],
    capture_output=True, text=True, timeout=30
)

print("\n📋 Decodo API 返回:")
print(result.stdout[:2000] if result.stdout else "无输出")
if result.stderr:
    print(f"错误: {result.stderr[:500]}")