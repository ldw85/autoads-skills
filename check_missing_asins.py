#!/usr/bin/env python3
import json, urllib.request, time

AUTH = "VTAwMDAzODA1MDQ6UFdfMWI3MjgzMzRmOTE4NjdlMmU3ZDY4ZWVmNzE4ZDEwMzY1"
URL = "https://scraper-api.decodo.com/v2/scrape"
missing = ['B0CS6GYDWC','B0CTMKNWF7','B0CZPRXQ3F','B0D3XLVJL3','B0DDQ71B9P',
'B0DF2DN7NM','B0DSDFV4Z2','B0FJ818NNZ','B0FVFGL38H','B0FVXPLCKX',
'B0FWZJXS1D','B0G1LDYYC3','B0G4W3DKGB']

for asin in missing:
    payload = json.dumps({"target":"amazon_pricing","query":asin,"headless":"html","page_from":"1","parse":True}).encode()
    req = urllib.request.Request(URL, data=payload, headers={"Accept":"application/json","Authorization":f"Basic {AUTH}","Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            pricing = data.get("results",[{}])[0].get("content",{}).get("results",{}).get("pricing",[])
            if pricing:
                p = pricing[0]
                print(f"VALID|{asin}|{p.get('price')}|{p.get('condition')}|{p.get('seller','')[:20]}")
            else:
                print(f"OOS|{asin}|0|||")
    except Exception as e:
        print(f"ERR|{asin}|0|||{str(e)[:30]}")
    time.sleep(0.2)
