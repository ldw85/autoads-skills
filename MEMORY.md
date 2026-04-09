# MEMORY.md - 长期记忆

> 小灰的记忆核心文件
> 每季度整理一次，将超过3个月的记忆归档

---

## 核心信息

### 关于 David
- **名字**: LiuDavid
- **时区**: Asia/Shanghai (GMT+8)
- **沟通方式**: 飞书
- **博客**: https://github.com/ldw85/my-blog
- **兴趣**: AI硬件、评测文章

### 关于小灰
- **名字**: 小灰 🐺
- **角色**: 个人AI助理
- **主要工作**: 产品调研、评测文章、热点分析、广告素材

---

## 用户偏好 (2026-03-17)

- **不感兴趣的领域**: 体育、WWE摔角、棒球、NBA、综艺娱乐
- **偏好的趋势**: AI硬件、科技评测、产品相关内容

---

## 工作准则 (2026-03-13)

1. 长任务告知计划完成时间，定时同步进展
2. 遇到错误尝试解决
3. 无法决策时给方案让用户选择
4. 陷入死循环停止并通知
5. 独立思考，不合理要求提出讨论
6. 安装skill前扫描安全问题
7. 会话过长时使用记忆压缩/重置
8. 超过3个月的记忆归档

---

## 定时任务

### 每日趋势简报 (2026-03-21)
- **Cron Job ID**: `5d4ea908-59e9-4f98-91d9-477a51baf2b3`
- **运行时间**: 每天 09:00 (Asia/Shanghai)
- **触发事件**: `systemEvent: "daily_trends"` 发送到 main session
- **执行脚本**: `/root/.openclaw/workspace/scripts/daily-trends.mjs`
- **过滤逻辑**: 排除体育、娱乐、政治内容，保留 AI/科技/产品相关内容
- **商机分析**: 自动分析亚马逊商品机会，支持10+品类
- **输出文件**: `/root/.openclaw/workspace/logs/trends_to_send.txt`
- **状态**: ✅ 已配置

### 每日亚马逊产品机会简报 (2026-03-23)
- **Cron Job ID**: `9d12052b-bb16-41e0-ad45-066f8fe6a999`
- **运行时间**: 每天 09:30 (Asia/Shanghai)
- **触发事件**: `systemEvent: "daily_amazon_opportunities"` 发送到 main session
- **执行脚本**: `/root/.openclaw/workspace/scripts/amazon-opportunities.mjs`
- **数据来源**: Google Trends RSS (免费) + AI分析
- **过滤逻辑**: 排除体育、娱乐、政治内容
- **产品映射**: 12个品类（音频/手机/电脑/智能家居/游戏/健身/摄影/生活等）
- **输出文件**: `/root/.openclaw/workspace/logs/amazon_to_send.txt`
- **状态**: ✅ 已配置
- **注意**: Amazon直接爬取被封锁，使用Google Trends趋势驱动产品推荐

### 每日亚马逊产品机会分析 (2026-03-23)
- **Cron Job ID**: `d032a513-3da9-45cf-8bfd-93b7d2a6711e`
- **运行时间**: 每天 09:00 (Asia/Shanghai)
- **目标**: isolated session，自动运行脚本并发送飞书
- **执行脚本**: `/root/.openclaw/workspace/scripts/amazon-opportunities.mjs`
- **包装脚本**: `/root/.openclaw/workspace/scripts/run-amazon-opportunities.sh`
- **数据来源**: Google Trends RSS (免费) + AI产品推荐映射
- **输出文件**: `/root/.openclaw/workspace/logs/amazon_to_send.txt`
- **状态**: ✅ 已配置
- **注意**: Amazon直接爬取被封锁，使用趋势映射方案

### Amazon库存检查定时任务 (2026-04-07 重新启用)
- **Cron Job ID**: `ec450839-69d8-46f6-b1de-9d07135ccd91`
- **运行时间**: 每天 20:00 (Asia/Shanghai)
- **目标**: isolated session，执行检查脚本并发送飞书
- **超时设置**: 300秒（修复了原30秒超时导致的中断问题）
- **执行脚本**: `/root/.openclaw/workspace/skills/amazon-inventory-monitor/check_inventory.py`
- **功能**: 检查所有Google Ads启用状态广告系列中的亚马逊商品链接，验证商品是否仍有货
- **数据来源**: Google Ads API + Decodo Amazon Scraper
- **Customer ID**: 3674729801
- **状态**: ✅ 已配置

### Amazon URL Suffix检查定时任务 (2026-04-05 更新)
- **Cron Job ID (12:00)**: `65f81bc0-e3dd-4e4a-a502-dd8299a66de1`
- **Cron Job ID (20:00)**: `db1d599f-ed97-4c50-8011-cbd2582782d5`
- **运行时间**: 每天 12:00 和 20:00 (Asia/Shanghai)
- **目标**: isolated session，执行检查脚本并发送飞书
- **超时设置**: 300秒（修复了原30秒超时导致的中断问题）
- **执行脚本**: `/root/.openclaw/workspace/autoads/scripts/check_suffix.py`
- **检查账户**: 3674729801, 6052559425
- **功能**: 
  - 检查所有Amazon广告 + 站内链接广告的final_url_suffix是否为空
  - **自动暂停**：如果发现Amazon广告缺少suffix，自动暂停该广告系列
  - 通过飞书发送检查报告
- **严重性**: 🔴 CRITICAL - Amazon缺少tag会丢失佣金，站内链接缺少suffix追踪不完整
- **状态**: ✅ 已配置

### 商机分析支持的品类
- 🤖 AI/科技产品 (AI工具订阅、Claude Pro、ChatGPT Plus等)
- 📱 消费电子 (手机配件、平板保护套、无线充电器等)
- 🏠 智能家居 (智能音箱、插座、门锁、摄像头等)
- 💻 生产力工具 (笔记本支架、机械键盘、显示器等)
- 🔐 网络安全 (VPN、密码管理器、安全密钥等)
- 🎮 游戏设备 (游戏耳机、鼠标、手柄等)
- 🏃 健康健身 (智能手表、健身手环、运动耳机等)
- 🎧 音频设备 (无线耳机、降噪耳机、蓝牙音箱等)
- 📸 摄影摄像 (三脚架、补光灯、麦克风、稳定器等)
- ☕ 生活品质 (咖啡机、空气炸锅、扫地机器人等)
- 🏆 体育赛事及用品 (球队周边、运动装备、粉丝商品、赛事装备等)

## 技能库

- feishu-doc, feishu-wiki, feishu-drive (飞书操作)
- qqbot-cron, qqbot-media (QQ提醒)
- skill-creator (技能创建)
- obsidian (笔记)
- landing-page-generator (落地页)
- marketing-mode (营销)
- seo系列 (SEO优化)
- google-trends (趋势)
- weather (天气)
- video-frames (视频)
- tencent-cloud-cos (腾讯云)
- tencentcloud-lighthouse-skill (腾讯云轻量服务器)
- **social-media-publisher** (社交媒体多平台发布: Reddit/Medium/X)
- **product-review-writer** (高质量产品评测写作: SEO+真实感)
- **autoads** (Google Ads广告自动创建)
- **amazon-inventory-monitor** (检查Google Ads中亚马逊商品库存状态)

---

## AutoAds 项目 (2026-03-21)

### 项目位置
```
/root/.openclaw/workspace/autoads/
```

### 功能
自动创建Google Ads广告系列，包含：
- AI驱动的用户痛点研究
- 营销素材智能生成 (PAS模型)
- 关键词精准优化
- Responsive Search Ads (RSA)
- 政策合规过滤

### 新AI工作流 (推荐)

**Step 1: 用户提供输入信息**
- URL、Brand名称、产品类型、特性、用户规模

**Step 2: AI痛点研究 (ad_researcher.py)**
- 模拟 review-analysis 技能逻辑
- 提取用户评论痛点

**Step 3: 营销素材生成**
- 模拟 affiliate-marketing-creator 技能
- PAS模型 + 双系统理论 + 需求层次

**Step 4: 关键词研究**
- 模拟 keyword-research 技能
- 核心词 + 长尾词 + 竞品词

**Step 5: autoads CLI 创建广告**

### 核心模块
| 模块 | 文件 | 功能 |
|------|------|------|
| AI调研 | `ad_researcher.py` | 串联AI技能生成素材 |
| 产品提取 | `product_extractor.py` | 从URL解析产品信息 |
| 旧AI研究 | `research_flow.py` | 原research流程(保留) |
| 关键词生成 | `keyword_generator.py` | 生成关键词变体 |
| 政策过滤 | `policy_filter.py` | Google Ads合规检查 |
| 广告构建 | `campaign_builder.py` | 组装广告系列 |
| Google Ads API | `google_ads_client.py` | 调用Google Ads API |

### 使用方法

**方式1: AI调研 + 创建广告 (推荐)**
```bash
cd /root/.openclaw/workspace/autoads
python3 -m src.main --command create \
  --url "https://example.com/product" \
  --brand-name "BrandName" \
  --product-type "product category" \
  --features "key features" \
  --user-base "user statistics" \
  --product-price 99.99 \
  --commission-rate 0.05 \
  --name "CampaignName" \
  --country US \
  --use-ai-research
# 注意：不要传 --tracking-template，除非用户明确要求！
```

**方式2: 仅调研(查看生成的素材)**
```bash
python3 -m src.main --command research \
  --url "https://example.com/product" \
  --brand-name "BrandName" \
  --product-type "product category" \
  --features "key features" \
  --user-base "user statistics"
```

### 注意事项
1. **无硬编码** - 所有品牌/产品信息由用户输入
2. **AI驱动** - 使用Claude Code调用AI生成素材
3. **技能串联** - review-analysis + affiliate-marketing-creator + keyword-research
4. **字符限制** - Headlines≤30, Descriptions≤90, Keywords≤8词
- `auto` - 自动检测（默认）

### 依赖技能
- `competitor-analysis` - 已安装 ✅
- `keyword-research` - 已安装 ✅
- `sentiment-bot` - 需要 AIPROX_SPEND_TOKEN

### 注意事项
1. 落地页URL必须是有效的（返回200）
2. 关键词单词数≤8（Google限制）
3. Headlines≤30字符，Descriptions≤90字符
4. 避免硬编码产品名称（已修复）

### CPC计算规则 (2026-03-29更新)
- **每日预算**: 固定20美元
- **CPC公式**: `商品价格 × 佣金率 / 50 × 0.9 × 6.98`
- **CPC范围**: 0.1 - 1.2（低于0.1用0.1，高于1.2用1.2）
- **自动提取**: 程序从文本中自动提取商品价格和佣金率
- **必需参数**: `--product-price` (商品金额美元) + `--commission-rate` (佣金率小数) 可选，程序自动提取

### Decodo自动提取 (2026-03-29)
- **触发条件**: 只提供URL和佣金率时，自动调用Decodo提取Amazon商品信息
- **提取内容**: 标题、品牌、价格、评分、图片、特性、评论等
- **流程**: URL + 佣金率 → Decodo提取 → 自动构建product_description → 创建广告
- **校验**: 创建广告后自动执行广告校验（使用verify_ads.py）

### ⚠️ URL Suffix 处理规则 (2026-04-04)
**【重要】用户提供完整Amazon URL时，程序应自动从?后提取suffix**
- **完整URL示例**: `https://www.amazon.com/dp/B00SU0QSZ8?maas=xxx&tag=xxx&aa_campaignid=...`
- **final_url**: `https://www.amazon.com/dp/B00SU0QSZ8`（?前面的部分）
- **suffix**: `maas=xxx&tag=xxx&aa_campaignid=...`（?后面的部分）
- **联盟名称 ≠ suffix**: suffix是URL参数，不是联盟名称
- **处理方式**: 直接传完整URL给autoads，程序会自动解析
- **错误做法**: 把suffix当作联盟名称传入，或把完整URL当作tracking_template

### ⚠️ 重要教训 (2026-03-31)
**跟踪模板URL处理规则：**
- **不要**把用户输入的完整Amazon URL设置为跟踪模板
- Amazon URL中的maas/tag等追踪参数会自动提取为`final_url_suffix`
- **只有用户明确说"跟踪模板URL"时才设置tracking_template参数**
- 典型错误命令：`--tracking-template "https://www.amazon.com/dp/XXX?maas=..."` ❌
- 正确做法：不传`--tracking-template`参数，让URL参数自动进入suffix ✅

**RSA图片说明：**
- Responsive Search Ad在搜索网络不直接显示营销图片
- 图片主要用于展示网络广告和动态搜索广告
- 图片已正确上传并关联到广告组（资产库可见）

---

## 完成的工作

### 2026-03-13
- ✅ 本地AI硬件评测文章 (3,390词)
- ✅ 发布到my-blog并推送GitHub
- ✅ 超时配置改为1小时

---

## my-blog 工程结构 (2026-03-15)

### 目录结构
- **文章目录**: `src/data/post/` (注意不是 `content/posts/`)
- **配置文件**: `astro.config.ts`
- **部署配置**: `wrangler.toml` (Cloudflare Pages)

### URL 规则
- **文章链接**: `https://techruling.com/{文件名}` (无 `/posts/` 前缀)
- **分类页面**: `https://techruling.com/category/{category}`
- **标签页面**: `https://techruling.com/tag/{tag}`

### 文章 Frontmatter 必填字段
```yaml
---
title: "文章标题"
description: "SEO描述"
pubDate: "2026-03-15"
heroImage: "/blog-placeholder-1.jpg"
category: "分类"  # 见下方分类列表
tags: ["标签1", "标签2"]
affiliateCategory: "electronics"  # 联盟营销分类
---
```

### 可用分类 (Category)
- AI News, AI Tools, Apple, Audio, Computing, Gift, Mobile, Open Source, Other, Peripherals, Productivity, Product Reviews, SaaS, Smart Home, tutorial

### 联盟营销分类 (affiliateCategory)
- electronics, audio, etc.

---

## 归档记录

> 以下是已归档的历史记忆

(暂无 - 2026年3月)
