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

## 🔴 全局反硬编码铁律 (2026-06-06)

**【最高优先级】禁止任何形式的硬编码fallback**

### 1. 绝对禁止的硬编码
- ❌ 硬编码ASIN / 产品URL（如 `B0DFF7SSMW`、`B0DYC8NQ5K`）
- ❌ 硬编码产品名称/品牌名（如 `JoyBerri Trampoline`）
- ❌ 硬编码headlines/description（如 `["JoyBerri Trampoline"]`、`["Best trampoline for backyard"]`）
- ❌ 硬编码产品变体（如 `f"open goal soccer"`、`f"goaaal soccer net"`）
- ❌ 硬编码产品类型判断（如 `if 'goaaal' in brand_lower or 'goal' in brand_lower`）
- ❌ 硬编码同品牌其他产品线（SHOKZ的Xtrainerz、OpenRun、Aeropex等不能当作变体使用）

### 2. fallback必须遵守的原则
- **报错优先**：如果必要信息缺失，直接报错让用户补充，而不是fallback
- **AI生成**：所有文案、变体、关键词必须由AI从传入的参数生成
- **从现有资源复制**：存量广告系列补充分层时，广告内容必须从Campaign现有的广告中复制
- **AI语义识别**：产品线过滤、竞品识别等由AI语义判断，禁止硬编码品牌名检查

### 3. 存量广告系列补充分层场景的完整原则
- **不传URL**：用户调用 `--campaign-id` 时不传URL
- **广告内容100%复制现有**：从该Campaign的Main广告组提取headlines/description/URL/suffix
- **品牌名从ad_content提取**：从广告内容中AI语义识别品牌，禁止作为参数硬编码
- **核心关键词从产品描述生成**：用户必须提供产品描述，AI生成核心产品词
- **产品线过滤**：AI判断同品牌其他产品线（Xtrainerz/OpenRun/Aeropex等）应DROP

### 4. 错误案例（2026-06-06 SHOKZ L0事件）
- 5个新建L0广告组使用了蹦床产品URL (`B0DFF7SSMW` = JoyBerri Trampoline) → 展示耳机广告
- L0关键词包含 `Shokz Openrun` / `Aftershokz Xtrainerz` / `Shokz Aeropex` → 同品牌其他产品线污染
- 原因：run_skill.py:391-396 硬编码了AdContent fallback (JoyBerri Trampoline + B0DFF7SSMW)
- 修复：fallback改为报错；AI提示词加强产品线过滤；删除所有硬编码产品变体

### 5. 验证检查命令
```bash
# 查找所有硬编码的ASIN/品牌
grep -nE "B0[A-Z0-9]{8}|goaaal|JoyBerri|Trampoline" \
  /root/.openclaw/workspace/autoads/src/*.py \
  /root/.openclaw/workspace/skills/refined-ads/*.py

# 期望结果：(no output)
```

### 6. 关键词 4 层过滤架构 (2026-06-07 新增)

**【背景】** 避免硬编码+让产品定义变更可复用,autoads 创建普通广告系列时使用 4 层过滤流水线。

**【新文件】** `autoads/src/keyword_filter.py` (UniversalKeywordFilter 类)

| 层 | 名称 | 职责 | 实现方式 |
|---|---|---|---|
| Layer 1 | 竞品识别 | 只识别**品牌层面**竞品 (其他品牌 + 同品牌不同产品线) | AI 语义 (不硬编码品牌) |
| Layer 2 | Amazon 平台过滤 | 精确字符串匹配 'amazon' 作为完整词或前缀 (产品名+amazon → KEEP) | 字符串 (严格精确) |
| Layer 3 | 产品相关性 | 识别关键词是否与主产品同义/相关 (变体/不同品类/通用词 → DROP) | AI 语义 (不硬编码产品词) |
| Layer 4 | 品牌层 (L0/L1 专用) | 仅保留品牌词 (精细化广告组 L0/L1 层使用) | AI 语义 |

**【调用模式】**
- **普通广告系列**: `filter_for_standard_campaign(keywords, product_description, brand)` → Layer 1+2+3
  - 保留范围: 品牌词 + 核心产品词 + 相同产品含义的长尾词
- **精细化 L0/L1 层**: `filter_for_brand_layer(keywords, product_description, brand)` → Layer 1+2+4
  - 保留范围: 仅品牌词
- **精细化程序独立**: `skills/refined-ads/run_skill.py` 的 `_ai_filter_l0_keywords` 和 `autoads/src/refined_campaign_creator.py` 的 L1 Brand 过滤未改动,本模块不覆盖

**【关键设计原则】**
- 缺信息即报错 (不静默fallback), `KeywordFilterError` 抛出
- 4 层各司其职, 互不重叠 (Layer 1 只管品牌, 不管变体/品类)
- 所有 AI 提示词基于"通用规则"而非硬编码 (如"使用同一原则判断任何品牌")
- Layer 2 "精确匹配" = 整体==amazon 或以 "amazon "/amazon./amazon's 开头; "amazon basics" / "amazonbasics" 视为Amazon自家品牌DROP
- "产品名+amazon" (如 "soccer goal amazon") KEEP — 客户有在amazon购买意图
- 测试场景: Open Goaaal 24x8ft 户外足球门, 42 测试关键词, 4 层最终保留 15 个 (品牌3 + 核心6 + 长尾3 + 产品+amazon 2 + 通用+产品 1), 完全符合预期

**【兼容性】**
- `ad_researcher.py` 的 `_ai_filter_brand_relevance` 和 `_filter_competitor_keywords` 保留 (带 DeprecationWarning), 内部转发到新模块
- `_generate_keywords` 内部已重写为调用 `filter_for_standard_campaign`
- 旧的 `filter_amazon_keywords` / `filter_generic_keywords` 内嵌函数 + `GENERIC_KEYWORDS` 硬编码黑名单 已彻底删除

**【验证】** Open Goaaal 端到端测试通过: 42 关键词 → Layer1 移除 12 竞品 → Layer2 移除 3 amazon → Layer3 移除 12 变体/品类/通用 → KEEP 15 合格关键词

## 🔴 故障即文档元规则 (2026-06-07 确立)

**【背景】** David 反复强调这是最高阶元规则, 与"全局反硬编码铁律"互为补充。

### 1. 故障即文档工作流 (每次 AI 误判时执行)

1. David 提出具体误判问题
2. AI **不**改硬编码字符串匹配来掩盖问题
3. AI **不**fallback 到全保留
4. AI **定位提示词哪条规则没说清** → 用**通用例子**补充规则 → 下次同类误判自然避免

### 2. 提示词通用性原则 (写提示词时遵守)

- ✅ **可以用例子**说明规则 (让 AI 理解边界) — 例子是**抽象类别**, 如 `[main product type]`、`[category]`、`X` 占位符
- ❌ **不硬编码产品信息** — 不能写 "Open Goaaal"、"SHOKZ"、"photo printer"、"soccer goal" 等任何具体产品名/品牌名
- 提示词必须适用于**任何产品** (不限品类/品牌)

### 3. 验收检查命令

```bash
# 扫描所有提示词模块是否有硬编码产品信息
grep -nE "Open Goaaal|SHOKZ|Shockz|Shoks|Aftershokz|KODAK|Bose|24x8|24 feet|soccer goal|soccer ball|photo printer|trampoline|open ear" \
  /root/.openclaw/workspace/autoads/src/keyword_filter.py

# 期望输出: 空白 (或仅命中通用形容词如 pop-up/portable/foldable - 这些是变体描述词,不是产品名)
```

### 4. 故障案例 - 2026-06-07 首次应用

**【故障】** 提交 fc83589 后, David 复查发现 4 层提示词硬编码了具体产品信息:
- Layer 1: "Open Goaaal soccer goal 24x8ft outdoor" / "KODAK photo printer" / "Bose QuietComfort 45"
- Layer 3: "24x8 ft full-size outdoor soccer goal" / "soccer ball vs soccer goal"
- Layer 4: "Shockz"/"Shoks"/"Aftershokz" 作为 SHOKZ 变体例子

**【规则没说清】** "提示词必须适用于所有产品" 原则未遵守 — 提示词中不能有具体产品名/品牌名

**【修正】** 全部替换为通用占位符:
- `[main product type]` / `[category]` / `X` / `{brand}` 作为参数占位符
- 变体描述保留通用形容词 ("pop-up"/"portable"/"foldable"/"collapsible"/"mini") — 这些是品类通用词,非产品名
- Layer 1/3/4 提示词顶部加 **NOTE ON EXAMPLES** 元说明, 告诉 AI "examples are abstract categories, not specific products"

**【验证】** 10 个关键回归测试用例全部通过, KEEP/DROP 行为与硬编码版本完全一致

## 🔴 CLI 工具 nargs 陷阱铁律 (2026-06-07 确立)

**【背景】** 修复 `scripts/search_term_negatives.py` 时的真实损失, 与"全局反硬编码铁律"+"故障即文档元规则"并列。

### 1. 铁律

**任何接收"列表型用户输入"的 CLI 参数, 禁止用 `nargs='+'` + 空格作为分隔符。** 必须改用 `type=str` + 内部解析不会与"项内容"冲突的字符(逗号/换行/Tab等)。

### 2. 陷阱原理

`nargs='+'` 让 argparse 按**空格**拆分用户输入为多个值。但当"项本身"包含空格(如多词短语 `"zevo flying insect trap"`)时, 程序分不清:
- 哪些空格是"项之间"的(应该拆)
- 哪些空格是"项内部"的(不应该拆)

结果: 多词短语被错误拆成单词, 单词级否定词(`flying`/`insect`/`fly`)误伤自家产品词。

### 3. 修复模板(适用于所有列表型 CLI 参数)

```python
# ❌ 错误(陷阱)
parser.add_argument('--add', type=str, nargs='+', help='添加否定词(空格分隔)')

# ✅ 正确(修复)
parser.add_argument('--add', type=str, default=None,
                  help='添加否定词(逗号/换行 分隔;空格不在分隔符集)')
parser.add_argument('--add-from-file', type=str, default=None,
                  help='从文件读取(每行一个,# 开头为注释)')

# 内部统一解析函数
def parse_list_input(text: str) -> List[str]:
    """逗号/换行 分隔, 不拆分空格, 去重+保序"""
    if not text or not text.strip():
        return []
    items = re.split(r'[,\n]+', text.strip())
    seen = set()
    result = []
    for item in items:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
```

### 4. 配套原则: 生成侧 & 输入侧必须用同一套规则

- **AI 在会话中输出列表** → 用统一的文本格式(每行一个, 代码块包裹)
- **用户从代码块复制** → 粘贴到 `--add "..."` → CLI 内部用相同解析函数
- **文件** → `--add-from-file` 走另一路径但用同一种"每行一个"格式

**保证**: 无论用户从哪种入口输入, 都走同一个 `parse_list_input()`, 避免"AI 输出格式 ≠ CLI 接收格式"的不一致。

### 5. 错误案例 (2026-06-07 真实损失)

**【场景】** 向 Campaign 23806773800 (Flowtron bug zapper) 添加 33 个否定词

**【命令】**
```bash
python3 search_term_negatives.py --add zevo flying insect trap raid fly trap raid fogger wondercide ...
```

**【错误结果】** argparse 把未加引号的 4 词短语拆成 4 个单词:
- `zevo` ✅ 单词 OK
- `flying` ❌ 过宽
- `insect` ❌ 误伤 "flowtron electronic **insect** killer"
- `trap` ❌ 过宽
- `raid` / `fly` ❌ 过宽
- `fogger` (基本无害)

**【损失】** 5 个过宽单词级否定词被错误添加, 3 个复合短语(`zevo flying insect trap`/`raid fly trap`/`raid fogger`)未被正确添加。

**【修复 Commit】** `889c2e3 fix(search_term_negatives): 停止按空格拆分否定词,改用逗号/换行分隔符`

### 6. 验收检查命令

```bash
# 扫描所有 CLI 工具, 查找危险的 nargs='+' + help='空格分隔' 组合
grep -rnE "nargs='\+'\s*[,)]|nargs=\"\+\"\s*[,)]" /root/.openclaw/workspace/scripts/ /root/.openclaw/workspace/autoads/scripts/ 2>/dev/null | grep -iE "add|negativ|list|items|words" | head -20

# 期望: (无输出) 或每个命中都有明确说明"已修复/有特殊原因"
```

### 7. 已应用修复的工具

| 工具 | 修复 Commit | 验证状态 |
|---|---|---|
| `scripts/search_term_negatives.py` | `889c2e3` | ✅ 12 个解析测试通过 + EVIQO 实测通过 |

## 第十一铁律: AI 推理归属 (2026-06-12 09:57 确立)

**【最高优先级】凡涉及「语义理解/品牌识别/策略判断/文本生成/AI 推理」，统一由小灰（主对话）完成；技能/工具只负责「数据查询/API 调用/IO 操作」。**

### 1. 判断边界
- **理解 / 判断 / 生成** → 小灰（主对话）
- **调用 API / 读写数据** → 工具/技能

### 2. 铁律确立根因 (2026-06-12 08:30-09:00 BJT)
- David 测试 Saris Bones EX 产品, 让 keyword-planner 技能查搜索量
- 技能返回结果把 "Bones"/"Bike"/"Trunk"/"Rack" 都当成"品牌词"
- 后续小灰分析时正确识别 "Saris" 才是品牌, "Bones" 是产品系列
- **同一产品, 两种 AI 推理, 表现差距巨大**:
  - keyword-planner 内置 AI: 看到大写名词就抽, 上下文缺失
  - 小灰 (主对话): 有世界知识 + MEMORY + 反例校验 + 多步推理

### 3. keyword-planner 错误实现根因
- `extract_brand_candidates()`: 纯规则, 把所有大写名词当品牌候选
- `extract_product_types()`: 硬编码产品类型列表 (PIURIFY/KODAK/Bose 等)
- `AI_EXTRACT_PROMPT`: 任务粒度太粗, 没有反例校验机制
- **核心问题**: 单一职责违反 - 数据查询工具塞了 AI 推理, 上下文丢失

### 4. 重构方案 (2026-06-12 David 拍板 D 方案)
**keyword-planner 拆为两层**:
1. **keyword-metrics (本技能, 纯数据查询)**: 接收调用方预定义的种子词, 调 GKP 查量
2. **小灰主对话 (AI 推理层)**: 品牌识别 / 种子词生成 / 4 层过滤 / 分层建议 / ROI 估算

### 5. keyword-metrics 重构要点
- 删除 `extract_brand_candidates` / `extract_product_types` / `extract_keywords_local` / `extract_keywords_categorized` / `AI_EXTRACT_PROMPT` / `analyze` 命令
- 删除 `--product-description` / `--url` 参数
- 唯一输入: `--keywords` (调用方预定义的种子词)
- 唯一职责: GKP 查量

### 6. 调用工作流 (新)
```
小灰(AI 推理):  看到产品描述
  → 识别品牌/子系列
  → 准备种子词 (例: "saris bike, saris bones, 2-bike trunk rack")

小灰(调用工具):  python3 run_skill.py --keywords "..." --ads-account 666...

keyword-metrics:  GKP 查量 → 返回 100 关键词 + 搜索量 + CPC (未过滤)

小灰(AI 推理):  4 层 keyword_filter 过滤 → 分层建议 + ROI 估算
```

### 7. 特例豁免
自动化场景 (cron 任务) 需要"无 AI 推理"的兜底实现:
- 4 层 keyword_filter 已成熟, 不依赖 LLM, 可直接用于 cron
- 品牌识别需预先生成 seed 列表 (数据库/配置文件)
- 不要在 cron 任务里调 LLM 推理 (6/11 ROI 虚假成功教训)

### 8. 教训 (2026-06-12)
- **把 AI 推理塞进工具 = 上下文丢失 + 单一职责违反**
- **AI 推理必须在能拿到完整上下文的地方**: 也就是主对话
- **"在工具里写 AI 提示词" 和 "在主对话里推理" 是两种不同的能力, 表现差异巨大**
- **设计原则**: 工具 = 数据, 主对话 = 智能, 两者分离

### 9. 验收检查命令
```bash
# 查找所有"工具内 AI 推理"违规
grep -rnE "AI_EXTRACT_PROMPT|extract_brand_candidates|extract_product_types" \
  /root/.openclaw/workspace/skills/ /root/.openclaw/workspace/autoads/src/ 2>/dev/null

# 期望: 无输出 (或每个命中都有明确豁免说明)
```

## 第十七铁律: 硬过滤 + AI 100% 复审架构原则 (2026-06-13 16:06 BJT 确立, David 拍板)

**【背景】** 2026-06-13 一天跑完 15 个产品 (PB 6 + Yeah 9 + Archer 3) / 314 词 / $1,500+ 花费, 完整验证从"硬过滤 + AI 复审"架构 vs "旧 if-then 字符串规则" 的准确率差距。

**【架构原则】** 
- 搜索词分析 = 「**硬过滤(防 100% 错误) + AI 100% 复审(做语义裁判)**」二段式架构
- **硬过滤 = 工程实现细节, 不算铁律** (可改清单/可加词/可减词)
- **AI 100% 复审架构 = 铁律** (普适设计哲学, 与第十一铁律同等级)

**【实证数据: 15 个产品 / 314 词对比】**

| 维度 | 旧 if-then 字符串规则 | 新硬过滤 + AI 100% 复审 |
|---|---|---|
| 误伤数 | **9 个** (C3 Anker Laptop Power Bank) | **0** |
| 漏标数 | 42 个 (规则 0 标不相关, AI 找出 42 个) | **0** (全靠 AI 找出) |
| 总错判率 | **15.7%** | **0%** |
| AI 找出真不相关词 | 0 / 56 = 0% | **56 / 56 = 100%** |
| 跨产品普适性 | 差 (N² 增长, 新边界 case 修不完) | 好 (硬过滤 12 词跨产品通用, AI 推理自适应) |

**【铁律三大原则 (David 拍板)】**

1. **硬过滤只能用于「亚马逊平台词」** (Amazon 平台 + 国家/地区变体)
   - 12 词清单 (EXACT 精确匹配, 不能用 PHRASE 会误伤 "amazon + 产品" KEEP 原则)
   - 清单在 `scripts/search_term_negatives.py: HARDFILTER_AMAZON_PLATFORM_TERMS` 权威定义
   - 通过 `scripts/add_amazon_hardfilter.py` 加到 3 账号 account-level 共享列表 (3×12=36 个, 幂等)
   - 硬过滤命中的标"不相关 - Amazon 平台词", AI 不用再看
   - 硬过滤不是铁律, 清单可改 (以后 Amazon 出新平台词随时加)

2. **AI 100% 复审做裁判 (这是铁律的核心)**
   - 在主对话做 (第十一铁律一致性: 工具不带 AI 推理)
   - 拿到 product_context (brand + product_type + product_name)
   - 逐个搜索词做语义判断, 输出 "DROP + 7 类理由"
   - 用户拍板后批量加词

3. **不再做 (这些由 AI 在主对话做, 工具不处理)**
   - 产品类型漂移 (printer/laptop/tv) 
   - 竞品品牌检测
   - 单字过宽词
   - 同品牌不同产品线
   - 品牌误拼
   - 西语/日语/德语意图查询
   - 零售商/平台词 (除 Amazon 平台词硬过滤)

**【架构示例】** (今天 6/13 全程)
```
搜索词 (N 个)
  ↓
[硬过滤: 12 Amazon 平台词 EXACT 匹配] → 命中 → "不相关 (Amazon 平台词)"
  ↓ 未命中
[AI 100% 复审] → 主对话推理 → "KEEP / DROP + 7 类理由"
  ↓
[用户拍板]
  ↓
[批量加词脚本: scripts/add_phrase_negatives.sh]
```

**【C3 Anker Laptop Power Bank 误伤案例作为反面教材】**
- 旧规则机械匹配 `laptop` 字符串 → 误判 9 个 "laptop power bank" / "portable laptop charger" 不相关
- 实际我们卖的就是 Laptop Power Bank, 这 9 个是核心搜索词
- 验证了: 字符串规则无法处理"产品名 = 品类词"的情况, 必须靠 AI 推理

**【今天 6/13 数据全貌】**

| 账号 | 产品 | 词 | AI 真不相关 | 已加 PHRASE 否定词 |
|---|---|---|---|---|
| PB (4772859239) | 6 | 89 | 16 | 15 |
| Yeah (6052559425) | 9 | 158 | 26 | 5 |
| Archer (6660356395) | 3 (top 3) | 67 | 7 | 7 |
| **合计** | **15** | **314** | **49** | **27** |

**【硬过滤 + AI 复审 与第十一铁律的协同】**
- 第十一铁律: AI 推理在主对话做, 工具只做 IO
- 第十七铁律: 搜索词分析用"硬过滤 + AI 100% 复审"架构
- 两者一致: 硬过滤是纯字符串 EXACT 匹配 (无 AI), AI 复审 100% 在主对话
- search_term_negatives.py 内部不做任何 AI 推理, 只调 GKP API + 写文件

**【6/13 C1 INTEX 修正案例 + 否定词判定铁律 (2026-06-13 16:33 BJT David 拍板)】**

**【案例】** C1 INTEX Ultra XTR (23931014140) 我在 AI 复审中误加 3 个 PHRASE 否定词:
- `intex ultra xtr 18x52` (实际是 18x9x52 省略中间 9)
- `intex ultra xtr 14x48` (可能省略某数字,或者 14x48 是另一型号)
- `pools for sale 18 x 52` (可能是 18x9x52 矩形,用户没打全)

**【David 纠正】** 
- 搜索词匹配原理: **Google Ads 是模糊匹配, 用户输入的词只要包含我们关键词的一部分, 也能匹配上**
- 人的搜索习惯: **懒**, 会省略/缩写/打字错误
- "搜索意图相同" > "搜索词字面不同"

**【否定词判定铁律 (David 拍板)】**

**判定否定词前, 必想:**
1. **"这个人的真实搜索意图是什么?"** (不是"这个词字面是什么")
2. **"他/她为什么会这么搜?"** (打字懒 / 找变体 / 找竞品 / 不确定)
3. **"这个意图跟我们的产品意图相同吗?"** (高意图/低意图/不相关)
4. **"意图相同的可能性 > 不同的可能性, 就不能加否定词"** (优先让 Google Ads 模糊匹配处理)

**【反面教材: 我今天 6/13 16:08 误加的 3 词】**
- 表面看: "18x52" / "14x48" / "18 x 52" 跟 18x9x52 矩形不同
- 实际: 省略/懒打字的概率 >> 找其他型号的概率
- **"型号不同" 不等于 "意图不同"** —— 型号可能用户没打完
- 正确判断: KEEP, 让 Google Ads 模糊匹配 18x9x52 的关键词

**【16:33 后修正动作】** 通过 CampaignCriterionService 移除 3 词:
- 资源名格式: `customers/{cid}/campaignCriteria/{cid}~{crit_id}` (用波浪号, 不是斜杠)
- Operation: `op.remove = "..."` (直接字符串, 不是 message)
- 通过 criterion_id 精确移除
- 验证: 验证查询确认 3 词已不在否定词列表

**【与其他铁律的协同】**
- 第十一铁律 (AI 推理归属): AI 推理在主对话做, 不在工具里
- 第十七铁律 (硬过滤 + AI 100% 复审架构): AI 复审要"思考人类搜索意图", 不只是字面匹配
- 两者结合: AI 复审 = "字面分析 + 搜索意图 + 搜索习惯" 三维度判断

**【铁律 18 草案 (保留为草案)】**

**【手动触发架构, 不考虑 Cron】**
- David 明确: 以后都是手动触发
- 不需要 fallback / 不需要 keyword_filter 兜底
- search_term_negatives.py 只跑 GKP + 写 JSON, AI 复审在主对话, 加词脚本手动跑

**【6/13 已落地工程产物】**
- `scripts/search_term_negatives.py`: `analyze_with_rules` 重写为硬过滤, 签名简化为 `(search_terms)` 去掉 campaign_name
- `scripts/add_amazon_hardfilter.py`: 通用化, 动态查 shared_set ID, 支持 `--customer-ids` / `--terms` / `--dry-run` 参数
- `scripts/add_phrase_negatives.sh`: 通用批量加 PHRASE 否定词模板, 内嵌 PB 实战
- 3 账号 account-level 共享列表: 36 个 Amazon 平台词硬过滤 (3×12)

**【验证检查命令】**
```bash
# 1. 跑硬过滤回归测试 (新硬过滤 = 12 词 EXACT)
python3 -c "import sys; sys.path.insert(0, '/root/.openclaw/workspace/scripts')
import importlib.util
spec = importlib.util.spec_from_file_location('stn', '/root/.openclaw/workspace/scripts/search_term_negatives.py')
stn = importlib.util.module_from_spec(spec); spec.loader.exec_module(stn)
print(f'硬过滤词: {len(stn.HARDFILTER_AMAZON_PLATFORM_TERMS)} 词 (预期 12)')"

# 2. 验证 3 账号账号级硬过滤 (应 222/131/222)
python3 /root/.openclaw/workspace/scripts/add_amazon_hardfilter.py --dry-run
```

## L0/L1 分层定义 (2026-06-12 13:13 BJT 修正)

**【背景】** 之前 L0 命名有错: 把"裸品牌名"当 L0 是不对的。L0 应该是"品牌+精确型号"，否则流量不精准。

### 1. 修正后的分层定义 (David 13:13 BJT 拍板)

| 层 | 含义 | 例子 (ZAFRO 14K BTU) | 例子 (Saris Bones EX) | 投放逻辑 |
|---|---|---|---|---|
| **L0** | 品牌+精确型号 | `zafro 14000 btu portable air conditioner` | `saris bones ex 2-bike trunk rack` | 最高竞价, 最高转化 |
| **L1** | 品牌+产品类别 | `zafro portable air conditioner` | `saris bike rack` | 中竞价, 品牌品类 |
| **L1_brand** | 裸品牌名(兑底) | `zafro` | `saris` | 低竞价, 捕获品牌泛搜 |
| **L2** | 行业品类大词 | `14000 btu portable ac` | `2-bike trunk rack` | 中竞价, 品类流量 |
| **L3** | 竞品词 | `lg lp1419ivsm`, `midea duo` | `thule easyfold`, `allen sports` | 低竞价, 需 brand 词排除 |
| **L5** | 长尾/特性词 | `ultra quiet portable ac`, `drainage free portable ac` | `rust-free trunk rack` | 低竞价, 长尾补充 |

### 2. ZAFRO 实测 (修正后)

| 关键词 | 实际月搜 | 正确层 | 修正前错误层 |
|---|---|---|---|
| `zafro 14000 btu portable air conditioner` | 10 | **L0** | L0  |
| `zafro portable air conditioner` | **1,900** | **L1** | L0  ← 错位 |
| `zafro` | 390 | **L1_brand** | L0  ← 错位 |
| `14000 btu portable ac` | 6,600 | L2 | L2  |
| `ultra quiet portable ac` | 170 | L5 | L5  |

**关键发现：L1 才是主流量词 (1,900/月)，L0 是精准但低量 (10/月)。分层需要 L0 配合 L1 一起投。**

### 3. 修正后的工程实现

**`autoads/src/brand_extractor.py` 新增 `layer` 子命令**:
```bash
# L0 精确型号层
python3 brand_extractor.py layer --layer L0 --brand ZAFRO --subseries "14,000 BTU" --product-type "portable air conditioner"

# L1 品牌品类层
python3 brand_extractor.py layer --layer L1 --brand ZAFRO --product-type "portable air conditioner" --product-abbrev "portable ac"

# L1_brand 兑底层
python3 brand_extractor.py layer --layer L1_brand --brand ZAFRO
```

**特殊字符自动过滤 (6/11 教训)**:
- `ZAFRO 14,000 BTU` 舍逗号 → `ZAFRO 14000 btu` (GKP 可接收)
- 14,000 BTU 的 逗号 被 validate_seeds 拦截

### 4. 修正前的错误记忆 (避免重复)

**错误**：L0 = 裸品牌名 (例: `zafro`, `saris`)
**原因**：误以为 L0 是"最高优先级品牌词"，但忽略了"品牌下可能有多个子品牌/产品线/型号"
**修正**：L0 = 品牌+精确型号 (锁定具体产品)；L1 = 品牌+产品类别；L1_brand = 裸品牌

**铁律11 项目**：`build_seed_keywords` (旧) → `build_seed_keywords_for_layer(..., layer=...)` (新)

### 5. 验证

- ZAFRO 案例: L0 `ZAFRO 14000 btu portable air conditioner` 10/月/CPC $5.72 (L0 实际是低量精准词)
- ZAFRO 案例: L1 `ZAFRO portable air conditioner` 1,900/月/CPC $5.72 (L1 才是主流量)
- Saris Bones EX 案例: 验证 L0 = `saris bones ex 2-bike trunk rack` (待补查)
- 实际意义: 营销资源在 L1 (高量) + L0 (精准) 双层, L1_brand 兑底

## V3 改造成与回退记录 (2026-06-07 4轮实验)

### 背景

David 2026-06-07 提出深层元规则: **AI 不能依赖预训练知识, 只应根据传入的 product_description + brand 做判断**。AI 输出波动是独立变量。

我据此设计 3 个版本, 跑 2 产品 × 多次重复实验。

### 4 轮实验结果 (Layer 3 提示词, 跑 2 产品 × 3 次重复 = 6 次 AI 调用/版本)

| 版本 | Open Goaaal | KODAK Step | 平均 | 跨产品波动 | 评估 |
|---|---|---|---|---|---|
| **V1 硬编码 + 丰富描述** | **93.3% (93-93)** | **96.1% (94-100)** | **94.7%** | 2.8% | **最佳, 采纳** |
| V2 全禁预训练 + 特征对比 | 53.3% (53-53) | 52.9% (53-53) | 53.1% | 0.4% | 走极端, 全部误判品牌词 |
| V3 温和 TRUST 政策 | 84.4% (53-100) | 52.9% (53-53) | 68.7% | 31.5% | 受伤不浅 |
| V4 抽象占位符 + 丰富描述 (无政策) | 84.4% (53-100) | 84.3% (53-100) | 84.4% | 0.1% | 有冷启动, 跳不稳定 |

### 关键发现

1. **V2 走极端** (全禁预训练 + Step1/2/3 特征对比) → 系统性伤害品牌词识别 (KODAK case 52.9% 稳定 3 次)
2. **V3 走中间** (TRUST PRODUCT_DESCRIPTION 政策) → 部分场景伤害 (Open Goaaal 波动, KODAK 稳定 52.9%)
3. **V4 抽象占位符** → 有冷启动 (第 1 次跳不稳, 第 2-3 次才稳定到 100%)
4. **V1 硬编码** → 第一次就稳定, 跨产品最均匀

### 4 层架构最终选择 (V1)

保留: V1 提示词原貌 (f4b2afd 提交后)
- 取消 V3 加的 TRUST PRODUCT_DESCRIPTION 政策声明 (在 Layer 1/3/4 都加了又删)
- 保留 Layer 3 里 "If product_description explicitly says 'NOT [variant]', trust that" 这条不冲突的规则
- 决定不进一步改造, V1 提示词已足够好 (94.7% 平均准确率, 跨产品波动 2.8%)

## V5 精准化升级 (2026-06-07 12:05 响应 David 指示)

### David 准确目标表述

David 指出: **"目标还是要保留和传入的产品名称，品牌名称，产品品牌型号含义相同的关键词，去掉不相关的，这需要ai语义理解，不完全依赖预训练知识"**

关键词是"含义相同"——比 V1 的"same core meaning/use"更精准。

### V5 实验数据 (2 产品 × 3 次重复)

| 提示词 | Open Goaaal | KODAK Step | 平均 |
|---|---|---|---|
| V1 简洁 | 68.9% | 68.6% | 68.8% |
| **V5 含义相同** | 68.9% | **84.3%** | **76.6%** |
| 差异 | 0 | +15.7% | +7.8% |

V5 在 KODAK 上显著优于 V1, 在 Open Goaaal 上持平。

### V5 提示词设计亮点

1. **TASK 明确为"含义相同"**: "Does this keyword have the SAME MEANING as the product name/brand/model in product_description?"
2. **双盲互换测试原理**: "Two keywords have the same meaning if a user wanting one would be equally satisfied with the other"
3. **DROP 规则分 6 类** (V1 是 4 类): 加了 "Different brand" 和 "Same brand but different product line"
4. **同品牌不同产品线明确化**: e.g., "[brand] photo printer" vs "[brand] camera" (同品牌但不同产品线) → DROP

### 生产版采用 V5

Layer 3 提示词从 V1 升级为 V5。
- 10 个关键回归测试全部通过
- V5 跟 David 12:05 表述的目标精准对齐

## 广告素材 rating/reviews_count Bug 修复 (2026-06-07 12:15)

### David 报告

创建普通广告系列时, headlines 出现两个问题:
1. "21K+ Happy Customers" - 是默认值, 不是传入参数
2. "500 Reviews 43 Stars" - 43 Stars 应该是 4.3 Stars, 传入参数是 4.3

### 根因 (3 个 Bug)

1. **main.py 不传 rating/reviews_count**: `researcher.research()` 调用时只传 product_description/product_url/brand_name 等, **没传 product_rating 和 product_reviews_count** (这两个参数接口存在但未被使用)
   - main.py 把 rating 塞进 product_description 文本 "Rating: 4.3/5 (500 reviews)", AI 从文本中无法精确抽取

2. **ad_researcher.py prompt 有硬编码默认值**: 第 482 行 "Examples: '21K+ Happy Customers', '4.6 Stars Rated'" - "21K" 和 "4.6" 是**例子数值**, AI 看到后误以为是参考值, 直接套用作为默认
   - 修复: 改为抽象占位符 + 明确指令 "If 'PRODUCT RATING' is provided, you MUST use that EXACT rating"

3. **policy_filter.py 丢了小数点** - 这才是 "43 Stars" 真正原因!
   - `normalize_to_title_case` 函数: 对每个 word, 先 `clean_word = ''.join(c for c in word if c.isalnum())` 去掉小数点
   - `clean_word = "43"` (原 word="4.3")
   - 后续 `result.append(clean_word.capitalize())` 用的是 "43" 而不是 "4.3"
   - AI 正确生成 "4.3 Stars Rated" → 被规范化丢小数点 → "43 Stars Rated"

### 修复

1. **ad_researcher.py prompt**: 移除"21K"和"4.6"硬编码, 改为抽象占位符 + "USE EXACT PASSED-IN VALUES" 明确指示
2. **main.py**: 显式传 `product_rating` 和 `product_reviews_count` 给 `researcher.research()` (从 Decodo 提取的 amazon_info 中取)
3. **ad_researcher.py _generate_keywords**: 新增 brand_name 参数透传 (供 4 层 filter 用)
4. **policy_filter.py normalize_to_title_case**: 特殊处理 `^\d+\.\d+$` 模式, 保留原 word 不去小数点

### 验证

端到端测试 (Bose QC45, rating=4.3, reviews=500):
- H4: "4.3 Stars Rated by 500" ✓
- H5: "500 Happy Customers" ✓
- H6: "Trusted by 500 Reviewers" ✓
- Issues: 0 (没出现 "43 Stars" 或 "21K")

8 个 keyword_filter 回归测试全部通过

### 教训 (2026-06-07)

- 同一个 bug 有 3 层原因叠加: (1) main.py 不传参 (2) prompt 硬编码默认值 (3) 规范化函数丢小数点
- **不能只修一层** - 修 1 和 2 不够, 3 是真正导火索
- 之前的 MEMORY 记录里 David 提过"Star 数应该是 4.0 而不是 46", 这次发现是"43" 而不是 "46" - 同一个问题换了形式

### 元规则更新 (2026-06-07)

**【核心发现】AI 提示词 "加约束指令" 可能伤害稳定性**

**【设计原则】**
- AI 接到 "IGNORE pre-trained knowledge" / "TRUST X" 这类约束指令后, 反而会过度反应 (选择过度保守, 大量误杀)
- **V1 简洁的 "Does this describe the same product?" 加上自由判断 = 最稳定**
- **不要试图用提示词 "控制" AI 的内部推理**——指令越简单, 表现越稳

**【未来警告】**
- 添加任何 TRUST / IGNORE / NEVER / ALWAYS 这类强约束词前, 先想: "这个指令会不会让 AI 变得过度保守?"
- 加约束后, **必须**跑多次重复验证 (AI 不稳定性 ±40%)

**【根本限制】AI 输出不稳定性是独立变量**
- 同一 prompt + 同一输入 + 同模型, 不同调用间波动 ±40%
- 这是 LLM 概率采样的本质, **不能消除**
- 实际工程: 取多次平均 + 人工校验边角案例

**【故障案例】2026-06-07 V3 改造误入歧途**
- 我读错了 David 原始需求, 把"以 product_description 为判断依据"过度解读为"完全禁止预训练"
- 加上 "Step 1/2/3 特征对比" 反而让 AI 过度严格, 把品牌词也误判
- V3 KODAK 稳定 52.9% 是提示词结构性问题, 不是 AI 噪声
- 修复: 回退 V3 改造, 恢复 V1 提示词

## 记忆机制 (2026-04-14)

### 每日日志规范
- **会话结束**：将当天对话精华压缩记录到 `memory/YYYY-MM-DD.md`
- **会话开始**：自动读取昨日和今日的日志，实现自动回忆
- **压缩原则**：保留上下文、决策、待办，不要流水账

### 日志格式模板
```markdown
# YYYY-MM-DD 日志

## 主题/项目
- 背景简述

## 完成的工作
- 具体事项

## 决策记录
- 重要选择及原因

## 待办/后续
- 未完成事项
- David 后续可能的需求
```

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
- **执行脚本**: `/root/.openclaw/workspace/autoads/archer-roi/check_suffix.py`
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

## 广告与ASIN映射数据库 (2026-05-23)

### ad_campaigns_db.json
- **位置**: `/root/.openclaw/workspace/autoads/logs/ad_campaigns_db.json`
- **用途**: 存储广告系列与ASIN映射关系（campaign_id、campaign_name、account_id、asin、product_name、price、commission_rate、network、url、cpc_bid、status）
- **记录数**: 287条
- **查询函数**:
```python
from ad_campaigns_db import get_campaigns_by_asin, get_campaigns_by_account
campaigns = get_campaigns_by_asin('B0D6J5B98H')
```

### asin_to_campaigns.json
- **位置**: `/root/.openclaw/workspace/autoads/logs/asin_to_campaigns.json`
- **用途**: ASIN反向查询对应广告系列
- **查询示例**:
```python
import json
with open('/root/.openclaw/workspace/autoads/logs/asin_to_campaigns.json') as f:
    lookup = json.load(f)
campaigns = lookup['mapping'].get('B0D6J5B98H', [])
```

---
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

### 暂停广告系列记录 (2026-04-25)
- **暂停日志**: `/root/.openclaw/workspace/autoads/archer-roi/logs/paused_campaigns.json`
- **必填字段**: ASIN, campaign_id, paused_at, reason, note
- **暂停原因选项**: 联盟通知暂停 / ROI过低 / 无订单 / 商品下架 / 其他
- **状态**: ✅ 已配置

### 联盟广告暂停规则 (2026-05-02 新增Rule 5)
**Archer** (`runner.py` → `check_low_roi_trends`):
- Rule 1: 累计花费>$50 AND ROI<100%持续3天 AND 每天aff_clicks>0 → pause
- Rule 5 (NEW): **总点击>50** AND 累计佣金<$20 AND confirmed CVR<3% → pause [佣金<$20 + CVR<3% + 点击>50三重条件]

**YeahPromos/PartnerBoost** (`generate_affiliate_report.py` → `check_pause_rules_new`):
- Rule 1: T-3/T-2有点击 AND 总点击>50 AND confirmed=0 → pause
- Rule 2: T-3/T-2有点击 AND 总点击>50 AND ROI_usd≤110% → pause
- Rule 3: T-3~T总点击>40 AND pending=0 → pause
- Rule 4: T-3~T总点击>40 AND CVR≤3% → pause [CVR=(confirmed+pending)/gads_clicks，无点击门槛]
- Rule 5 (NEW): **总点击>50** AND 佣金<$20 AND confirmed CVR<3% → pause [confirmed CVR=confirmed/gads_clicks，点击>50门槛]

**Rule 4 vs Rule 5 区别**：
| | Rule 4 | Rule 5 |
|---|---|---|
| 点击门槛 | >40（无） | >50（有） |
| CVR公式 | (confirmed+pending)/gads_clicks | confirmed/gads_clicks |
| 佣金门槛 | 无 | <$20 |
| 适用 | Y/PB通用 | Y/PB通用 |

### 联盟广告预算增加规则 (2026-05-02 新增)
**文件**: `/root/.openclaw/workspace/autoads/archer-roi/budget_rules.py`
**逻辑**: 独立查询每日cost（不改roi_history），触发时自动+CNY 20

**规则条件**:
- Archer: 连续2天花费>=预算 AND (confirmed CVR>=150% OR ROI>=150%)
- YeahPromos/PartnerBoost: 连续2天花费>=预算 AND confirmed CVR>=150%

**实现函数**:
| 函数 | 功能 |
|------|------|
| `get_gads_daily_costs_by_asin()` | 独立按天查询每日cost |
| `get_campaign_budget()` | 查询Campaign当前每日预算 |
| `increase_campaign_budget()` | 预算+CNY 20 |
| `check_and_increase_budgets()` | 主规则逻辑 |

**待集成**: `runner.py` main() 流程中调用 `check_and_increase_budgets()`

### 广告系列数据库 (2026-04-25)
**新建广告时自动记录的数据库表**
- **数据库文件**: `/root/.openclaw/workspace/autoads/logs/ad_campaigns_db.json`
- **模块**: `autoads/src/ad_campaigns_db.py`

**记录字段**:
| 字段 | 说明 |
|------|------|
| campaign_id | Google Ads广告系列ID |
| campaign_name | 广告系列名称 |
| account_id | Google Ads账户ID |
| asin | Amazon ASIN |
| product_name | 商品名称 |
| price | 商品单价(USD) |
| commission_rate | 佣金率 |
| network | 联盟网络(archer/yeahpromos/partnerboost) |
| url | 产品URL |
| cpc_bid | CPC出价 |
| status | 状态(ENABLED/PAUSED) |
| created_at | 创建时间 |

**查询函数**:
```python
from ad_campaigns_db import (
    save_campaign_record,      # 保存记录
    get_campaigns_by_asin,     # 按ASIN查询
    get_campaigns_by_account,   # 按账户查询
    get_campaign_by_id,        # 按ID查询
    get_campaigns_by_network,  # 按联盟查询
    get_campaigns_for_cpc_check,  # 获取需CPC检查的 campaigns
    get_summary               # 获取统计摘要
)
```

**状态**: ✅ 已配置，创建广告成功后自动记录

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

### 2026-06-21 (今日)
- ✅ Launch X431 CRP919XBT (Campaign 23959722689) L0=0 故障根因诊断 + 修复闭环
  - **首轮误诊 → 三轮修正**: 第一轮归因"V3 LLM 幻觉 DROP CRP919XBT" → 第二轮归因"policy_filter 全大写过滤" → 第三轮 dry-run 实测发现都不是
  - **真实根因**: `src/refined_campaign_creator.py:1313-1338` 内部 one-shot 调用漏传 `seed_keywords=` 参数 (与 run_skill.py:381 行为不一致)
  - **修复 (commit 9d1e14f 之后)**: 改 2 处:
    1. one-shot 内部调用补传 `seed_keywords=_brand_seed_for_oneshot` (单次 + 分批两路)
    2. L0=0 兑底升级为 L0 **无条件强制注入** user-provided seed (不依赖 L0 是否空)
  - **验证**: dry-run 3 分 24 秒, L0=3 含 `Launch X431 CRP919XBT` ✅
  - **顺手发现**: 6/20 实跑时 `--product-model CRP919XBT` **没传**到 CLI (主对话有写, 透传漏了), 这是独立于 L0 兑底的参数透传缺口
- ✅ **第二十二铁律确立** (David 9:44 BJT 拍板): 「改代码的综合影响面分析原则」
  - 核心: 修被多处调用的模块/函数前, 必须基于**可靠日志和代码**做综合影响面分析, 不能为了改 A 不管 B, 不能基于估计和猜测
  - 8 节结构: 原文 / 三大原则 / 5 步工作流 / 错误案例 / 正确做法 / 验收命令 / 与已有铁律协同 / 教训
  - 6/21 Launch X431 诊断全过程作为 4 个错误案例 (凭印象给方案 / 修 dead code 当修复 / 误诊 100% / 函数体注释 ≠ 实现)
  - 加入「错误案例 + 正确做法」对偶写法, 未来同源问题可复用

### 2026-06-08 (今日)
- ✅ L0/L1 分层优化 (David 13:36 15:02)
  - L0: bid_rate=1.0, cap=$7 (5/29 立, 公式 max_cpc 超 $7 封顶)
  - L1: bid_rate=0.5 (原 0.8), cap=$2 (16:17 明确, 取代原 $2.4 限)
  - L2/L5: bid_rate=1.0/0.7, cap=$2
  - B 方案: L0 词 (brand + 严格 product_model) 也加到 L1 ad group (同词双层)
  - classify_keyword L0 优先级最高 (避免 5+ 词被 L5 抢)
  - X431 PROS V 5.0 v2 (Campaign 23914011987): L0=4/$7 + L1=39/$2 + L2=69/$2 + L5=10/$2
- ✅ L1/L2/L5 bid cpc_cap 修复 (David 16:17)
  - LAYER_CONFIG 加 cpc_cap: 2.0 到 L1/L2/L5 (L0 已有 cpc_cap: 7.0)
  - 4 个 ad group bid 修复: 旧 23913131214 L1 $7.09→$2 + 新 23914011987 L1 $4.43→$2 / L2 $8.86→$2 / L5 $6.20→$2
- ✅ PIURIFY 精细化分层 (Campaign 23912114112, 模式 A)
  - 8 个 ad group: L0_3-7 (5 个 $3-$7) + L1 ($1.80) + L2 ($1.80) + L5 ($1.80)
  - 65 关键词 / 12 sitelinks / 0 negative
- ✅ 广告创建模式决策 (David 16:41 同意)
  - 模式 A (备选): 已有普通广告 -> refined-ads 一次性补 8 层
  - 模式 B (默认, 新产品): refined-campaign-new 4 层 -> 观察 -> refined-ads 升级 L0
  - 记入 SKILL.md: skills/refined-ads/SKILL.md + skills/refined-campaign-new/SKILL.md

### 2026-04-12
- ✅ 修复Archer ROI报告中ASIN网络归属错误
- **问题**: B008I4XFWU, B0BYS93PTL, B07DQVNSP8, B07DNYSJ8W 被错误归为Archer（实际是YeahPromos）
- **原因**: 代码仅根据ASIN是否出现在Archer API来判断，没有检查广告系列名称
- **修复**: 增加 `is_yeahpromos_campaign()` 函数，根据广告系列名称前缀判断网络
- **匹配模式**: `yeahpromos -`, `- yeahpromos`, `yeahpromos-` (不区分大小写)
- **文件**: `/root/.openclaw/workspace/autoads/archer-roi/runner.py`

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

## 🔴 联盟产品状态监控 ASIN 抽取铁律 (2026-06-11 确立)

**【最高优先级】根据广告系列获取 ASIN 的方法, 要使用 Google Ads API 接口从广告的 final_url 抽 ASIN。**

### 实现要点
- **主路径**: GAQL 查 `ad_group_ad.ad.final_urls`, 正则 `amazon\.com/dp/(B0[A-Z0-9]{8})` 抽 ASIN
- **Fallback**: DB 映射 `campaign_id → asin` (从 `ad_campaigns_db.json`)
- **禁止用广告系列名模板** (template 不准确且可能缺失, 6/11 BJT 实证 4 个漏检)

### 6/11 BJT 漏检事故
- v4 改造: 从 `campaign.name` 用正则 `\b(B0[A-Z0-9]{8}|[A-Z0-9]{10})\b` 抽 ASIN
- 漏检 4 个 price=0 广告 (B0BSP4NS28 RhinoUSA / B001IWNDDA Intex / B0D6J5B98H ROVE / B082LV2VH6 bedmettress)
- 根因 1: 历史遗留广告 name 里没 ASIN → 正则抽不出
- 根因 2: tracking ID (10 位数字如 1774619504) 被 `[A-Z0-9]{10}` 误识别为 ASIN → 用"假 ASIN" 查 API 返回空 → 错归类为 unknown 告警
- David 明确指示: "提取 ASIN 应该从广告系列下的正在运行的广告系列下的广告的最终到达网址中, 根据正则提取网址最后面的那个 ASIN。Offset 逻辑应该是从数据库端去找到对应的 ASIN。不能用广告名称模板"

### v5 改造文件
- `autoads/archer-roi/scripts/monitor_product_status.py` (`load_campaigns()` 函数)
- Commit: `0a3d9b1` (2026-06-11 12:48 BJT)

## 🔴 第二十一铁律草案: user-provided L0 种子词强制入 L0 (2026-06-19 Autofull G7 故障确立)

**【背景】** 2026-06-19 Autofull G7 Gaming Chair (Campaign 23961493414) 创建时，V3 one-shot LLM 输出 `L0=0`，导致程序跳过 L0 ad group 创建。根因：GKP 没拉到含 "G7" 的词（低搜索量新型号），LLM 看到的 product_model 扩展词被误分到 L1。

**【铁律草案】** V3 one-shot 输入范围是 GKP 拉取词 + 用户种子词，**用户提供的 L0 种子词（product_model 扩展）应该默认作为 L0，不经过 LLM 判断**。

**【修复方向】**
- 当 `product_model` 参数传入时，其扩展的 10 个变体（`creator._expand_product_model_variants`）应该**强制入 L0**，不做 one-shot 分类
- 只把 GKP 拉的词送 one-shot 分类
- LLM 输出只影响 GKP 词，不覆盖 user-provided L0 种子词

**【验证场景】**
- Autofull G7: product_model=G7 → 扩展 10 词 → 强制 L0 ✅
- SIHOO M57: product_model=M57 → 扩展后入 L1（早期 bug，已修复）
- CRAFT RESIN: 无 product_model → 跳过 L0（正确）

---

---

## 🔴 第二十二铁律: 改代码的综合影响面分析原则 (2026-06-21 09:44 BJT David 拍板)

**【最高优先级】修改被多处调用的模块/函数前，必须基于可靠日志和代码做综合影响面分析，不能为了改 A 不管 B，不能基于估计和猜测就动刀。**

### 1. 铁律原文 (David 9:44 BJT 飞书原话)

> "你要从整体视角制定优化方案，如果一个模块或者函数被多个功能使用，不能为了改 A，而不管 B。比如政策检查过滤模块，'我只要去掉关键词过滤部分的全大写检查和过滤'，你就需要分析修改的模块对引用这个模块的其他代码有什么影响，不能影响 headlines 和 description 的政策过滤，因为 headlines 和 description 不允许全大写。关键词过滤部分，是不是只有全大写过滤，还是有其他过滤内容，其他的过滤内容是否有效？你要做综合分析，基于可靠的日志和代码的综合分析，而不是估计和猜测。"

### 2. 铁律核心三大原则

**原则 1: 调用方 × 检查对象 全量矩阵（不允许只盯改 A）**
- 任何修改前必须列出**所有调用方**（grep 模块/函数名全工程）
- 列出每个调用方的**检查对象**（关键词？headlines？description？sitelinks？）
- 列出每个调用方**当前实际行为**（生效中？no-op？被注释？）
- 用矩阵表达，矩阵有空单元 = 分析没做完

**原则 2: 改之前先做死代码审计（不允许凭印象说"修了"）**
- 看函数体**实际实现**——不是看注释/外部调用方
- 函数体注释 "已禁用" 跟函数体实现 "no-op" 是不是一致？
- 函数的 dead code（注释掉的、return 后的）包含什么过滤逻辑？这些是不是还有效？
- **铁律 7「交叉引用扫描」的延伸**：不仅看谁调了，还要看函数体里实际在跑什么

**原则 3: 基于可靠日志和代码，不允许估计和猜测**
- "可能是"、"大概是"、"应该不会影响" = 不允许
- 必须有：grep 结果 + 函数体行号 + dry-run 实际输出 + 至少 1 个回归测试
- 静默 fall back 也算"估计猜测"——如果不能给出"修了等于修 dead code，零回归风险"这种**确定性结论**，就别动

### 3. 启动"改 X 影响面分析"的标准工作流

**Step 1: grep 全部调用方**
```bash
grep -rn "from .module_name import\|module_name\." src/ --include="*.py" | grep -v ".pyc"
```
输出: 调用方列表 (文件:行)

**Step 2: 列出每个调用方的检查对象 + 当前行为**
| # | 调用方 | 文件:行 | 调用方法 | 检查对象 | 实际行为 (有/无/部分) |
|---|---|---|---|---|---|

**Step 3: 看目标函数体实际实现**
- 函数体是 no-op (return 立即) → 修了等于修 dead code，零回归
- 函数体有真实逻辑 → 列出**所有**分支（DANGEROUS_TERMS / COUNTERFEIT_GOODS / UNAPPROVED_SUBSTANCES...）
- 哪些分支当前仍在生效？哪些是 dead code？

**Step 4: 画影响面矩阵**
- 修 X 后，A 调用方影响 = ？
- 修 X 后，B 调用方影响 = ？
- 修 X 后，C 调用方影响 = ？
- 矩阵里有任何一个不确定 = **停下来，先做实验验证，再改**

**Step 5: 给出"确定性结论"才能动刀**
- ✅ 允许的表述: "修 X 等于修 dead code，3 个调用方全部 no-op，0 回归"
- ❌ 禁止的表述: "估计不会影响"、"大概是 no-op"、"应该只影响 A 调用方"

### 4. 错误案例 (2026-06-21 Launch X431 CRP919XBT 诊断过程)

**【错误 1: AI 凭印象给方案，没看函数体】**
- AI 第一轮提了 3 个修复方案（"加 text_type 参数"/"加 skip_caps_check 参数"/"拆成两个独立函数"）
- **问题：3 个方案都假设 `policy_filter.check_keyword()` 在关键词路径仍生效**
- **真相：函数体 line 842-843 已是 no-op (return True, [])，dead code 200+ 行**
- **AI 之前一整轮都在讨论"如何拆分一个根本不执行的函数"**

**【错误 2: AI 给出"如果 A 修 1 行就能解决"的轻量方案】**
- AI 第一轮说"修 X 只改 policy_filter.py 一行 diff"
- **真相：政策过滤的"全大写检查"在 5 个独立路径都有副本（ad_prevalidator / policy_filter.check_keyword / policy_filter.check_ad_copy / LLM one-shot / V3 post-relocate）**
- **修 A 不修 B = B 仍 DROP 关键词**
- **修 A 不看 B = A 可能误伤 B 路径的合法 headline（如 "SAVE 50% OFF" 这种促销词）**

**【错误 3: AI 第一次根因诊断 100% 错（V3 LLM 幻觉）】**
- AI 第一轮说"LLM 看到 CRP919XBT 当成违反 Google Ads 大小写政策 DROP 到 drop 列表"
- **没有验证：直接调 `ai_filter_and_classify_one_shot` 实测**
- **真相：LLM 没 DROP CRP919XBT**，根因是 `refined_campaign_creator.py` 的 one-shot 调用**没传 `seed_keywords=` 参数**（6/20 拍板时的"漏传"代码缺口）

### 5. 正确做法 (6/21 验证通过版)

**Step 1: 不看 AI 推理，先看代码 + 跑实测**
- grep `policy_filter` 全部调用方 → 5 处
- 看 `check_keyword` 函数体 line 842 → 已是 no-op
- **结论：关键词路径所有政策过滤 + 全大写过滤**全部 dead code**，"修 policy_filter" 等于修 dead code**

**Step 2: 跑 dry-run 实测 V3 one-shot 行为**
- 直接调 `wf.ai_filter_and_classify_one_shot(keywords=..., brand='Launch', product_model='CRP919XBT', seed_keywords=[...])`
- 实测结果：LLM 看到 `Launch X431 CRP919XBT` **正常入 L0**，没幻觉 DROP
- **结论：根因不在 LLM，在调用链上游**

**Step 3: 走真实路径 dry-run（run_skill.py --dry-run）**
- 完整 10 阶段准备 + 0 写入
- 实测 L0=2（不是 6/20 实跑的 0）→ 怀疑 LLM 推理不稳定 → 进一步查代码
- 发现 `create_layered_campaign` 内部 one-shot 调用**漏传 `seed_keywords=`**（line 1313-1338）

**Step 4: 修两处**
- 改动 1: 内部 one-shot 补传 `seed_keywords=`（修复"漏传"代码缺口）
- 改动 2: L0=0 兜底升级为 L0 无条件强制注入（应对未来类似 LLM 推理不稳定）
- 改完 dry-run 验证：L0=3 ✅ `Launch X431 CRP919XBT` 在 L0

### 6. 验收检查命令

```bash
# Step 1: 列出被修改模块的全部调用方
grep -rn "from .MODULE_NAME import\|MODULE_NAME\." src/ --include="*.py" | grep -v ".pyc"

# Step 2: 验证"修 X 等于修 dead code"的假设
# 找函数体是否在 return 立即 / 是否全部被注释
sed -n '/^    def FUNCTION_NAME/,/^    def [a-z]/p' src/MODULE_NAME.py | head -30

# Step 3: 跑最小回归测试
python3 -c "from src.MODULE_NAME import FUNCTION; print(FUNCTION('test_input'))"

# Step 4: 跑端到端 dry-run 验证
python3 skills/refined-campaign-new/run_skill.py ... --dry-run
```

### 7. 与已有铁律的协同

| 已有铁律 | 协同点 |
|---|---|
| 第十一铁律「AI 推理归属」 | 工具/规则模块不带 AI 推理 → 改工具时基于"被调用的代码"做影响面分析 |
| 「全局反硬编码铁律」 | 同一过滤逻辑在多处副本 = 反硬编码铁律延伸：应在唯一权威源维护 |
| 「故障即文档元规则」 | 误判时**先做综合影响面分析**，再写提示词规则 |
| 「CLI 工具 nargs 陷阱铁律」 | 改 CLI 参数类型前，先 grep 全部 CLI 调用方 + 看实际解析函数 |
| 第十八铁律草案（手动触发架构） | 手动触发的搜索词分析流程，**不**属于"高频调用"——改搜索词分析工具时无需担心自动化场景 |
| 第二十一铁律草案「user-provided L0 强制入 L0」 | 本次修复是第二十一铁律的工程化落地 + 加了"create_layered_campaign 路径漏传 seed"的额外修复 |

### 8. 教训（2026-06-21 09:44 BJT）

- **"我只要改 A" 是危险信号** — 触发后立即强制做"调用方 × 检查对象"矩阵
- **dead code 是隐藏的真相** — 函数注释 "已禁用" 不等于函数体 no-op，必须看函数体
- **可靠日志 > 估计猜测** — 任何"修 X"决策前必须有 dry-run 实测输出或 grep 结果做依据
- **错误诊断比不改还糟糕** — 6/21 第一轮 AI 提的 3 个方案全部基于错误前提，等于把"修 dead code"包装成"实质修复"
- **AI 推理不确定性要用工程化兜底** — LLM 输出统计性结果 → 不能依赖 LLM 100% 把 user-provided seed 入 L0 → 必须 Python 循环硬注入兜底

---

> 以下是已归档的历史记忆

(暂无 - 2026年3月)
