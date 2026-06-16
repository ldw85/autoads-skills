#!/usr/bin/env python3
"""
Refined Campaign New Skill - Create NEW Campaign from Scratch

Creates a brand NEW refined/layered keyword campaign in Google Ads.
Uses AI to generate new ad creative, does not rely on existing ads.

Usage:
    python3 run_skill.py --url "https://..." --brand ROVE --customer-id 6052559425 ...
"""

import sys
import os
import argparse
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AUTOADS_DIR = '/root/.openclaw/workspace/autoads'

# 【2026-06-15】Google Ads API 限制 (架构级常量, 不硬编码产品)
# - L0_MAX_KEYWORDS: L0 ad group 最多 10 词 (Google Ads API 限制)
# - KEYWORD_MAX_CHARS: 关键词最多 80 字符 (Google Ads API 限制)
# - 这些是 API 限制, 不是产品相关, 可以作为常量定义
L0_MAX_KEYWORDS = 10
KEYWORD_MAX_CHARS = 80
KEYWORD_MAX_WORDS = 10  # Google Ads 推荐 8 词, API 严格限制 10 词
os.chdir(AUTOADS_DIR)
sys.path.insert(0, AUTOADS_DIR)

from src.refined_campaign_creator import RefinedCampaignCreator
from src.keyword_workflow import KeywordPipeline


def main():
    parser = argparse.ArgumentParser(
        description='Refined Campaign New Skill - Create NEW Layered Campaign',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required
    parser.add_argument('--url', required=True, help='Product URL (Amazon)')
    parser.add_argument('--brand', required=True, help='Brand name')
    parser.add_argument('--product-name', required=True, help='Product name')
    parser.add_argument('--customer-id', required=True, dest='customer_id', help='Google Ads customer ID')
    
    # Optional
    parser.add_argument('--campaign-name', help='Campaign name (auto-generated if not provided)')
    parser.add_argument('--product-description', default='', help='Product description for AI')
    parser.add_argument('--price', type=float, help='Product price (USD)')
    parser.add_argument('--commission-rate', type=float, dest='commission_rate', help='Commission rate (decimal)')
    parser.add_argument('--country', default='US', help='Target country (default: US)')
    parser.add_argument('--budget', type=float, default=20.0, help='Daily budget (default: 20)')
    parser.add_argument('--rating', help='Product rating (e.g., "4.6")')
    parser.add_argument('--reviews-count', type=int, dest='reviews_count', help='Number of reviews (e.g., 21000)')
    parser.add_argument('--network', default=None, help='Affiliate network name (e.g. archer, yeahpromos, partnerboost). Default: from creator init')
    parser.add_argument('--seed-keywords', dest='seed_keywords', default=None,
                        help='Comma-separated seed keywords (OPTIONAL). When provided, these '
                             'are GUARANTEED to be in core_keywords. Typical content: brand name, '
                             'product model, important variants. AI-extracted keywords added on top. '
                             'Example: --seed-keywords "ROVE,R2-4K,ROVE R2-4K DUAL"')
    parser.add_argument('--product-model', dest='product_model', default=None,
                        help='Comma-separated L0 product_model keywords (OPTIONAL, 2026-06-08 L0/L1 '
                             'optimization). L0 (Brand_Model_Strict) requires brand + at least one of '
                             'these model keywords. AI expands with same-semantic variants only '
                             '(spelling/case/spacing), never other brand product lines. '
                             'Example: --product-model "X431 PROS V 5.0,X431 PROS,X431,creader"')
    # 2026-06-11 David 拍板: --l2l5-keywords 让 13:56 需求在新建模式也完整
    # L2/L5 种子词 (产品类别 + 变体)  → GKP 拉词 → 4 层 filter → L2/L5 关键词
    parser.add_argument('--l2l5-keywords', dest='l2l5_keywords', default=None,
                        help='Comma-separated L2/L5 product category + variant keywords (OPTIONAL, '
                             '2026-06-11 David 拍板). These are used as GKP seed words to generate '
                             'L2 (core product) and L5 (long-tail) keywords. AI filters for relevance '
                             '(same product category) and drops competitors/accessories. Example: '
                             '--l2l5-keywords "Vibration Plate,Whole Body Vibration,Standing Vibrating Platform"')
    # 【2026-06-15 19:41 David 拍板】CA GKP 拉词失败, 提供手动 GKP 关键词清单接口
    parser.add_argument('--gkw-keywords', dest='gkw_keywords', default=None,
                        help='Comma-separated manually-retrieved GKP keywords (David 手动 拉取 2026-06-15). '
                             'Bypass GKP API call (e.g. CA country GKP fails on Archer account). '
                             'Example: --gkw-keywords "bodegacooler,bodega cooler,bodega car fridge"')
    parser.add_argument('--dry-run', action='store_true', dest='dry_run',
                        help='Dry run: only generate AI keywords + filter via ad_prevalidator. '
                             'Do NOT create any Google Ads campaign. Print filtered keywords for review.')
    parser.add_argument('--simplified-l0', dest='simplified_l0', action='store_true', default=True,
                        help='Use simplified L0 mode (1 L0 ad group @ max_cpc, cap $7) — DEFAULT. '
                             'This is the recommended mode for new products (Mode B in SKILL.md). '
                             'When False, would create 5 L0_3-7 testing groups ($3/$4/$5/$6/$7) '
                             'to find optimal bid (Mode A — only for mature campaigns with baseline data). '
                             'NOTE (2026-06-10): RefinedCampaignCreator only implements the simplified path; '
                             '--no-simplified-l0 is accepted for API stability but currently logged-only.')
    parser.add_argument('--no-simplified-l0', dest='simplified_l0', action='store_false',
                        help='Disable simplified L0 (use 5 L0_3-7 testing groups). '
                             'Same as --simplified-l0=False. Currently logged-only in this skill.')
    
    args = parser.parse_args()
    
    # Validate
    if not args.price or args.price <= 0:
        logger.error("Price is required and must be > 0")
        sys.exit(1)
    if args.commission_rate is None:
        logger.error("Commission rate is required")
        sys.exit(1)
    
    print("="*70)
    print("🔧 Refined Campaign New Skill - Creating NEW Layered Campaign")
    print("="*70)
    print(f"\n📋 URL: {args.url}")
    print(f"📋 Brand: {args.brand}")
    print(f"📋 Product: {args.product_name}")
    print(f"📋 Price: ${args.price}")
    print(f"📋 Commission: {args.commission_rate * 100}%")
    print(f"📋 Budget: ${args.budget}/day")
    print(f"📋 Country: {args.country}")
    print(f"📋 Network: {args.network or 'partnerboost (default)'}")

    campaign_name = args.campaign_name
    if not campaign_name:
        campaign_name = f"{args.brand} {args.product_name[:30]} - {args.country}"
    
    product_description = args.product_description
    if not product_description:
        product_description = f"{args.brand} {args.product_name}"
    
    # Parse seed keywords (comma-separated string → list)
    seed_keywords = None
    if args.seed_keywords:
        seed_keywords = [s.strip() for s in args.seed_keywords.split(',') if s.strip()]
        logger.info(f"User-provided seed keywords ({len(seed_keywords)}): {seed_keywords[:5]}...")
    
    # Parse product_model keywords (comma-separated string → list)
    product_model = None
    if args.product_model:
        product_model = [s.strip() for s in args.product_model.split(',') if s.strip()]
        logger.info(f"User-provided L0 product_model keywords ({len(product_model)}): {product_model}")

    # 2026-06-11 David 拍板: 解析 l2l5_keywords (产品类别 + 变体) 作为 L2/L5 GKP 种子
    l2l5_keywords = None
    if args.l2l5_keywords:
        l2l5_keywords = [s.strip() for s in args.l2l5_keywords.split(',') if s.strip()]
        logger.info(f"User-provided L2/L5 category keywords ({len(l2l5_keywords)}): {l2l5_keywords}")

    # Log L0 mode selection (for clarity)
    if args.simplified_l0:
        logger.info("L0 mode: SIMPLIFIED (1 ad group @ max_cpc, cap $7) — Mode B [default for new products]")
    else:
        logger.warning("L0 mode: STANDARD (5 L0_3-7 testing groups $3-$7) — Mode A [for mature campaigns]")
        logger.warning("  ⚠️ RefinedCampaignCreator currently only implements the simplified path; "
                       "this flag is logged-only in refined-campaign-new. Use refined-ads skill for Mode A.")

    # Create campaign
    creator = RefinedCampaignCreator(network=args.network)

    # ===== DRY-RUN MODE: 跑 10 个阶段 (不写 Google Ads) =====
    # 2026-06-11 David 拍板: 完整 dry-run 覆盖全部准备阶段 + 0 写入
    if args.dry_run:
        print("\n" + "="*70)
        print("🧪 DRY-RUN MODE: 10 阶段完整准备 + 0 写入 (2026-06-11 David 拍板)")
        print("="*70)

        # ===== PHASE 1: AI ad creative (headlines/descriptions/core/long-tail) =====
        print(f"\n{'='*70}")
        print("📋 PHASE 1: Generating AI Ad Creative")
        print("="*70)
        ad_creative = creator.generate_ad_creative(
            product_description=product_description,
            product_url=args.url,
            brand=args.brand,
            product_name=args.product_name,
            price=args.price,
            commission_rate=args.commission_rate,
            product_rating=args.rating,
            product_reviews_count=args.reviews_count,
            seed_keywords=seed_keywords
        )
        core = ad_creative.get('core_keywords', [])
        long_tail = ad_creative.get('long_tail_keywords', [])
        print(f"  Headlines: {len(ad_creative.get('headlines', []))}")
        print(f"  Descriptions: {len(ad_creative.get('descriptions', []))}")
        print(f"  Core keywords: {len(core)}")
        print(f"  Long-tail keywords: {len(long_tail)}")

        # ===== PHASE 2: ad_prevalidator filter (201 AMAZON tokens) =====
        print(f"\n{'='*70}")
        print("📋 PHASE 2: ad_prevalidator Filter (201 AMAZON tokens)")
        print("="*70)
        from src.ad_prevalidator import validate_and_filter_keywords
        all_ai_kws = core + long_tail
        valid, filtered = validate_and_filter_keywords([{'text': k} for k in all_ai_kws])
        # 【2026-06-16 David 拍板】修复: 赋值回 all_ai_kws (原代码 valid 被丢弃, 过滤后词仍混入合并池)
        all_ai_kws = [v['text'] for v in valid]
        print(f"  AI KEEP: {len(valid)}, DROP: {len(filtered)}")
        for f in filtered[:5]:
            print(f"    DROP: {f['text']!r}: {f['reason']}")

        # ===== PHASE 3: L0 product_model AI 扩展 (同型号拼写变体) =====
        print(f"\n{'='*70}")
        print("📋 PHASE 3: L0 product_model AI 扩展")
        print("="*70)
        if product_model:
            product_model_keywords = creator._expand_product_model_variants(
                brand=args.brand,
                product_model_keywords=product_model,
                product_description=product_description,
                product_name=args.product_name,
            )
            print(f"  User L0 model: {product_model}")
            print(f"  After AI expansion: {len(product_model_keywords)}")
            print(f"  Variants: {product_model_keywords[:8]}")
        else:
            product_model_keywords = None
            print("  product_model not provided, L0 will not be created (all brand keywords → L1)")

        # ===== PHASE 4: Sitelinks 生成 (含 4-6 fallback 验证) =====
        print(f"\n{'='*70}")
        print("📋 PHASE 4: Sitelinks 生成 (含 4-6 fallback 验证)")
        print("="*70)
        try:
            ai_sitelinks = creator.researcher.generate_sitelinks(
                product_description=product_description,
                pain_points=ad_creative.get('pain_points', []),
                headlines=ad_creative.get('headlines', []),
                keywords=ad_creative.get('core_keywords', []) + ad_creative.get('long_tail_keywords', []),
                brand_name=args.brand,
                product_rating=args.rating,
                product_reviews_count=args.reviews_count,
                has_discount=False,
                has_warranty=False,
                price_info=f"${args.price}" if args.price else None
            )
            if ai_sitelinks:
                sitelinks = [{'link_text': sl.get('title', '')[:25],
                              'description1': sl.get('description1', '')[:35],
                              'description2': sl.get('description2', '')[:35]} for sl in ai_sitelinks]
            else:
                sitelinks = creator._get_product_sitelinks(args.product_name, ad_creative.get('pain_points', []))
        except Exception as e:
            print(f"  ⚠️ Sitelink AI failed: {e}, using product-specific fallback")
            sitelinks = creator._get_product_sitelinks(args.product_name, ad_creative.get('pain_points', []))

        # 2026-06-11 David: 验证 < 4 fallback 逻辑
        if len(sitelinks) < 4:
            print(f"  ⚠️ AI returned {len(sitelinks)} sitelinks (<4), using fallback")
            sitelinks = creator._get_fallback_sitelinks()
        print(f"  Final sitelinks: {len(sitelinks)} (Google 最佳实践: 4-6)")
        for sl in sitelinks:
            print(f"    - {sl.get('link_text', '')[:25]} | {sl.get('description1', '')[:35]}")

        # ===== PHASE 5: GKP 拉词 (含 l2l5_keywords 种子) =====
        print(f"\n{'='*70}")
        print("📋 PHASE 5: GKP 拉词 (含 l2l5_keywords 种子)")
        print("="*70)
        # 【2026-06-15 19:41 David 拍板】如果用户提供了 --gkw-keywords, 跳过 GKP API 调用
        if args.gkw_keywords:
            google_kw_texts = [k.strip() for k in args.gkw_keywords.split(',') if k.strip()]
            print(f"  【2026-06-15 拍板】使用 David 手动 GKP 关键词 (跳过 GKP API, CA Archer 账号 INVALID_VALUE)")
            print(f"  GKP keywords (manual): {len(google_kw_texts)} 词")
            for kw in google_kw_texts[:10]:
                print(f"    - {kw}")
            if len(google_kw_texts) > 10:
                print(f"    ... and {len(google_kw_texts) - 10} more")
        else:
            # GKP seed: 用户 --seed-keywords 优先, 其次 l2l5_keywords, 最后 URL (2026-06-13 David 拍板)
            gkp_seed = seed_keywords if seed_keywords else (l2l5_keywords if l2l5_keywords else None)
            if seed_keywords:
                print(f"  GKP seed (user --seed-keywords): {seed_keywords[:5]}")
            elif l2l5_keywords:
                print(f"  GKP seed (L2/L5 from AI): {l2l5_keywords[:5]}")
            else:
                print(f"  GKP seed: None (fallback to URL seed)")
            try:
                from src.google_ads_client import GoogleAdsClientWrapper
                google_kw_client = GoogleAdsClientWrapper(config=creator.config.google_ads)
                google_keywords = google_kw_client.generate_keyword_ideas(
                    customer_id=args.customer_id,
                    url=args.url,
                    country=args.country,
                    language='EN',
                    keyword_texts=gkp_seed
                )
                google_kw_texts = [kw['text'] for kw in google_keywords if kw.get('text')]
                print(f"  GKP returned: {len(google_kw_texts)} keywords")
            except Exception as e:
                print(f"  ⚠️ GKP failed: {e}")
                google_kw_texts = []

        # ===== PHASE 6: 4 层 filter (UniversalKeywordFilter) =====
        # 【2026-06-16 David 拍板】精细化路径不调 4 层 AI, 只保留规则匹配
        # 原因: V3 one-shot 已经一次分桶 (含 AI 含义过滤 + 分桶), 4 层是双跑
        # 规则匹配 (Phase 6.5 ad_prevalidator 8 词/全大写 + Amazon 平台词 EXACT) 保留
        print(f"\n{'='*70}")
        print("📋 PHASE 6: 规则匹配 (跳过 4 层 AI 调) - 保留 Phase 6.5 8 词/UPPERCASE 过滤")
        print("="*70)
        if google_kw_texts:
            # 4 层 AI filter 跳过 - 交给 V3 one-shot AI 一次性分桶
            google_filtered = google_kw_texts
            print(f"  跳过 4 层 AI filter, 直接进入 Phase 6.5 规则匹配 ({len(google_kw_texts)} 词)")
        else:
            google_filtered = []
            print("  (skipped: no GKP results)")

        # ===== PHASE 6.5: 二次预校验 (L0 model + GKP 词过 8 词/UPPERCASE 过滤) =====
        # 【2026-06-15 19:41 修复】Phase 2 只过滤 AI core+long_tail, 没过滤 L0 model 变体 + GKP 词
        # 后果: 8+ 词 / UPPERCASE 词漏到 L0/L1 → Google Ads 拒绝创建
        # 修复: Phase 7 之前再用 ad_prevalidator 过滤一遍 全部 词
        print(f"\n{'='*70}")
        print("📋 PHASE 6.5: 二次预校验 (L0 model + GKP 词 过 8 词/UPPERCASE 过滤)")
        print("="*70)
        from src.ad_prevalidator import validate_and_filter_keywords
        # 收集 L0 model 变体 + GKP 词
        pre_check_kws = []
        if product_model_keywords:
            pre_check_kws.extend(product_model_keywords)
        if google_kw_texts:
            pre_check_kws.extend(google_kw_texts)
        # 加主对话手工种子词 (BODEGACOOLER 12 Volt Car Refrigerator, BODEGA COOLER 等)
        if seed_keywords:
            pre_check_kws.extend(seed_keywords)
        # 去重
        pre_check_kws = list(set(pre_check_kws))
        valid_pc, filtered_pc = validate_and_filter_keywords([{'text': k} for k in pre_check_kws])
        # 建立过滤后的白名单集合 (lowercase)
        pre_check_white = {v['text'].lower() for v in valid_pc}
        pre_check_drops_set = {f['text'].lower() for f in filtered_pc}
        print(f"  Input: {len(pre_check_kws)} 词, KEEP: {len(valid_pc)}, DROP: {len(filtered_pc)}")
        for f in filtered_pc[:10]:
            print(f"    DROP: {f['text']!r}: {f['reason']}")
        # 【关键】过滤 GKP 词 + L0 model 变体
        original_gkp_count = len(google_kw_texts)
        google_kw_texts = [k for k in google_kw_texts if k.lower() in pre_check_white]
        print(f"  GKP 词过滤: {original_gkp_count} -> {len(google_kw_texts)} (移除 {original_gkp_count - len(google_kw_texts)} 个 8+词/UPPERCASE)")
        if product_model_keywords:
            original_l0_count = len(product_model_keywords)
            product_model_keywords = [k for k in product_model_keywords if k.lower() in pre_check_white]
            print(f"  L0 model 过滤: {original_l0_count} -> {len(product_model_keywords)} (移除 {original_l0_count - len(product_model_keywords)} 个)")

        # ===== PHASE 7: 合并 + 分类到 L0/L1/L2/L5 =====
        print(f"\n{'='*70}")
        print("📋 PHASE 7: 合并 AI + GKP + 分类到 L0/L1/L2/L5")
        print("="*70)
        # 合并关键词 (Google Ads L0 词上限 10 词, 总词上限 80-100)
        # 【2026-06-16 David 拍板】删除主动追加 brand + brand+product_name 逻辑
        # 原因: 1) 全大写污染 (args.brand 原样追加)  2) 8+ 词污染 (brand+product_name 拼接)  3) 绕过 Phase 6.5 预校验
        # 修法: 全部词从 AI 核心 + AI 长尾 + GKP 池子来, 不再主动追加
        all_keywords = list(set(all_ai_kws + google_filtered))
        print(f"  Total before classify: {len(all_keywords)} (AI: {len(all_ai_kws)} + GKP_filtered: {len(google_filtered)})")

        # 【2026-06-15 拍板】V3 路径全部走 one-shot (commit ba3f8fb 后续, 优化了 AI 调用)
        # 品牌向 + 品类向 1 次 AI 调用 = 一次分桶
        # 之前: ai_meaning_filter + ai_classify_brand_layer + split_l2l5 多次调用
        try:
            from src.keyword_workflow import V3KeywordWorkflow
            wf = V3KeywordWorkflow()
            # seed_keywords 拆分为品牌种子词 (L0) + 品类种子词 (L2/L5)
            # 品牌种子词: --seed-keywords (用户预给) + [品牌+型号变体]
            brand_seed = list(seed_keywords) if seed_keywords else []
            if args.product_model:
                if isinstance(args.product_model, list):
                    brand_seed.extend(args.product_model)
                else:
                    brand_seed.append(str(args.product_model))
            # 品类种子词: --l2l5-keywords (用户预给品类 + 变体)
            category_seed = list(l2l5_keywords) if l2l5_keywords else []

            # 品牌向 one-shot
            brand_one_shot = wf.ai_filter_and_classify_one_shot(
                keywords=all_keywords,
                brand=args.brand,
                product_model=str(args.product_model) if args.product_model else '',
                product_description=product_description,
                is_brand_path=True,
                seed_keywords=brand_seed,  # 传品牌种子词 → L0 强制起点
            )
            kept = brand_one_shot['L0'] + brand_one_shot['L1'] + brand_one_shot['L2']
            drops = brand_one_shot['drop']
            l0l1 = {'L0': brand_one_shot['L0'], 'L1': brand_one_shot['L1'], 'L2': brand_one_shot['L2']}
            print(f"  V3 品牌向 one-shot: {len(all_keywords)} -> keep={len(kept)} drop={len(drops)} (L0={len(brand_one_shot['L0'])} L1={len(brand_one_shot['L1'])} L2={len(brand_one_shot['L2'])})")

            # 品类向 one-shot
            category_one_shot = wf.ai_filter_and_classify_one_shot(
                keywords=all_keywords,
                brand=args.brand,
                product_model=str(args.product_model) if args.product_model else '',
                product_description=product_description,
                is_brand_path=False,
                seed_keywords=category_seed,  # 传品类种子词 → L2 起点
            )
            l2l5 = {'L2': category_one_shot['L2'], 'L5': category_one_shot['L5']}
            print(f"  V3 品类向 one-shot: L2={len(l2l5['L2'])} L5={len(l2l5['L5'])} drop={len(category_one_shot['drop'])}")

            # 合并
            # 【2026-06-15 20:07 修复】L0 词上限: Google Ads L0 ad group 最多 10 词
            # 超出的词降级到 L1 (保留, 但不再高价争)
            l0_list = l0l1.get('L0', [])
            l0_overflow = []
            if len(l0_list) > L0_MAX_KEYWORDS:
                l0_overflow = l0_list[L0_MAX_KEYWORDS:]
                l0_list = l0_list[:L0_MAX_KEYWORDS]
                print(f"  ⚠️ L0 词超 {L0_MAX_KEYWORDS} 词上限: 移 {len(l0_overflow)} 词到 L1 (overflow)")
                for kw in l0_overflow:
                    print(f"    overflow: {kw}")

            # 【2026-06-16 David 拍板】V3 post-process 兑底
            # 问题 1: L0 出现不含 brand 的词 (例 "330 lbs office chair" / "big and tall office chair")
            # 后果 1: 违反 L0 硬规则 (MUST contain brand)
            # 修法 1: L0 不含 brand 强制重分 L2/L5 (按词数, <5 -> L2, >=5 -> L5)
            #
            # 问题 2: L1 出现"同品牌其他产品线"词 (例 "sihoo doro c300" - SIHOO 另一产品线)
            # 后果 2: 违反"L1 只收同品牌同产品线"架构原则
            # 修法 2: L1 词不含 seed_keywords 里同产品线词/类别描述词 → 重分 L2/DROP
            #
            # 【为什么不在 V3 prompt 里加 fuzzy_clause】:
            # - LLM 推理负担大, 加 fuzzy_clause 后 V3 one-shot 从 5min -> 10min 超时
            # - 用 post-process + seed_keywords 产品线词作为判定基准更快更准
            _brand_lower_local = (args.brand or '').lower().strip()
            _l2l5_keywords_lower = [k.lower().strip() for k in (l2l5_keywords or [])]
            _seed_keywords_lower = [k.lower().strip() for k in (seed_keywords or [])]
            # 提取产品类别词 (从 l2l5_keywords 提取单词)
            _category_words = set()
            for _ckw in _l2l5_keywords_lower:
                for _w in _ckw.split():
                    if len(_w) > 2 and _w not in _brand_lower_local:
                        _category_words.add(_w)
            # 从 seed_keywords 提取"产品类别描述词" (如 "sihoo m57 office chair" -> "office chair")
            _seed_product_words = set()
            for _skw in _seed_keywords_lower:
                # 去除 brand 和 model 后剩下的词
                _words = _skw.split()
                _no_brand = [w for w in _words if w != _brand_lower_local and w != 'm57']
                _seed_product_words.update(_no_brand)
            _relevant_words = _category_words | _seed_product_words
            # 【2026-06-16 补充】提取主型号 (product_model) 变体, 用于 L1 反查同品牌其他产品线
            # 如果 L1 词含 brand + 含 product_model 变体, 表示是同型号 -> KEEP L1
            # 如果 L1 词含 brand + 含其他型号代码 (m18/m90d/m16 等) -> 同品牌其他产品线 -> 重分 L2
            # 注意: product_model 是 list (--product-model "M57" 解析为 ['M57']), 取第一个为主型号
            _product_model_lower = ''
            if product_model:
                if isinstance(product_model, list):
                    _product_model_lower = str(product_model[0]).lower().strip() if product_model else ''
                else:
                    _product_model_lower = str(product_model).lower().strip()
            print(f"  [V3 post-process] 提取产品类别词 ({len(_relevant_words)} 个): {list(_relevant_words)[:10]}...")

            _l0_relocate_log = {'to_L2': 0, 'to_L5': 0}
            _l1_relocate_log = {'to_L2': 0, 'to_L5': 0, 'to_DROP': 0}
            _l5_relocated = []
            _l2_relocated = []
            _l5_relocated_from_l1 = []
            _l2_relocated_from_l1 = []
            _drop_from_l1 = []

            # 处理 L0: 不含 brand → 重分 L2/L5
            _l0_kept = []
            for _kw in l0_list:
                if _brand_lower_local and _brand_lower_local not in _kw.lower():
                    _wc = len(_kw.split())
                    _target = 'L5' if _wc >= 5 else 'L2'
                    print(f"  [V3 post-relocate] L0 -> {_target}: '{_kw}' (no brand, {_wc} words)")
                    if _target == 'L5':
                        _l5_relocated.append(_kw)
                    else:
                        _l2_relocated.append(_kw)
                    _l0_relocate_log[f'to_{_target}'] += 1
                    continue
                _l0_kept.append(_kw)
            l0_list = _l0_kept

            # 处理 L1: 验证是否同产品线
            # 判定标准 (五层检查, 顺序重要 - "同品牌其他产品线型号"优先级高于 product_words):
            # 1. 裸 brand "SIHOO" → KEEP L1 (品牌兜底)
            # 2. 含 brand + 含其他型号代码 (m18/m90d/m16/m82c/m76/m59b/m81/m56/m7) → 同品牌其他产品线 → 重分 L2 (优先级高)
            # 3. 含 product_model 主型号 (m57) → KEEP L1 (同型号)
            # 4. 含 product_words (office chair / desk chair / etc.) → KEEP L1 (同产品线)
            # 5. 含 brand + 不含 product_words + 不含型号代码 (如 "sihoo doro c300") → 其他产品线 → L2 or DROP
            # 6. 不含以上任一 → DROP
            import re as _re_l1
            # 产品型号代码匹配: 字母+数字 (如 m18, m90d, m82c, m57)
            # 但需要排除主型号 (m57) 以免误判自己
            _l1_kept = []
            for _kw in l0l1.get('L1', []):
                _kw_lower = _kw.lower()
                # 裸 brand 单独 → KEEP
                if _kw_lower.strip() == _brand_lower_local:
                    _l1_kept.append(_kw)
                    continue
                # 含 brand + 含其他型号代码 (m18/m90d 等) → 同品牌其他产品线 → 重分 L2 (优先级高)
                # 型号代码: \b[a-z]\d+  (字母 + 1个以上数字)
                _model_code_matches = _re_l1.findall(r'\b[a-z]\d+[a-z0-9]*\b', _kw_lower)
                _other_model_codes = [m for m in _model_code_matches if m != _product_model_lower]
                if _brand_lower_local in _kw_lower and _other_model_codes:
                    _wc = len(_kw.split())
                    _target = 'L5' if _wc >= 5 else 'L2'
                    print(f"  [V3 post-relocate] L1 -> {_target}: '{_kw}' (同品牌其他产品线, 含其他型号 {_other_model_codes}, {_wc} words)")
                    if _target == 'L5':
                        _l5_relocated_from_l1.append(_kw)
                    else:
                        _l2_relocated_from_l1.append(_kw)
                    _l1_relocate_log[f'to_{_target}'] += 1
                    continue
                # 含 product_model 主型号 → KEEP (同型号同产品线)
                if _product_model_lower and _product_model_lower in _kw_lower:
                    _l1_kept.append(_kw)
                    continue
                # 含 product_words → KEEP (同产品线)
                if _relevant_words and any(_rw in _kw_lower for _rw in _relevant_words):
                    _l1_kept.append(_kw)
                    continue
                # 含 brand + 不含 product_words + 不含型号代码 (如 "sihoo doro c300") → 重分 L2
                if _brand_lower_local in _kw_lower:
                    _wc = len(_kw.split())
                    _target = 'L5' if _wc >= 5 else 'L2'
                    print(f"  [V3 post-relocate] L1 -> {_target}: '{_kw}' (同品牌其他产品线, 不含同产品线词, {_wc} words)")
                    if _target == 'L5':
                        _l5_relocated_from_l1.append(_kw)
                    else:
                        _l2_relocated_from_l1.append(_kw)
                    _l1_relocate_log[f'to_{_target}'] += 1
                    continue
                # 不含 brand + 不含 product_words → DROP (本来就不该进 L1)
                print(f"  [V3 post-DROP] L1: '{_kw}' (不含 brand + 不含 product_words)")
                _drop_from_l1.append(_kw)
                _l1_relocate_log['to_DROP'] += 1
            l0l1['L1'] = _l1_kept

            if any(v > 0 for v in _l0_relocate_log.values()):
                print(f"  V3 L0 重分(无brand): to_L2 - {_l0_relocate_log['to_L2']}, to_L5 - {_l0_relocate_log['to_L5']}")
            if any(v > 0 for v in _l1_relocate_log.values()):
                print(f"  V3 L1 重分(其他产品线/DROP): to_L2 - {_l1_relocate_log['to_L2']}, to_L5 - {_l1_relocate_log['to_L5']}, to_DROP - {_l1_relocate_log['to_DROP']}")

            classified = {
                'L0': l0_list,
                'L1': l0l1.get('L1', []) + l0_overflow,  # L0 overflow 进 L1
                'L2': l2l5.get('L2', []) + _l2_relocated + _l2_relocated_from_l1,
                'L3': [],
                'L5': l2l5.get('L5', []) + _l5_relocated + _l5_relocated_from_l1,
            }
            print(f"  V3 AI 分类: L0={len(classified['L0'])}, L1={len(classified['L1'])}, L2={len(classified['L2'])}, L5={len(classified['L5'])}")

            # 【2026-06-17 David 拍板】V3 LLM 幻觉兑底: 再次过滤 8 词+UPPERCASE (L0/L1)
            # 问题: V3 LLM 有时会 hallucinate 添加完整产品名 (8+ 词) 到 L0/L1 (例 "SIHOO SIHOO M57 Ergonomic Mesh Office Chair")
            # 后果: Google Ads 拒绝创建 (超过 8 词限制)
            # 修法: 合并后用 ad_prevalidator 再过滤一遍 L0/L1, 避免幻觉产物逃出
            # L2/L5 不过滤 (8+ 词可能是长尾调色)
            from src.ad_prevalidator import validate_and_filter_keywords
            for _layer in ['L0', 'L1']:
                _valid_layer, _filtered_layer = validate_and_filter_keywords([{'text': k} for k in classified[_layer]])
                if _filtered_layer:
                    print(f"  [V3 hallucination 兑底] {_layer} 过滤 {len(_filtered_layer)} 个幻觉词:")
                    for _f in _filtered_layer:
                        print(f"    {_layer} DROP: {_f['text']!r}: {_f['reason']}")
                classified[_layer] = [v['text'] for v in _valid_layer]
        except Exception as e:
            print(f"  ⚠️ V3 AI 分类失败: {e}, fallback 到旧规则分类")
            core_terms = []
            for kw in ad_creative.get('core_keywords', []):
                words = kw.split()[:3]
                core_terms.extend(words)
            core_terms = list(set(core_terms))[:10]

            classified = {'L0': [], 'L1': [], 'L2': [], 'L3': [], 'L5': []}
            for kw in all_keywords:
                layer = creator.classify_keyword(kw, args.brand, core_terms, product_model_keywords)
                if kw not in classified[layer]:
                    classified[layer].append(kw)

        # 2026-06-08 David Q4=B: L0 词双层加到 L1
        for kw in classified['L0']:
            if kw not in classified['L1']:
                classified['L1'].append(kw)

        for layer_key, kws in classified.items():
            print(f"  {layer_key}: {len(kws)} keywords")
            for kw in kws:
                print(f"    - {kw}")

        # ===== PHASE 8: L0 词数计算 + L0/L1 词覆盖率检查 =====
        print(f"\n{'='*70}")
        print("📋 PHASE 8: L0/L1 词数验证")
        print("="*70)
        # 13:56 David 需求: L0 严格型号, L1 含品牌名 (或型号名) 即可
        l0_brand_coverage = sum(1 for kw in classified['L0'] if args.brand.lower() in kw.lower())
        l1_brand_coverage = sum(1 for kw in classified['L1'] if args.brand.lower() in kw.lower())
        l0_model_coverage = sum(1 for kw in classified['L0']
                                if product_model_keywords and any(m.lower() in kw.lower() for m in product_model_keywords))
        print(f"  L0: {len(classified['L0'])} (含品牌名: {l0_brand_coverage}, 含型号: {l0_model_coverage})")
        print(f"  L1: {len(classified['L1'])} (含品牌名: {l1_brand_coverage})")
        if l0_brand_coverage < len(classified['L0']):
            print(f"  ⚠️ {len(classified['L0']) - l0_brand_coverage} L0 词不含品牌名 (David 13:56: 严格型号应含品牌)")

        # ===== PHASE 9: Negative 关键词预估 =====
        print(f"\n{'='*70}")
        print("📋 PHASE 9: Negative 关键词预估 (本事件不写 Google Ads)")
        print("="*70)
        # 2026-06-11: 预估 negatives 来源
        # 1) GKP 中的平台词 (amazon, etc.)
        # 2) AI 自动识别的 ACCESSORY/COMPETITOR 等
        # 3) 默认 hardcoded negatives
        platform_negatives = [k for k in google_kw_texts if 'amazon' in k.lower() or 'walmart' in k.lower()]
        print(f"  GKP platform negatives (estimated): {len(platform_negatives)}")

        # ===== PHASE 10: Final report =====
        print(f"\n{'='*70}")
        print("🧪 DRY-RUN COMPLETE: 10 阶段全部跑过, 0 写入 Google Ads")
        print("="*70)
        print(f"  AI core: {len(core)}")
        print(f"  AI long-tail: {len(long_tail)}")
        print(f"  GKP raw: {len(google_kw_texts)}")
        print(f"  GKP 4-layer filter: {len(google_filtered)}")
        print(f"  L0 model variants: {len(product_model_keywords) if product_model_keywords else 0}")
        print(f"  Sitelinks: {len(sitelinks)}")
        print(f"  Platform negatives (est): {len(platform_negatives)}")
        print(f"  Classified: L0={len(classified['L0'])}, L1={len(classified['L1'])}, L2={len(classified['L2'])}, L5={len(classified['L5'])}")

        # Bid calculation
        from src.refined_campaign_creator import LAYER_CONFIG
        max_cpc = creator.calculate_max_cpc(args.price, args.commission_rate)
        print(f"\n{'='*70}")
        print(f"📊 BID PREVIEW (max_cpc=${max_cpc:.2f})")
        print("="*70)
        for layer_key, cfg in LAYER_CONFIG.items():
            bid = creator.get_layer_bid(max_cpc, layer_key)
            cap = cfg.get('cpc_cap')
            if cap and bid > cap:
                actual_bid = cap
                capped = f" (capped from ${bid:.2f})"
            else:
                actual_bid = bid
                capped = ""
            print(f"  {layer_key} | {cfg['name']:18s} | bid ${actual_bid:.2f}{capped} | match={cfg['match_type']}")

        print(f"\n🧪 Layered preview only (not classified into buckets; full classification happens in create_layered_campaign)")
        sys.exit(0)

    result = creator.create_layered_campaign(
        customer_id=args.customer_id,
        campaign_name=campaign_name,
        product_url=args.url,
        product_description=product_description,
        brand=args.brand,
        product_name=args.product_name,
        price=args.price,
        commission_rate=args.commission_rate,
        country=args.country,
        budget=args.budget,
        product_rating=args.rating,
        product_reviews_count=args.reviews_count,
        network=args.network,
        seed_keywords=seed_keywords,
        product_model=product_model,
        l2l5_keywords=l2l5_keywords,  # 2026-06-11 David 拍板
        gkw_keywords=([k.strip() for k in args.gkw_keywords.split(',') if k.strip()] if args.gkw_keywords else None)  # 2026-06-15 19:41 手动 GKP 词
    )
    
    print("\n" + "="*70)
    if result['success']:
        print("✅ SUCCESS: Campaign Created")
        print("="*70)
        print(f"\n📊 Campaign ID: {result['campaign_id']}")
        print(f"📊 Layers Created:")
        for layer, data in result.get('layers', {}).items():
            if isinstance(data, dict):
                status = '✅' if data.get('ad_group_id') else '❌'
                print(f"  {status} {layer}: {data.get('name')} - {data.get('keywords_added')} keywords")
    else:
        print("❌ FAILED")
        print(f"\nErrors: {result.get('errors', [])}")
        sys.exit(1)


if __name__ == '__main__':
    main()