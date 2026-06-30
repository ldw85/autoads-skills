---
name: affiliate-selection
description: AI-powered单ASIN联盟选品分析技能。自动分析指定ASIN的商品数据、关键词搜索量、CPC、规则判断，并联网查询竞品价格，输出完整的选品分析报告。触发词：根据ASIN进行选品分析、根据ASIN进行联盟商品分析、单ASIN选品分析、指定商品分析。
credentials:
  - Archer API 凭证（通过环境变量或cred-agent）
  - Google Ads API 凭证（via autoads配置）
env:
  autoads_config: true
outputs:
  report_text: "完整选品分析报告（含联网竞品价格）"
  report_json: "JSON格式报告数据"
---

# Affiliate Selection Skill

AI-powered affiliate product selection with automatic web competitor price lookup.

## 功能

1. **单ASIN分析** - 分析指定ASIN的联盟商品数据
2. **关键词查询** - 调用Google Keyword Planner获取搜索量和CPC
3. **规则判断** - 价格/销量/评分/评价数/品牌CPC/品类CPC门槛检查
4. **ROI预估** - 预估CPC、佣金、ROI正向性
5. **投放策略** - 推荐品牌词投放/品类词投放/不推荐
6. **联网竞品价格** 🌐 - 自动调用web_search查询竞品价格，生成性价比分析
7. **联网用户评价** 🌐 - 自动查询品牌用户评价，分析优点/硬伤/受欢迎程度

## 触发方式

**触发后自动执行所有步骤，一次性输出完整报告（包含联网查询）**

直接输入以下信息即可：
- "分析商品 B0DN1DKNGZ, 品牌Niphean, 品类Inflatable Paddle Board, 评分4.7, 评价数4000, 销量300"
- "选品分析 Niphean B0DN1DKNGZ"
- "帮我分析这个ASIN"
- "Ray-Ban B00346VLGE 选品分析"

## 使用方法

### 方式1：完整参数（推荐）
```
分析商品 [ASIN], 品牌 [品牌名], 品类 [品类名], 评分 [评分], 评价数 [评价数], 销量 [月销量]
```

### 方式2：基础参数
```
分析商品 [ASIN], 品牌 [品牌名], 品类 [品类名]
```

### 方式3：仅ASIN（需要品牌和品类识别）
```
分析商品 [ASIN]
```

## 输出报告格式

### 基础数据
- ASIN、价格、佣金（百分比+金额）、月销量、评分、评价数

### 关键词数据
- 品牌关键词搜索量/CPC
- 品类关键词搜索量/CPC
- 长尾关键词搜索量/CPC

### 规则判断
- 价格区间（low/optimal/high）
- 销量门槛、评分门槛、评价数门槛
- 品牌CPC门槛、品类CPC门槛
- 品牌搜索量

### ROI预估
- 预估CPC、预估佣金、ROI正向性

### 投放策略
- 推荐：品牌词投放 / 品类词投放 / 不推荐
- 原因说明

### 商品覆盖度
- 品牌商品数量
- 品类商品数量
- 覆盖率（品牌/品类百分比）

### CPC门槛标准
- 品牌CPC上限（单价×佣金率×0.05）
- 品类CPC上限（单价×佣金率×0.02）

### 联网竞品价格分析 🌐
- 竞品品牌价格对比表
- 竞品平均价、最低、最高价
- 性价比分析（vs竞品）

### 联网用户评价分析 🌐
- 整体评价（定位/目标用户/受欢迎程度）
- 优点（用户真实反馈）
- 缺点/硬伤（用户反馈问题）
- 结论（适合人群/购买建议）

## 工作流程（一次性完整输出）

**触发技能时，所有步骤按顺序自动执行，AI 在同一次回复中完成全部 8 个步骤，不等待用户二次触发**

```
步骤1: 运行选品脚本 → 获取基础数据（ASIN/价格/佣金/销量/评分）
步骤2: 调用GKP API → 获取搜索量和CPC
步骤3: 规则判断 → 生成投放策略 + 商品覆盖度
步骤4: web_search → 查询竞品价格（联网竞品价格查询）
步骤5: web_fetch → 抓取竞品价格详情
步骤6: web_search → 查询品牌用户评价/硬伤
步骤7: web_fetch → 抓取用户评价详情
步骤8: 合并为完整报告一次性输出
```

**【自动触发规则 - 核心要求】**
- 步骤 1-3：脚本执行（纯数据查询，无需 AI 推理）
- 步骤 4-7：**脚本返回结果后，AI 立即在同一对话轮次中自动调用 web_search + web_fetch，不等待用户提示**
- 步骤 8：AI 将脚本输出 + 联网数据合并为完整报告，在同一次回复中呈现
- **禁止行为**：脚本跑完后直接展示报告而跳过步骤 4-7；分多次消息输出报告内容

**【联网搜索词规范 - 必须遵守】**
- 竞品价格搜索：`[品类名称] price competitors Amazon 2026`
- 用户评价搜索：`[品类名称] user review pros cons Amazon 2026`
- 示例：用户提供品类 "Inverter Portable Air Conditioners"
  - 竞品价格搜索：`inverter portable air conditioners price competitors Amazon 2026`
  - 用户评价搜索：`inverter portable air conditioners user review pros cons Amazon 2026`

## 技术实现

### 模块结构
```
autoads/affiliate-selection/
├── base.py              # 抽象基类 + 核心分析逻辑
├── archer.py           # Archer联盟实现
├── gkp.py              # Google Keyword Planner客户端
├── web_price_lookup.py # 联网竞品价格查询
├── run_skill.py        # CLI入口
└── _gkp_query.py       # GKP查询脚本
```

### 环境要求
- Python 3.8+
- archer-apipackage
- google-ads
- pandas
- requests

## 示例输出

```
📊 完整选品分析报告 - Niphean B0DN1DKNGZ

【基础数据】
  • ASIN: B0DN1DKNGZ
  • 价格: $186.99
  • 佣金: $13.09 (7.0%)
  • 月销量: 300
  • 评分: 4.7
  • 评价数: 4,000

【关键词数据】
  • niphean inflatable paddle board: 搜索量 320/月, CPC ¥3.50
  • inflatable paddle board: 搜索量 74,000/月, CPC ¥3.50

【规则判断】
  ✅ 价格区间: optimal
  ✅ 销量门槛: ✅
  ✅ 评分门槛: ✅
  ✅ 评价数门槛: ✅
  ❌ 品牌CPC门槛: (CPC ¥3.50 > 门槛 ¥0.65)
  ❌ 品类CPC门槛: (CPC ¥3.50 > 门槛 ¥0.26)
  ❌ 品牌搜索量: (搜索量 320 < 阈值 400)

【商品覆盖度】
  • 品牌商品数: 153
  • 品类商品数: 97
  • 覆盖率: 157.7%

【CPC门槛标准】
  • 品牌CPC上限: ¥0.65 (单价×佣金率×0.05)
  • 品类CPC上限: ¥0.26 (单价×佣金率×0.02)

【投放策略】
  🔵 推荐: 品牌词投放
  📝 原因: Price in optimal range, good brand search volume and CPC

【联网竞品价格分析】🌐
  品牌          价格    评分    承重
  Niphean       $229.99  4.6/5  500lbs
  MYBOAT       $219.99  4.6/5  430lbs
  Roc          $229.99  4.8/5  350lbs
  Skatinger    $319.98  4.9/5  450lbs
  FBSPORT      $159.98  4.6/5  350lbs

  你的价格: $186.99
  竞品平均: ~$225
  ✅ 性价比: 低于竞品平均价 - 有价格优势

【联网用户评价分析】🌐
  定位: 预算-中端 inflatable SUP
  目标用户: 初学者、家庭、休闲玩家
  ✅ 受欢迎: 快速增长，Amazon畅销 + 自有Shopify店
  
  ✅ 优点 (用户真实反馈):
    - 稳定性好: 宽板面，站立舒适，新手也能平稳
    - 配件超丰富: paddle/尾鳍/泵/背包/防水袋/维修套件
    - 售后响应快: 客户服务评价好
    - 质保较长: 3年质保
    - 轻量: Pro 11'6仅22磅，易搬运
  
  ❌ 缺点/硬伤 (用户反馈问题):
    - 偶发配件损坏: 偶尔缺失或损坏配件（尤其数字压力表）
    - Pro系列硬度: 部分用户反映硬度不如预期
    - 碳纤维支撑: Pro 11'6碳纤维支撑实际效果存疑
  
  📊 结论:
    ✅ 适合: 初学者、家庭、休闲瑜伽用户
    ❌ 不适合: 竞速、硬核touring玩家
    ✅ 购买建议: 推荐Classic系列入门
```

## 注意事项

1. **月销量必须提供**：联盟API不返回月销量，如果用户没提供 `--sales`，脚本会阻断并提醒
2. **CPC门槛动态计算**：
   - 品牌CPC门槛 = 单价 × 佣金率 × 0.05
   - 品类CPC门槛 = 单价 × 佣金率 × 0.02
3. **品牌关键词使用品牌+品类**：如 "Niphean inflatable paddle board" 而非仅 "Niphean"
4. 联网查询需要网络连接，如失败会跳过竞品价格分析
5. 默认查询美国市场、英语，如需其他国家请说明
6. 联网竞品价格和用户评价由AI在主对话中自动调用（步骤4-7），脚本只负责步骤1-3