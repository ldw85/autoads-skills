---
name: google-ads-creator
description: Google Ads素材生成。根据输入的产品信息和营销文案，生成符合Google Ads格式的关键词(Keywords)、广告标题(Headlines)、描述(Descriptions)、附加链接(Sitelinks)等。自动遵守Google Ads字符数限制。输出英文。
---

# Google Ads素材生成

本skill根据输入的产品信息和营销文案，生成完整的Google Ads广告素材。

## Google Ads规范

| 字段 | 数量限制 | 字符限制 |
|------|---------|---------|
| Headlines | 15个 | 30字符/个 |
| Descriptions | 4个 | 90字符/个 |
| Sitelinks | 4-6个 | 25字符/个 |
| Callouts | 5个 | 25字符/个 |
| Keywords | 建议50-100个 | 长尾优先 |

## Google Ads 政策要求（必须遵守）

### 1. 禁止内容 Prohibited Content
生成素材时，**绝对禁止**包含以下内容：
- 假冒商品（Counterfeit goods）
- 危险产品/服务（武器、毒品、烟草、爆炸物等）
- 促成不诚实行为（黑客软件、假证件、学术作弊）
- 不当内容（仇恨言论、歧视、暴力、成人内容）

### 2. 禁止行为 Prohibited Practices
- **禁止**虚假陈述（Misrepresentation）
- **禁止**误导性承诺（"立即致富"、"保证减肥X斤"）
- **禁止**隐瞒收费信息

### 3. 编辑规范 Editorial
- **禁止** gimmicky 写法：
  - "FREE", "100% FREE", "f-r-e-e"
  - "Guaranteed", "No risk", "No questions asked"
  - 过多感叹号 "!!!" 
  - 过度大写 "ALL CAPS"
- **禁止**过于泛泛的表达：
  - "Buy products here"
  - "Best product ever"
  - "Unbeatable price"

### 4. 字符限制（严格遵守）
- Headline ≤ 30字符
- Description ≤ 90字符
- Sitelink ≤ 25字符
- Callout ≤ 25字符

---

## 违规词过滤列表

生成素材时，**必须过滤**以下词汇和表达：

### 绝对禁止（触发即拒）
| 类别 | 违规词/表达 |
|------|------------|
| 虚假承诺 | "guaranteed", "100% free", "no risk", "no questions asked", "instant money", "lose weight fast", "miracle cure" |
| 夸大宣传 | "best ever", "number 1", "unbeatable", "never before", "once in a lifetime" |
| 诱导性词汇 | "act now", "limited time only", "today only", "don't miss out"（可用但需谨慎） |
| 绝对化 | "never", "always", "every time", "all", "100%"（除真实数据外） |

### 需要谨慎（视产品而定）
| 类别 | 词汇 |
|------|------|
| 健康声称 | "cure", "treat", "prevent", "heal"（非保健品可用） |
| 金融声称 | "make money", "earn", "profit", "investment returns" |
| 比较级 | "better than", "best", "worst"（需有依据） |

---

## 输出要求

1. **全部使用英文输出**
2. **纯文本格式**，无多余符号
3. **输出到文件**，每条换行
4. **章节只保留**：keywords, headlines, descriptions, sitelinks, callouts
5. **严格遵守政策**：真实、专业、不夸大
6. **生成后必须检查**：使用违规词过滤列表扫描输出

## 输入要求

用户提供以下信息：
1. **产品名称和类型**
2. **目标受众**
3. **主要卖点**
4. **落地页URL**

## 关键词策略

### 关键词分类
1. **Brand**: 产品名、品牌名
2. **Category**: 产品类别
3. **Benefit**: 产品解决的问题
4. **Pain Point**: 用户困扰和焦虑
5. **Long-tail**: 问题+产品类型+场景

## 输出格式

### Keywords
```
Brand
apple watch series 11
apple watch 11

Category
smartwatch
fitness watch

Benefit
ecg watch
heart rate monitor

Pain Point
battery life smartwatch
small screen smartwatch

Long-tail
best apple watch for health monitoring
```

### Headlines（每个≤30字符）
```
Apple Watch Series 11
Thinnest Design Ever
Largest Display Screen
ECG Heart Monitoring
100+ Workout Modes
```

### Descriptions（每条≤90字符）
```
The thinnest Apple Watch ever with largest display. ECG heart monitoring and 100+ workout modes. Order now.
```

### Sitelinks
```
Health Features
Fitness Tracking
Technical Specs
FAQ
```

### Callouts
```
Free Shipping
30-Day Returns
```

---

## 生成后检查清单

完成素材生成后，**必须**执行以下检查：

1. **字符数检查**
   - [ ] 所有 Headline ≤ 30字符
   - [ ] 所有 Description ≤ 90字符
   - [ ] 所有 Sitelink ≤ 25字符
   - [ ] 所有 Callout ≤ 25字符

2. **违规词检查**
   - [ ] 无 "guaranteed", "100% free", "no risk"
   - [ ] 无 "best ever", "unbeatable", "miracle"
   - [ ] 无过度感叹号或全大写
   - [ ] 无虚假承诺

3. **政策合规**
   - [ ] 内容真实可验证
   - [ ] 无假冒产品推广
   - [ ] 无危险/违法产品
