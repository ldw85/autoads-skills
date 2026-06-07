#!/bin/bash
# 创建新的WOLFBOX汽车应急启动电源精细化分层广告系列
# ====================================

cd /root/.openclaw/workspace/skills/refined-campaign-new

python3 run_skill.py \
  --url "https://www.amazon.com/dp/B0CRRKRJ2S?maas=maas_adg_api_583998684602708158_static_9_129&ref_=aa_maas&tag=maas&aa_campaignid=lv_oib2eYQgO0eXn9yyKR&aa_adgroupid=lv_Fu3wWS3bvnwJ6mreGC&aa_creativeid=lv_qfaEvLEARtotwU4KF3&m=A2KR0J0CK34VOC" \
  --brand "WOLFBOX" \
  --product-name "4000A Jump Starter" \
  --product-description "WOLFBOX 4000A Jump Starter is a portable 12V car battery jumper with 65W quick charger and LED display. 88.8Wh capacity can start engines up to 10L gas or diesel. Includes LED light for emergency illumination. Compact and portable design." \
  --price 109.99 \
  --commission-rate 0.12 \
  --customer-id 6052559425 \
  --country US \
  --budget 20.0 2>&1

echo "Exit code: $?"