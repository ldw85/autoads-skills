---
name: autoads
description: |
  Google Ads自动化广告创建工具。通过提供落地页URL、跟踪模板、痛点信息等参数，
  自动创建完整的Google Ads广告系列（包括关键词、标题、描述、附加链接等）。
  替代手动调用autoads项目CLI。
triggers:
  - 创建广告
  - Google Ads
  - autoads
  - 广告系列
  - campaign
  - 创建广告系列
input:
  type: object
  required:
    - landing_url
  properties:
    landing_url:
      type: string
      description: 广告落地页URL（必填）
      example: https://merachfit.com/products/novarow-r50-air-resistance-rower
    tracking_template:
      type: string
      description: 跟踪模板URL（可选，需包含{lpurl}占位符）
      example: https://tatrck.com/h/0Hu30_Cb0ueB?model=cpa&url={lpurl}
    country:
      type: string
      description: 目标国家代码（默认US）
      default: US
    budget:
      type: number
      description: 日预算，单位为账户货币（默认100）
      default: 100
    cpc:
      type: number
      description: CPC出价（默认0.56）
      default: 0.56
    pain_points:
      type: array
      description: 痛点列表，每项包含topic和pain_text
      items:
        type: object
        properties:
          topic:
            type: string
            description: 痛点主题
          pain_text:
            type: string
            description: 痛点描述
      example:
        - topic: space
          pain_text: bulky gym equipment takes up too much space
        - topic: noise
          pain_text: noisy workouts disturb family and neighbors
    marketing_copy:
      type: object
      description: 营销文案素材（可选，将覆盖AI生成的内容）
      properties:
        headlines:
          type: array
          items:
            type: string
          description: 广告标题列表（每个≤30字符）
        descriptions:
          type: array
          items:
            type: string
          description: 广告描述列表（每个≤90字符）
        keywords:
          type: array
          items:
            type: string
          description: 关键词列表
    campaign_name:
      type: string
      description: 广告系列名称（可选，自动生成）
output:
  type: object
  properties:
    success:
      type: boolean
    campaign:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        status:
          type: string
    ad_groups:
      type: integer
    ads:
      type: integer
    keywords:
      type: integer
    errors:
      type: array
      items:
        type: string
    warnings:
      type: array
      items:
        type: string
---

# Autoads - Google Ads 自动创建技能

本技能封装autoads项目的CLI，提供标准化的广告创建接口。

## 工作目录
```
/root/.openclaw/workspace/autoads
```

## 核心命令

### 创建广告（create）
```bash
cd /root/.openclaw/workspace/autoads && python3 -m src.main --command create \
  --url "<landing_url>" \
  --country <country> \
  --tracking-template "<tracking_template>" \
  --budget <budget> \
  --cpc <cpc> \
  --name "<campaign_name>" \
  --manual-pain-points '<pain_points_json>' \
  --product-description "<description>"
```

### 查看状态（status）
```bash
cd /root/.openclaw/workspace/autoads && python3 -m src.main --command status
```

### 测试连接（test）
```bash
cd /root/.openclaw/workspace/autoads && python3 -m src.main --command test
```

## 使用流程

1. **验证配置** - 运行 `--command test` 确认Google Ads连接正常
2. **准备参数** - 收集landing_url、tracking_template、pain_points
3. **执行创建** - 调用CLI创建广告
4. **返回结果** - 解析输出返回结构化结果

## 痛点格式（pain_points）

JSON数组格式：
```json
'[{"topic":"space","pain_text":"bulky gym equipment takes up too much space"},{"topic":"noise","pain_text":"noisy workouts disturb neighbors"}]'
```

## 注意事项

- 使用 `--manual-pain-points` 传递痛点（避免AI技能调用失败）
- 跟踪模板建议包含 `{lpurl}` 占位符
- 关键词会自动通过关键词生成器扩展（EXACT + PHRASE）
- 政策过滤会自动应用（过滤禁用词、夸大宣传等）

## AI技能调用失败问题分析

### 问题原因
`research_flow.py` 中的 `call_skill()` 函数依赖Claude Code CLI调用AI技能：
```python
result = subprocess.run(
    ["claude", "--print", "--output-format", "json", full_prompt],
    ...
)
```

**失败原因：**
1. Claude Code CLI (`claude`) 存在但未配置正确的API认证
2. 环境变量 `MINIMAX_API_KEY` 或 `ANTHROPIC_API_KEY` 未设置
3. `ANTHROPIC_BASE_URL` 可能指向错误的端点

### 解决方案
1. **使用手动痛点** - 传递 `--manual-pain-points` 参数完全绕过AI调用
2. **修复API配置** - 设置正确的API key环境变量
3. **使用内置生成器** - 当AI调用失败时，`policy_filter.py` 和 `keyword_generator.py` 会使用内置规则生成素材

### 验证API配置
```bash
# 检查环境变量
env | grep -i "minimax\|anthropic"

# 测试Claude Code
claude --version
```

### 当前推荐用法
提供完整的 `pain_points` 和 `marketing_copy` 参数，使用 `--manual-pain-points` 选项，确保广告创建不依赖AI技能调用。
