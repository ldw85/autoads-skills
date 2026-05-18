#!/bin/bash
cd ~/.openclaw/workspace/autoads
python3 -m src.refined_campaign_creator \
  --url "https://www.amazon.com/dp/B0FJ818NNZ?maas=maas_adg_api_590892048320336634_static_12_201&ref_=aa_maas&tag=maas&aa_campaignid=PB87d91be16a8fd2a9f3cf7677f11ef384&aa_adgroupid=77c1bhHVGNDx3U_aStqy5msovo5umc8uNUdVUO93hYCubEAAPVqpn6_baZyUcZ7m2_bwxWK0R_ahD3n9UFxe4p0xIpR2&aa_creativeid=3b3a8bRBjNoARwxyVLYPGGnIcF5jJy4sWyICitxU4_agbrrg_c&th=1" \
  --brand "Aiper Scuba" \
  --product-name "Aiper Scuba S1 Robotic Pool Cleaner" \
  --price 549.98 \
  --commission-rate 0.10 \
  --customer-id 4772859239 \
  --campaign-name "Aiper Scuba S1 Pool Cleaner - PartnerBoost - US" \
  --product-description "Aiper Scuba S1 Robotic Pool Cleaner, Wall & Waterline Cleaning, Dual Filtration, Extended 180-Min Battery Life, Smarter Navigation with High-Precision Sensors, App Support, OTA Upgrade" \
  --country US \
  --budget 20 \
  2>&1