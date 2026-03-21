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
