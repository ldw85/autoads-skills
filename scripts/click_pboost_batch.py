#!/usr/bin/env python3
"""点击脚本: 串行访问5个PartnerBoost短链，每个10次，间隔30-60s"""
import asyncio
import random
import sys
from playwright.async_api import async_playwright

LINKS = [
    "https://pboost.me/x1ez7S4K1",
    "https://pboost.me/K1ez84SE",
    "https://pboost.me/h1eyZe51D",
    "https://pboost.me/N1eyaVZ0a",
    "https://pboost.me/D1ew3PDOD"
]
CLICK_COUNT = 10
MIN_INTERVAL = 30
MAX_INTERVAL = 60

async def main():
    print(">>> Starting click script...", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        
        total_ok = 0
        for link in LINKS:
            page = await context.new_page()
            short_code = link.split('/')[-1]
            ok = 0
            
            for i in range(CLICK_COUNT):
                try:
                    print(f"Visiting {link}...", flush=True)
                    await page.goto(link, timeout=15000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(1500)
                    ok += 1
                    print(f"[{short_code}] [{i+1}/10] OK", flush=True)
                except Exception as e:
                    print(f"[{short_code}] [{i+1}/10] FAIL: {e}", flush=True)
                
                if i < CLICK_COUNT - 1:
                    wait_time = random.randint(MIN_INTERVAL, MAX_INTERVAL)
                    print(f"  Waiting {wait_time}s...", flush=True)
                    await asyncio.sleep(wait_time)
            
            total_ok += ok
            print(f">>> [{short_code}] Done: {ok}/10", flush=True)
            await page.close()
        
        await browser.close()
        print(f"\n=== All done: {total_ok}/50 ===", flush=True)

if __name__ == "__main__":
    asyncio.run(main())