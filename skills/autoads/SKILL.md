---
name: autoads
description: |
  Google Ads广告自动创建工具。通过AI调研生成精准广告素材，支持任何品牌和产品。
  工作流：用户输入 → AI痛点研究 → AI素材生成(PAS模型) → AI关键词研究 → Google Ads API创建。
triggers:
  - 创建广告
  - Google Ads
  - autoads
  - 广告系列
  - campaign
  - 创建广告系列
input:
  type: object
  required:
    - landing_url
  properties:
    landing_url:
      type: string
      description: 广告落地页URL（必填）
      example: https://example.com/products/product-name
    tracking_template:
      type: string
      description: 跟踪模板URL（需包含{lpurl}占位符）
      example: https://tatrck.com/h/xxx?url={lpurl}
    country:
      type: string
      description: 目标国家代码
      default: US
    budget:
      type: number
      description: 日预算（固定20美元）
      default: 20
    product_price:
      type: number
      description: 商品金额（美元），用于计算每次点击最大金额
      example: 99.99
    commission_rate:
      type: number
      description: 佣金率（小数格式，如0.05代表5%），用于计算每次点击最大金额
      example: 0.05
    campaign_name:
      type: string
      description: 广告系列名称
    use_ai_research:
      type: boolean
      description: 使用AI调研工作流（推荐）
      default: true
    brand_name:
      type: string
      description: 品牌名称（AI调研必需）
      example: BrandName
    product_type:
      type: string
      description: 产品类型描述（AI调研用）
      example: fitness equipment, rowing machines
    features:
      type: string
      description: 产品特性（AI调研用）
      example: patented technology, smart app, quiet operation
    user_base:
      type: string
      description: 用户规模/统计数据（AI调研用）
      example: 10M+ users in 24 countries
output:
  type: object
  properties:
    success:
      type: boolean
    campaign:
      type: object
    ad_groups:
      type: integer
    ads:
      type: integer
    keywords:
      type: integer
---

# Autoads - Google Ads 广告自动创建

## 工作流

### 推荐: AI调研工作流

```
用户输入 → AI痛点研究 → AI素材生成 → AI关键词研究 → Google Ads API
```

**Step 1: 用户提供产品信息**
- URL、品牌、产品类型、特性

**Step 2: AI痛点研究**
- 模拟 review-analysis 技能逻辑
- 提取用户评论中的痛点

**Step 3: AI素材生成 (PAS模型)**
- 模拟 affiliate-marketing-creator 技能
- Problem-Agitate-Solution 框架
- 双系统理论 (情感+理性)
- 生成 Headlines 和 Descriptions

**Step 4: AI关键词研究**
- 模拟 keyword-research 技能
- 核心关键词 + 长尾关键词
- 搜索意图分类

**Step 5: Google Ads API创建广告**

---

## 使用方法

### 创建广告（AI调研模式）

```bash
cd /root/.openclaw/workspace/autoads
python3 -m src.main --command create \
  --url "https://example.com/products/product-name" \
  --brand-name "BrandName" \
  --product-type "product category" \
  --features "key features, benefits" \
  --user-base "user statistics" \
  --tracking-template "https://tatrck.com/h/xxx?url={lpurl}" \
  --product-price 99.99 \
  --commission-rate 0.05 \
  --name "CampaignName" \
  --country US \
  --use-ai-research
```

**注意**: 
- 每日预算固定为 20 美元
- CPC 计算公式: `商品价格 × 佣金率 / 50 × 0.9 × 6.98`
- CPC 范围: **0.1 - 0.56**（低于0.1则用0.1，高于0.56则用0.56）
- 程序会从文本中自动提取商品价格和佣金率
- 示例: $202 × 0.025 / 50 × 0.9 × 6.98 = $0.63 → 超过0.56上限，使用 $0.56

### 仅调研（查看生成的素材）

```bash
python3 -m src.main --command research \
  --url "https://example.com/products/product-name" \
  --brand-name "BrandName" \
  --product-type "product category" \
  --features "key features" \
  --user-base "user statistics"
```

### 查看状态

```bash
python3 -m src.main --command status
```

### 测试连接

```bash
python3 -m src.main --command test
```

---

## 参数说明

| 参数 | 必需 | 说明 |
|------|------|------|
| `--url` | ✅ | 落地页URL |
| `--brand-name` | ✅ (AI模式) | 品牌名称 |
| `--product-type` | ✅ (AI模式) | 产品类型 |
| `--features` | ✅ (AI模式) | 产品特性 |
| `--tracking-template` | ❌ | 跟踪模板，需包含{lpurl} |
| `--product-price` | ❌* | 商品金额（美元），可从文本自动提取 |
| `--commission-rate` | ❌* | 佣金率（小数），可从文本自动提取 |
| `--budget` | ❌ | 日预算（固定20美元，不建议修改） |
| `--country` | ❌ | 国家代码，默认US |
| `--use-ai-research` | ❌ | 使用AI调研，默认true |

*`--product-price` 和 `--commission-rate` 用于计算CPC，程序也会尝试从文本描述中自动提取

---

## 素材规格

- **Headlines**: ≤30字符
- **Descriptions**: ≤90字符
- **Keywords**: ≤8单词

---

## 示例输出

**Headlines:**
- Best Home Gym Equipment
- Ultimate Silent Workouts
- Easy Home Fitness Setup
- Proven Home Rowing Machine

**Keywords:**
- rowing machine, best rowing machine for home
- foldable treadmill for apartment
- quiet treadmill for condo

**Descriptions:**
- No bulky equipment or loud machines. Easy setup, AI-driven workouts, professional results.
- Professional-grade home gym with smart app. 16 resistance levels for all fitness goals.
