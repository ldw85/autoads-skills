#!/usr/bin/env python3
"""
Keyword Metrics Skill (formerly keyword-planner)

【2026-06-12 重构·铁律11】AI 推理归属
─────────────────────────────────────────
本技能只负责一件事：调 Google Keyword Planner API 查关键词的搜索量 + CPC。
- 不做品牌识别（调用方负责）
- 不做产品类型识别（调用方负责）
- 不做关键词过滤（调用方负责）

调用方（小灰主对话）负责：
- 从产品描述里识别品牌、子系列、种子词
- 用 4 层 keyword_filter 过滤 GKP 返回结果
- 输出分层建议、ROI 估算

作者：小灰
日期：2026-06-03 (original) / 2026-06-12 (refactored to metrics-only)
"""

import argparse
import json
import sys
import os
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Any

# Add autoads to path (config module is required)
sys.path.insert(0, '/root/.openclaw/workspace/autoads/src')


# === 配置 ===
DEFAULT_COUNTRY = "US"
DEFAULT_LANGUAGE = "en"
DEFAULT_MONTHS = 3

# === Rate Limit 控制 ===
API_CALL_INTERVAL = 2.0
MAX_RETRIES = 3
RETRY_WAIT = 60

# === Google Ads Geo Target IDs (主路径 GKP) ===
# 参考: https://developers.google.com/google-ads/api/reference/data/geotargets
GEO_TARGET_MAP = {
    'US': '2840',  # United States
    'GB': '2826', 'UK': '2826',  # United Kingdom
    'CA': '2124',  # Canada
    'AU': '2036',  # Australia
    'DE': '2276',  # Germany
    'FR': '2250',  # France
    'JP': '2392',  # Japan
    'IT': '2380',  # Italy
    'ES': '2724',  # Spain
    'NL': '2528',  # Netherlands
    'SE': '2752',  # Sweden
    'BR': '2076',  # Brazil
    'MX': '2484',  # Mexico
    'IN': '2356',  # India
    'KR': '2410',  # South Korea
    'SG': '2702',  # Singapore
    'HK': '2344',  # Hong Kong
    'TW': '2158',  # Taiwan
    'MY': '2458',  # Malaysia
    'AE': '2784',  # UAE
    'SA': '2682',  # Saudi Arabia
    'PL': '2616',  # Poland
    'TR': '2792',  # Turkey
    'RU': '2643',  # Russia
    'ID': '2360',  # Indonesia
    'TH': '2764',  # Thailand
    'VN': '2704',  # Vietnam
    'PH': '2608',  # Philippines
    'NZ': '2554',  # New Zealand
    'ZA': '2710',  # South Africa
}

# === Google Ads Language IDs ===
# 参考: https://developers.google.com/google-ads/api/reference/data/codes-formats
LANGUAGE_MAP = {
    'en': '1000',
    'de': '1001',
    'fr': '1002',
    'es': '1003',
    'it': '1004',
    'ja': '1005',
    'nl': '1010',
    'ko': '1012',
    'sv': '1015',
    'pt': '1014',
    'pt-BR': '1014',
    'zh': '1017', 'zh-CN': '1017',
    'zh-TW': '1018',
    'ar': '1019',
    'pl': '1030',
    'ru': '1031',
    'tr': '1037',
    'th': '1044',
    'vi': '1040',
    'id': '1025',
    'hi': '1023',
    'ms': '1102',
}

# === gotrends.app Fallback ===
GOTRENDS_API_URL = 'https://insitto.gotrends.app/kw/gethistorymetric'
GOTRENDS_COUNTRY_MAP = {
    'US': '2840',
    'GB': '2826', 'UK': '2826',
    'CA': '2124',
    'AU': '2036',
    'DE': '2276',
    'FR': '2250',
    'JP': '2392',
}


# 尝试导入autoads的config
try:
    from config import get_config
    AUTOADS_CONFIG_AVAILABLE = True
except ImportError:
    AUTOADS_CONFIG_AVAILABLE = False


def parse_args():
    parser = argparse.ArgumentParser(
        description='Keyword Metrics - 纯GKP查量工具(品牌识别/关键词过滤由调用方完成)'
    )
    parser.add_argument(
        '--keywords', type=str, required=True,
        help='种子关键词（多个用逗号分隔, 由调用方预先确定品牌/子系列）'
    )
    parser.add_argument(
        '--ads-account', type=str, required=True,
        help='Google Ads账户ID'
    )
    parser.add_argument(
        '--months', type=int, default=3,
        help='历史数据月份范围（默认3个月）'
    )
    parser.add_argument(
        '--use-fallback', action='store_true', default=False,
        help='启用 gotrends.app fallback (429时自动切换)'
    )
    parser.add_argument(
        '--output', choices=['console', 'file', 'feishu'], default='console',
        help='输出形式'
    )
    parser.add_argument(
        '--page-size', type=int, default=100,
        help='每个种子词生成的最大关键词数 (默认100)'
    )
    parser.add_argument(
        '--country', type=str, default=DEFAULT_COUNTRY,
        help=f'地域代码 (ISO 2-letter, 默认 {DEFAULT_COUNTRY}). 例: US/GB/DE/JP/AU/CA/FR/IT/ES/BR/MX/IN/KR/SG/HK/TW/AE'
    )
    parser.add_argument(
        '--language', type=str, default=DEFAULT_LANGUAGE,
        help=f'语言代码 (ISO, 默认 {DEFAULT_LANGUAGE}). 例: en/de/fr/ja/es/it/zh/zh-TW/ko/pt/ar/ru/tr/th/vi'
    )
    return parser.parse_args()


def load_google_ads_config():
    """从autoads config加载Google Ads配置"""
    
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
        import tempfile
        
        # Service Account优先
        service_account_path = None
        service_account_json = config.get('service_account_json', '')
        
        if service_account_json:
            if service_account_json.startswith('./'):
                abs_path = os.path.join('/root/.openclaw/workspace/autoads', service_account_json.lstrip('./'))
                if os.path.exists(abs_path):
                    service_account_path = abs_path
            elif os.path.exists(service_account_json):
                service_account_path = service_account_json
            elif service_account_json.startswith('{'):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(service_account_json)
                    service_account_path = f.name
        
        if service_account_path:
            credentials = {
                'developer_token': config.get('developer_token'),
                'json_key_file_path': service_account_path,
                'login_customer_id': config.get('login_customer_id'),
                'use_proto_plus': True,
            }
        else:
            credentials = {
                'developer_token': config.get('developer_token'),
                'login_customer_id': config.get('login_customer_id'),
                'client_id': config.get('client_id'),
                'client_secret': config.get('client_secret'),
                'refresh_token': config.get('refresh_token'),
                'use_proto_plus': True,
            }
        
        credentials = {k: v for k, v in credentials.items() if v}
        
        if credentials:
            return GoogleAdsClient.load_from_dict(credentials)
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
    """使用gotrends.app API获取关键词指标"""
    
    country_upper = country.upper() if country else 'US'
    country_id = GOTRENDS_COUNTRY_MAP.get(country_upper, '2840')
    if country_upper not in GOTRENDS_COUNTRY_MAP:
        print(f"[Warning] gotrends.app fallback does not support '{country}', using US (2840)")
    
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


def fetch_keyword_metrics(
    client, customer_id: str, keywords: List[str],
    months: int = 3, use_fallback: bool = False, page_size: int = 100,
    country: str = 'US', language: str = 'en'
) -> List[Dict]:
    """
    唯一职责: 接收调用方提供的种子关键词, GKP 查量
    
    输入: 调用方已经识别好的种子词(品牌+子系列+核心产品词)
    输出: 原始 GKP 数据(未过滤)
    """
    
    from google.ads.googleads.v23.services.services.keyword_plan_idea_service import KeywordPlanIdeaServiceClient
    from google.ads.googleads.v23.services.types.keyword_plan_idea_service import GenerateKeywordIdeasRequest, KeywordSeed
    from google.ads.googleads.v23.enums.types.keyword_plan_network import KeywordPlanNetworkEnum
    from google.ads.googleads.v23.common.types.keyword_plan_common import HistoricalMetricsOptions
    
    # 解析 country/language 到 Google Ads ID
    country_upper = country.upper() if country else 'US'
    geo_id = GEO_TARGET_MAP.get(country_upper)
    if not geo_id:
        raise ValueError(f"Unsupported country '{country}'. Supported: {sorted(set(k for k in GEO_TARGET_MAP.keys() if len(k) == 2))}")

    lang_id = LANGUAGE_MAP.get(language)
    if not lang_id:
        lang_id = LANGUAGE_MAP.get(language.lower() if language else 'en')
    if not lang_id:
        raise ValueError(f"Unsupported language '{language}'. Supported: {sorted(LANGUAGE_MAP.keys())}")

    print(f"[Info] Geo target: {country_upper} (ID {geo_id}) | Language: {language} (ID {lang_id})")

    # Fallback 优先路径
    if use_fallback:
        print("[Info] Trying gotrends.app fallback API...")
        try:
            results = fetch_gotrends_metrics(keywords, country_upper)
            if results:
                print(f"[Info] gotrends.app returned {len(results)} results")
                return results
        except Exception as e:
            print(f"[Warning] gotrends.app failed: {e}, falling back to Google Keyword Planner")
    
    # 主路径: Google Keyword Planner + 429 重试
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
                request.geo_target_constants = [f'geoTargetConstants/{geo_id}']
                request.language = f'languageConstants/{lang_id}'
                
                request.historical_metrics_options = HistoricalMetricsOptions()
                request.page_size = page_size
                
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
                        
                        if m.low_top_of_page_bid_micros:
                            data['cpc_low'] = m.low_top_of_page_bid_micros / 1_000_000
                        if m.high_top_of_page_bid_micros:
                            data['cpc_high'] = m.high_top_of_page_bid_micros / 1_000_000
                        if data['cpc_low'] and data['cpc_high']:
                            data['cpc_average'] = (data['cpc_low'] + data['cpc_high']) / 2
                        elif data['cpc_high']:
                            data['cpc_average'] = data['cpc_high']
                    
                    results.append(data)
            
            return results
            
        except Exception as e:
            if is_rate_limit_error(e) and retry < MAX_RETRIES:
                wait_time = RETRY_WAIT * (retry + 1)
                print(f"[Warning] Rate limit detected (attempt {retry+1}/{MAX_RETRIES}), waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"[Error] Google Keyword Planner failed: {e}")
                if not use_fallback:
                    print("[Info] Retrying with gotrends.app fallback...")
                    try:
                        return fetch_gotrends_metrics(keywords, country_upper)
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
    
    header = f"{'Keyword':<35} {'Avg Monthly Searches':>20} {'Competition':>12} {'CPC Low':>10} {'CPC High':>10} {'CPC Avg':>10}"
    separator = "-" * len(header)
    
    lines = [header, separator]
    
    for r in results:
        keyword = r.get('keyword', '')
        if len(keyword) > 35:
            keyword = keyword[:32] + '...'
        searches = r.get('avg_monthly_searches', 0)
        competition = r.get('competition', 'UNKNOWN')[:10]
        cpc_low = r.get('cpc_low', 0.0)
        cpc_high = r.get('cpc_high', 0.0)
        cpc_avg = r.get('cpc_average', 0.0)
        
        line = f"{keyword:<35} {searches:>20,} {competition:>12} ${cpc_low:>9.2f} ${cpc_high:>9.2f} ${cpc_avg:>9.2f}"
        lines.append(line)
    
    return '\n'.join(lines)


def generate_feishu_content(results: List[Dict], input_text: str) -> str:
    """生成飞书表格内容"""
    
    content = f"# 🔍 Keyword Metrics 关键词分析报告\n\n"
    content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"**种子词**: {input_text}\n\n"
    content += f"**注意**: 本工具只负责 GKP 查量，过滤/分层/ROI 估算由调用方(小灰)完成。\n\n"
    
    content += "| Keyword | 月均搜索量 | 竞争程度 | CPC Low | CPC High | CPC Avg |\n"
    content += "|---------|------------|----------|---------|---------|--------|\n"
    
    for r in results[:50]:
        keyword = r.get('keyword', '')[:30]
        searches = r.get('avg_monthly_searches', 0)
        competition = r.get('competition', 'UNKNOWN')
        cpc_low = f"${r.get('cpc_low', 0):.2f}"
        cpc_high = f"${r.get('cpc_high', 0):.2f}"
        cpc_avg = f"${r.get('cpc_average', 0):.2f}"
        
        content += f"| {keyword} | {searches:,} | {competition} | {cpc_low} | {cpc_high} | {cpc_avg} |\n"
    
    return content


def write_output_file(content: str, prefix: str = "keyword_metrics") -> str:
    """写入文件"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"/root/.openclaw/workspace/logs/{prefix}_{timestamp}.txt"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename


def main():
    args = parse_args()
    
    # === 单一职责: 接收调用方预先确定的种子词, GKP 查量 ===
    input_text = args.keywords
    seed_keywords = [kw.strip() for kw in args.keywords.split(',') if kw.strip()]
    
    if not seed_keywords:
        print("Error: --keywords required (comma-separated list)")
        print("Hint: 品牌识别/产品词识别由调用方(小灰)完成后传入")
        sys.exit(1)
    
    print(f"🔍 Querying GKP for {len(seed_keywords)} seed keywords...")
    print(f"📋 Seed keywords: {seed_keywords[:5]}{'...' if len(seed_keywords) > 5 else ''}")
    
    # 加载配置
    print(f"📡 Loading Google Ads config...")
    config = load_google_ads_config()
    if not config:
        print("Error: Failed to load Google Ads config")
        sys.exit(1)
    
    client = create_google_ads_client(config)
    if not client:
        print("Error: Failed to create Google Ads client")
        sys.exit(1)
    
    # 查量
    print(f"🔑 Fetching keyword data ({args.country}/{args.language})...")
    results = fetch_keyword_metrics(
        client, args.ads_account, seed_keywords,
        args.months, args.use_fallback, args.page_size,
        country=args.country, language=args.language
    )
    
    if not results:
        print("Warning: No results from GKP")
        return
    
    # 输出
    if args.output == 'console':
        print("\n" + format_results_table(results))
    elif args.output == 'file':
        content = format_results_table(results)
        filename = write_output_file(content)
        print(f"✅ Results saved to: {filename}")
    elif args.output == 'feishu':
        content = generate_feishu_content(results, input_text)
        filename = write_output_file(content, "keyword_metrics_feishu")
        print(f"✅ Feishu content saved to: {filename}")
        print("\n" + content[:2000])
    
    print(f"\n📊 Total keywords: {len(results)}")


if __name__ == '__main__':
    main()
