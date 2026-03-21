# 每日简报配置

## 简报内容

### 1. Google Trends 美国趋势
- **数据源**: `curl -s "https://trends.google.com/trending/rss?geo=US"`
- **过滤规则**: 
  - ❌ 排除: 体育(Sports)、WWE、棒球(MLB)、NBA、综艺(Reality TV)、American Idol
  - ✅ 保留: AI、科技(Tech)、硬件(Hardware)、产品(Product)、商业(Business)、游戏(Gaming)

### 2. 可选趋势源
- **GitHub Trending**: 技术开发者关注的项目
- **Product Hunt**: 新产品发布
- **Hacker News**: 科技 news

## 简报格式示例

📈 **每日趋势简报** - [日期]

**🔥 科技/AI热点:**
- [关键词1]: [热度] - [简短的新闻摘要]
- [关键词2]: [热度] - [简短的新闻摘要]

**💡 产品/硬件:**
- [关键词]: [热度] - [相关产品/发布信息]

## 执行频率
- 每日早上 9:00 (北京时间)
- 可通过 heartbeat 或 cron 触发

## 过滤关键词黑名单
```
sports, wwe, wrestling, baseball, mlb, nba, basketball, football, 
american idol, reality tv, celebrity, gossip, movie, tv show, 
entertainment, wrestler, wrestler
```

## 过滤关键词白名单 (可选，用于更精准筛选)
```
AI, artificial intelligence, machine learning, LLM, chatbot,
apple, google, microsoft, amazon, nvidia, tesla,
hardware, laptop, phone, chip, processor, gpu,
gaming, steam, playstation, xbox, nintendo,
product launch, review, announcement
```
