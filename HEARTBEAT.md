# HEARTBEAT.md

# 系统事件处理

收到以下 systemEvent 时执行对应任务：

## 每日简报任务 (早上9点)

### 任务: 每日趋势简报

1. 获取美国Google Trends: `curl -s "https://trends.google.com/trending/rss?geo=US"`
2. **AI智能筛选**: 使用AI判断每条趋势是否与用户兴趣相关
3. **判断标准**: 仅保留AI、科技、硬件、产品发布、商业等相关内容
4. **排除标准**: 体育赛事、娱乐综艺、名人八卦、生活方式类内容
5. 整理成简报格式发送给用户

## Archer ROI 报告 (8:00 和 12:00)

当收到 `systemEvent: "archer_roi_8am"` 或 `systemEvent: "archer_roi_12pm"` 时：

1. 执行: `cd /root/.openclaw/workspace/autoads/archer-roi && python3 runner.py --roi --network archer --days 30`
2. 整理ROI报告（佣金/成本）
3. 发送给用户

## Archer 产品监控 (每2小时)

当收到 `systemEvent: "archer_product_check"` 时：

1. 执行: `cd /root/.openclaw/workspace/autoads/archer-roi && python3 runner.py --check --pause --network archer`
2. 检查商品状态
3. **如有不可用商品，自动暂停对应广告系列，并通知用户**

---

# 以下是静态任务配置（保留参考）

## 简报模板

📈 **每日趋势简报** - YYYY-MM-DD

### 🔥 科技/AI热点
- [经AI判断后的科技相关趋势]

### 💡 产品/硬件
- [经AI判断后的产品相关趋势]

---

## AI筛选准则

### ✅ 应保留的内容
- AI、机器学习、LLM相关
- 消费电子、硬件产品发布
- 科技公司动态、商业新闻
- 软件、App、SaaS服务
- 开发者工具、开源项目
- 评测、对比、测评内容

### ❌ 应排除的内容
- 体育赛事、球队、运动员
- 娱乐综艺、电影、音乐
- 名人八卦、网红、社交媒体
- 政治、战争、灾难新闻
- 与科技/商业无关的生活方式
