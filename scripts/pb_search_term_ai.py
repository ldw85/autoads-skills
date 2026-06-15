#!/usr/bin/env python3
"""PartnerBoost 账号搜索词 AI 分析 - 完整流程

【背景】(2026-06-12)
- David 要求: 给 PartnerBoost 账号 4772859239 下所有 ENABLED 广告系列跑搜索词分析
- 跑 search_term_all.py 拿到规则分析结果 (规则是硬编码, 不够智能)
- 然后由 AI (小灰) 做语义复审, 输出否定词建议

【流程】
1. 拿所有 ENABLED + 有花费 (>=1 USD, 7 天) 的广告系列
2. 拿每个 campaign 的搜索词 + 规则分析结果
3. 写到一个 JSON 文件, 给小灰 AI 读 + 语义复审
"""
import sys, os, json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

PROJECT_ROOT = '/root/.openclaw/workspace/autoads'
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, f'{PROJECT_ROOT}/src')
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

import importlib.util
spec = importlib.util.spec_from_file_location(
    'search_term_negatives',
    '/root/.openclaw/workspace/scripts/search_term_negatives.py'
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
analyze_with_rules = m.analyze_with_rules

spec2 = importlib.util.spec_from_file_location('sta', '/root/.openclaw/workspace/scripts/search_term_all.py')
sta = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(sta)

from src.google_ads_client import GoogleAdsClientWrapper

env_path = Path(PROJECT_ROOT) / 'archer-roi' / '.env'
if env_path.exists():
    load_dotenv(env_path)

CUSTOMER_ID = '4772859239'
DAYS = 7
MIN_COST = 1.0
OUTPUT = '/tmp/pb_search_terms_ai.json'

client = GoogleAdsClientWrapper()

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=DAYS)).strftime('%Y-%m-%d')

print(f'=== PartnerBoost ({CUSTOMER_ID}) 搜索词 AI 分析 ===', flush=True)
print(f'时间范围: {start_date} ~ {end_date}', flush=True)
print(f'最小花费: ${MIN_COST}', flush=True)
print()

# 1) 拿所有有花费的 ENABLED + PAUSED campaign
camps = sta.get_active_campaigns_with_spend(client, CUSTOMER_ID, DAYS, MIN_COST)
# 过滤只保留 ENABLED (David 要求)
# 注意: sta.get_active_campaigns_with_spend 返回的 status 是 ENUM 名字, 不是字符串
enabled_camps = []
for c in camps:
    status = c.get('status', '')
    # ENUM 名字和字符串都接受
    if hasattr(status, 'name'):
        status_name = status.name
    else:
        status_name = str(status)
    if status_name == 'ENABLED':
        enabled_camps.append(c)
print(f'所有有花费 campaign: {len(camps)}, ENABLED: {len(enabled_camps)}', flush=True)
print(f'总 campaign: {len(camps)} (ENABLED: {len(enabled_camps)})', flush=True)

# 2) 逐个拿搜索词 + 规则分析 + 产品定位上下文
from src.extract_product_context import extract_product_context

results = {
    'customer_id': CUSTOMER_ID,
    'date_range': {'start': start_date, 'end': end_date},
    'campaigns': []
}

for camp in enabled_camps:
    cid = str(camp['id'])
    name = camp['name']
    cost = camp['cost']
    print(f'  ▶ {name[:50]}... (${cost:.2f})', flush=True)

    terms = sta.get_search_terms(client, CUSTOMER_ID, cid, start_date, end_date)
    if not terms:
        print(f'    无搜索词', flush=True)
        continue

    analysis = analyze_with_rules(terms)
    relevant = analysis.get('relevant', [])
    irrelevant = analysis.get('irrelevant', [])

    # 【2026-06-12】产品定位提取 (多源融合: GADS keyword + PartnerBoost + Campaign name)
    # 优先级: final_url 正则 > campaign_name 正则
    import re as re_mod
    asin = None
    try:
        # 1) 从 ad_group_ad.final_urls 抽 (权威, 与 monitor_product_status.py 同源)
        final_url_query = f"SELECT ad_group_ad.ad.final_urls FROM ad_group_ad WHERE campaign.id = {cid}"
        url_rows = client.search(final_url_query, CUSTOMER_ID)
        for r in url_rows:
            for u in (r.ad_group_ad.ad.final_urls or []):
                m = re_mod.search(r'amazon\.com/dp/(B0[A-Z0-9]{8})', u)
                if m:
                    asin = m.group(1)
                    break
            if asin:
                break
    except Exception as e:
        logger.warning(f'final_url 抽 ASIN 失败: {e}')

    # 2) fallback: 从 campaign name 抽
    if not asin:
        asin_match = re_mod.search(r'(B0[A-Z0-9]{8})', name)
        asin = asin_match.group(1) if asin_match else None

    product_ctx = None
    if asin:
        try:
            product_ctx = extract_product_context(asin, cid, CUSTOMER_ID, gads_client=client)
            ctx_short = f'brand={product_ctx.get("brand")} | type={product_ctx.get("product_type")} | name={(product_ctx.get("product_name") or "(空)")[:40]}'
            print(f'    ASIN: {asin} | 产品定位: {ctx_short}', flush=True)
        except Exception as e:
            print(f'    ⚠️ 产品定位提取失败: {e}', flush=True)
    else:
        print(f'    ⚠️ 无法抽出 ASIN (final_url 和 campaign name 都没有)', flush=True)

    print(f'    {len(terms)} 搜索词, 相关 {len(relevant)}, 不相关 {len(irrelevant)}', flush=True)

    results['campaigns'].append({
        'campaign_id': cid,
        'campaign_name': name,
        'asin': asin,
        'spend': round(cost, 2),
        'total_terms': len(terms),
        'relevant': relevant,
        'irrelevant': irrelevant,
        'all_terms': terms,
        'product_context': product_ctx,  # 【2026-06-12 新增】给 AI 复审用
    })

# 3) 保存
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print()
print(f'=== 完成, 结果保存到 {OUTPUT} ===', flush=True)
print(f'共分析 {len(results["campaigns"])} 个 ENABLED 广告系列', flush=True)
