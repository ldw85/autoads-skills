# Search Term Analyzer Skill

分析Google Ads广告系列的搜索词，识别语义不相关的搜索词并建议添加到否定关键词列表。

## 功能

1. **语义分析**：基于规则识别与广告产品不相关的搜索词
2. **分类输出**：按问题类型分类（办公打印机、价格导向、竞品品牌等）
3. **定时任务**：每2小时自动分析当天有花费的广告系列
4. **飞书通知**：分析完成后推送结果供用户确认

## 分析规则

### 🔴 高风险（建议加否定）

- **办公打印机**：laser, laserjet, inkjet, officejet, deskjet, envy, officejet
- **竞品品牌**：Canon selphy/pixma/tr/ts, Epson ecotank/et/l/wf/xp, HP deskjet/envy/officejet, Brother mfc/dcp
- **价格导向**：price, buy, cheap, discount, sale, for sale, budget
- **办公功能**：all in one, multifunction, copier, scanner, fax
- **购物平台**：amazon, walmart, best buy
- **错误类型**：sublimation, dtf（热转印设备）

### 🟡 中风险（建议优化匹配）

- 过于宽泛的词：printer, photo printer（无产品定向）
- 泛功能词：wireless printer（无照片打印定向）

## 触发方式

### 手工触发
```
执行搜索词分析
```

### 定时任务
- 每2小时执行一次（0:00, 2:00, 4:00, 6:00, 8:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00）
- 分析所有过去7天有花费>=$1的广告系列
- 有发现时发送飞书通知

## 输出格式

```
📊 搜索词质量分析报告

广告系列: Liene-Photo-Printer-PartnerBoost-US (ID: 23792756828)
总搜索词: 14 | 高风险: 6

🔴 建议添加否定关键词:
- carverall laser printer ($1.93, 1 click)
- hp 525 printer price ($1.92, 1 click)
- canon printer price ($1.81, 1 click)
...

🟡 可优化匹配:
- printer price in usa ($1.43, 1 click)
...
```

## 否定关键词添加规则

1. **严格匹配**：用于完全无关的搜索词（如激光打印机）
2. **词组匹配**：用于有一定相关性但意图模糊的词
3. **用户确认**：AI生成建议后需用户确认才实际添加