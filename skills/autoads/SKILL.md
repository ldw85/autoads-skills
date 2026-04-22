---
name: autoads
description: |
  Google Ads广告自动创建工具。通过AI驱动的工作流生成精准广告素材。
  
  **核心定位**：AI负责自然语言理解 + 参数构造，脚本负责验证 + 执行。
  
  工作流：自然语言输入 → AI解析 → 构造参数 → run_skill.py验证 → autoads执行
triggers:
  - 创建广告
  - Google Ads
  - autoads
  - 广告系列
  - campaign
  - 创建广告系列
input:
  type: object
  properties:
    url:
      type: string
      description: 落地页URL
      example: "https://www.amazon.com/dp/B0DYJKWLV8?maas=xxx&tag=xxx"
    customer_id:
      type: string
      description: Google Ads广告账号ID
      example: "3674729801"
    affiliate_name:
      type: string
      description: 联盟名称
      example: "yeahpromos"
    product_price:
      type: number
      description: 商品金额（美元）
      example: 29.99
    commission_rate:
      type: number
      description: 佣金率（小数，0.05=5%）
      example: 0.0375
    product_description:
      type: string
      description: 产品描述（AI从中提取痛点和广告素材）
    theme:
      type: string
      description: 广告主题（如"母亲节礼物"）
output:
  type: object
  properties:
    success:
      type: boolean
    campaign_id:
      type: string
---

# Autoads Skill

## 架构原则

**AI做理解，脚本做验证执行。**

AI负责：
- 理解用户自然语言
- 提取广告创建所需的参数
- 构造结构化参数调用run_skill.py

run_skill.py负责：
- 验证URL格式（Amazon必须含追踪参数）
- 验证必填参数（url, price, commission_rate）
- 执行autoads程序

## 使用流程

当用户说"创建广告..."时：

1. **AI解析用户输入**，提取参数
2. **AI调用run_skill.py**，传入结构化参数
3. **run_skill.py验证 + 执行**

### 示例

用户输入：
```
创建广告，广告账号: 3674729801，联盟名称: yeahpromos，
落地页url: https://www.amazon.com/dp/B0DYJKWLV8?maas=xxx&tag=xxx，
佣金率: 3.75%
```

AI构造并执行：
```bash
cd /root/.openclaw/workspace/autoads
python3 -m src.main \
  --url "https://www.amazon.com/dp/B0DYJKWLV8?maas=xxx&tag=xxx" \
  --customer-id 3674729801 \
  --affiliate-name yeahpromos \
  --product-price 29.99 \
  --commission-rate 0.0375 \
  --product-description "Amazon product B0DYJKWLV8, Mother's Day Gift theme" \
  --use-ai-research
```

## 参数说明

| 参数 | 必需 | 说明 |
|------|------|------|
| `--url` | ✅ | 落地页URL（Amazon必须含追踪参数） |
| `--product-price` | ✅ | 商品金额（USD） |
| `--commission-rate` | ✅ | 佣金率（小数） |
| `--customer-id` | ❌ | 广告账号ID |
| `--affiliate-name` | ❌ | 联盟名称 |
| `--product-description` | ❌* | 产品描述（AI调研用） |
| `--name` | ❌ | 广告系列名称 |

*建议提供，AI会从中提取更精准的广告素材

## URL验证规则

| URL类型 | 要求 | 失败原因 |
|---------|------|----------|
| Amazon | 必须含`?`及追踪参数(maas/tag等) | 缺少追踪参数 |
| 非Amazon | 直接通过 | - |

## 执行脚本

```bash
cd /root/.openclaw/workspace/autoads
python3 -m src.main --command create \
  --url "https://..." \
  --product-price 29.99 \
  --commission-rate 0.05 \
  --use-ai-research
```

## CPC计算

- 公式: `商品价格 × 佣金率 / 50 × 6.9 × 0.9`
- 范围: **0.1 - 1.2**（低于0.1用0.1，高于1.2用1.2）