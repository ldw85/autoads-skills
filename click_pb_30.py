#!/usr/bin/env python3
"""点击 PartnerBoost 链接30次，间隔20分钟以上"""
import time
import random
import requests
import sys

url = "https://pboost.me/W1kKIgZ0"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}

print(f"开始点击 {url}")
print(f"目标: 30次, 间隔20分钟+\n")

for i in range(30):
    try:
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        print(f"第{i+1}/30: status={resp.status_code}")
    except Exception as e:
        print(f"第{i+1}/30: 失败 - {e}")
    
    if i < 29:  # 29次等待
        delay = random.randint(1200, 1800)  # 20-30分钟
        print(f"  等待 {delay}秒 ({delay/60:.1f}分钟)...")
        time.sleep(delay)

print("\n✓ 30次点击完成!")