---
name: refined-campaign-new
description: |
  创建全新的Google Ads精细化分层广告系列。
  
  **功能**：
  - 从零开始创建全新的Campaign
  - 创建L1/L2/L3/L5分层广告组结构
  - 所有层级关键词使用词组匹配 (PHRASE)
  - 使用AI生成全新广告素材（不依赖存量广告）
  - 自动创建Sitelinks
  
  **使用场景**：
  - 当用户说"创建全新精细化广告"、"从零创建分层广告"时使用
  - 不需要已有Campaign，完全新建

triggers:
  - 创建全新精细化广告
  - 创建分层广告系列
  - 新建精细化广告
  - 从零创建广告
  - new refined ads
  - fresh layered campaign
  - 创建精细化广告系列
  - 创建一个新的精细化
  - 新产品精细化
  - 全新产品 精细化
  - refined-campaign-new
  - 为新产品做精细化
  - 全新产品开广告

## 🎯 广告创建模式决策 (2026-06-08 16:41 David 确认)

2 种广告创建模式 (跟「渐进式测试+保留现有」哲学一致):

| 场景 | 推荐模式 | 路径 |
|---|---|---|
| **新产品** (无历史数据) | **模式 B** (默认) | 1. refined-campaign-new (本 skill) 建 4 层: L0 简化 (1 个 ad group $7) + L1 ($2) + L2 ($2) + L5 ($2) 2. 观察 7-14 天 L0 $7 vs L1 $2 表现 3. 如果 L0 转化好, 调 refined-ads 升级 L0 到 5 个 L0_3-7 测试组 ($3/$4/$5/$6/$7) 找最优 bid |
| **老产品** (已有普通广告) | **模式 A** (备选) | 1. 调 refined-ads 一次性补 8 个精细化分层 ad group: L0_3-7 (5 个 $3-7) + L1 ($1.80) + L2 ($1.80) + L5 ($1.80) |
| **老产品** (已有精细化分层) | 增量模式 | 调 refined-ads 增量加 ad group (不重复创建, 跟现有 ad group 并存对比) |

**模式 B 为什么是默认**:
- ✅ 跟「渐进式测试」哲学一致 (先 4 个, 再 8 个, 逐步验证)
- ✅ 1 个 L0 $7 作 baseline, 再 5 个 L0_3-7 找最优 bid (避免一开始 5 个 ad group 都无数据)
- ⚠️ 模式 A 适合「老产品迁移」场景, 不适合新产品 (高风险: 5 个 L0_3-7 都没 baseline)

**架构标准** (David 5/29 立 + 6/7 固化):
- L0: 5 个 Brand_Model_3-7 测试组 (CPC $3/$4/$5/$6/$7) [仅模式 A 完整, 模式 B 默认 1 个 $7]
- L1: Brand (CPC $1.80 或 $2)
- L2: Core (CPC $1.80 或 $2)
- L5: LongTail (CPC $1.80 或 $2)
- L1/L2/L5 CPC 封顶 $2 (David 2026-06-08 16:17 明确, 取代原 $2.4 限)

input:
  type: object
  properties:
    url:
      type: string
      description: Amazon商品URL（必须包含追踪参数）
      example: "https://www.amazon.com/dp/B0D6J5B98H?maas=xxx&tag=xxx"
    brand:
      type: string
      description: 品牌名称
      example: "Coolife"
    product_name:
      type: string
      description: 产品名称
      example: "Coolife 4K WiFi Dash Cam"
    price:
      type: number
      description: 商品价格（美元）
      example: 79.99
    commission_rate:
      type: number
      description: 佣金率（小数）
      example: 0.075
    customer_id:
      type: string
      description: Google Ads账号ID
      example: "6052559425"
    campaign_name:
      type: string
      description: 广告系列名称（可选，自动生成）
    country:
      type: string
      description: 目标国家代码（默认US）
      default: "US"
    budget:
      type: number
      description: 每日预算美元（默认20）
      default: 20
    product_description:
      type: string
      description: 产品描述（用于AI生成素材，可选）

output:
  type: object
  properties:
    success:
      type: boolean
    campaign_id:
      type: string
    campaign_name:
      type: string
    layers:
      type: object
    sitelinks_count:
      type: integer
    errors:
      type: array
---

# Refined Campaign New Skill

## 功能说明

创建**全新的**Google Ads精细化分层广告系列，所有素材由AI从零生成：

| 层级 | 名称 | 匹配类型 | 出价系数 | 说明 |
|------|------|---------|---------|------|
| L1 | Brand | PHRASE | 80% | 品牌关键词 |
| L2 | Core | PHRASE | 100% | 核心产品词 |
| L3 | Generic | PHRASE | 80% | 通用产品词 |
| L5 | LongTail | PHRASE | 70% | 长尾关键词 |

**关键词匹配类型**：全部使用 PHRASE（词组匹配）

## 广告素材

- **15条Headlines**：AI从产品信息生成
- **4条Descriptions**：AI从产品信息生成
- **4-6条Sitelinks**：AI针对电商常见场景生成

## 工作流程

1. **解析URL** - 提取final_url和url_suffix
2. **AI素材生成** - 生成 headlines、descriptions、sitelinks
3. **创建Campaign** - 新建广告系列
4. **创建分层广告组** - L1/L2/L3/L5
5. **添加关键词** - 词组匹配
6. **创建RSA广告** - 每个广告组
7. **创建Sitelinks** - 投放到Campaign级别

## 使用方式

用户需要提供：
- `url` - Amazon商品URL（必须含追踪参数）
- `brand` - 品牌名称
- `product_name` - 产品名称
- `price` - 价格（美元）
- `commission_rate` - 佣金率（小数）
- `customer_id` - Google Ads账号

可选：
- `campaign_name` - 广告系列名称
- `country` - 目标国家（默认US）
- `budget` - 每日预算（默认20美元）
- `product_description` - 产品描述

### CLI调用示例

```bash
cd /root/.openclaw/workspace/autoads
python3 -m src.refined_campaign_creator \
  --url "https://www.amazon.com/dp/B0D6J5B98H?maas=xxx&tag=xxx" \
  --brand "Coolife" \
  --product-name "Coolife 4K Dash Cam" \
  --price 79.99 \
  --commission-rate 0.075 \
  --customer-id 6052559425 \
  --campaign-name "Coolife Dash Cam US" \
  --country US \
  --budget 20
```

## 注意事项

1. **URL必须有suffix**：Amazon URL必须包含追踪参数，否则创建会失败
2. **CPC计算公式**：`price × commission_rate / 50 × 6.9 × 0.9`
3. **不依赖存量广告**：所有素材全新AI生成
4. **词组匹配**：所有层级使用PHRASE匹配
