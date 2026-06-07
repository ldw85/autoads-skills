# PartnerBoost Product Selector

从 PartnerBoost API 获取亚马逊商品数据，支持筛选和导出。

## API 端点

```
POST https://api.partnerboost.com/api/datafeed/get_fba_products
```

## 凭据配置

需要设置以下凭据到 cred_agent：

```bash
# 设置凭据
python3 cred_agent.py --set PARTNERBOOST_TOKEN=your_token PARTNERBOOST_UID=your_uid
```

## 使用方法

```bash
# 基本用法 - 获取美国区商品
python3 main.py --token YOUR_TOKEN --uid YOUR_UID

# 自定义筛选
python3 main.py \
  --token YOUR_TOKEN \
  --uid YOUR_UID \
  --country US \
  --min-price 100 \
  --min-reviews 20 \
  --min-rating 4.0

# 指定输出文件
python3 main.py -t TOKEN -u UID -o /path/to/output.csv
```

## 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --token/-t | | | PartnerBoost API Token |
| --uid/-u | | | PartnerBoost UID |
| --country/-c | US | 国家代码 (US/UK/DE等) |
| --page-size/-ps | 50 | 每页数量 (最大100) |
| --max-pages/-mp | 50 | 最大页数 |
| --min-price | 0 | 最低价格 ($) |
| --max-price | 9999 | 最高价格 ($) |
| --min-reviews | 20 | 最少评论数 |
| --min-rating | 4.0 | 最低评分 (0-5) |
| --min-discount | 0 | 最低折扣 (%) |
| --has-promo | | 必须有优惠码 |
| --has-acc | | 必须有加速佣金 |
| --output/-o | logs/partnerboost_selected_products.csv | 输出CSV路径 |
| --export-md | | 输出Markdown文件 |

## 输出格式

CSV 包含以下字段：

- ASIN
- product_name
- brand_name  
- original_price
- discount_price
- discount
- rating
- reviews
- commission
- acc_commission
- category
- subcategory
- availability
- url
- link (联盟链接)

## 示例

```bash
# 获取美国区价格>$100、评论>20、评分>4的商品
python3 main.py -t XXX -u YYY --min-price 100 --min-reviews 20 --min-rating 4.0

# 获取英国区有优惠码的商品
python3 main.py -t XXX -u YYY --country UK --has-promo
```

## API 返回字段参考

根据 /api/datafeed/get_fba_products 接口：

| 字段 | 类型 | 说明 |
|------|------|------|
| product_id | string | 产品ID |
| product_name | string | 产品名称 |
| asin | string | ASIN |
| discount | string | 折扣率 |
| commission | string | 佣金率 |
| category | string | 分类 |
| rating | string | 评分 |
| reviews | string | 评论数 |
| url | string | Amazon URL |
| brand_name | string | 品牌名 |
| original_price | string | 原价 |
| discount_price | string | 折后价 |
| acc_commission | string | 加速佣金 |
| promo_code_list | array | 优惠码列表 |
| link | string | 联盟链接 |