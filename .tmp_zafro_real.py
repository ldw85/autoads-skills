#!/usr/bin/env python3
"""ZAFRO 8000 BTU refined-campaign-new REAL execution (v3 confirmed by David 19:34)"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/refined-campaign-new')

if __name__ == "__main__":
    from run_skill import main
    sys.argv = [
        "run_skill.py",
        "--url", "https://www.amazon.com/dp/B0D62XSBPZ?maas=maas_adg_api_582978684579272445_static_12_113&ref_=aa_maas&tag=maas&aa_campaignid=Link018c9c8dc9&aa_adgroupid=LDWLDW85eb3aa1ffdc1942fc912de27109423b43&aa_creativeid=a0f4e71b04024a8aaee2b904d7a143e1",
        "--brand", "ZAFRO",
        "--product-name", "ZAFRO 8000 BTU Portable Air Conditioner",
        "--price", "249.99",
        "--commission-rate", "0.18",
        "--customer-id", "6660356395",
        "--campaign-name", "Archer - ZAFRO 8000 BTU Portable AC - B0D62XSBPZ",
        "--country", "US",
        "--budget", "20",
        "--network", "archer",
        "--product-description", "ZAFRO 8,000 BTU Portable Air Conditioners, 4 Modes Portable AC Unit with Fast Cooling/Energy Efficient/Remote/24Hrs Timer for Bedroom/Dorms/Indoor Rooms, White. Brand: ZAFRO. Brand keywords: ZAFRO 8000 BTU Portable Air Conditioners, ZAFRO Portable Air Conditioners. Price: 249.99. Rating 4 / 2.1K+ reviews. Features: Fast cooling (350 sq.ft), energy saving, 4 modes (Cool/Dehumidifier/Fan/Sleep), low noise, easy move with wheels, removable washable double-layer filters, premium customer service.",
        "--simplified-l0",
        "--product-model", "8000 btu",
        "--seed-keywords", "zafro 8000 btu portable air conditioner, zafro portable air conditioner, zafro air conditioner, zafro portable ac, zafro",
        "--l2l5-keywords", "8000 btu portable air conditioner, 8000 btu air conditioner, portable ac for room, portable ac for bedroom, portable air conditioner for small room, small room air conditioner, mini air conditioner for room, quiet portable air conditioner, portable air conditioner with remote, small portable ac",
    ]
    main()
