---
name: archer-product-selector
description: Archer联盟平台选品技能。从Archer API筛选优质商品，结合Google Keyword Planner API获取真实搜索量和CPC数据，输出完整选品报告到飞书文档。触发词：Archer选品、筛选商品、从Archer选品、执行选品分析、帮我选品。
credentials:
  - Archer API 凭证（环境变量 ARCHER_USERNAME, ARCHER_PASSWORD）
  - Google Ads API 凭证（via autoads 配置，已有 developer_token + service_account_json）
env:
  required:
    - ARCHER_USERNAME
    - ARCHER_PASSWORD
  autoads_config: true
outputs:
  feishu_doc_url: "https://feishu.cn/docx/Ly7XdBWptoNWxVxMha3cwhLbn7f"
---

# Archer Product Selector Skill

从Archer联盟平台筛选优质商品，结合Google Keyword Planner API获取真实搜索量和CPC数据。

## 筛选条件

从Archer API 224,839个商品中按以下条件筛选：
1. **评论数 ≥ 500** — 有一定销量基础
2. **评分 ≥ 4.0** — 口碑良好
3. **有排名** — 在搜索结果中有排名
4. **有价格** — 价格有效

## 关键词提取规则

- **关键词1** = 品牌 + 产品类型（如 "RENPHO Foot Massager"）
- **关键词2** = 品牌 + 型号（如 "RENPHO Foot"）

## Google API 数据

通过 Google Keyword Planner API 获取：
- **搜索量/月** — 关键词月度搜索量
- **CPC** — 竞价范围（人民币元）

## 触发方式

- "帮我从Archer联盟选品"
- "执行Archer选品分析"
- "从Archer筛选一些商品"
- "运行选品脚本"

## 输出

选品报告自动发布到飞书文档：
https://feishu.cn/docx/Ly7XdBWptoNWxVxMha3cwhLbn7f

字段：ASIN、产品名称、评论数、star、品牌词、关键词、搜索量/月、CPC

## 核心脚本

### 方式1：Python模块调用（推荐）
```bash
cd /root/.openclaw/workspace/autoads
python3 -m src.archer_selector --run
```

### 方式2：Shell脚本
```bash
cd /root/.openclaw/workspace/autoads
bash scripts/run_archer_selector.sh
```

### 3. 直接运行
```bash
python3 /root/.openclaw/workspace/autoads/archer_selector_main.py --run
```

## 技术实现

### Step 1: Archer API获取商品
- 调用 Archer Products API 获取全量商品列表
- 字段：product_id, title, reviews, rating, price, rank, asin

### Step 2: Python筛选
- 过滤：reviews >= 500, rating >= 4.0, rank > 0, price > 0

### Step 3: 品牌/关键词提取
- AI语义分析提取品牌词
- 生成两种关键词组合

### Step 4: Google Keyword Planner查询
- 为每个商品查询关键词搜索量和CPC
- API：KeywordPlanIdeaService.generateKeywordIdeas

### Step 5: 去重+合并
- 按ASIN去重，取搜索量最大值
- 按搜索量降序排列

### Step 6: 飞书文档输出
- 更新飞书文档，包含完整53个商品数据