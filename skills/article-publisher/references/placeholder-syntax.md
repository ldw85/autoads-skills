# 占位符语法

## 产品链接占位符

```markdown
[AFFILIATE: 产品名称]
```

**示例**：
```markdown
[AFFILIATE: Audio-Technica ATH-M50x]
[AFFILIATE: Sennheiser HD 560S]
```

**替换为**：
```html
<a href="https://amzn.to/43n1M4g">Audio-Technica ATH-M50x</a>
<a href="https://amzn.to/3PP8Nb3">Sennheiser HD 560S</a>
```

## 产品图片占位符

```markdown
[IMAGE: 产品名称]
```

**示例**：
```markdown
[IMAGE: Audio-Technica ATH-M50x]
```

**替换为**：
```html
<a href="https://amzn.to/43n1M4g">
  <img src="https://m.media-amazon.com/images/I/B00HVLUR86._SX679_.jpg" alt="Audio-Technica ATH-M50x" loading="lazy" style="max-width:300px">
</a>
```

## 组合使用

在文章中组合使用：
```markdown
### Audio-Technica ATH-M50x

[IMAGE: Audio-Technica ATH-M50x]

**Price:** ~$149 | **Impedance:** 38 ohms

The [AFFILIATE: Audio-Technica ATH-M50x] is the defining headphones...
```

## 替换优先级

1. 如果产品存在于 `affiliate-products.json`，使用数据库中的 link 和 image
2. 如果产品不存在，保留原始占位符文本并报告警告

## 注意事项

- 占位符名称必须**精确匹配**产品数据库中的键名
- 匹配时大小写不敏感，但建议保持一致
- 图片使用 Amazon CDN 官方图片，加载速度快且稳定