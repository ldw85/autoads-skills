#!/bin/bash
# ============================================================
# add_phrase_negatives.sh - 通用批量加 PHRASE 否定词到指定 campaign
# ============================================================
# 【2026-06-13 创建 (David 拍板)】
# 背景: search_term_negatives.py 一次只加一个 campaign,批量场景需要循环脚本
# 用法:
#   1. 复制本脚本为新的脚本 (如 add_phrase_negatives_pb_20260613.sh)
#   2. 改写下面的 CID / Campaign ID / 否定词清单
#   3. 跑脚本: bash add_phrase_negatives_<...>.sh
#
# 注意:
#   - 每个 campaign 加它专属的否定词 (精准定位,不影响其他 campaign)
#   - --add 参数支持逗号/换行分隔 (空格是多词短语内部字符,不用作分隔符)
#   - 跑前建议 dry-run: 把 "python3" 改成 "echo" 验证
# ============================================================

set +e
PY=/root/.openclaw/workspace/scripts/search_term_negatives.py
MT=PHRASE

# ========== 配置区: 改成你的目标 ==========
# CID: customer_id (PB: 4772859239 / Yeah: 6052559425 / Archer: 6660356395)
# 下面每行是一个 campaign + 它专属的否定词 (PHRASE)

# 格式: campaign_id|negatives (多词用 \\n 分隔,shell 内部用 $'...\n...' 语法)

# add_one_campaign() { ... }  # 详见下面模板

# ========== 添加 campaign 函数 (改写后调用) ==========

add_to_campaign() {
    local camp_id=$1
    local negatives=$2
    local label=$3
    
    echo "===== $label (Campaign: $camp_id) ====="
    python3 "$PY" --customer-id "$CID" --campaign-id "$camp_id" --match-type "$MT" \
        --add "$negatives"
    echo ""
}

# ========== 在这里调用 add_to_campaign 加否定词 ==========
# 例子 (复制后改写):
# CID=4772859239
# add_to_campaign "23849915004" "anker 737 powercore 24k 140w" "Anker 20000mAh"
# add_to_campaign "23797288256" $'cosori double stack air fryer\ncosori pro 3 air fryer oven combo' "Cosori TurboBlaze"

# ========== 今天 (2026-06-13) PartnerBoost 6 个 ENABLED campaign 实战 (15 词) ==========

CID=4772859239

add_to_campaign "23849915004" "anker 737 powercore 24k 140w" "C1: Anker 20000mAh (1 词)"

add_to_campaign "23797288256" $'cosori double stack air fryer\ncosori pro 3 air fryer oven combo\ncosori stacked air fryer\nninja crispi amazon usa' "C2: Cosori TurboBlaze (4 词)"

add_to_campaign "23790668588" $'hp laptop portable charger\nportable dell laptop charger' "C3: Anker Laptop 25000mAh (2 词, 9 个误伤词不加)"

add_to_campaign "23787547830" "henske hair dryer" "C4: Wavytalk Hair Dryer (1 词)"

add_to_campaign "23825124148" $'kohl\'s luggage sale\ntravel select sets\ndelsey paris bags\nusa luggage brands' "C5: Coolife Luggage (4 词)"

add_to_campaign "23787556755" $'dyson corrale\nhair smooth cream\ncomo plancharse el pelo sola' "C6: Wavytalk Steam Straightener (3 词)"

echo "===== 全部 6 个 campaign 处理完毕 ====="
echo "C1: 1 词, C2: 4 词, C3: 2 词, C4: 1 词, C5: 4 词, C6: 3 词 = 15 PHRASE 否定词"
echo ""
echo "如需重跑,直接 bash $0 (15 词已加过,会重复添加-不影响,Google Ads 幂等)"
