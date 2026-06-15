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

## 联盟产品状态监控 — v8 双节奏架构【2026-06-15 David 拍板重构】

**架构变革**: 拆为「**每 2 小时检查** (有异常才推)」+「**每 20:00 日报** (有货报平安)」双 cron, 避免过去 12 次/天的"全零报告"对飞书噪言污染。

### 任务 A：每 2 小时检查 (有异常才推) (`affiliate_product_monitor_bi2h`)

1. 执行: `cd /root/.openclaw/workspace/autoads && python3 archer-roi/scripts/monitor_product_status.py --json-summary`
2. 脚本会输出监控报告到 stdout（自动捕获到本地log）
3. 脚本会调用 `pause_campaigns()` 自动暂停 unavailable 状态的商品
4. **【v8 新增】智能推送判断** (在 agent 层做, 不改脚本):
   - 从 stdout 抓取 `===JSON_SUMMARY_START===` 与 `===JSON_SUMMARY_END===` 之间的 JSON 块
   - 读 `should_push_feishu` 字段 (脚本已算好: `paused_count > 0 OR unknown_alerts_count > 0`)
   - **`true` → 调 message tool (channel=feishu, target=user:ou_1ba51a4ca094652b84fc99909c10b8e7) 推送报告中**所有**已暂停项 + 首次未知告警 (含 ASIN / Campaign ID / 原因)**
   - **`false` → 不推送飞书** (脚本输出有 "0 暂停 0 告警", David 不想被 12 条/天"全零报告"刷屏)
5. 脚本本身失败时, **必须**用 `message` tool 推送失败告警到飞书（绝不静默吞掉）

### 任务 B：每日 20:00 (BJT) 日终汇总 (`affiliate_product_monitor_daily_20h`)

1. 执行: `cd /root/.openclaw/workspace/autoads && python3 archer-roi/scripts/monitor_product_status.py --daily-summary`
2. 脚本会拉取最新状态, 报告中增加「当日累计」段 (今日 00:00 - 20:00 累计暂停数, 含 unavailable/price_zero/consecutive_unknown 三类分计数)
3. **【v8 新增】无论是否异常, 都推送飞书** (这是用户明确要的"报平安"机制)
   - 调 message tool (channel=feishu, target=user:ou_1ba51a4ca094652b84fc99909c10b8e7) 推送完整报告
   - 报告包含: 当前各池各货状态分布 + 当日累计暂停数 + 当前跟踪中 unknown ASIN 数
4. 脚本本身失败时, **必须**用 `message` tool 推送失败告警到飞书

### v8 重构 (2026-06-15 David 拍板): 双节奏拆分

| 频率 | 任务 | 推送条件 | 推送内容 | CLI flag |
|---|---|---|---|---|
| 每 2 小时 | 检查双池状态 | `should_push_feishu=true` 才推 | 仅异常 (已暂停项 + 首次未知) | `--json-summary` |
| 每日 20:00 (BJT) | 日终汇总 | **总是推** (报平安) | 完整报告 + 当日累计 | `--daily-summary` |

**双节奏的工程化价值**:
- 减少 12x/天 → 1x/天 飞书消息量 (3/2/1 节奏: 有货/有异常/日终)
- "报平安"机制让 David 知道监控仍在运行 (6/12 事故中 4 天未推送才被发现)
- 异常不隐藏 (2h 节奏一旦 should_push=true 立即推, 延迟 ≤ 2h)
- 日终可看当日趋势 (累计暂停/累计 unknown, 历史决策参考)

### v6 重构 (2026-06-12 David 拍板): 启用 PartnerBoost 池
- **Archer 池**账号 666-035-6395 (原有)
- **PartnerBoost 池**账号 477-285-9239 (v6 新增, 6/12 启用)
- 双池均从 Google Ads API 拉取 ENABLED ASIN 列表
- 同一份暂停规则同时适用于两个池
- PB token: 优先从 cred agent 读 (PARTNERBOOST_API_TOKEN), 缺失回退到文件硬编码

### 暂停规则 v2 (2026-06-10 重构, David 拍板)
- `available` → 不动
- `unavailable` / `out_of_stock` / `inactive` → **立即暂停** + 飞书通知
- `pending` / `unknown` (API 异常/超时/空值) → **不暂停** + 飞书告警"首次未知状态"
- 同一 ASIN **连续 2 次** pending/unknown → **暂停** + 飞书通知"连续 2 次未知"
- Archer 和 PartnerBoost 池**使用完全相同规则**
- 连续 unknown 跟踪: `autoads/archer-roi/logs/monitor_unknown_state.json` (7 天自动清理)

### 6/12 事故+修复记录
- 事故: 6/8 之后 4 天没跑 (HEARTBEAT.md 记"每2小时"但实际 main+systemEvent 在 main 不在线时空跑, 8秒完成无推送)
- 修复: cron 配置改为 isolated + agentTurn + delivery.announce (与 ROI 报告同架构, 6/11 验证有效)

注意：
- 已处理的检查结果记录在 `/root/.openclaw/workspace/autoads/archer-roi/logs/monitor_YYYYMMDD_HHMMSS.log`
- 推送目标：飞书 user David（target=user:ou_1ba51a4ca094652b84fc99909c10b8e7）
- 推送失败处理：retry 1次，失败后用 `message` tool 改发 text message（fallback）

## Amazon URL Suffix检查 (每日20:00) 【2026-06-10 重构】

当收到 cron 触发时 (`amazon_suffix_check`):

1. 执行: `cd /root/.openclaw/workspace/autoads && python3 archer-roi/check_suffix.py --pause`
2. 脚本会检查所有Google Ads广告的final_url_suffix合规性
3. 缺失suffix的广告会被自动暂停
4. **推送飞书**: 用 `message` tool (channel=feishu, target=user:ou_1ba51a4ca094652b84fc99909c10b8e7) 主动推送报告

## 每日ROI报告 (早7-8点) 【2026-06-10 重构, 2026-06-11 修复】

**正确架构**（`isolated + agentTurn + delivery.announce`）：
- `sessionTarget: isolated`（独立 session 跑，不依赖 main）
- `payload: agentTurn`（直接给 agent 完整任务，含报告生成+推送飞书）
- `delivery: { mode: announce, channel: feishu, to: oc_16f4d501..., bestEffort: true }`
- 飞书群 chat_id: `oc_16f4d501d4e13793db85c88e17a9f110`（三平台 ROI 报告共用）

**特例豁免**：本任务的 `isolated + agentTurn` 模式**不受 6/10 「delivery 模式已废弃」备注影响**。
- 6/10 备注针对的是 Composio 邮件监控（`isolated + channel=last` 14次失败）
- ROI 报告的 isolated 是正确架构（独立 session 自跑自推，不依赖 main 在线）
- 绝不要改回 `main + systemEvent`（main 不在线时 systemEvent 投递即空跑，4-36ms 完成无推送）

**6/11 修复事故记录**：
- 6/10 12:30 有人把 3 个 ROI cron 改成 `main + systemEvent`，6/10-6/11 共 3 天早上 7:40-8:00 全部空跑（durationMs 4-36ms，sessionId=null，无飞书推送）
- 6/11 21:43 David 拍板改回 `isolated + agentTurn` + delivery 显式 channel/to
- 端到端验证：YeahPromos 21:47:38 跑通，agent 真发飞书（a232e31d session 的 message tool 调用记录在册）

报告log: `/root/.openclaw/workspace/autoads/archer-roi/logs/affiliate_report_YYYYMMDD_HHMMSS.txt`

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
