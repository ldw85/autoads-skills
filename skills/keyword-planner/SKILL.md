# keyword-planner Skill

## 功能

调用Google Keyword Planner API获取关键词在美国地区的搜索量和CPC数据。

- **功能1（AI提取 + API）**: 输入商品描述 → AI语义分析提取品牌词/型号 → 调用API生成关键词 + 获取数据
- **功能2（纯API）**: 直接输入关键词 → 调用API生成相关关键词 + 获取数据
- **Fallback**: 当Google Keyword Planner触发429限流时，自动调用gotrends.app作为fallback

## 功能增强（2026-06-04）

- 429错误自动检测和重试（最多3次，指数退避）
- API调用间隔控制（默认2秒，避免触发限流）
- gotrends.app fallback API（当Google被限流时自动切换）

## 使用方法

```bash
# 功能1：商品描述 → AI提取 → API生成（完整流程）
cd ~/.openclaw/workspace/skills/keyword-planner
python3 run_skill.py --command analyze \
  --product-description "KODAK LUMA350 Portable Bluetooth Speaker - Waterproof, 20H Playtime, Rich Bass" \
  --ads-account 6660356395 \
  --output console

# 功能1：URL → AI提取 → API生成
python3 run_skill.py --command analyze \
  --url "https://www.amazon.com/dp/B0DYHW4GKP" \
  --ads-account 6660356395 \
  --output console

# 功能2：直接输入关键词 → API生成
python3 run_skill.py --command generate \
  --keywords "KODAK LUMA350 bluetooth speaker" \
  --ads-account 6660356395 \
  --output console

# 功能2：多关键词 → API生成
python3 run_skill.py --command generate \
  --keywords "bluetooth speaker, waterproof speaker, portable speaker" \
  --ads-account 6660356395 \
  --output console

# 启用fallback（当429时自动切换到gotrends.app）
python3 run_skill.py --command generate \
  --keywords "bluetooth speaker" \
  --ads-account 6660356395 \
  --use-fallback \
  --output console

# 输出到文件
python3 run_skill.py --command generate \
  --keywords "KODAK LUMA350" \
  --ads-account 6660356395 \
  --output file

# 输出到飞书文档
python3 run_skill.py --command generate \
  --keywords "KODAK LUMA350" \
  --ads-account 6660356395 \
  --output feishu
```

## 参数

| 参数 | 必填 | 说明 |
|------|-----|------|
| --command | 是 | analyze（功能1） 或 generate（功能2） |
| --product-description | 否 | 商品描述文本（command=analyze时使用） |
| --url | 否 | Amazon商品URL（command=analyze时使用，优先于description） |
| --keywords | 否 | 种子关键词（command=generate时使用，多个用逗号分隔） |
| --ads-account | 是 | Google Ads账户ID |
| --output | 是 | console / file / feishu |
| --use-fallback | 否 | 启用gotrends.app fallback（429时自动切换） |

## 输出格式

表格形式呈现，包含列：
- Keyword（关键词）
- Avg Monthly Searches（月均搜索量）
- Competition（竞争程度：LOW/MEDIUM/HIGH）
- CPC Low（最低CPC，单位：美元）
- CPC High（最高CPC单位：美元）
- CPC Average（CPC平均值单位：美元）

## 注意

- 搜索量地域默认美国
- 语言默认英语
- 功能1使用AI语义分析提取关键词，无需额外配置LLM
- 默认调用间隔2秒，避免触发429
- fallback会在Google被限流后自动重试gotrends.app