#!/usr/bin/env python3
"""
Keyword Planner Skill - 获取美国地区关键词搜索量和CPC数据

功能1：商品描述 → AI提取关键词 → API生成相关词 + 数据
功能2：直接关键词 → API生成相关词 + 数据

功能增强（2026-06-04）：
- 429错误自动等待重试
- 调用间隔控制（避免触发限流）
- gotrends.app fallback API

作者：小灰
日期：2026-06-03
"""

import argparse
import json
import sys
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add autoads to path
sys.path.insert(0, '/root/.openclaw/workspace/autoads/src')

# 配置
DEFAULT_COUNTRY = "US"
DEFAULT_LANGUAGE = "en"

# 添加时间范围参数 默认最近3个月
DEFAULT_MONTHS = 3

# === Rate Limit 控制配置 ===
API_CALL_INTERVAL = 2.0  # 每次API调用间隔（秒），避免触发429
MAX_RETRIES = 3       # 最大重试次数
RETRY_WAIT = 60       # 429后等待秒数

# === gotrends.app Fallback API 配置 ===
GOTRENDS_API_URL = 'https://insitto.gotrends.app/kw/gethistorymetric'
GOTRENDS_COUNTRY_MAP = {
    'US': '2840',
    'GB': '2826',
    'CA': '2286',
    'AU': '2276',
}


# AI提取函数
# AI提取品牌/产品关键词的Prompt模板
AI_EXTRACT_PROMPT = """\
你是一个专业的亚马逊产品关键词分析师。你的任务是从商品描述中提取用于Google Ads广告投放的关键词。

## 提取规则
从商品描述中提取：
1. 品牌词 + 产品类型（如 "KODAK speaker"）
2. 品牌词 + 型号（如 "KODAK LUMA350"）
3. 产品类型词（如 "bluetooth speaker"）
4. 产品特性词（如 "waterproof"）

## 输出格式
JSON数组：[关键词1, 关键词2, ...]
不要其他文字。
"""


def extract_keywords_local(description: str) -> List[str]:
    """本地规则提取品牌+产品关键词 - 不依赖外部API"""
    
    keywords = []
    text = description.strip()
    
    # 步骤1：识别品牌
    # 1.1 大写字母开头的词（如Betta）
    words = re.findall(r'\b([A-Z][a-zA-Z]{2,15})\b', text)
    # 1.2 全大写的品牌（如MERACH，4个及以上字母）
    words_upper = re.findall(r'\b([A-Z]{4,15})\b', text)
    words.extend(words_upper)
    
    brand_candidates = []
    excluded_brands = {'The', 'With', 'And', 'For', 'From', 'Best', 'Top', 'New', 'Pro', 'Plus', 'SE', 'Dual', 'Twin', 'LED', 'USB', 'HDMI', 'WiFi', 'GPS', 'TV', 'DIY', 'Real', 'Time', 'Home', 'Women', 'Men'}
    for w in words:
        if w not in excluded_brands and len(w) >= 2:
            brand_candidates.append(w)
    
    # 去重保持顺序
    brand_candidates = list(dict.fromkeys(brand_candidates))
    
    # 步骤2：识别产品类型词（扩展列表）
    product_types = [
        # 电子类
        'speaker', 'headphone', 'earphone', 'earbud', 'charger', 'cable',
        'case', 'cover', 'mount', 'stand', 'holder', 'keyboard', 'mouse',
        'monitor', 'webcam', 'camera', 'light', 'lamp', 'bulb', 'plug',
        'outlet', 'switch', 'sensor', 'lock', 'doorbell', 'watch', 'band',
        'tracker', 'fitness', 'pod', 'drone', 'controller', 'gamepad',
        'soundbar', 'subwoofer', 'mic', 'microphone', 'projector',
        'adapter', 'hub', 'drive', 'storage',
        # Pool相关
        'pool skimmer', 'pool cleaner', 'pool robot', 'solar charger', 'solar panel',
        'robot', 'robotic', 'cleaner', 'skimmer', 'chlorinator',
        # 健身相关
        'vibration plate', 'vibrating plate', 'vibration machine', 'vibrating machine',
        'exercise machine', 'workout equipment', 'fitness equipment',
        'treadmill', 'bike', 'cycling', 'rowing', 'elliptical', 'stepper',
        # 医美/护肤类（新增）
        'scar sheet', 'scar tape', 'silicone scar', 'scar cream', 'scar gel',
        'silicone sheet', 'silicone tape', 'wrinkle patch', 'face tape',
        'skin care', 'skincare', 'beauty product', 'anti aging',
        # 眼部护理类
        'eye massager', 'eye mask', 'sleep mask', 'eye strain', 'head massager', 'massager',
    ]
    
    found_products = []
    for pt in product_types:
        if pt in text.lower():
            found_products.append(pt)
    
    # 步骤3：识别型号（B0XXXX, XB7, SE Plus, WH-1000XM5等，含特殊字符）
    models = re.findall(r'\b([A-Z]+[0-9]+\s*[A-Z0-9]*)\b', text)
    
    # 提取 带 - 和 + 的组合词
    models2 = re.findall(r'\b([A-Z]+[0-9]*[-+][A-Z0-9+]+)\b', text)
    models.extend(models2)
    
    # 组合品牌+产品
    for brand in brand_candidates[:1]:  # 取第一个品牌
        for ptype in found_products[:2]:
            keywords.append(f"{brand} {ptype}")
        for model in models[:1]:
            keywords.append(f"{brand} {model}")
    
    # 添加产品类型（不带品牌）
    for ptype in found_products[:3]:
        combined = ' '.join(keywords)
        if ptype not in combined:
            keywords.append(ptype)
    
    # 如果没找到品牌+型号，尝试提取 "品牌 + SE/Plus"这种
    if not keywords and brand_candidates:
        for brand in brand_candidates[:1]:
            # Betta SE Plus -> "Betta SE Plus"
            se_matches = re.findall(r'\b(Betta\s*SE\s*Plus)\b', text, re.IGNORECASE)
            for m in se_matches:
                keywords.append(m.replace(' ', ''))
            # 也尝试 "品牌 + 型号" 如 Betta SE
            model_match = re.search(r'(Betta\s*\w+)', text, re.IGNORECASE)
            if model_match:
                keywords.append(model_match.group(1).replace(' ', ''))
    
    # 去重
    seen = set()
    result = []
    for kw in keywords:
        clean_kw = kw.strip().lower()
        if clean_kw and len(clean_kw) > 2 and clean_kw not in seen:
            seen.add(clean_kw)
            result.append(kw.strip())
    
    return result[:6]  # 最多6个


def extract_keywords_with_ai(description: str) -> List[str]:
    """使用外部AI提取关键词（如可用）"""
    # TODO: 当MiniMax API可用时实现
    # 目前直接使用本地提取
    return extract_keywords_local(description)



def extract_keywords_from_text(text: str) -> List[str]:
    """从商品描述提取关键词，使用本地规则"""
    return extract_keywords_local(text)


def extract_brand_candidates(description: str) -> List[str]:
    """仅提取品牌候选词（不组合产品类型）"""
    text = description.strip()
    words = re.findall(r'\b([A-Z][a-zA-Z]{2,15})\b', text)
    words_upper = re.findall(r'\b([A-Z]{4,15})\b', text)
    words.extend(words_upper)

    excluded_brands = {
        'The', 'With', 'And', 'For', 'From', 'Best', 'Top', 'New', 'Pro',
        'Plus', 'SE', 'Dual', 'Twin', 'LED', 'USB', 'HDMI', 'WiFi', 'GPS',
        'TV', 'DIY', 'Real', 'Time', 'Home', 'Women', 'Men', 'BPA', 'Free',
        'SPE', 'PEM', 'Tritan', 'Water', 'Hydrogen', 'Machine', 'Generator',
        'Filter', 'Pitcher', 'Magnetic', 'Vortex', 'Structured', 'Calcium',
        'Sulfite', 'Tritan'
    }
    brand_candidates = []
    for w in words:
        if w not in excluded_brands and len(w) >= 2 and w not in brand_candidates:
            brand_candidates.append(w)
    return brand_candidates[:5]


def extract_product_types(description: str) -> List[str]:
    """从商品描述中识别产品类型词（支持两词组合如 hydrogen water machine）"""
    text_lower = description.lower()
    # 扩展产品词典（包含两词组合）
    product_types = [
        # 氢水机相关
        'hydrogen water machine', 'hydrogen water generator', 'hydrogen water pitcher',
        'hydrogen water', 'hydrogen generator', 'water ionizer', 'water pitcher',
        # 通用电子
        'speaker', 'headphone', 'earphone', 'earbud', 'charger', 'cable',
        'case', 'cover', 'mount', 'stand', 'holder', 'keyboard', 'mouse',
        'monitor', 'webcam', 'camera', 'light', 'lamp', 'bulb', 'plug',
        'outlet', 'switch', 'sensor', 'lock', 'doorbell', 'watch', 'band',
        'tracker', 'fitness', 'pod', 'drone', 'controller', 'gamepad',
        'soundbar', 'subwoofer', 'mic', 'microphone', 'projector',
        'adapter', 'hub', 'drive', 'storage',
        # Pool相关
        'pool skimmer', 'pool cleaner', 'pool robot', 'solar charger', 'solar panel',
        'robot', 'robotic', 'cleaner', 'skimmer', 'chlorinator',
        # 健身相关
        'vibration plate', 'vibrating plate', 'vibration machine', 'vibrating machine',
        'exercise machine', 'workout equipment', 'fitness equipment',
        'treadmill', 'bike', 'cycling', 'rowing', 'elliptical', 'stepper',
        # 医美/护肤类
        'scar sheet', 'scar tape', 'silicone scar', 'scar cream', 'scar gel',
        'silicone sheet', 'silicone tape', 'wrinkle patch', 'face tape',
        'skin care', 'skincare', 'beauty product', 'anti aging',
        # 眼部护理类
        'eye massager', 'eye mask', 'sleep mask', 'eye strain', 'head massager', 'massager',
    ]
    found = []
    for pt in product_types:
        if pt in text_lower and pt not in found:
            found.append(pt)
    return found[:5]


def extract_keywords_categorized(description: str) -> Dict[str, List[str]]:
    """从商品描述提取三类关键词：品牌词 / 品牌+产品 / 产品词

    Returns:
        {
            "brand": ["PIURIFY", ...],
            "brand_product": ["PIURIFY hydrogen water machine", ...],
            "product": ["hydrogen water machine", ...]
        }
    """
    brands = extract_brand_candidates(description)
    products = extract_product_types(description)

    brand_product = []
    for brand in brands[:2]:
        for product in products[:3]:
            combined = f"{brand} {product}"
            if combined not in brand_product:
                brand_product.append(combined)
    brand_product = brand_product[:6]

    return {
        "brand": brands,
        "brand_product": brand_product,
        "product": products
    }
    
    
# 尝试导入autoads的config
try:
    from config import get_config
    AUTOADS_CONFIG_AVAILABLE = True
except ImportError:
    AUTOADS_CONFIG_AVAILABLE = False

# AI提取品牌/产品关键词的Prompt模板
AI_EXTRACT_PROMPT = """\
你是一个专业的亚马逊产品关键词分析师。你的任务是从商品描述中提取用于Google Ads广告投放的关键词。

## 提取规则
1. 从商品描述中提取两类关键词：
   - 品牌词 + 产品类型词组合（如 "KODAK bluetooth speaker"）
   - 品牌词 + 产品型号词组合（如 "KODAK LUMA350"）

2. 关键词必须符合Google Ads规范：
   - 英文为主
   - 长度适中（3-50字符）
   - 包含实质产品信息

3. 输出格式（严格的JSON数组）：
   ["品牌词+产品类型", "品牌词+型号", ...]

## 示例
商品描述: "KODAK LUMA350 Portable Bluetooth Speaker - Waterproof, 20H Playtime, Rich Bass"
输出: ["KODAK bluetooth speaker", "KODAK LUMA350", "portable speaker", "waterproof speaker"]

商品描述: "Sony WH-1000XM5 Wireless Noise Canceling Headphones"
输出: ["Sony headphones", "Sony WH-1000XM5", "noise canceling headphones", "wireless headphones"]


## 现在提取
商品描述: {description}

输出（JSON数组，仅输出JSON，不要其他内容）：
"""


def parse_args():
    parser = argparse.ArgumentParser(description='Keyword Planner - 获取关键词搜索量和CPC')
    parser.add_argument('--command', choices=['analyze', 'generate'], required=True,
                      help='analyze: AI提取+API生成, generate: 纯API生成')
    parser.add_argument('--product-description', type=str,
                      help='商品描述（command=analyze时使用）')
    parser.add_argument('--url', type=str,
                      help='Amazon商品URL（command=analyze时使用）')
    parser.add_argument('--keywords', type=str,
                      help='种子关键词，多个用逗号分隔（command=generate时使用）')
    parser.add_argument('--ads-account', type=str, required=True,
                      help='Google Ads账户ID')
    parser.add_argument('--months', type=int, default=3,
                      help='历史数据月份范围（默认3个月）')
    parser.add_argument('--use-fallback', action='store_true', default=False,
                      help='Enable gotrends.app fallback on 429 rate limit')
    parser.add_argument('--output', choices=['console', 'file', 'feishu'], default='console',
                      help='输出形式')
    return parser.parse_args()


# AI提取品牌/产品关键词的Prompt模板
AI_EXTRACT_PROMPT = """"
你是一个专业的亚马逊产品关键词分析师。你的任务是从商品描述中提取用于Google Ads广告投放的关键词。

## 提取规则
1. 从商品描述中提取两类关键词：
   - 品牌词 + 产品类型词组合（如 "KODAK bluetooth speaker"）
   - 品牌词 + 产品型号词组合（如 "KODAK LUMA350"）

2. 关键词必须符合Google Ads规范：
   - 英文为主
   - 长度适中（3-50字符）
   - 包含实质产品信息

3. 输出格式（严格的JSON数组）：
   ["品牌词+产品类型", "品牌词+型号", ...]

## 示例
商品描述: "KODAK LUMA350 Portable Bluetooth Speaker - Waterproof, 20H Playtime, Rich Bass"
输出: ["KODAK bluetooth speaker", "KODAK LUMA350", "portable speaker", "waterproof speaker"]

商品描述: "Sony WH-1000XM5 Wireless Noise Canceling Headphones"
输出: ["Sony headphones", "Sony WH-1000XM5", "noise canceling headphones", "wireless headphones"]

## 现在提取
商品描述: {description}

输出（JSON数组，仅输出JSON，不要其他内容）：
"""


def load_google_ads_config():
    """从autoads config加载Google Ads配置"""
    global AUTOADS_CONFIG_AVAILABLE
    
    if AUTOADS_CONFIG_AVAILABLE:
        try:
            cfg = get_config()
            if cfg.google_ads and cfg.google_ads.is_configured:
                config = {
                    'developer_token': cfg.google_ads.developer_token,
                    'login_customer_id': cfg.google_ads.login_customer_id,
                    'customer_id': cfg.google_ads.customer_id,
                    'client_id': cfg.google_ads.client_id,
                    'client_secret': cfg.google_ads.client_secret,
                    'refresh_token': cfg.google_ads.refresh_token,
                    'service_account_json': cfg.google_ads.service_account_json,
                }
                # 过滤空值
                config = {k: v for k, v in config.items() if v}
                return config
        except Exception as e:
            print(f"Warning: Failed to load from autoads config: {e}")
    
    # Fallback to Secret Manager
    try:
        from secret_manager import get_secret_manager
        sm = get_secret_manager()
        if sm.client:
            from secret_manager import load_google_ads_config as load_sm_config
            return load_sm_config()
    except Exception as e:
        print(f"Warning: Secret Manager not available, {e}")
    
    # Fallback to env vars
    return {
        'developer_token': os.environ.get('GOOGLE_ADS_DEVELOPER_TOKEN'),
        'login_customer_id': os.environ.get('GOOGLE_ADS_LOGIN_CUSTOMER_ID'),
        'customer_id': os.environ.get('GOOGLE_ADS_CUSTOMER_ID'),
    }


def create_google_ads_client(config: Dict[str, Any]):
    """创建Google Ads客户端"""
    try:
        from google.ads.googleads.client import GoogleAdsClient
        import json
        import tempfile
        
        # 检查是否有Service Account配置
        service_account_path = None
        service_account_json = config.get('service_account_json', '')
        
        if service_account_json:
            if service_account_json.startswith('./'):
                # 相对路径，转换为绝对路径
                abs_path = os.path.join('/root/.openclaw/workspace/autoads', service_account_json.lstrip('./'))
                if os.path.exists(abs_path):
                    service_account_path = abs_path
            elif os.path.exists(service_account_json):
                service_account_path = service_account_json
            elif service_account_json.startswith('{'):
                # 已经是JSON，写入临时文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(service_account_json)
                    service_account_path = f.name
        
        if service_account_path:
            # 使用Service Account方式
            credentials = {
                'developer_token': config.get('developer_token'),
                'json_key_file_path': service_account_path,
                'login_customer_id': config.get('login_customer_id'),
                'use_proto_plus': True,
            }
        else:
            # 使用OAuth2方式
            credentials = {
                'developer_token': config.get('developer_token'),
                'login_customer_id': config.get('login_customer_id'),
                'client_id': config.get('client_id'),
                'client_secret': config.get('client_secret'),
                'refresh_token': config.get('refresh_token'),
                'use_proto_plus': True,
            }
        
        # 过滤None值
        credentials = {k: v for k, v in credentials.items() if v}
        
        if credentials:
            client = GoogleAdsClient.load_from_dict(credentials)
            return client
        
        return None
    except Exception as e:
        print(f"Error creating Google Ads client: {e}")
        import traceback
        traceback.print_exc()
        return None


def is_rate_limit_error(e: Exception) -> bool:
    """检查是否是429 rate limit错误"""
    err_str = str(e).lower()
    return '429' in err_str or 'rate limit' in err_str or 'quota' in err_str or 'too many requests' in err_str


def fetch_gotrends_metrics(keywords: List[str], country: str = 'US') -> List[Dict]:
    """使用gotrends.app API获取关键词指标（同步版本）"""
    
    country_id = GOTRENDS_COUNTRY_MAP.get(country, '2840')
    
    params = {
        'keywords': keywords,
        'geoTargetConstants': [f'geoTargetConstants/{country_id}'],
        'historicalMetricsOptions': {
            'includeAverageCpc': True,
            'yearMonthRange': {
                'start': {'year': '2025', 'month': 'JULY'},
                'end': {'year': '2025', 'month': 'JULY'}
            }
        }
    }
    
    # 同步请求
    data = None
    try:
        req = urllib.request.Request(
            GOTRENDS_API_URL,
            data=json.dumps(params).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 429:
                raise Exception("429 Rate Limit from gotrends.app")
            data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Exception("429 Rate Limit from gotrends.app")
        raise Exception(f"gotrends.app API error: {e.code}")
    
    results = []
    for item in data.get('results', []):
        results.append({
            'keyword': item.get('keyword', ''),
            'avg_monthly_searches': item.get('avgMonthlySearches', 0) or 0,
            'competition': item.get('competition', 'UNKNOWN'),
            'cpc_low': 0.0,
            'cpc_high': 0.0,
            'cpc_average': float(item.get('averageCpc', 0) or 0),
        })
    
    return results



def generate_keyword_ideas(client, customer_id: str, seed_keywords: List[str], use_fallback: bool = False) -> List[Dict]:
    """使用KeywordPlanner API生成关键词 ideas，带429重试和调用间隔控制"""
    
    from google.ads.googleads.v23.services.services.keyword_plan_idea_service import (
        KeywordPlanIdeaServiceClient,
    )
    from google.ads.googleads.v23.services.types.keyword_plan_idea_service import (
        GenerateKeywordIdeasRequest,
        KeywordSeed,
    )
    from google.ads.googleads.v23.enums.types.keyword_plan_network import (
        KeywordPlanNetworkEnum,
    )
    from google.ads.googleads.v23.common.types.keyword_plan_common import (
        HistoricalMetricsOptions,
    )
    
    keyword_ideas = []
    
    # 如果启用fallback，先尝试gotrends
    if use_fallback:
        print("[Info] Trying gotrends.app fallback API...")
        try:
            results = fetch_gotrends_metrics(seed_keywords, 'US')
            if results:
                print(f"[Info] gotrends.app returned {len(results)} results")
                return results
        except Exception as e:
            print(f"[Warning] gotrends.app failed: {e}, falling back to Google Keyword Planner")
    
    # 主API：Google Keyword Planner + 重试逻辑
    for retry in range(MAX_RETRIES + 1):
        try:
            service = client.get_service('KeywordPlanIdeaService')
            
            # 分批处理 + 调用间隔
            for i, chunk in enumerate([seed_keywords[i:i+50] for i in range(0, len(seed_keywords), 50)]):
                if i > 0:
                    print(f"[Info] Waiting {API_CALL_INTERVAL}s between batches...")
                    time.sleep(API_CALL_INTERVAL)
                
                request = GenerateKeywordIdeasRequest()
                request.customer_id = customer_id
                
                seed = KeywordSeed()
                seed.keywords = chunk
                request.keyword_seed = seed
                
                request.keyword_plan_network = KeywordPlanNetworkEnum.KeywordPlanNetwork.GOOGLE_SEARCH_AND_PARTNERS
                request.geo_target_constants = ['geoTargetConstants/2840']  # US
                request.language = 'languageConstants/1000'  # English
                request.historical_metrics_options = HistoricalMetricsOptions()
                request.page_size = 100
                
                response = service.generate_keyword_ideas(request=request)
                
                for idea in response.results:
                    keyword_ideas.append({
                        'keyword': idea.text,
                        'avg_monthly_searches': idea.keyword_idea_metrics.avg_monthly_searches if idea.keyword_idea_metrics else 0,
                        'competition': idea.keyword_idea_metrics.competition.name if idea.keyword_idea_metrics and idea.keyword_idea_metrics.competition else 'UNKNOWN',
                        'cpc_low': 0.0,
                        'cpc_high': 0.0,
                        'cpc_average': (idea.keyword_idea_metrics.average_cpc_micros / 1_000_000) if idea.keyword_idea_metrics and idea.keyword_idea_metrics.average_cpc_micros else 0.0,
                    })
            
            # 成功，跳出重试循环
            break
            
        except Exception as e:
            if is_rate_limit_error(e) and retry < MAX_RETRIES:
                wait_time = RETRY_WAIT * (retry + 1)  # 指数退避
                print(f"[Warning] Rate limit detected (attempt {retry+1}/{MAX_RETRIES}), waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                # 非429错误或重试次数用尽，尝试fallback
                print(f"[Error] Google Keyword Planner failed: {e}")
                if not use_fallback:
                    print("[Info] Retrying with gotrounds.app fallback...")
                    try:
                        return fetch_gotrends_metrics(seed_keywords, 'US')
                    except Exception as fe:
                        print(f"[Error] Fallback also failed: {fe}")
                        import traceback
                        traceback.print_exc()
                raise
    
    return keyword_ideas


def fetch_keyword_metrics(client, customer_id: str, keywords: List[str], months: int = 3, use_fallback: bool = False) -> List[Dict]:
    """获取关键词搜索量和CPC数据，带429重试和调用间隔控制"""
    
    from google.ads.googleads.v23.services.services.keyword_plan_idea_service import KeywordPlanIdeaServiceClient
    from google.ads.googleads.v23.services.types.keyword_plan_idea_service import GenerateKeywordIdeasRequest, KeywordSeed
    from google.ads.googleads.v23.enums.types.keyword_plan_network import KeywordPlanNetworkEnum
    from google.ads.googleads.v23.common.types.keyword_plan_common import HistoricalMetricsOptions
    
    # 如果启用fallback，先尝试gotrends
    if use_fallback:
        print("[Info] Trying gotrends.app fallback API...")
        try:
            results = fetch_gotrends_metrics(keywords, 'US')
            if results:
                print(f"[Info] gotrends.app returned {len(results)} results")
                return results
        except Exception as e:
            print(f"[Warning] gotrends.app failed: {e}, falling back to Google Keyword Planner")
    
    # 主API：Google Keyword Planner + 重试逻辑
    for retry in range(MAX_RETRIES + 1):
        try:
            results = []
            service = client.get_service('KeywordPlanIdeaService')
            
            for i, chunk in enumerate([keywords[i:i+50] for i in range(0, len(keywords), 50)]):
                if i > 0:
                    print(f"[Info] Waiting {API_CALL_INTERVAL}s between batches...")
                    time.sleep(API_CALL_INTERVAL)
                
                request = GenerateKeywordIdeasRequest()
                request.customer_id = customer_id
                
                seed = KeywordSeed()
                seed.keywords = chunk
                request.keyword_seed = seed
                
                request.keyword_plan_network = KeywordPlanNetworkEnum.KeywordPlanNetwork.GOOGLE_SEARCH_AND_PARTNERS
                request.geo_target_constants = ['geoTargetConstants/2840']  # US
                request.language = 'languageConstants/1000'  # English
                
                request.historical_metrics_options = HistoricalMetricsOptions()
                request.page_size = 100
                
                response = service.generate_keyword_ideas(request=request)
                
                for idea in response.results:
                    data = {
                        'keyword': idea.text,
                        'avg_monthly_searches': 0,
                        'competition': 'UNKNOWN',
                        'cpc_low': 0.0,
                        'cpc_high': 0.0,
                        'cpc_average': 0.0,
                    }
                    
                    if idea.keyword_idea_metrics:
                        m = idea.keyword_idea_metrics
                        data['avg_monthly_searches'] = m.avg_monthly_searches or 0
                        data['competition'] = m.competition.name if m.competition else 'UNKNOWN'
                        
                        # CPC: 使用 low/high page bid (单位micros -> dollars)
                        if m.low_top_of_page_bid_micros:
                            data['cpc_low'] = m.low_top_of_page_bid_micros / 1_000_000
                        if m.high_top_of_page_bid_micros:
                            data['cpc_high'] = m.high_top_of_page_bid_micros / 1_000_000
                        # 平均CPC = (Low + High) / 2
                        if data['cpc_low'] and data['cpc_high']:
                            data['cpc_average'] = (data['cpc_low'] + data['cpc_high']) / 2
                        elif data['cpc_high']:
                            data['cpc_average'] = data['cpc_high']
                    
                    results.append(data)
            
            # 成功，跳出重试循环
            return results
            
        except Exception as e:
            if is_rate_limit_error(e) and retry < MAX_RETRIES:
                wait_time = RETRY_WAIT * (retry + 1)
                print(f"[Warning] Rate limit detected (attempt {retry+1}/{MAX_RETRIES}), waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                # 非429错误或重试次数用尽，尝试fallback
                print(f"[Error] Google Keyword Planner failed: {e}")
                if not use_fallback:
                    print("[Info] Retrying with gotrends.app fallback...")
                    try:
                        return fetch_gotrends_metrics(keywords, 'US')
                    except Exception as fe:
                        print(f"[Error] Fallback also failed: {fe}")
                import traceback
                traceback.print_exc()
                return []
    
    return []


def format_results_table(results: List[Dict]) -> str:
    """格式化输出表格"""
    
    if not results:
        return "No results found."
    
    # 表头
    header = f"{'Keyword':<35} {'Avg Monthly Searches':>20} {'Competition':>12} {'CPC Low':>10} {'CPC High':>10} {'CPC Avg':>10}"
    separator = "-" * len(header)
    
    lines = [header, separator]
    
    for r in results:
        keyword = r.get('keyword', '')[:32] + '...' if len(r.get('keyword', '')) > 35 else r.get('keyword', '')
        searches = r.get('avg_monthly_searches', 0)
        competition = r.get('competition', 'UNKNOWN')[:10]
        cpc_low = r.get('cpc_low', 0.0)
        cpc_high = r.get('cpc_high', 0.0)
        cpc_avg = r.get('cpc_average', 0.0)
        
        line = f"{keyword:<35} {searches:>20,} {competition:>12} ${cpc_low:>9.2f} ${cpc_high:>9.2f} ${cpc_avg:>9.2f}"
        lines.append(line)
    
    return '\n'.join(lines)


def generate_feishu_content(results: List[Dict], command: str, input_text: str) -> str:
    """生成飞书表格内容"""
    
    content = f"# 🔍 Keyword Planner 关键词分析报告\n\n"
    content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"**输入**: {input_text}\n\n"
    
    # 表格
    content += "| Keyword | 月均搜索量 | 竞争程度 | CPC Low | CPC High | CPC Avg |\n"
    content += "|---------|------------|----------|---------|---------|--------|\n"
    
    for r in results[:50]:  # 最多50条
        keyword = r.get('keyword', '')[:30]
        searches = r.get('avg_monthly_searches', 0)
        competition = r.get('competition', 'UNKNOWN')
        cpc_low = f"${r.get('cpc_low', 0):.2f}"
        cpc_high = f"${r.get('cpc_high', 0):.2f}"
        cpc_avg = f"${r.get('cpc_average', 0):.2f}"
        
        content += f"| {keyword} | {searches:,} | {competition} | {cpc_low} | {cpc_high} | {cpc_avg} |\n"
    
    return content


def write_output_file(content: str, prefix: str = "keyword_planner") -> str:
    """写入文件"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"/root/.openclaw/workspace/logs/{prefix}_{timestamp}.txt"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename


def main():
    args = parse_args()
    
    # Step 1: 确定输入
    if args.command == 'analyze':
        if args.url:
            # 从URL提取商品信息（简化版，实际可用Decodo）
            input_text = args.url
            # TODO: 实际可以从URL解析产品名称
            product_desc = f"Product from {args.url}"
        elif args.product_description:
            input_text = args.product_description
            product_desc = args.product_description
        else:
            print("Error: --product-description or --url required for analyze command")
            sys.exit(1)
        
        # AI提取关键词（使用新分类提取器）
        print(f"🔍 Analyzing: {input_text}")
        categorized = extract_keywords_categorized(product_desc)
        print(f"📋 品牌词: {categorized['brand']}")
        print(f"📋 品牌+产品: {categorized['brand_product']}")
        print(f"📋 产品词: {categorized['product']}")

        # 优先级：品牌+产品 > 品牌词 > 产品词
        seed_keywords = (categorized['brand_product'] + categorized['brand'] + categorized['product'])[:8]

        if not seed_keywords:
            print("Error: No keywords extracted from description, please provide a valid product description")
            sys.exit(1)
    
    else:  # generate
        if not args.keywords:
            print("Error: --keywords required for generate command")
            sys.exit(1)
        
        input_text = args.keywords
        seed_keywords = [kw.strip() for kw in args.keywords.split(',')]
    
    # Step 2: 加载配置和创建客户端
    print(f"📡 Loading Google Ads config...")
    config = load_google_ads_config()
    
    if not config:
        print("Error: Failed to load Google Ads config")
        sys.exit(1)
    
    client = create_google_ads_client(config)
    if not client:
        print("Error: Failed to create Google Ads client")
        sys.exit(1)
    
    # Step 3: 获取关键词数据
    print(f"🔑 Fetching keyword data for: {seed_keywords[:5]}...")
    results = fetch_keyword_metrics(client, args.ads_account, seed_keywords, args.months, args.use_fallback)
    
    if not results:
        print("Warning: No results from API, trying alternative method...")
        results = generate_keyword_ideas(client, args.ads_account, seed_keywords, args.use_fallback)
    
    # Step 4: 输出
    if args.output == 'console':
        print("\n" + format_results_table(results))
    
    elif args.output == 'file':
        content = format_results_table(results)
        filename = write_output_file(content)
        print(f"✅ Results saved to: {filename}")
    
    elif args.output == 'feishu':
        content = generate_feishu_content(results, args.command, input_text)
        # 写入临时文件供飞书使用
        filename = write_output_file(content, "keyword_planner_feishu")
        print(f"✅ Feishu content saved to: {filename}")
        print("\n" + content[:2000])
    
    print(f"\n📊 Total keywords: {len(results)}")


if __name__ == '__main__':
    main()