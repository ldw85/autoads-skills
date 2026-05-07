---
name: amazon-product-fetcher
description: Fetch complete Amazon product data including title, current price, currency, star rating, review count, availability, main image, and product URL. Works from an Amazon URL or ASIN. Uses Decodo API (no direct Amazon scraping, no CAPTCHA). Trigger when asked to "get Amazon product info", "fetch Amazon price", "look up product on Amazon", "what does X cost on Amazon".
version: 2.0.0
license: MIT
metadata: {"openclaw": {"emoji": "🛒", "requires": {"bins": []}}}
---

# Amazon Product Fetcher 🛒

通过 Decodo API 获取 Amazon 商品完整数据，**无 CAPTCHA 封禁**，纯 Python 标准库。

## When to Use

- "Get the details for this Amazon product: [URL]"
- "What's the price of ASIN B0XXXXXXXX on Amazon?"
- "Fetch product info from amazon.com/dp/B0XXXXXXXX"
- "Look up [product] on Amazon and tell me the price"

## Quick Start

```bash
# 通过 ASIN
python scripts/fetch.py --asin B0CX44VMKZ

# 通过 URL
python scripts/fetch.py --url "https://www.amazon.com/dp/B0CX44VMKZ"

# JSON 格式输出
python scripts/fetch.py --asin B0CX44VMKZ --json
```

## Output Fields

| 字段 | 说明 |
|------|------|
| `asin` | Amazon 商品编号 |
| `title` | 商品标题 |
| `price` | 当前价格数字 |
| `currency` | 货币符号（如 `USD`） |
| `rating` | 星级评分（如 `4.5`） |
| `reviews` | 评论数量 |
| `availability` | 库存状态 |
| `image_url` | 主图 URL |
| `product_url` | Amazon 商品链接 |

## Decodo API

使用 Decodo scraper-api (`https://scraper-api.decodo.com/v2/scrape`)：

1. **amazon_pricing** — 获取价格、Condition、Seller（优先使用）
2. **amazon** — 全量解析（fallback，包含标题/评分/评论/图片）

内置速率限制：**每请求间隔 0.1~0.3 秒**（约 5 req/s）。

## Authentication

内置了默认 Decodo token。如需使用自己的 token，设置环境变量：

```bash
export DECODO_AUTH_TOKEN="your_base64_token"
```

或通过 `--token` 参数传入。

## Troubleshooting

| 问题 | 解决方案 |
|------|----------|
| 价格为空 | 商品无定价或 API 解析失败，尝试换 ASIN |
| error: fetch_failed | 网络问题或 Decodo API 不可用 |
| error: no_response | Decodo API 无响应，检查网络连接 |
