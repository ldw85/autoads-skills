# HEARTBEAT.md

# 系统事件处理

收到以下 systemEvent 时执行对应任务：

## Composio Outlook 邮件监控 (每日2次)

当收到 cron 触发时 (`composio_email_monitor`):

1. 执行: `python3 /root/.openclaw/workspace/scripts/composio_email_monitor.py --check`
2. 读取 Outlook 邮件，过滤 yeahpromos.com 发来的邮件
3. 提取 ASIN 和 MID
4. 通过 MID→ASIN 映射查找关联的 ASIN
5. 汇总需要暂停的 ASIN 列表
6. 用户确认后执行暂停并记录

注意：
- 已处理的邮件ID记录在 `logs/processed_emails.json`
- MID→ASIN 映射记录在 `logs/mid_asin_mapping.json`
- 暂停日志记录在 `logs/paused_campaigns.json`

## 搜索词质量分析 (每2小时)

当收到 cron 触发时 (`search_term_analyzer`):

1. 执行: `python3 /root/.openclaw/workspace/scripts/search_term_analyzer.py --all-spending --cron`
2. 分析过去7天有花费>=$1的所有广告系列
3. 语义分析：识别办公打印机、价格导向、竞品品牌等不相关搜索词
4. 按问题类型分类输出（OFFICE_PRINTER/SHOPPING/PLATFORM等）
5. 发送飞书通知给用户确认

注意：仅当发现高风险搜索词时才发送通知

## 每日趋势简报 (早上9点)

### 任务: 每日趋势简报

1. 获取美国Google Trends: `curl -s "https://trends.google.com/trending/rss?geo=US"`
2. **AI智能筛选**: 使用AI判断每条趋势是否与用户兴趣相关
3. **判断标准**: 仅保留AI、科技、硬件、产品发布、商业等相关内容
4. **排除标准**: 体育赛事、娱乐综艺、名人八卦、生活方式类内容
5. 整理成简报格式发送给用户

## 每日Affiliate ROI报告 (8:00)

当收到 cron 触发时 (`affiliate_roi_report`):

1. 执行: `cd /root/.openclaw/workspace/autoads/archer-roi && bash scripts/run-affiliate-report.sh`
2. 生成YeahPromos和PartnerBoost的详细ROI报告（含CVR、佣金、成本、点击等）
3. 检查暂停规则，整理飞书报告并发送给用户

报告格式：
```
ASIN: B0D4QVWHFN | GADS Clicks: 317 | Orders: 9 (Cnf: 2, Pnd: 7) | Comm: $44.00 | GADS Cost: $367.18 | ROI: 75.3% | CVR: 2.84% | ConfirmedCVR: 0.63%
```

暂停规则检测：Rule 2(低ROI)、Rule 3(Pending为0)、Rule 4(低CVR)、Rule 5(低佣金+低CVR)

---

# 以下是静态任务配置（保留参考）

## 简报模板

📈 **每日趋势简报** - YYYY-MM-DD

### 🔥 科技/AI热点
- [经AI判断后的科技相关趋势]

### 💡 产品/硬件
- [经AI判断后的产品相关趋势]

---

## 亚马逊促销提醒 (每周一)

当收到 cron 触发时 (`亚马逊促销提醒 (每周一)`):

1. 执行: `bash /root/.openclaw/workspace/scripts/run-promotion-reminder.sh`
2. 生成未来90天内的促销节点提醒
3. 通过飞书发送给用户

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
