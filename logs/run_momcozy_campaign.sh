#!/bin/bash
cd /root/.openclaw/workspace/skills/refined-campaign-new
python3 run_skill.py \
  --url "https://www.amazon.com/dp/B0DQXPWHSK?maas=maas_adg_api_578435546800514248_static_9_129&ref_=aa_maas&tag=maas&aa_campaignid=lv_Qdr2IHhjDPl2LcCV8q&aa_adgroupid=lv_ciorfyK3auf36BzGKU&aa_creativeid=lv_x0vjm9nHCN9nq1XAJs" \
  --brand Momcozy \
  --product-name "Smart WiFi Baby Monitor with Camera and Audio" \
  --customer-id 6052559425 \
  --price 169.99 \
  --commission-rate 0.135 \
  --campaign-name "Momcozy BM04 Baby Monitor - US" \
  --product-description "Momcozy Smart WiFi Baby Monitor BM04 features: 5-inch 1080P screen, WiFi connectivity, motion & cry detection, safe fence alert, night vision, 5000mAh battery, 2-way talk, photo & video recording. For baby monitoring, elderly care, pet monitoring. NOTE: Also used for dementia patient monitoring - allows remote caregivers to check in via app." \
  --budget 20