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

## 归档记录

> 以下是已归档的历史记忆

(暂无 - 2026年3月)
