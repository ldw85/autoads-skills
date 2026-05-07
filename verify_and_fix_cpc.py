#!/usr/bin/env python3
"""
Verify all campaign names' maxbidcpc matches calculated value.
For campaigns missing price, fetch via Decodo.
"""
import json, time, random, urllib.request, urllib.error, re, sys
from pathlib import Path

AUTH = "VTAwMDAzODA1MDQ6UFdfMWI3MjgzMzRmOTE4NjdlMmU3ZDY4ZWVmNzE4ZDEwMzY1"
SCRAPE_URL = "https://scraper-api.decodo.com/v2/scrape"
DB_FILE = "/root/.openclaw/workspace/autoads/logs/ad_campaigns_db.json"

def calculate_maxbidcpc(price, commission_rate):
    """Calculate maxbidcpc from price/rate - matches main.py formula"""
    BASE_CPC = 1.2
    calculated_cpc = price * commission_rate / 50 * 6.9 * 0.9
    if calculated_cpc > BASE_CPC * 4:
        return round(BASE_CPC * 2.0, 4)    # 2.4
    elif calculated_cpc > BASE_CPC * 3:
        return round(BASE_CPC * 1.5, 4)    # 1.8
    elif calculated_cpc > BASE_CPC * 2:
        return round(BASE_CPC * 1.2, 4)    # 1.44
    else:
        return round(calculated_cpc * 1.2, 4)

def decodo_fetch_price(asin):
    """Fetch price via Decodo API"""
    payload = json.dumps({"target":"amazon_pricing","query":asin,"headless":"html","page_from":"1","parse":True}).encode()
    req = urllib.request.Request(SCRAPE_URL, data=payload, headers={
        "Accept":"application/json","Authorization":f"Basic {AUTH}","Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            pricing = data.get("results",[{}])[0].get("content",{}).get("results",{}).get("pricing",[])
            if pricing:
                return pricing[0].get("price", 0)
    except Exception:
        pass
    return None

def main():
    # Load database
    with open(DB_FILE) as f:
        db = json.load(f)

    # Get all campaigns (enabled + paused)
    campaigns = [c for c in db["campaigns"] if c.get("asin") and c.get("status") in ("ENABLED", "PAUSED")]
    print(f"Total campaigns to check: {len(campaigns)}")

    # Find campaigns missing price
    missing_price = []
    for c in campaigns:
        if not c.get("price") or c.get("price") <= 0:
            missing_price.append(c)

    # Fetch missing prices via Decodo
    if missing_price:
        print(f"\nFetching {len(missing_price)} missing prices via Decodo...")
        for c in missing_price:
            asin = c["asin"]
            print(f"  Fetching {asin}...", end=" ", flush=True)
            price = decodo_fetch_price(asin)
            if price:
                c["price"] = price
                print(f"${price}")
            else:
                print("FAILED")
            time.sleep(random.uniform(0.1, 0.3))

        # Save updated DB
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=2)
        print(f"Saved updated prices to DB")

    # Verify all campaign names
    print(f"\n{'='*80}")
    print(f"{'ASIN':<15} {'CampaignID':<15} {'Status':<10} {'Name CPC':<10} {'DB CPC':<10} {'Calc CPC':<10} {'Match':<6}")
    print(f"{'='*80}")

    mismatches = []
    no_price = []

    for c in campaigns:
        asin = c["asin"]
        cid = c["campaign_id"]
        status = c["status"]
        name = c["campaign_name"]
        price = c.get("price", 0)
        rate = c.get("commission_rate", 0)

        # Get CPC from name
        name_match = re.search(r'\[maxbidcpc:\$\d+\.\d+\]', name)
        name_cpc = float(name_match.group(0).replace("[maxbidcpc:$","").replace("]","")) if name_match else None
        db_cpc = c.get("maxbidcpc", 0)

        # Calculate expected
        if price and rate:
            calc_cpc = calculate_maxbidcpc(price, rate)
        else:
            calc_cpc = None

        # Determine match
        if calc_cpc is None:
            match = "N/A"
            no_price.append(c["campaign_id"])
        elif name_cpc is None:
            match = "NO_CPC"
        elif abs(name_cpc - calc_cpc) < 0.01:
            match = "✅"
        else:
            match = "❌"
            mismatches.append({
                "asin": asin,
                "campaign_id": cid,
                "status": status,
                "name_cpc": name_cpc,
                "db_cpc": db_cpc,
                "calc_cpc": calc_cpc,
                "price": price,
                "rate": rate
            })

        name_cpc_str = f"${name_cpc:.2f}" if name_cpc else "None"
        db_cpc_str = f"${db_cpc:.2f}" if db_cpc else "None"
        calc_str = f"${calc_cpc:.2f}" if calc_cpc else "None"
        print(f"{asin:<15} {cid:<15} {status:<10} {name_cpc_str:<10} {db_cpc_str:<10} {calc_str:<10} {match}")

    print(f"{'='*80}")
    print(f"\n总结:")
    print(f"  总检查: {len(campaigns)}")
    print(f"  缺价格无法计算: {len(no_price)}")
    print(f"  名称CPC正确: {len(campaigns) - len(mismatches) - len(no_price)}")
    print(f"  名称CPC错误(需修复): {len(mismatches)}")

    if mismatches:
        print(f"\n需要修复的广告系列:")
        for m in mismatches:
            print(f"  {m['asin']} | {m['campaign_id']} | name=${m['name_cpc']:.2f} calc=${m['calc_cpc']:.2f} | price=${m['price']} rate={m['rate']}")

        # Fix mismatches
        print(f"\n正在修复 {len(mismatches)} 个错误名称...")
        fixed = 0
        for m in mismatches:
            asin = m["asin"]
            cid = m["campaign_id"]
            calc = m["calc_cpc"]
            for c in db["campaigns"]:
                if c["campaign_id"] == cid:
                    old_name = c["campaign_name"]
                    # Replace name CPC
                    new_name = re.sub(r'\[maxbidcpc:\$\d+\.\d+\]', f"[maxbidcpc:${calc:.2f}]", old_name)
                    c["campaign_name"] = new_name
                    c["maxbidcpc"] = calc
                    print(f"  Fixing {cid} ({asin}): name=${m['name_cpc']:.2f} → ${calc:.2f}")
                    fixed += 1
                    break

        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=2)
        print(f"\n✅ 已修复 {fixed} 个广告系列名称")

    else:
        print(f"\n✅ 所有广告系列名称中的CPC均正确")

if __name__ == "__main__":
    main()