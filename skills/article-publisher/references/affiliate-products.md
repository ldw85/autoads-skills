# Affiliate 产品数据库

## 说明

存储产品名称与 affiliate 链接、图片的映射关系。供 `[AFFILIATE: xxx]` 和 `[IMAGE: xxx]` 占位符替换使用。

## 格式

```json
{
  "产品名称（精确匹配键名）": {
    "link": "https://affiliate-link.com",
    "image": "https://product-image-url.jpg"
  }
}
```

## 当前产品

```json
{
  "Audio-Technica ATH-M50x": {
    "link": "https://amzn.to/43n1M4g",
    "image": "https://m.media-amazon.com/images/I/B00HVLUR86._SX679_.jpg"
  },
  "Sennheiser HD 560S": {
    "link": "https://amzn.to/3PP8Nb3",
    "image": "https://m.media-amazon.com/images/I/B08J9MVB6W._SX679_.jpg"
  },
  "Beyerdynamic DT 770 Pro": {
    "link": "https://amzn.to/49IY20C",
    "image": "https://m.media-amazon.com/images/I/B071XKQQ57._SX679_.jpg"
  },
  "Sennheiser HD 820": {
    "link": "https://amzn.to/4f4O3Xb",
    "image": "https://m.media-amazon.com/images/I/B07D41MTT7._SX679_.jpg"
  }
}
```

## 更新规则

- 添加新产品：创建新条目，键名为产品名称（需与文章占位符完全匹配）
- 更新链接：修改对应键名的 `link` 值
- 图片 URL：优先使用 Amazon CDN 格式 `m.media-amazon.com/images/I/XXX._SX679_.jpg`