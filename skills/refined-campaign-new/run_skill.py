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
        print(f"\n{'='*70}")
        print("📋 PHASE 6: 4 层 filter (UniversalKeywordFilter)")
        print("="*70)
        if google_kw_texts:
            from src.keyword_filter import UniversalKeywordFilter
            universal_filter = UniversalKeywordFilter()
            google_filtered = universal_filter.filter_for_standard_campaign(
                keywords=google_kw_texts,
                product_description=product_description,
                brand=args.brand
            )
            print(f"  GKP → 4-layer filter: {len(google_kw_texts)} → {len(google_filtered)}")
        else:
            google_filtered = []
            print("  (skipped: no GKP results)")

        # ===== PHASE 7: 合并 + 分类到 L0/L1/L2/L5 =====
        print(f"\n{'='*70}")
        print("📋 PHASE 7: 合并 AI + GKP + 分类到 L0/L1/L2/L5")
        print("="*70)
        # 合并关键词
        all_keywords = list(set(all_ai_kws + google_filtered))
        if args.brand:
            all_keywords.append(args.brand)
            all_keywords.append(f"{args.brand} {args.product_name}")
        print(f"  Total before classify: {len(all_keywords)} (AI: {len(all_ai_kws)} + GKP_filtered: {len(google_filtered)})")

        # 【2026-06-13 David 拍板】V3 默认工作流: AI 过滤 + AI 分类
        # Fallback: 旧 rule-based classify_keyword
        try:
            from src.keyword_workflow import KeywordPipeline
            wf = KeywordPipeline()
            # AI 含义过滤
            kept, drops = wf.ai_meaning_filter(
                keywords=all_keywords,
                product_description=product_description,
                brand=args.brand,
                product_model=args.product_model,
            )
            print(f"  V3 AI meaning filter: {len(all_keywords)} -> {len(kept)} 词")

            # AI L0/L1/L2 分类
            l0l1 = wf.ai_classify_brand_layer(
                keywords=kept,
                brand=args.brand,
                product_model=args.product_model,
                product_description=product_description,
            )
            l2l5 = wf.split_l2l5_by_word_count(kept)

            # 合并
            classified = {
                'L0': l0l1.get('L0', []),
                'L1': l0l1.get('L1', []),
                'L2': l2l5.get('L2', []),
                'L3': [],
                'L5': l2l5.get('L5', []),
            }
            print(f"  V3 AI 分类: L0={len(classified['L0'])}, L1={len(classified['L1'])}, L2={len(classified['L2'])}, L5={len(classified['L5'])}")
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
            for kw in kws[:5]:
                print(f"    - {kw}")
            if len(kws) > 5:
                print(f"    ... +{len(kws) - 5} more")

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
        l2l5_keywords=l2l5_keywords  # 2026-06-11 David 拍板
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