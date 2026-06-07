---
name: refined-ads
description: |
  创建Google Ads精细化分层广告系列。
  
  **功能**：
  - 创建精细化分层广告结构（L0品牌型号/L1品牌词/L2核心词/L3通用词/L5长尾词）
  - 从现有Main广告提取完整素材（headlines + descriptions + sitelinks + URL suffix）
  - 使用AI从广告素材中识别品牌名和核心产品词
  - 自动复制广告和Sitelinks到各精细化广告组
  
  **L0品牌型号广告组**：
  - 关键词：品牌名+产品型号/产品名组合
  - CPC上限：7.0（使用公式 price×commission_rate/50×6.98计算）
  - 匹配方式：PHRASE
  
  **使用场景**：
  - 为现有Campaign创建精细化分层广告组
  - 当用户说"创建精细化分层广告"时使用
  
  **注意**：此skill用于在现有Campaign中添加精细化广告组，不创建新Campaign。
triggers:
  - 精细化
  - refined
  - 分层广告
  - layered keywords
  - 精细化分层
input:
  type: object
  properties:
    campaign_id:
      type: string
      description: 目标Campaign ID（必须是已存在的Campaign）
      example: "23838920800"
    customer_id:
      type: string
      description: Google Ads账号ID
      example: "6052559425"
    brand:
      type: string
      description: 品牌名称（可由AI从现有广告素材自动识别）
      example: "Rove"
    product_name:
      type: string
      description: 产品名称（用于关键词生成）
      example: "Rove 5G WiFi Dash Cam"
    product_model:
      type: string
      description: 产品型号（可选，用于L0关键词生成）
      example: "R2"
    product_url:
      type: string
      description: 商品URL（用于Google关键词工具）
      example: "https://www.amazon.com/dp/B0D6J5B98H"
    price:
      type: number
      description: 商品价格（美元）
      example: 129.99
    commission_rate:
      type: number
      description: 佣金率（小数）
      example: 0.075
    create_ads:
      type: boolean
      description: 是否创建广告素材（默认True，复制Main广告内容）
      default: true
output:
  type: object
  properties:
    success:
      type: boolean
    layers_created:
      type: array
      items:
        type: object
        properties:
          layer: string
          ad_group_id: string
          keywords_count: integer
          ads_created: boolean
          sitelinks_count: integer
    error:
      type: string
---

# Refined Ads Skill

## 功能说明

创建Google Ads精细化分层广告结构：

| 层级 | 名称 | 匹配类型 | 出价系数 | max_cpc |
|------|------|---------|---------|--------|
| L0 | Brand_Model | PHRASE | 100% | 7.0 |
| L1 | Brand | EXACT/PHRASE | 80% | 2.4 |
| L2 | Core | PHRASE | 100% | 2.4 |
| L3 | Generic | PHRASE | 80% | 2.4 |
| L5 | LongTail | BROAD/PHRASE | 70% | 2.4 |

## L0品牌型号广告组说明

**L0 (Brand_Model)** 是新增的最高优先级广告组，专门投放品牌名+产品型号/产品名组合关键词：

- 关键词类型：`品牌名 + 型号` 或 `品牌名 + 产品名`
- 示例：`JADENS LDGE`, `Rove R2 Dash Cam`
- CPC计算：`price × commission_rate / 50 × 6.98`，最高7.0
- 匹配方式：PHRASE
- 预期效果：品牌词产品型号组合转化率最高，适合测试不同CPC出价

## 使用方式

当用户说"创建精细化分层广告"时：

1. 确认用户提供了 `campaign_id` 和 `customer_id`
2. 调用 run_skill.py 执行

### 示例调用

```bash
python3 run_skill.py \
  --campaign-id 23838920800 \
  --customer-id 6052559425 \
  --brand Rove \
  --product-name "Rove 5G WiFi Dash Cam" \
  --product-model "R2" \
  --product-url "https://www.amazon.com/dp/B0D6J5B98H" \
  --price 129.99 \
  --commission-rate 0.075
```

## 工作流程

1. **查找Main广告组** - 在指定Campaign中查找名称包含"main"的广告组
2. **提取广告素材** - 提取 headlines、descriptions、URL、URL suffix、Sitelinks
3. **AI品牌识别** - 使用AI从headlines分析识别品牌名和核心产品词
4. **生成关键词** - 使用Google关键词工具 + 本地生成器生成L0/L1/L2/L3/L5各层关键词
5. **创建广告组** - 创建L0/L1/L2/L3/L5各层广告组
6. **复制广告素材** - 复制完整广告内容（15条headlines + 4条descriptions + sitelinks）

## L0关键词生成逻辑

1. **Google Keyword Planner** - 搜索"品牌名+产品型号"组合，AI语义分析筛选
2. **本地关键词生成** - 基于brand+product_model生成变体（同义词/拼写错误/简写）
3. **合并去重** - 所有关键词使用PHRASE匹配

## 注意事项

- 必须指定已存在的Campaign ID
- 如果Campaign没有Main广告组，会返回警告但仍尝试创建
- AI品牌识别从现有广告素材提取，不依赖用户输入
- Sitelinks从Campaign级别复制，会继承URL suffix
- L0广告组CPC上限7.0，不同于其他广告组的2.4上限