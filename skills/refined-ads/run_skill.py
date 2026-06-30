#!/usr/bin/env python3
"""
Refined Ads Skill - Create Layered Ad Groups with AI-powered Brand Extraction

This script creates refined/layered keyword ad groups in Google Ads.
It extracts existing ad content from Main ad group, uses AI to identify brand/core_terms,
and creates L1/L2/L5 layered (no L3) ad groups with proper keywords and ads.

Usage:
    python3 run_skill.py --campaign-id 23838920800 --customer-id 6052559425 [--brand Rove] [--product-url ...]
"""

import sys
import os
import subprocess
import argparse
import json
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Change to autoads directory
AUTOADS_DIR = '/root/.openclaw/workspace/autoads'
os.chdir(AUTOADS_DIR)

# Import the refined_bid_optimizer directly
sys.path.insert(0, AUTOADS_DIR)
from src.refined_bid_optimizer import RefinedBidOptimizer, AdContent, SitelinkInfo


# ============================================================
# Helper Functions
# ============================================================

def check_brand_blacklist(brand: str) -> bool:
    """Check if brand is in blacklist.

    Args:
        brand: Brand name

    Returns:
        True if brand is blacklisted
    """
    import json
    import os

    blacklist_file = '/root/.openclaw/workspace/autoads/logs/blacklist_brands.json'

    if not os.path.exists(blacklist_file):
        return False

    with open(blacklist_file) as f:
        data = json.load(f)

    brands = data.get('brands', [])
    brand_lower = brand.lower().strip()

    # Check exact match or partial match
    for blacklisted in brands:
        if brand_lower == blacklisted.lower() or brand_lower in blacklisted.lower():
            logger.warning(f"⚠️ WARNING: Brand '{brand}' is in blacklist!")
            return True

    return False


# ============================================================
# L0 Keywords Generation (FIXED: Google Keyword Planner + AI)
# ============================================================
def generate_l0_keywords(
    brand: str,
    product_description: str = None,
    product_model: str = None,
    product_url: str = None,
    customer_id: str = None,
    user_seed: list = None  # 2026-06-11 David: 用户提供的 L0 词也作为 GKP 种子 (需求: 13:56 拍板)
) -> list:
    """Generate L0 (Brand_Model) keywords - 合并GKP和AI生成。

    Simple flow:
    1. Call GKP API with simple seed → get real user search keywords
    2. Call AI to generate keywords from product description → get more variations
    3. AI validates AI-generated keywords → filter out wrong-product/competitor
    4. Merge GKP + validated AI → dedup → final list

    没搜索量的词不浪费钱(不被触发),所以 AI 生成的词可以多。
    但 AI 生成的词必须在品牌含义上正确、在产品代表上正确 (不能混入其他产品)。

    Args:
        brand: Brand name (e.g., "RhinoUSA")
        product_description: Full product description for context
        product_model: Model number (e.g., "B0BSP4NS28")
        product_url: Product URL for Google Keyword Planner
        customer_id: Google Ads customer ID

    Returns:
        List of L0 keywords (brand + product combinations)
    """
    import sys

    keywords = []
    brand_clean = brand.strip() if brand else ""

    if not brand_clean:
        return []

    # ============================================================
    # Stage 1: GKP - 从真实用户搜索中获取关键词
    # ============================================================
    gkp_raw = []  # GKP返回的原始关键词
    gkp_filtered = []  # AI从GKP过滤后的
    gkp_negatives = []  # AI从GKP识别的负面词
    if customer_id:
        try:
            # 2026-06-07 David: AI 从产品描述中动态生成【复合种子词】(品牌+型号, 品牌+类别)
            # 不硬编码 ROVE / R2-4K
            # 复合 seed 是 GKP 返回配件/安装/比较词的关键
            ai_composite_seeds = _generate_composite_seeds(brand_clean, product_description)
            if ai_composite_seeds:
                logger.info(f"AI generated {len(ai_composite_seeds)} composite seeds: {ai_composite_seeds}")
            else:
                ai_composite_seeds = []
            sys.path.insert(0, '/root/.openclaw/workspace/autoads')
            from src.refined_bid_optimizer import RefinedBidOptimizer

            # 构造种子词 - GKP最多支持10个,要尽量提供,【尤其短的】
            # 短的seed扩展范围更广,长的seed会限死GKP返回
            seed_keywords = []

            # 1) 品牌名 (2-3个变体)
            if brand:
                seed_keywords.append(brand)
                seed_keywords.append(brand.lower())
                # 不带空格的品牌名 (例如 "RhinoUSA")
                if ' ' in brand:
                    seed_keywords.append(brand.replace(' ', ''))

            # 2) 品牌简写/常拼 (2-3个)
            # 取品牌名前 4-5 个字符作为 GKP 扩展种子
            if brand and len(brand) >= 4:
                # 首字母+一些常见变体
                seed_keywords.append(brand[:4].lower())
                seed_keywords.append(brand[:5].lower())

            # 3) 从产品描述中提取【短的产品类型词】
            # 优先短词 (如 "earbuds", "headphones", "wireless")
            if product_description:
                # 提取产品描述中的词
                import re
                desc_words = re.findall(r'\b[a-zA-Z][a-zA-Z]+\b', product_description.lower())
                # 过滤: 长度>=4, 不等于品牌, 不在停用词中
                stop_words = {'with', 'from', 'this', 'that', 'your', 'our', 'for', 'and',
                              'the', 'are', 'has', 'have', 'was', 'were', 'will', 'would',
                              'can', 'could', 'should', 'may', 'might', 'must', 'shall',
                              'enabled', 'certified', 'resistant', 'comfortable', 'carrying'}
                product_type_words = []
                seen = set()
                for w in desc_words:
                    if (4 <= len(w) <= 12 and
                        w not in stop_words and
                        w != brand.lower() and
                        w not in seen):
                        product_type_words.append(w)
                        seen.add(w)
                    if len(product_type_words) >= 4:
                        break
                seed_keywords.extend(product_type_words)

            # 4) 产品型号 (从描述中提取含数字的型号代码)
            # 2026-06-07 David: ROVE R2-4K 是关键品牌型号, 之前硬编码 pattern 只匹配大写开头词
            # -> 错过 R2-4K / R2 4K / X431 PROS V 等含数字型号
            # 新 pattern: 提取包含数字的型号 (不是纯字母)
            if product_description:
                # 提取型号候选: 1) 含连字符+数字 2) 含数字+字母混合
                # 例: R2-4K, R2 4K, X431 PROS V, P500, M2.5
                model_candidates = []
                # Pattern 1: 大写+数字+连字符+数字 (e.g., R2-4K)
                model_candidates.extend(re.findall(r'\b[A-Z]\d+(?:[-][A-Z0-9]+)+\b', product_description))
                # Pattern 2: 大写+数字 (e.g., X431, P500, M2)
                model_candidates.extend(re.findall(r'\b[A-Z]\d{2,}[A-Z]?\b', product_description))
                # Pattern 3: 大写字母+数字+大写字母 (e.g., R2 4K, V5.0)
                model_candidates.extend(re.findall(r'\b[A-Z]\d+(?:\s[A-Z0-9]+)+\b', product_description))
                # Pattern 4: 词首是数字的型号 (e.g., 128GB, 5G - 一般不是型号但是个制式)
                # 保留含字母+数字混合的: 4K, 5G 跳过

                seen_seed = set()
                for p in model_candidates:
                    p_clean = p.strip()
                    p_lower = p_clean.lower()
                    # 过滤: 长度>=2, 不是纯数字, 不是品牌
                    if (p_lower not in seen_seed and
                        p_lower not in brand.lower() and
                        len(p_clean) >= 2 and
                        any(c.isdigit() for c in p_clean) and
                        # 过滤掉纯制式词 (4K, 5G, 128GB, 24H)
                        not re.match(r'^\d+[A-Z]{1,3}$', p_clean)):
                        seed_keywords.append(p_clean)
                        seen_seed.add(p_lower)
                    if len(seed_keywords) >= 12:  # 保留 room 给品牌名+短词
                        break

            # 去重保序,限制最多10个 (GKP 限制)
            # 2026-06-07 David: 复合种子词 (品牌+型号/品牌+类别) 优先
            # AI 生成的复合 seed 排在前部, 单独的 brand/model 放后面
            # 2026-06-11 David: 用户提供的 L0 词 (--l0-keywords) 作为 GKP 种子, 优先于 AI 复合 seed
            if user_seed:
                user_seed_clean = [k.strip() for k in user_seed if k and k.strip()]
                # 去重后插入到最前面 (优先级最高)
                seed_keywords = list(dict.fromkeys(user_seed_clean + seed_keywords))
                logger.info(f"User L0 seed added to GKP seed list: {user_seed_clean[:5]}")
            all_keywords_seed = ai_composite_seeds + seed_keywords
            # 去重保序
            all_keywords = list(dict.fromkeys(all_keywords_seed))[:10]
            logger.info(f"Final GKP seed (复合优先): {all_keywords}")

            if len(all_keywords) >= 2:
                opt = RefinedBidOptimizer()
                if product_url:
                    # URL + seed (KeywordAndUrlSeed) - 最全面
                    gkws = opt.client.generate_keyword_ideas(
                        customer_id=customer_id,
                        url=product_url,
                        country=args.country,
                        language=args.language,
                        limit=80,
                        keyword_texts=all_keywords,
                    )
                else:
                    # 纯 KeywordSeed (不传URL)
                    gkws = opt.client.generate_keyword_ideas(
                        customer_id=customer_id,
                        url=None,
                        country=args.country,
                        language=args.language,
                        limit=80,
                        keyword_texts=all_keywords,
                    )
                gkp_raw = [kw.get('text', '') if isinstance(kw, dict) else kw for kw in gkws]
                logger.info(f"GKP returned {len(gkp_raw)} keywords (seed: {all_keywords})")

            # AI 从 GKP 中过滤品牌关键词 (3 路分类: brand / negative / drop)
            # 【2026-06-15 拍板】--use-one-shot opt-in 路径: 走 one-shot 分类
            if gkp_raw and product_description:
                if getattr(args, 'use_one_shot', False):
                    # one-shot 路径 (V3 推荐)
                    logger.info("【one-shot 路径】使用 V3 one-shot 分类 (commit 4d5292b)")
                    try:
                        from src.keyword_workflow import V3KeywordWorkflow
                        wf = V3KeywordWorkflow()
                        # seed_keywords: --l0-keywords + --product-model + 品牌名
                        one_shot_seeds = []
                        if user_seed:
                            one_shot_seeds.extend([s.strip() for s in user_seed if s.strip()])
                        if product_model:
                            one_shot_seeds.append(str(product_model))
                        one_shot_seeds.append(brand_clean)
                        # 去重
                        one_shot_seeds = list(dict.fromkeys(one_shot_seeds))
                        # 跑 one-shot 品牌向
                        one_shot_result = wf.ai_filter_and_classify_one_shot(
                            keywords=gkp_raw,
                            brand=brand_clean,
                            product_model=str(product_model) if product_model else '',
                            product_description=product_description,
                            is_brand_path=True,
                            seed_keywords=one_shot_seeds,
                        )
                        gkp_filtered = one_shot_result['L0'] + one_shot_result['L1']
                        # drop 词转换为 negative_keywords 格式 [{keyword, reason}]
                        gkp_negatives = [
                            {'keyword': d.get('keyword', ''), 'reason': d.get('reason', '')}
                            for d in one_shot_result['drop']
                        ]
                        logger.info(f"one-shot: L0={len(one_shot_result['L0'])} L1={len(one_shot_result['L1'])} drop={len(gkp_negatives)}")
                    except Exception as e:
                        logger.warning(f"one-shot 路径失败: {e}, 降级到 _ai_filter_l0_keywords")
                        gkp_result = _ai_filter_l0_keywords(gkp_raw, brand_clean, product_description)
                        gkp_filtered = gkp_result.get('brand_keywords', [])
                        gkp_negatives = gkp_result.get('negative_keywords', [])
                else:
                    # 默认路径: _ai_filter_l0_keywords (存量补充逻辑)
                    gkp_result = _ai_filter_l0_keywords(gkp_raw, brand_clean, product_description)
                    gkp_filtered = gkp_result.get('brand_keywords', [])
                    gkp_negatives = gkp_result.get('negative_keywords', [])
                logger.info(f"AI extracted {len(gkp_filtered)} brand keywords from GKP")
                logger.info(f"AI identified {len(gkp_negatives)} negative keywords from GKP")
                if gkp_negatives:
                    logger.info(f"  Negative samples: {gkp_negatives[:5]}")
        except Exception as e:
            logger.warning(f"GKP failed: {e}")

    # ============================================================
    # Stage 2: AI 生成 - 从产品描述中生成关键词
    # ============================================================
    ai_raw = []
    if product_description:
        ai_raw = _generate_l0_from_description(brand_clean, product_description)
        logger.info(f"AI generated {len(ai_raw)} keywords from product description")

    # ============================================================
    # Stage 3: AI 验证 - 过滤 AI 生成的关键词 (避免混入其他产品/竞品)
    # ============================================================
    ai_validated = []
    if ai_raw and product_description:
        ai_validated = _validate_ai_generated_l0(ai_raw, brand_clean, product_description)
        logger.info(f"AI validated {len(ai_validated)}/{len(ai_raw)} AI-generated keywords")

    # ============================================================
    # Stage 4: 合并去重
    # ============================================================
    all_keywords_raw = list(gkp_filtered) + list(ai_validated)
    cleaned = list(set([k.strip().title() for k in all_keywords_raw if k.strip() and len(k.strip()) > 2]))

    logger.info(f"Final: {len(cleaned)} L0 keywords (GKP: {len(gkp_filtered)}, AI validated: {len(ai_validated)})")

    # 2026-06-07 David: GKP 阶段识别出的负面词, 加为 campaign negatives
    # 不传 campaign_id 时不添加, 只能从 caller 处理
    # 返回元组 (L0 keywords, negative_keywords)
    if gkp_negatives:
        # 去重, 提取 keyword 文本
        seen_neg = set()
        neg_keyword_set = set()
        for neg in gkp_negatives:
            if isinstance(neg, dict):
                kw = neg.get('keyword', '').strip().lower()
            else:
                kw = str(neg).strip().lower()
            if kw and kw not in seen_neg:
                seen_neg.add(kw)
                neg_keyword_set.add(kw)
        logger.info(f"GKP Negative keywords: {sorted(neg_keyword_set)}")
        return cleaned[:30], sorted(neg_keyword_set)
    return cleaned[:30], []


def _validate_ai_generated_l0(ai_keywords: list, brand: str, product_description: str) -> list:
    """Validate AI-generated L0 keywords to filter out wrong-product/competitor keywords.

    AI may generate keywords that are:
    - Same brand but different product model (detected via product description's technology/use case)
    - Competitor products
    - Generic terms

    This validation ensures only brand + THIS specific product keywords remain.

    IMPORTANT: Spelling variants are valuable - users who misspell still want
    this product. Keep severe misspellings if the intent is the same.
    """
    import json
    import subprocess

    if not ai_keywords:
        return []

    keywords_text = "\n".join([f"- {kw}" for kw in ai_keywords])

    prompt = f"""验证以下AI生成的关键词是否属于"品牌+该产品"。

【品牌】{brand}
【产品描述】{product_description}

【关键词列表】
{keywords_text}

【任务】只保留【用户搜索后想买本产品】的关键词。使用语义理解判断:
- 读【产品描述】了解本产品是什么
- 读【关键词列表】每个词
- 问: "如果用户在Google上搜这个词,他们想买的是【本产品】吗?"

【保留 - KEEP】:
1. ✅ 品牌名 + 当前产品型号/变体
2. ✅ 品牌名 + 当前产品词 (产品描述中明确出现的词语)
3. ✅ 品牌名错拼 + 当前产品 (拼写错误严重仍保留)
4. ✅ 品牌旧名/曾用名 + 当前产品 (品牌曾用名用户还在用)
5. ✅ 型号变体 (如 "X Pro" / "X Pro Plus" / "X-Pro" 都保留)
6. ✅ 包含产品特性词的词 (产品描述中明确列出的特性)

【过滤 - REMOVE】:
1. ❌ 同品牌但【不同产品型号】 - 使用语义理解判断型号是否与【本产品】相同
   【判断原理】
   - 读产品描述了解本产品的技术特征、使用场景、设计类型
   - 同品牌不同型号 = 不同技术 / 不同使用场景 / 不同设计
   - 例如: 本产品如果使用 [技术 A] 和 [场景 X],则带 [技术 B] 或 [场景 Y] 的同品牌词不是当前产品
   - 提示: 对比关键词中的产品词与本产品描述中的特征是否一致
2. ❌ 竞品品牌
3. ❌ 纯品牌名 (无产品词)
4. ❌ 通用购物词 (best/cheap/amazon/free shipping)
5. ❌ 完全无关词

【关键原则】
1. 拼写错误不是过滤理由! 只要搜索意图是当前产品就保留。
2. 使用语义理解判断【同品牌不同型号】 - 不要靠列举型号名
3. 核心判断: 产品描述中的【型号名/产品名/技术特征/使用场景】是判断依据

【返回】JSON
{{
  "valid_keywords": ["keyword 1", "keyword 2", ...]
}}

只返回JSON。"""

    try:
        # 2026-06-11 David: 改用 _call_claude_stream (stream-json 避免 pipe 死锁, timeout 真正生效)
        # 原 120s x 2 = 240s
        output = _call_claude_stream(prompt, timeout=240, label="validate_ai_l0")

        # 解析响应 - AI 可能在 JSON 后添加解释文本
        try:
            inner = output
            # 策略: 提取第一个完整的 JSON 对象 {...}
            # 这样可以避免 AI 后续解释文本导致 "Extra data" 错误
            import re
            # 优先提取 ```json ... ``` 代码块
            code_block = re.search(r'```json\s*(\{.*?\})\s*```', inner, re.DOTALL)
            if code_block:
                json_str = code_block.group(1)
            else:
                # Fallback: 提取第一个 { ... } 块 (非贪婪, 匹配首个)
                # 使用非贪婪让 } 限定符避免包含多个 } 的后续文本
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', inner, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    # 清理后尝试解析
                    inner_clean = inner.replace('```json', '').replace('```', '').strip()
                    json_str = inner_clean

            data = json.loads(json_str)

            if isinstance(data, dict):
                return data.get('valid_keywords', [])
            elif isinstance(data, list):
                return data
        except Exception as e:
            logger.warning(f"AI validation parse failed: {e}")
            return ai_keywords
    except Exception as e:
        logger.warning(f"AI validation failed: {e}")

    # Fallback: 返回原始 AI 关键词 (不推荐但避免丢失)
    return ai_keywords


def _generate_composite_seeds(brand: str, product_description: str) -> list:
    """Use AI to generate COMPOSITE GKP seed keywords from product description.

    Per David 2026-06-07: GKP 不返回配件词 (sd card / memory card / installation)
    根因是种子词不对。复合 seed (品牌+型号, 品牌+类别) 才是 GKP 返回配件词的关键。

    本函数从 product_description 动态生成复合种子词, 不硬编码任何产品信息。

    Args:
        brand: Brand name
        product_description: Product description for context

    Returns:
        List of composite seed keywords (e.g., ["Rove R2 4K", "Rove R2-4K", "Rove Dash Cam"])
    """
    import json
    import subprocess

    if not brand or not product_description:
        return []

    prompt = f"""从产品描述中生成【复合 GKP 种子词】。

【背景】
Google Keyword Planner (GKP) 用复合种子词 (品牌+型号, 品牌+类别) 查查时,
会返回**配件/安装/比较/平台**等周边词。例如:
  - GKP("Rove R2 4K") -> 60+ 词含 "sd card" / "hardwire kit" / "reddit" / "installing" 等周边词
  - GKP("Rove") -> 80 词全是 Rove Concepts 家具 (同品牌不同产品线)
所以必须用【复合种子词】, 不能单独用品牌名。

【品牌】{brand}
【产品描述】{product_description}

【任务】
从产品描述中识别出**最有效的复合种子词** (5-7 个)。原则:
1. 全部种子词必须含【品牌名】+【产品相关词】
2. 产品相关词 可以是:
   - 型号名 (从描述中识别含数字的型号, 例如 R2-4K, X431 PROS V)
   - 产品类别 (例如 Dash Cam, Camera, Headphones)
   - 品牌+型号 组合 (如 "[品牌] R2-4K", "[品牌] R2 4K", "[品牌] R2-4K DUAL")
   - 品牌+类别 组合 (如 "[品牌] Dash Cam", "[品牌] Car Camera")
3. 不在种子词里:
   - 配件词 (如 "SD card" - 让 GKP 主动发现, 不是手动)
   - 安装词 (如 "install" - 同上)
   - 竞品词 (如 "VIOFO" - 同上)
4. 优先顺序:
   1) 【品牌】+【型号】 (高优先 - 最精确, 容易返回高价值配件词)
   2) 【品牌】+【型号变体】 (如 R2-4K 空格变体 R2 4K)
   3) 【品牌】+【产品类别】 (返回品牌同类产品词)
5. 输出的【全部】种子词将作为 GKP 的 KeywordSeed 输入

【严格禁止】不硬编码特定产品信息:
- 任何产品型号/品牌/类别名都应该从【产品描述】动态提取
- 生成的种子词应该【适用于任何产品】, 不限于 dash cam

【返回格式】JSON
{{"composite_seeds": ["[品牌] [型号1]", "[品牌] [型号2]", "[品牌] [类别]", ...]}}

只返回 JSON。"""

    try:
        # 2026-06-11 David: 改用 _call_claude_stream (stream-json 避免 pipe 死锁, timeout 真正生效, 2x)
        # 原 timeout 360s x 2 = 720s
        output = _call_claude_stream(prompt, timeout=720, label="composite_seeds")

        try:
            inner = output
            import re
            code_block = re.search(r'```json\s*(\{.*?\})\s*```', inner, re.DOTALL)
            if code_block:
                json_str = code_block.group(1)
            else:
                # 栈找平衡 {...}
                def extract_first_balanced_json(text):
                    start = text.find('{')
                    if start == -1:
                        return None
                    depth = 0
                    in_string = False
                    escape = False
                    for i in range(start, len(text)):
                        c = text[i]
                        if escape:
                            escape = False
                            continue
                        if c == '\\':
                            escape = True
                            continue
                        if c == '"':
                            in_string = not in_string
                            continue
                        if in_string:
                            continue
                        if c == '{':
                            depth += 1
                        elif c == '}':
                            depth -= 1
                            if depth == 0:
                                return text[start:i+1]
                    return None
                json_str = extract_first_balanced_json(inner)
                if not json_str:
                    json_str = inner.replace('```json', '').replace('```', '').strip()
            data = json.loads(json_str)
            if isinstance(data, dict):
                seeds = data.get('composite_seeds', [])
                # 过滤: 含品牌名
                brand_lower = brand.lower()
                filtered = [s for s in seeds if brand_lower in s.lower() and isinstance(s, str) and len(s.strip()) >= 4]
                return filtered[:7]  # 限制 7 个
            return []
        except Exception as e:
            logger.warning(f"AI composite seeds parse failed: {e}")
            return []
    except Exception as e:
        logger.warning(f"AI composite seeds failed: {e}")
        return []


class AIRetryExhausted(RuntimeError):
    """2026-06-11 David: 连续 N 次 AI 调用 fail-fast 异常。
    携带重试次数, 供上层 caller 透传到飞书报错. 避免程序在 AI API 慢响应时静默吞掉. """
    def __init__(self, message: str, attempts: int, last_error: str):
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


# 2026-06-11 David: 全局 AI fail-fast 计数器
# 同一次 run_skill.py 运行中, AI 调用连续失败超 N 次就拋 AIRetryExhausted
_AI_FAIL_COUNT = 0
_AI_FAIL_THRESHOLD = 3  # 连续 3 次 AI 失败 -> 拋异常
_AI_TOTAL_COUNT = 0


def _call_claude_stream(prompt: str, timeout: int = 240, label: str = "AI") -> str:
    """2026-06-11 David: 调 claude CLI 用 stream-json 模式 (避免 pipe 死锁 + timeout 真正生效)。

    实际测出 claude --print --output-format json 需要 130s+ (vs stream-json 2.3s)
    stream-json 逐 chunk 推, pipe 不会 block, timeout 不会被 pipe 死锁蒙骗.

    Args:
        prompt: AI prompt
        timeout: subprocess timeout (默认 240s, 原 120s 的 2x)
        label: 用于日志的调用标识 (如 "GKP filter" / "L1 classify")

    Returns:
        最终的 text/result 字符串 (累积所有 streaming chunk)

    Raises:
        AIRetryExhausted: 连续 3 次 AI 失败
        subprocess.TimeoutExpired: 单次调用超时
    """
    global _AI_FAIL_COUNT, _AI_TOTAL_COUNT
    _AI_TOTAL_COUNT += 1

    try:
        result = subprocess.run(
            ['claude', '--print', '--output-format', 'stream-json', '--verbose', '--include-partial-messages', prompt],
            capture_output=True, text=True, timeout=timeout,
            start_new_session=True
        )

        # 2026-06-11: stream-json 逐行解析, 累积 final result
        text_accumulated = []
        final_result = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev_type = event.get('type')
            # assistant 事件有完整 content (最完整)
            if ev_type == 'assistant':
                msg = event.get('message', {})
                for block in msg.get('content', []):
                    if block.get('type') == 'text':
                        text_accumulated.append(block.get('text', ''))
            # 最终 result 事件
            elif ev_type == 'result':
                final_result = event.get('result', '')
                if final_result and not text_accumulated:
                    text_accumulated.append(final_result)
                break  # 遇到 result 就停

        if not text_accumulated:
            raise RuntimeError(f"Empty response from claude stream (label={label})")

        output = ''.join(text_accumulated).strip()
        if not output:
            raise RuntimeError(f"Empty text after parse (label={label})")

        _AI_FAIL_COUNT = 0  # 成功, 重置计数器
        return output

    except subprocess.TimeoutExpired as e:
        _AI_FAIL_COUNT += 1
        logger.warning(f"AI call [{label}] timeout after {timeout}s (fail_count={_AI_FAIL_COUNT}/{_AI_FAIL_THRESHOLD})")
        if _AI_FAIL_COUNT >= _AI_FAIL_THRESHOLD:
            raise AIRetryExhausted(
                f"AI call [{label}] failed {_AI_FAIL_COUNT} times consecutively, aborting",
                attempts=_AI_FAIL_COUNT,
                last_error=f"timeout {timeout}s"
            )
        raise
    except Exception as e:
        _AI_FAIL_COUNT += 1
        logger.warning(f"AI call [{label}] failed: {e} (fail_count={_AI_FAIL_COUNT}/{_AI_FAIL_THRESHOLD})")
        if _AI_FAIL_COUNT >= _AI_FAIL_THRESHOLD:
            raise AIRetryExhausted(
                f"AI call [{label}] failed {_AI_FAIL_COUNT} times consecutively, aborting",
                attempts=_AI_FAIL_COUNT,
                last_error=str(e)
            )
        raise


def _ai_filter_l0_keywords(gkp_keywords: list, brand: str, product_description: str) -> dict:
    """Use AI to filter GKP keywords into 3 categories.

    Per David 2026-06-07: GKP 阶段也能发现负面词 (配件/安装/竞品/对比/平台等),
    不应该只丢入, 应该 AI 提前识别为 negative_keywords, 加为 campaign 否定词。

    Args:
        gkp_keywords: List of keywords from Google Keyword Planner
        brand: Brand name
        product_description: Product description for context

    Returns:
        Dict with 3 lists:
        {
          "brand_keywords": [str, ...],   # L0 保留
          "negative_keywords": [str, ...], # 加为 campaign negatives
          "drop": [str, ...]              # 完全丢弃
        }
    """
    import json
    import subprocess

    # 生成品牌变体
    brand_lower = brand.lower().replace(' ', '')
    brand_variants = [brand, brand_lower]

    keywords_text = "\n".join([f"- {kw}" for kw in gkp_keywords[:50]])  # 2026-06-07 David: 80 词让 AI 超时, 50 词平衡
    # 2026-06-07 David: 不要限制太死, 至少 50 词让 AI 看到完整型号变体

    # 2026-06-07 David: 3 路分类 (brand / negative / drop)
    prompt = f"""从GKP返回的关键词中,提取"有真实用户搜索量"且"与品牌+产品同含义"的品牌关键词。
同时,识别出"有购买意外性"的词为否定关键词。

【背景】这些关键词来自Google Keyword Planner, 代表真实用户搜索。
我们使用品牌型号作为 seed 词查询 GKP, 会返回三类词:
1. **品牌型号相关词** (L0) - 本产品的品牌型号变体, 保留为正向关键词
2. **周边词/相关词** (NEGATIVE) - 配件/安装/使用场景/竞品/平台等, 虽相关但不是购买意图, 应加为否定词
3. **完全无关词** (DROP) - 与本产品无关, 丢弃

【品牌变体】{', '.join(set(brand_variants))}
【产品描述】{product_description}

【GKP返回的关键词】(最多 80 个)
{keywords_text}

【3 路分类任务】

【A. brand_keywords (L0 保留)】从GKP返回中提取"品牌 + 当前产品同义词"组合的关键词。
  - Brand + Standard Product Term
  - Brand + Model Identifier
  - Brand + Spelling Variants (GKP 返回说明用户实际这样搜索)

【B. negative_keywords (负面词, 加为 campaign negatives)】从GKP返回中识别"周边/相关但不是购买意图"的词。
  **重要: 负面词必须从 GKP 返回列表中存在, 不能凭空生成**。
  (这些词 GKP 返回说明有真实用户搜索, 证明他们会点击广告但不是购买意图)
  6 大负面词类别 (严格按语义判断, 不列举具体词):

  【【【重要】产品类别词判定 - 必须先于 B1-B6 判断】】
  2026-06-11 David 投诉: “portable battery charger” / “portable charger” / “battery pack” / “power banks”
  等【本产品类别词】被误判为 ACCESSORY 类 negative。加为 campaign negatives 后
  会【主动误伤 L2 Core 和 L5 LongTail】的同义流量 (这些词本身就是 L2/L5 的目标词)。

  判定规则 (先于 B1-B6):
  - 读 product_description 提取【本产品类别核心词】 (如“power bank” / “portable charger” / “air fryer” / “headphones” / “drill”)
  - 如果 GKP 词是 product_description 描述的产品类别/产品同义词 (即使不带 brand), 仍应 KEEP 进 brand_keywords,
    【绝对不能】进 negative_keywords
  - 只有在 KEEP 之后, 这个词才可能被 L2/L5 当作同义词复用 -- 加为 negative 等于自我矛盾

  通用 examples (抽象占位符, 不硬编码产品):
  - Product = “[portable power bank for phones]” → GKP 返回 “portable charger” / “battery pack” / “power banks” → KEEP (本产品类别同义词)
  - Product = “[cordless drill for home]” → GKP 返回 “electric drill” / “power drill” → KEEP (本产品类别)
  - Product = “[noise canceling headphones]” → GKP 返回 “wireless headphones” / “bluetooth headphones” → KEEP (本产品类别)
  - Product = “[mirrorless camera]” → GKP 返回 “digital camera” / “dslr camera” → KEEP (本产品类别)

  判定失败才进 B1 ACCESSORY (例子别要误判):
  - Product = “[camera with SD card slot]” → GKP 返回 “sd card” → NEGATIVE ACCESSORY (SD card 是配件, 不是相机)
  - Product = “[phone with USB-C port]” → GKP 返回 “usb c cable” → NEGATIVE ACCESSORY (cable 是配件, 不是 phone)
  - 但 Product = “[usb c cable]” → GKP 返回 “usb c charger” → KEEP (本产品类别同义)

  【自我检查 (必走)】在输出 negative_keywords 之前, 再问一次: 列表里有没有本产品类别同义词?
  如果有, 转移到 brand_keywords 或 drop, 【不能进 negative_keywords】。

  【【【重要】L0 范围控制 - 同品牌其他产品线 DROP】】 2026-06-11 David 报告
  之前多次 L0 重复误判: brand 返回的 GKP 词中含同品牌其他产品线/型号变体
  (e.g., "Anker 521" (是氮化镥发电站不是本产品 power bank) / "Anker Powercore" (其他容量系列)
   / "Anker 633 Magnetic Battery" (磁吸电池不是本产品) / "Anker 733" (氮化镥充电器) 等)
  这些词加为 L0 关键词会【主动误伤预算】, 抢跟本产品不同型号/类目的竞标。

  判定规则 (适用于 brand_keywords 列表):
  - 只保留跟 product_description 描述的【本产品】同型号/同容量/同规格的变体
  - 【同品牌但不同产品线/不同型号/不同容量/不同类目】一律 DROP, 不能进 brand_keywords
  - 【DROP 后不进入 negative_keywords】(同品牌其他产品线不等于用户搜索意图负面,
    只是不该作为本产品 L0 关键词)
  - 如果不肯定该词是不是本产品同型号, 保守 KEEP, 报告者后续手动判断

  通用 examples (抽象占位符, 不硬编码品牌/产品):
  - Brand = X, Product = "[X 20000mAh Power Bank]" → GKP 返回 "X 521 portable power station" → DROP (不同产品类目)
  - Brand = X, Product = "[X Power Bank 20000mAh]" → GKP 返回 "X PowerCore" → DROP (同品牌其他容量/系列)
  - Brand = X, Product = "[X Power Bank 20000mAh]" → GKP 返回 "X 633 magnetic battery" → DROP (同品牌磁吸电池, 不同产品线)
  - Brand = X, Product = "[X Power Bank 20000mAh]" → GKP 返回 "X USB C" → DROP (通用词, 不含产品型号变体)
  - Brand = X, Product = "[X 20000mAh]" → GKP 返回 "X power bank 20000" → KEEP (同型号/同容量)
  - Brand = X, Product = "[X 20000mAh]" → GKP 返回 "X portable charger 20000" → KEEP (本产品类别同义 + 容量匹配)
  - Brand = X, Product = "[X TurboBlaze 6qt air fryer]" → GKP 返回 "X 6qt air fryer" → KEEP (同型号变体)
  - Brand = X, Product = "[X TurboBlaze 6qt air fryer]" → GKP 返回 "X 5qt air fryer" → DROP (同品牌不同容量)
  - Brand = X, Product = "[X TurboBlaze 6qt air fryer]" → GKP 返回 "X Air Fryer Max Xl" → DROP (同品牌不同产品线, Max Xl 是另一个型号)

  【自我检查 (必走, 第 2 轮)】输出 brand_keywords 之前再问一次:
  "列表中有没有同品牌但【不同产品线/不同型号/不同容量/不同类目】的词?"
  如果有, 从 brand_keywords 中【移除】(转移到 drop, 不进 negative_keywords)。

  B1. **ACCESSORY (配件)** - 用户想买配件, 不是本产品
    **【严格】只能从 GKP 返回列表中选, 不能凭空生成**
    例: SD card, memory card, charger, mount, case, cable, holder, adapter, battery
    判定原则: 这个词是否在 GKP 返回列表中, 并且描述一个"产品配件"而非产品本身?

  B2. **INSTALLATION (安装/使用)** - 用户想看安装/使用方法, 不是买产品
    **【严格】只能从 GKP 返回列表中选, 不能凭空生成**
    例: installation, install, setup, manual, how to use, instructions, wiring, hardwire
    判定原则: 这个词是否在 GKP 返回列表中, 并且描述"使用/安装"动作而非"购买"意图?

  B3. **COMPETITOR (竞品品牌)** - 其他品牌产品, 会争夺预算
    **【严格】只能从 GKP 返回列表中选, 不能凭空生成**
    例: 同品类其他品牌名 (VIOFO, Garmin, Nextbase, etc.)
    判定原则: 这个词是否在 GKP 返回列表中, 并且是一个"竞品品牌"名?

  B4. **COMPARISON (对比/比较词)** - 看过对比, 不是必买意图
    **【严格】只能从 GKP 返回列表中选, 不能凭空生成**
    例: vs, alternative, alternative to, comparison, review, best, top, ranked
    判定原则: 这个词是否在 GKP 返回列表中, 并且用于"对比/评价"而非"购买"?

  B5. **PLATFORM (平台/购物场景词)** - 跳出购买场景
    **【严格】只能从 GKP 返回列表中选, 不能凭空生成**
    例: amazon basics, walmart, target, ebay, costco, reddit, youtube
    判定原则: 这个词是否在 GKP 返回列表中, 并且代表"另一个购物/信息平台"?

  B6. **USE_CASE (特定使用场景)** - 限定场景下使用
    **【严格】只能从 GKP 返回列表中选, 不能凭空生成**
    例: for car, for truck, for SUV, for motorcycle, with parking mode (单独的特性), rear view mirror version
    判定原则: 这个词是否在 GKP 返回列表中, 并且描述一个"特定使用场景/配置"而非"产品本身"?

  **【重要】如果某个负面词类别在 GKP 返回中不存在, 留空不要填**. 例如: GKP 返回 80 个词中
  没有 'sd card' / 'installation', 这些词由 PRODUCT_SPECIFIC_NEGATIVES 模块负责 (不依赖 GKP).
  你的任务只是从 GKP 返回中识别 negative, 不要在 GKP 之外的领域生成.

【C. drop】其他完全无关词, 丢弃。
  - **Rove Concepts 家具这类"同品牌不同产品线"** 应该 drop (不要加为 L0, 也不要加为 negative)
  - 因为这些词太冷门, 加为 negative 反而误伤其他产品

【严格过滤 - 必须 drop】
- 同品牌其他产品线
- 纯品牌名 (不带产品词)
- 通用购物词 (free shipping, discount, deal)
- 与产品完全无关的词

【返回格式】JSON
{{
  "brand_keywords": ["{brand} [产品词1]", "{brand} [型号变体]", ...],
  "negative_keywords": [
    {{"keyword": "sd card", "category": "ACCESSORY"}},
    {{"keyword": "installation", "category": "INSTALLATION"}}
  ],
  "drop": ["unrelated keyword 1", ...]
}}

只返回 JSON。"""


    try:
        # 2026-06-11 David: 改用 _call_claude_stream (stream-json 避免 pipe 死锁, timeout 真正生效)
        # 原 120s x 2 = 240s
        output = _call_claude_stream(prompt, timeout=240, label="filter_l0_keywords")

        # 解析JSON格式响应
        try:
            inner = output
            # AI 可能在 JSON 后添加解释文本,用正则优先提取 ```json 块
            import re
            code_block = re.search(r'```json\s*(\{.*?\})\s*```', inner, re.DOTALL)
            if code_block:
                json_str = code_block.group(1)
            else:
                # Fallback: 栈找平衡 {...}
                def extract_first_balanced_json(text):
                    start = text.find('{')
                    if start == -1:
                        return None
                    depth = 0
                    in_string = False
                    escape = False
                    for i in range(start, len(text)):
                        c = text[i]
                        if escape:
                            escape = False
                            continue
                        if c == '\\':
                            escape = True
                            continue
                        if c == '"':
                            in_string = not in_string
                            continue
                        if in_string:
                            continue
                        if c == '{':
                            depth += 1
                        elif c == '}':
                            depth -= 1
                            if depth == 0:
                                return text[start:i+1]
                    return None
                json_str = extract_first_balanced_json(inner)
                if not json_str:
                    json_str = inner.replace('```json', '').replace('```', '').strip()
            data = json.loads(json_str)

            # 2026-06-07 David: 3 路分类返回 (brand_keywords + negative_keywords + drop)
            if isinstance(data, dict):
                return {
                    'brand_keywords': data.get('brand_keywords', []),
                    'negative_keywords': data.get('negative_keywords', []),
                    'drop': data.get('drop', [])
                }
            elif isinstance(data, list):
                # Fallback: 老格式, 全部当 L0
                return {'brand_keywords': data, 'negative_keywords': [], 'drop': []}
        except Exception as e:
            logger.warning(f"JSON parse failed: {e}")

        # Fallback: 旧的解析逻辑
        response = result.stdout.strip()
        # Parse JSON from response - handle both {"keywords": [...]} and [...]
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]

        try:
            data = json.loads(response)
            if isinstance(data, dict):
                return data.get('keywords', [])
            elif isinstance(data, list):
                return data
        except:
            pass
    except Exception as e:
        logger.warning(f"AI filter failed: {e}")

    # 2026-06-07 修复: fallback 返回空 dict (不是 list), 避免 caller AttributeError
    return {'brand_keywords': [], 'negative_keywords': [], 'drop': []}


def _generate_l0_from_description(brand: str, product_description: str) -> list:
    """Generate L0 keywords from product description using AI."""
    import json
    import subprocess

    prompt = f"""Generate L0 (Brand + THIS Product) keywords for Google Ads.

Brand: {brand}
Product Description: {product_description}

TASK: Generate 15-20 keywords that combine the brand with THIS SPECIFIC product.

CORE PRINCIPLE: Use semantic understanding to identify what THIS product is.
- Read the product description carefully
- Identify the product's key characteristics: name, model, technology, use case, features
- Generate keywords that match THESE characteristics

STEP 1: Identify the product's MODEL NAME from the description first.
- A model name typically CONTAINS NUMBERS + LETTERS (e.g., 'R2-4K', 'R2 4K', 'X431 PROS V', 'P500')
- The model name is a SPECIFIC identifier that distinguishes THIS product from OTHER products
- Do NOT confuse the model with general features like '4K' (resolution) or '128GB' (storage) or '5G' (WiFi)
- Do NOT confuse the model with the product category (e.g., 'Dash Cam' is category, 'R2-4K DUAL' is model)
- Examples of MODEL extraction (abstract, not specific to your product):
  - If description is '[Brand] [Model] [Category] [Features]', the model is the [Model] part
  - If description has '[Brand] [Category] Model [Number]', the model is [Number]

STEP 2: Include ALL four types. Per David 2026-06-07, do NOT hard-limit the count of any type.
  The number of keywords should be **data-driven** (how many real spelling variants exist), not prompt-limited.
  If a model has 15+ valid spelling variants, generate all 15. If it has 3, that's fine.
  GKP search volume will validate which are worth keeping.

【Type 1: Brand + Product Model Combinations (HIGHEST PRIORITY)】
- Brand + Model (e.g., "[Brand] R2-4K", "[Brand] R2 4K", "[Brand] R2")
- Model + Category Word (e.g., "R2-4K dash cam", "R2 4K car camera")
- Model alone variations: "R2-4K", "R2 4K", "R2 4k"
- Per David 2026-06-07: These model keywords are HIGH-VALUE because users searching for the model
  know exactly what they want - high intent, high conversion. Generate ALL valid model combinations,
  not limited by a hard count.

【Type 2: Brand + Product Type Combinations】
- Brand + Product Type (the product category from description)
- Brand + Feature (a key feature mentioned in description)
- Brand + Use Case (the use case implied by description)
- Brand + Attribute (a key attribute mentioned in description)

【Type 3: Brand + Product Model Spelling Variants】
- Spacing/hyphen variations: "R2-4K" -> "R2 4K", "R24K", "R-2-4K"
- Number form: "R2 4K" -> "R2 4k" (lowercase k)
- Model + extra word: "R2-4K DUAL", "R2 4K Dual", "R2-4K dash cam"
- Word order: "Dash Cam R2-4K" vs "R2-4K Dash Cam"

【Type 4: Other Misspellings】
- Common misspellings of brand: [brand] -> misspelled variants
- Word order variations
- Spacing/hyphen variations

STRICT RULES (use semantic understanding - do NOT list specific product names):
1. ALL keywords must be brand + THIS specific product combination
2. Use semantic understanding to identify DIFFERENT products from the same brand:
   - The key is: would a user searching for THIS keyword want to buy THIS product?
   - Different products have different features, technology, use case, design
   - Skip any keyword that would match a different product from the same brand
   - Example reasoning: if this product uses one specific technology, skip keywords about products using a different technology
3. NO pure brand alone (must combine with a product word)
4. NO ASIN
5. NO competitor product names
6. NO generic shopping terms
7. Include ALL 4 types above (especially model combinations in Type 1)
8. Aim for 15-25 keywords total (not a hard limit; if model has many valid variants, expand the list)
9. **Type 1 (Model combinations) is the highest priority - generate as many valid variants as exist, not limited by a hard count**

Return ONLY JSON array: ["Keyword 1", "Keyword 2", ...]"""

    try:
        # 2026-06-11 David: 改用 _call_claude_stream (stream-json 避免 pipe 死锁, timeout 真正生效)
        # 原 120s x 2 = 240s
        output = _call_claude_stream(prompt, timeout=240, label="generate_l0_keywords")

        # 解析JSON格式响应
        try:
            inner = output
            # 移除markdown code blocks
            inner_clean = inner.replace('```json', '').replace('```', '').strip()
            if '[' in inner_clean:
                start = inner_clean.find('[')
                end = inner_clean.rfind(']') + 1
                data = json.loads(inner_clean[start:end])
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.warning(f"AI generation failed: {e}")
            return []
    except Exception as e:
        logger.warning(f"AI generation failed: {e}")

    return []


def is_l0_keyword(keyword_text: str, brand: str, product_model: str = '', product_name: str = '') -> bool:
    """Check if keyword is a L0 (Brand_Model) keyword using AI语义分析.

    Args:
        keyword_text: Keyword to check
        brand: Brand name
        product_model: Product model
        product_name: Full product name

    Returns:
        True if matches L0 pattern
    """
    text_lower = keyword_text.lower()
    brand_lower = brand.lower() if brand else ""

    # Must contain brand
    if brand_lower and brand_lower not in text_lower:
        return False

    # Check product model (with default)
    if product_model and product_model:
        model_lower = product_model.lower()
        if model_lower in text_lower:
            return True

    # Check product name components (with default)
    if product_name and product_name:
        words = product_name.split()
        for word in words:
            word_clean = word.lower().strip()
            if len(word_clean) > 2 and word_clean != brand_lower:
                if word_clean in text_lower:
                    return True

    return False

def validate_params(args) -> tuple:
    """Validate all parameters before execution."""
    if not args.campaign_id:
        return False, "Campaign ID is required (--campaign-id)"

    if not args.customer_id:
        return False, "Customer ID is required (--customer-id)"

    # Product description is REQUIRED for accurate brand keywords
    if not args.product_description or len(args.product_description.strip()) < 10:
        return False, "Product description is required (--product-description). Please provide a product description for accurate brand keyword generation."

    if args.price and (args.price <= 0 or args.price > 10000):
        return False, f"Price must be between 0 and 10000 (got {args.price})"

    if args.commission_rate is not None:
        if args.commission_rate <= 0 or args.commission_rate > 1:
            return False, f"Commission rate must be between 0 and 1 (got {args.commission_rate})"

    return True, ""


def get_campaign_info(customer_id, campaign_id, args=None):
    """Get campaign info including existing ad content."""
    from src.refined_bid_optimizer import RefinedBidOptimizer, AdContent

    optimizer = RefinedBidOptimizer()

    # Extract existing ad content
    ad_content = optimizer.extract_existing_ad_content(customer_id, campaign_id)

    # If no Main ad group, fail with clear error - do NOT use hardcoded fallback
    if not ad_content:
        error_msg = (
            "No Main ad group found in campaign %s. "
            "Cannot create ad content with hardcoded fallback. "
            "Please provide --product-url, --product-name, --product-description, --brand "
            "to generate AI-based ad content."
            % campaign_id
        )
        logger.error(error_msg)
        return None, error_msg

    if not ad_content:
        return None, "Could not extract ad content from Main ad group"

    return ad_content, None


def create_layered_ads(customer_id, campaign_id, ad_content,
                        brand=None, price=None,
                        commission_rate=None, max_cpc=None, product_url=None,
                        product_description=None,
                        l0_keywords_user=None, l1_keywords_user=None,
                        simplified_l0=False):
    """Create layered ad groups using existing ad content.

    Args:
        product_description: Product description (REQUIRED for accurate keywords)
        l0_keywords_user: User-provided L0 keywords (overrides AI-generated L0).
                          Useful for precise brand+model targeting.
        l1_keywords_user: User-provided L1 keywords (overrides L0-top-10 reuse).
                          Useful for precise brand-only targeting.
        simplified_l0: If True, use 1 L0 ad group @ max_cpc (instead of 5 L0_3-7 testing groups).
                       Required for low max_cpc products (< \$3) where 5 L0_3-7 are duplicate.
    """
    optimizer = RefinedBidOptimizer()

    # Use provided brand (from --brand parameter), OR extract from product_description using AI
    # DON'T use ad_content.brand (which is extracted from old ad素材, often wrong)

    # If user provided --brand, use it
    if brand and brand.strip():
        effective_brand = brand.strip()
    # Otherwise, use AI to extract brand from product_description
    elif product_description:
        import subprocess, json
        prompt = f"""Extract the brand name from this product description.

Product: {product_description}

Return ONLY the brand name as JSON: {{"brand": "BrandName"}}"""
        try:
            # 2026-06-11 David: 改用 _call_claude_stream (stream-json 避免 pipe 死锁, timeout 真正生效)
            # 原 30s x 2 = 60s
            output = _call_claude_stream(prompt, timeout=60, label="extract_brand")
            if '{"brand":' in output:
                data = json.loads(output)
                effective_brand = data.get('brand', 'Product').strip()
        except:
            effective_brand = 'Product'
    else:
        effective_brand = 'Product'

    effective_url = product_url or ad_content.final_url

    # ===== CRITICAL: Parse suffix from product_url =====
    # Extract ?后的追踪参数作为final_url_suffix
    effective_suffix = ''
    base_url = effective_url

    if product_url and '?' in product_url:
        # 分割URL,取?后部分
        url_parts = product_url.split('?')
        base_url = url_parts[0]  # 不带参数的base URL
        query = url_parts[1] if len(url_parts) > 1 else ''
        # 解析参数
        from urllib.parse import parse_qs, quote
        params = parse_qs(query)
        suffix_parts = []
        for key, vals in params.items():
            for v in vals:
                # URL编码值
                encoded_val = quote(v, safe='')
                suffix_parts.append(f"{key}={encoded_val}")
        effective_suffix = '&'.join(suffix_parts)

    # 如果没有从product_url解析到suffix,使用ad_content中已有的
    if not effective_suffix and ad_content.url_suffix:
        effective_suffix = ad_content.url_suffix
        logger.info(f"Using existing suffix from ad_content")

    # 更新ad_content的suffix和final_url
    if effective_suffix:
        ad_content.url_suffix = effective_suffix
        ad_content.final_url = base_url
        logger.info(f"Set suffix: {effective_suffix[:50]}...")
    else:
        logger.warning("WARNING: No suffix found!")

    # Calculate max_cpc if not provided
    if price and commission_rate and not max_cpc:
        max_cpc = optimizer.calculate_max_cpc(price, commission_rate)
    elif max_cpc:
        logger.info(f"Using user-specified max_cpc: ${max_cpc:.2f} (David 2026-06-11: brand words 竞价高, 不适用公式)")
    else:
        max_cpc = 1.0  # Default
        logger.warning("No price/commission/max_cpc provided, using default CPC")

    # Generate keywords with better brand/core_terms from AI
    logger.info(f"Generating keywords with brand={effective_brand}, core_terms={ad_content.core_product_terms}")

    # ===== USE PRODUCT DESCRIPTION FOR ACCURATE KEYWORDS =====
    # If product_description provided, use it for better L0/L1 keyword generation
    product_desc_for_keywords = product_description or ""

    try:
        result = optimizer.generate_from_product_info(
            product_name=effective_brand,
            brand=effective_brand,
            price=price or 99.99,
           commission_rate=commission_rate or 0.05,
            url=effective_url or "https://www.amazon.com",
            customer_id=customer_id,
            country='US',
            product_description=product_description,  # FIX: Enable AI semantic classification (not just 50% word match)
            core_terms=ad_content.core_product_terms if ad_content and ad_content.core_product_terms else None  # FIX: Use AI-extracted core terms
        )

        # Override brand/core_terms with AI-extracted values
        if ad_content.brand:
            result['brand'] = ad_content.brand
        if ad_content.core_product_terms:
            result['core_product_terms'] = ad_content.core_product_terms

        # If product_description provided, use it for L0 keywords
        if product_desc_for_keywords and len(product_desc_for_keywords) > 10:
            logger.info(f"Using product description for L0 keywords: {product_desc_for_keywords[:50]}...")
            # 确保在此处定义product_model
            pm_for_l0 = None
            pu_for_l0 = None
            if ad_content and ad_content.final_url:
                import re
                match = re.search(r'amazon\.com/dp/([A-Z0-9]{10})', ad_content.final_url)
                if match:
                    pm_for_l0 = match.group(1)
                pu_for_l0 = ad_content.final_url

            l0_from_desc, neg_from_desc = generate_l0_keywords(
                brand=effective_brand,
                product_description=product_desc_for_keywords,
                product_model=pm_for_l0,
                product_url=pu_for_l0,
                customer_id=customer_id,
                user_seed=l0_keywords_user
            )
            if l0_from_desc:
                result['L0_keywords'] = l0_from_desc
                logger.info(f"Generated {len(l0_from_desc)} L0 keywords from product description")
                if neg_from_desc:
                    result.setdefault('gkp_negatives', []).extend(neg_from_desc)
                    logger.info(f"  + {len(neg_from_desc)} GKP negative candidates")

        logger.info(f"Generated keywords for layers: {list(result.get('layers', {}).keys())}")

        # ===== ADD L0 KEYWORDS FOR BRAND MODEL TESTING =====
        # Generate brand + product combination keywords for L0 multi-bid testing
        # Use Google Keyword Planner + AI semantics (FIXED)

        # Use proper product_description instead of brand name
        # product_desc_for_keywords was already set above
        product_for_l0 = product_desc_for_keywords or effective_brand
        # 确保在此处定义product_model
        pm_for_l0 = None
        pu_for_l0 = None

        if ad_content:
            # Extract ASIN from final_url as product_model
            final_url = ad_content.final_url or ''
            if 'amazon.com/dp/' in final_url:
                # Extract ASIN: amazon.com/dp/B0XXXXXX
                import re
                match = re.search(r'amazon\.com/dp/([A-Z0-9]{10})', final_url)
                if match:
                    pm_for_l0 = match.group(1)
            pu_for_l0 = final_url

        l0_keywords, neg_keywords = generate_l0_keywords(
            brand=effective_brand,
            product_description=product_for_l0,
            product_model=pm_for_l0,
            product_url=pu_for_l0,
            customer_id=customer_id,
            user_seed=l0_keywords_user
        )
        result['L0_keywords'] = l0_keywords
        logger.info(f"Generated {len(l0_keywords)} L0 keywords for Brand_Model testing")
        if neg_keywords:
            result.setdefault('gkp_negatives', []).extend(neg_keywords)
            logger.info(f"  + {len(neg_keywords)} GKP negative candidates from L0 generation")

        # 2026-06-11 David: User-provided L0 keywords MERGE (不是 override)
        # 需求: 用户词全收 + GKP 扩展 + AI 提取合并去重
        if l0_keywords_user:
            user_set = set([k.lower().strip() for k in l0_keywords_user if k and k.strip()])
            ai_kws = result.get('L0_keywords', []) or []
            # 用户词优先 (保留原始大小写/拼写), AI 词去重后追加
            new_ai = [k for k in ai_kws if k and k.lower().strip() not in user_set]
            merged = list(l0_keywords_user) + new_ai
            result['L0_keywords'] = merged
            logger.info(f"  MERGE: User-provided {len(l0_keywords_user)} + AI-extracted {len(new_ai)} (skipped {len(ai_kws)-len(new_ai)} dups) = {len(merged)} L0 keywords")
        else:
            logger.info(f"  No user L0 keywords; using {len(result.get('L0_keywords', []))} AI-generated only")

        # 2026-06-07 David: L1 可以和 L0 关键词一样, 因为都是品牌词广告组
        # L1 是 baseline ($2.4), L0_3-7 是 CPC 测试组 ($3-7)
        # 强制 L1 复用 L0 的 brand+model 组合词, 避免被 _reclassify_keywords_with_better_info 分到 L2
        if l0_keywords or l0_keywords_user:
            l1_source = l1_keywords_user if l1_keywords_user else (l0_keywords or l0_keywords_user)[:10]
            l1_ad_group_name = f"{effective_brand}_Brand"
            l1_bid = min(max_cpc * 0.5, 2.0)  # L1 = 50% max_cpc, cap $2
            # 用 L0 关键词的纯 brand + model 变体 (保留前 10)
            l1_kw_data = [
                {
                    'text': kw,
                    'match_type': 'PHRASE',
                    'bid': l1_bid,
                    'layer': 'L1'
                }
                for kw in l1_source[:10]
            ]
            if 'layers' not in result:
                result['layers'] = {}
            result['layers']['L1'] = {
                'name': l1_ad_group_name,
                'bid': l1_bid,
                'keywords': l1_kw_data
            }
            src_label = "User-provided" if l1_keywords_user else "L0-reuse"
            logger.info(
                f"L1 ad group '{l1_ad_group_name}' will use {len(l1_kw_data)} keywords ({src_label}, David 2026-06-07 指示)"
            )

        # Create ad groups with ads
        # Pass product_description to enable GKP-based negative keywords
        # 2026-06-08 David: simplified_l0 mode (1 ad group @ max_cpc vs 5 L0_3-7 testing groups)
        created = optimizer.create_ad_groups(
            customer_id=customer_id,
            campaign_id=campaign_id,
            result=result,
            include_ads=True,
            ad_content=ad_content,
            product_description=product_description,
            simplified_l0=simplified_l0,
            price=price,
            commission_rate=commission_rate,
            max_cpc=max_cpc
        )

        # 2026-06-07 David: GKP 阶段 AI 识别的负面词, 添加为 campaign negatives
        # 例: ROVE R2-4K 查 GKP 会返回 "sd card" / "memory card" / "installation" 等
        # 这些词虽相关但不是购买意图, 应加为否定词
        # 2026-06-07 23:35: 同时用 negative_keyword_generator.merge_with_l0_negatives() 归类
        gkp_negatives = result.get('gkp_negatives', [])
        if gkp_negatives and campaign_id:
            try:
                from src.negative_keyword_generator import NegativeKeywordGenerator
                gen = NegativeKeywordGenerator()
                # 1) 用 negative_keyword_generator 归类 L0 negatives -> CategorizedNegative
                categorized = gen.merge_with_l0_negatives(
                    l0_negatives=gkp_negatives,
                    product_description=product_description,
                    brand=effective_brand
                )
                logger.info(f"✓ merge_with_l0_negatives: {len(gkp_negatives)} L0 negatives -> {len(categorized)} CategorizedNegative")
                # 2) 用 categorized API 添加到 campaign (按 category 可选不同 match type)
                if categorized:
                    added = optimizer.client.create_negative_keywords_categorized(
                        campaign_id=campaign_id,
                        categorized_negatives=categorized,
                        customer_id=customer_id
                    )
                    logger.info(f"✓ Added {len(categorized)} categorized negative keywords to campaign {campaign_id}")
                    logger.info(f"  Samples: {[(n.keyword, n.category) for n in categorized[:5]]}")
            except Exception as e:
                logger.warning(f"Failed to add GKP negative keywords: {e}")

        return created, None

    except AIRetryExhausted as e:
        # 2026-06-11 David: 连续 AI 失败 (fail-fast), 透出异常 (不静默吞)
        logger.error(f"❌ AIRetryExhausted: {e}")
        # 飞书报错
        try:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Traceback:\n{tb}")
        except:
            pass
        raise
    except Exception as e:
        logger.error(f"Failed to create layered ads: {e}")
        return None, str(e)


# ============================================================
# Ad Content Expansion Functions
# ============================================================

def expand_headlines(headlines: list, target: int = 15, brand: str = "") -> list:
    """Expand headlines to target count using templates."""
    if len(headlines) >= target:
        return headlines[:target]

    # Template headlines (brand-agnostic, policy-safe)
    templates = [
        "Premium Quality",
        "Best Seller",
        "Free Shipping",
        "Fast Delivery",
        "Satisfaction Guaranteed",
        "New Arrival",
        "Top Rated",
        "Official Store",
        "Limited Stock",
        "Order Now"
    ]

    # Add brand if available
    if brand:
        brand_templates = [
            f"Shop {brand}",
            f"Buy {brand}",
            f"{brand} Official",
            f"{brand} Reviews",
            f"Best {brand}",
            f"{brand} Deals"
        ]
        templates = brand_templates + templates

    # Combine and deduplicate
    expanded = list(headlines)
    for t in templates:
        if len(expanded) >= target:
            break
        if t not in expanded:
            expanded.append(t)

    return expanded[:target]


def expand_descriptions(descriptions: list, target: int = 4) -> list:
    """Expand descriptions to target count."""
    if len(descriptions) >= target:
        return descriptions[:target]

    templates = [
        "Premium quality product. Order now and enjoy fast shipping.",
        "Trusted by thousands of customers. 30-day return policy.",
        "Best value for money. Limited stock available.",
        "Professional grade product. Contact us for questions."
    ]

    expanded = list(descriptions)
    for t in templates:
        if len(expanded) >= target:
            break
        if t not in expanded:
            expanded.append(t)

    return expanded[:target]


def expand_sitelinks(sitelinks: list, target: int = 6) -> list:
    """Expand sitelinks to target count. Returns SitelinkInfo objects.

    NOTE: Only sitelinks with valid asset_id can be copied to ad groups.
    New template sitelinks (empty asset_id) need to be created separately.
    """
    # Filter out empty asset_ids first - keep only valid sitelinks with asset_id
    valid = [sl for sl in sitelinks if (hasattr(sl, 'asset_id') and sl.asset_id)]
    if not valid:
        # Try to get asset_id from dict
        valid = [sl for sl in sitelinks if isinstance(sl, dict) and sl.get('asset_id')]
        if valid:
            valid = [SitelinkInfo(
                asset_id=v['asset_id'],
                link_text=v.get('link_text', ''),
                description1=v.get('description1', ''),
                description2=v.get('description2', '')
            ) for v in valid]

    if len(valid) >= target:
        return valid[:target]

    # For templates, create with placeholder that we'll handle specially
    templates = [
        {"link_text": "Shop Now", "description1": "Browse collection", "description2": "Free shipping $50+"},
        {"link_text": "Reviews", "description1": "Customer reviews", "description2": "4.5+ stars"},
        {"link_text": "Specs", "description1": "Product details", "description2": "Full specifications"},
        {"link_text": "Support", "description1": "Contact us 24/7", "description2": "We're here to help"},
        {"link_text": "Shipping", "description1": "Fast delivery", "description2": "Free over $50"},
        {"link_text": "Returns", "description1": "Easy returns", "description2": "30-day policy"}
    ]

    for s in templates:
        if len(valid) >= target:
            break
        valid.append(SitelinkInfo(
            asset_id='',  # Empty - will be skipped in copy
            link_text=s['link_text'],
            description1=s['description1'],
            description2=s['description2']
        ))

    return valid[:target]


def ensure_ad_content_quantity(ad_content, brand: str = "") -> None:
    """Ensure ad_content has enough headlines/descriptions/sitelinks.

    Modifies ad_content in-place to meet Google Ads requirements:
    - 15 headlines
    - 4 descriptions
    - 6 sitelinks
    """
    # Expand headlines to 15
    ad_content.headlines = expand_headlines(ad_content.headlines, 15, brand)

    # Expand descriptions to 4
    ad_content.descriptions = expand_descriptions(ad_content.descriptions, 4)

    # Expand sitelinks to 6
    ad_content.sitelinks = expand_sitelinks(ad_content.sitelinks, 6)

    logger.info(f"Expanded: {len(ad_content.headlines)} headlines, "
                f"{len(ad_content.descriptions)} descriptions, "
                f"{len(ad_content.sitelinks)} sitelinks")


# ============================================================
# Main Function
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Refined Ads Skill - Create Layered Ad Groups',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required parameters
    parser.add_argument('--campaign-id', required=True, help='Target campaign ID')
    parser.add_argument('--customer-id', required=True, help='Google Ads customer ID')
    parser.add_argument('--product-description', required=True,
                        help='Product description (required for accurate brand keywords)')

    # Optional parameters for better keyword generation
    parser.add_argument('--brand', help='Brand name (will be extracted from ads if not provided)')
    parser.add_argument('--product-url', help='Product URL for keyword research')
    parser.add_argument('--price', type=float, help='Product price in USD')
    parser.add_argument('--commission-rate', type=float, dest='commission_rate', help='Commission rate')
    parser.add_argument('--country', default='US',
                        help='Target country (ISO 2-letter, default: US). 例: US/GB/DE/JP/AU/CA/FR 等')
    parser.add_argument('--language', default='EN',
                        help='Target language (ISO code, default: EN). 例: EN/DE/FR/JA/ES/IT/ZH 等')
    parser.add_argument('--start-date', default=None,
                        help='Campaign start date (YYYY-MM-DD, 或 IMMEDIATE). 默认: IMMEDIATE')
    parser.add_argument('--end-date', default=None,
                        help='Campaign end date (YYYY-MM-DD). 默认: 无结束')

    # 2026-06-08 David: 精确控制 L0/L1 关键词 + 简化 L0 模式
    parser.add_argument('--l0-keywords', dest='l0_keywords', default=None,
                        help='Comma-separated L0 (brand_model) keywords. When provided, these '
                             'OVERRIDE AI-generated L0 keywords. Use for precise brand+model targeting. '
                             'Example: --l0-keywords "INTEX 28272EH,28272EH Pool"')
    parser.add_argument('--l1-keywords', dest='l1_keywords', default=None,
                        help='Comma-separated L1 (brand) keywords. When provided, these OVERRIDE the '
                             'default L1 keyword reuse of L0 top 10. Use for precise brand-only targeting '
                             '(without model). Example: --l1-keywords "INTEX Above Ground Pool"')
    parser.add_argument('--simplified-l0', dest='simplified_l0', action='store_true',
                        help='Use simplified L0 (1 ad group @ max_cpc) instead of 5 L0_3-7 testing groups. '
                             'Required when max_cpc < \$3 (e.g. low-price products) to avoid 5 duplicate ad groups. '
                             'Bid = min(max_cpc, \$7 cap). Ad group name: {Brand}_Brand_Model_Strict.')
    parser.add_argument('--max-cpc', dest='max_cpc', type=float, default=None,
                        help='2026-06-11 David: 直接指定 max_cpc (跳过 price*commission 公式)。'
                             'Brand word 竞价本来就很高, 不适用那个公式。'
                             'Example: --max-cpc 5.0')
    parser.add_argument('--use-one-shot', dest='use_one_shot', action='store_true',
                        help='【2026-06-15 拍板】使用 one-shot 分类 (V3 路径) 替代默认 _ai_filter_l0_keywords。'
                             'L0 起点: --l0-keywords + --product-model + 品牌名.'
                             'L1 起点: 品牌名 + 同产品线变体.'
                             '默认: opt-in 不启用, 保持 _ai_filter_l0_keywords().')
    parser.add_argument('--from-campaign-history', dest='from_campaign_history', action='store_true',
                        help='【2026-06-30 P0】从 Campaign 历史搜索词拉取竞品分析, 复用为否定词。'
                             '仅在 --campaign-id 路径 (补充分层) 生效, 新建路径不暴露。'
                             '调用 BrandCompetitionAnalyzer.analyze_from_campaign_history()。')

    args = parser.parse_args()

    # Validate parameters
    is_valid, error_msg = validate_params(args)
    if not is_valid:
        logger.error(f"Validation failed: {error_msg}")
        print(f"ERROR: {error_msg}")
        sys.exit(1)

    print("="*70)
    print("🔧 Refined Ads Skill - Creating Layered Ad Groups")
    print("="*70)
    print(f"\n📋 Campaign ID: {args.campaign_id}")
    print(f"📋 Customer ID: {args.customer_id}")
    if args.brand:
        print(f"📋 Brand: {args.brand}")
    if args.price:
        print(f"📋 Price: ${args.price}")

    # Step 1: Get existing ad content from Main ad group
    print("\n⏳ Step 1: Extracting ad content from Main ad group...")
    ad_content, error = get_campaign_info(args.customer_id, args.campaign_id, args)

    if error:
        print(f"\n❌ FAILED: {error}")
        sys.exit(1)

    print(f"   ✅ Extracted {len(ad_content.headlines)} headlines")
    print(f"   ✅ Extracted {len(ad_content.descriptions)} descriptions")
    print(f"   ✅ Extracted {len(ad_content.sitelinks)} sitelinks")
    if ad_content.brand:
        print(f"   ✅ AI identified brand: {ad_content.brand}")
    if ad_content.core_product_terms:
        print(f"   ✅ AI extracted core terms: {ad_content.core_product_terms}")
    if ad_content.url_suffix:
        print(f"   ✅ URL suffix present")

    # ===== EXPAND AD CONTENT TO MEET REQUIREMENTS =====
    # Ensure we have 15 headlines, 4 descriptions, 6 sitelinks
    effective_brand = args.brand or ad_content.brand or ""

    # ===== CHECK BLACKLIST =====
    if effective_brand and check_brand_blacklist(effective_brand):
        print(f"   ⚠️ Brand '{effective_brand}' is in blacklist! Confirm to proceed anyway?")

    ensure_ad_content_quantity(ad_content, effective_brand)

    print(f"   ✅ Expanded to {len(ad_content.headlines)} headlines, "
          f"{len(ad_content.descriptions)} descriptions, "
          f"{len(ad_content.sitelinks)} sitelinks")

    time.sleep(1)

    # Step 2: Create layered ad groups
    print("\n⏳ Step 2: Creating layered ad groups...")

    # 2026-06-08 David: 解析 user-provided L0/L1 keywords (精确控制模式)
    l0_keywords_user = None
    if args.l0_keywords:
        l0_keywords_user = [s.strip() for s in args.l0_keywords.split(',') if s.strip()]
        logger.info(f"User-provided L0 keywords ({len(l0_keywords_user)}): {l0_keywords_user[:5]}...")
        print(f"📋 User-provided L0 keywords: {len(l0_keywords_user)}")

    l1_keywords_user = None
    if args.l1_keywords:
        l1_keywords_user = [s.strip() for s in args.l1_keywords.split(',') if s.strip()]
        logger.info(f"User-provided L1 keywords ({len(l1_keywords_user)}): {l1_keywords_user[:5]}...")
        print(f"📋 User-provided L1 keywords: {len(l1_keywords_user)}")

    if args.simplified_l0:
        print(f"📋 Simplified L0 mode: 1 ad group @ max_cpc (cap \$7)")
    else:
        print(f"📋 Standard L0 mode: 5 L0_3-7 testing groups (\$3/\$4/\$5/\$6/\$7)")

    # 2026-06-30: P0 - --from-campaign-history 竞品分析
    if args.from_campaign_history and args.brand and args.product_description:
        try:
            from src.brand_competition_analyzer import BrandCompetitionAnalyzer
            analyzer = BrandCompetitionAnalyzer()
            comp_result = analyzer.analyze(
                brand=args.brand,
                product_description=args.product_description,
            )
            print(f"\n📊 Brand Competition Analysis:")
            print(f"  Competitors ({len(comp_result.competitor_brands)}): {comp_result.competitor_brands}")
            print(f"  Same-brand lines: {comp_result.same_brand_product_lines}")
            print(f"  Source: {comp_result.source}")
            print(f"  Confidence: {comp_result.confidence:.2f}")
            
            # 可选: 自动添加竞品否定词
            if comp_result.competitor_brands:
                negatives = comp_result.to_phrase_negatives()
                print(f"\n💡 Suggestion: Add these as PHRASE negatives: {negatives[:5]}...")
                print(f"   Run: python3 scripts/search_term_negatives.py --campaign-id {args.campaign_id} --add \"{','.join(negatives)}\"")
                
        except Exception as e:
            logger.warning(f"Brand competition analysis failed: {e}")
    
    created, error = create_layered_ads(
        customer_id=args.customer_id,
        campaign_id=args.campaign_id,
        ad_content=ad_content,
        brand=args.brand,
        price=args.price,
        commission_rate=args.commission_rate,
        max_cpc=args.max_cpc,
        product_url=args.product_url,
        product_description=args.product_description,
        l0_keywords_user=l0_keywords_user,
        l1_keywords_user=l1_keywords_user,
        simplified_l0=args.simplified_l0
    )

    if error:
        print(f"\n❌ FAILED: {error}")
        sys.exit(1)

    # Print results
    print("\n" + "="*70)
    print("✅ SUCCESS: Layered Ad Groups Created")
    print("="*70)

    total_layers = 0
    total_keywords = 0
    total_sitelinks = 0

    for layer, data in created.items():
        if isinstance(data, dict) and 'ad_group_id' in data:
            total_layers += 1
            total_keywords += data.get('keywords_added', 0)
            total_sitelinks += data.get('sitelinks_added', 0)
            status = '✅' if data.get('ad_group_id') else '❌'
            print(f"\n  {status} {layer}: {data.get('name', 'N/A')}")
            print(f"     AdGroup ID: {data.get('ad_group_id', 'N/A')}")
            print(f"     Keywords: {data.get('keywords_added', 0)}")
            print(f"     Ads: {'✅' if data.get('ads_created') else '❌'}")
            print(f"     Sitelinks: {data.get('sitelinks_added', 0)}")

    print(f"\n📊 Summary:")
    print(f"   Total Layers Created: {total_layers}")
    print(f"   Total Keywords: {total_keywords}")
    print(f"   Total Sitelinks: {total_sitelinks}")
    print("\n" + "="*70)


if __name__ == '__main__':
    main()