# keyword-metrics Skill

## 功能

**唯一职责**：调用 Google Keyword Planner (GKP) API 查量。接收调用方提供的种子关键词，返回 GKP 原始数据（未过滤）。

**本技能不负责：**
- ❌ 品牌识别
- ❌ 产品类型识别
- ❌ 关键词过滤
- ❌ 关键词分层
- ❌ ROI 估算

**调用方（小灰主对话）负责：**
- ✅ 从产品描述识别品牌 / 子系列 / 核心产品词
- ✅ 准备种子关键词
- ✅ 用 4 层 keyword_filter 过滤 GKP 返回结果
- ✅ 分层建议 + ROI 估算

## 铁律 11: AI 推理归属（2026-06-12 确立）

**凡涉及"语义理解/品牌识别/策略判断/文本生成/AI 推理"，统一由小灰（主对话）完成；技能/工具只负责"数据查询/API 调用/IO 操作"。**

判断边界：
- 理解 / 判断 / 生成 → 小灰
- 调用 API / 读写数据 → 工具

## 使用方法

```bash
# 接收调用方提供的种子词, GKP 查量
cd ~/.openclaw/workspace/skills/keyword-planner
python3 run_skill.py \
  --keywords "saris bones, saris bike, 2-bike trunk rack" \
  --ads-account 6660356395 \
  --output console

# 多关键词 (逗号分隔)
python3 run_skill.py \
  --keywords "saris bike, saris bones, 2-bike trunk rack, made in usa bike rack" \
  --ads-account 6660356395 \
  --output console

# 启用 gotrends.app fallback (429 时自动切换)
python3 run_skill.py \
  --keywords "saris bike, saris bones" \
  --ads-account 6660356395 \
  --use-fallback \
  --output console

# 输出到文件
python3 run_skill.py \
  --keywords "saris bike, saris bones" \
  --ads-account 6660356395 \
  --output file

# 输出到飞书文档
python3 run_skill.py \
  --keywords "saris bike, saris bones" \
  --ads-account 6660356395 \
  --output feishu
```

## 参数

| 参数 | 必填 | 说明 |
|------|-----|------|
| --keywords | 是 | 种子关键词（多个用逗号分隔，调用方已识别品牌/子系列） |
| --ads-account | 是 | Google Ads 账户 ID |
| --months | 否 | 历史数据月份范围（默认 3 个月） |
| --use-fallback | 否 | 启用 gotrends.app fallback (429 时切换) |
| --output | 是 | console / file / feishu |
| --page-size | 否 | 每个种子词生成的最大关键词数 (默认 100) |

## 输出格式

表格形式呈现，包含列：
- Keyword（关键词）
- Avg Monthly Searches（月均搜索量）
- Competition（竞争程度：LOW / MEDIUM / HIGH）
- CPC Low（最低 CPC，单位：美元）
- CPC High（最高 CPC，单位：美元）
- CPC Average（CPC 平均值，单位：美元）

## 典型调用工作流

```
小灰（AI 推理）:
  1. 看到产品描述 "Saris Bones EX 2-Bike Trunk Rack..."
  2. 识别品牌 = Saris, 子系列 = Bones
  3. 准备种子词: ["saris bike", "saris bones", "saris bones ex", "2-bike trunk rack"]

小灰（调用工具）:
  $ python3 run_skill.py --keywords "saris bike, saris bones, saris bones ex, 2-bike trunk rack" --ads-account 6660356395

keyword-metrics（数据查询）:
  → 调用 GKP, 返回 100 关键词 + 搜索量 + CPC

小灰（AI 推理 + 过滤）:
  → 用 4 层 keyword_filter 过滤掉 "bones and all" 等垃圾词
  → 输出分层建议 + ROI 估算
```

## 注意

- 搜索量地域默认美国 (US)
- 语言默认英语 (en)
- 默认调用间隔 2 秒，避免触发 429
- fallback 会在 Google 被限流后自动重试 gotrends.app
- 特殊字符 (`°` / `&` / `,` 等) 需调用方预处理（6/11 教训）

## 历史

- **2026-06-12**: 重构为 keyword-metrics，删除 AI 推理模块，确立铁律 11（AI 推理归属小灰）
- **2026-06-04**: 429 fallback + 调用间隔控制
- **2026-06-03**: 初始版本
