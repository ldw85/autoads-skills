# AutoAds 技能详解

> 生成时间: 2026-03-30

## 📁 模块总览

| 文件 | 行数 | 职责 |
|------|------|------|
| `main.py` | 730 | 入口，CLI 参数解析 + 命令分发 |
| `ad_researcher.py` | 557 | **AI 调研**（新版 claude --print 驱动）|
| `research_flow.py` | 711 | 旧版调研流程（MiniMax API + 技能串联）|
| `campaign_builder.py` | 811 | Google Ads 广告系列结构构建 |
| `google_ads_client.py` | 1181 | Google Ads API 封装 |
| `campaign_verifier.py` | 782 | 广告校验 |
| `verify_ads.py` | 730 | 验证广告是否合规 |
| `keyword_generator.py` | 311 | 关键词生成 |
| `product_extractor.py` | 329 | URL 中提取产品信息 |
| `product_researcher.py` | 355 | 产品专项研究 |
| `policy_filter.py` | 440 | Google Ads 政策合规过滤 |
| `config.py` | 601 | 配置加载 |
| `feishu_handler.py` | 609 | 飞书 Bot 处理 |
| `amazon_scraper.py` | 83 | 亚马逊爬虫（基础版）|
| `secret_manager.py` | 237 | 密钥管理 |

---

## 🔑 核心流程（`main.py`）

```
create 命令:
  → fetch_amazon_product_info()     # Decodo 提取 Amazon
  → AdResearcher.research()          # AI 调研 (claude --print)
  → extract_price_and_rate()         # 提价格 + 佣金率
  → CampaignBuilder.build()         # 构建广告系列
  → GoogleAdsClient.create_*()       # API 创建
  → verify_campaign()                # 校验
```

---

## 🧠 AI 调研模块（`ad_researcher.py`）

```python
class AdResearcher:
    def research(product_description, product_url, brand_name, features, user_reviews)
        → _extract_pain_points()      # 提取用户痛点
        → _generate_marketing_copy() # PAS 文案 + Headlines + Descriptions  
        → _generate_keywords()        # 核心词 + 长尾词 + 竞品词
        → generate_sitelinks()       # 生成附加链接
```

**每步均通过 `claude --print` 调用 Claude 生成纯 JSON 输出。**

---

## 🔧 关键词模块（`keyword_generator.py`）

```python
class KeywordGenerator:
    def generate_keywords(product_info, pain_points, count=30)
    def generate_keyword_variants(keywords)
    def validate_keywords(keywords)  # Google 8词限制检查
```

---

## 🏗️ 广告系列构建（`campaign_builder.py`）

```python
class CampaignBuilder:
    def build(budget, cpc_bid, keywords, headlines, descriptions, sitelinks, ...)
    def create_campaign()
    def create_ad_group()
    def create_text_ads()
    def create_keywords()
    def create_sitelinks()
```

---

## 🛡️ 政策过滤（`policy_filter.py`）

```python
class GoogleAdsPolicyFilter:
    def filter_headlines(headlines)
    def filter_descriptions(descriptions)
    def check_policy_violation(text) -> list  # 返回违规原因
```

---

## 📋 CLI 命令格式（`main.py`）

```bash
# AI 调研模式（推荐）
python3 -m src.main --command create \
  --url "https://www.amazon.com/dp/XXX" \
  --brand-name "品牌名" \
  --product-type "产品类型" \
  --features "特性..." \
  --commission-rate 0.05 \
  --product-price 99.9 \
  --tracking-template "https://track.com/h/xxx?url={lpurl}" \
  --budget 20 \
  --use-ai-research

# 仅调研
python3 -m src.main --command research \
  --url "..." --brand-name "..." --product-type "..."
```

---

## 📊 数据流

```
URL + 品牌 + 产品描述
       ↓
  Decodo → Amazon 商品信息（标题/价格/评分/评论/图片）
       ↓
  AdResearcher.research()
    ├─ 痛点提取  → pain_points[]
    ├─ PAS文案  → headlines[15] + descriptions[4]
    └─ 关键词   → core[12] + long_tail[15] + competitor[5]
       ↓
  提取价格 + 佣金率 → 计算 CPC
       ↓
  CampaignBuilder 组装
       ↓
  Google Ads API 创建广告系列
       ↓
  verify_campaign() 政策校验
```

---

## Decodo 提取的 Amazon 商品信息

| 字段 | 说明 |
|------|------|
| **title** | 商品标题 |
| **product_name** | 产品名称 |
| **brand** | 品牌名 |
| **price** | 当前价格（price_buybox、price_initial 兜底） |
| **rating** | 评分（满分5） |
| **reviews_count** | 评论数量 |
| **description** | 商品描述 |
| **bullet_points** | 要点/特性列表 |
| **images** | 产品图片 URL 列表 |
| **product_details** | 键值对形式的产品规格详情 |
| **reviews** | 用户评论列表（含 title、rating、content） |

---

## 技能调用关系

### 新版 AI 调研流程（`--use-ai-research`）

| 步骤 | 工具/技能 | 说明 |
|------|----------|------|
| 1 | `decodo-scraper` | 提取 Amazon 商品信息 |
| 2 | `claude --print` × 3 | 痛点提取 → PAS文案 → 关键词生成 |
| 3 | `google-ads-client` | Google Ads API 创建广告 |
| 4 | `verify_ads` | 政策合规校验 |

### 旧版调研流程（`research_flow.py`）

| 步骤 | 工具/技能 | 说明 |
|------|----------|------|
| 1 | `decodo-scraper` | 提取 Amazon 商品信息 |
| 2 | `competitor-analysis` | 竞品分析，提取竞品痛点 |
| 3 | `sentiment-bot` | 用户情感分析 |
| 4 | `keyword-research` | 关键词研究 |
| 5 | `product-researcher` | 产品专项研究 |
| 6 | `policy_filter` | 政策合规过滤 |
| 7 | `google-ads-client` | Google Ads API 创建广告 |
