---
name: social-media-publisher
description: 社交媒体多平台发布Agent。用于在Reddit、Medium、X(Twitter)上发布内容。触发场景：(1)需要将内容发布到多个社交媒体平台 (2)需要将原始内容按照各平台格式改写 (3)接受内容创建Agent生成的原始内容并发布到社交媒体
---

# 社交媒体多平台发布

## 快速开始

此Skill用于将内容发布到Reddit、Medium、X三个平台。

### 支持的平台

1. **Reddit** - 社区论坛，适合短标题+正文，互动性强
2. **Medium** - 长文平台，适合深度文章
3. **X (Twitter)** - 短内容平台，有字符限制

### 工作流程

1. 接收原始内容（标题+正文）
2. 根据目标平台改写内容
3. 调用对应平台API发布
4. 返回发布结果

## 内容改写规则

### Reddit改写

- 标题：简洁有力，可带问句引发讨论
- 正文：添加"有什么想法？"等互动结尾
- 标签：使用r/子版块标签
- 长度：标题<300字符，正文<40000字符

### Medium改写

- 标题：可保留或优化
- 正文：保持段落清晰，添加适当的章节标题
- 封面图：建议添加
- 标签：添加相关标签
- 长度：无严格限制

### X改写

- 内容：拆分为多条推文（线程）
- 限制：每条<280字符
- 元素：添加话题标签(#)，可@提及相关账号
- 开头：可使用emoji增加吸引力

## 使用方法

### 直接发布

```python
from scripts.publisher import SocialMediaPublisher

publisher = SocialMediaPublisher()
result = publisher.publish(content, platforms=['reddit', 'medium', 'x'])
```

### 平台配置

在`references/platforms.md`中配置各平台的API凭证。

## 注意事项

- 首次使用需配置各平台的API凭证
- 遵守各平台的内容政策和社区规则
- 发布频率需符合平台限制
