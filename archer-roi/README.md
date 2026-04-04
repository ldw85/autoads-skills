# Archer × Google Ads ROI 计算器

## 功能
计算 Google Ads 广告系列在 Archer 联盟平台上的收益率（ROI / ROAS）

## 工作原理

### 数据关联
Google Ads 广告 URL 包含追踪参数：
```
https://www.amazon.com/dp/B08DL8WH9V
  ?maas=maas_adg_api_...
  &aa_campaignid=lv_xxx     ← Archer link 对应
  &aa_adgroupid=lv_yyy
  &aa_creativeid=lv_zzz
```

通过 `aa_campaignid` / `aa_adgroupid` / `aa_creativeid` 将：
- **Google Ads 花费数据** ↔ **Archer 佣金数据**

## 安全说明

- **密码不存储在任何文件中**
- 凭证仅从环境变量读取
- Access Token 仅存内存，不过期重试

## 使用步骤

### 1. 安装依赖
```bash
pip install requests
```

### 2. 配置凭证
```bash
export ARCHER_USERNAME=你的用户名
export ARCHER_PASSWORD=你的密码
```
或运行交互式配置：
```bash
python3 main.py --configure
```

### 3. 测试连接
```bash
python3 main.py --test
```

### 4. 生成报告
```bash
# 最近30天报告
python3 main.py --report

# 指定日期范围
python3 main.py --report --start 20260301 --end 20260331

# 输出 JSON
python3 main.py --report --format json --output /path/to/report.json
```

## 输出指标

| 指标 | 说明 |
|------|------|
| ROAS | 广告支出回报率 = 销售额 / 广告花费 |
| ROI% | 投资回报率 = (销售额 - 花费) / 花费 × 100% |
| CPA | 每次转化成本 = 花费 / 转化数 |
| RPC | 每次点击收入 = 销售额 / 点击数 |
| 佣金率 | Archer 佣金 / 销售额 |

## 关联逻辑说明

由于 Archer API 返回的 `link_data` 按 `link_name` 组织，
而 Google Ads 数据按 `campaign_id` 组织，关联方式如下：

1. **直接匹配**：Archer `link_name` ≈ Google Ads `campaign_name`
2. **ASIN 匹配**：两者都有 ASIN 时按 ASIN 关联
3. **参数匹配**：从 Archer 获取所有 link 后，按 URL 中的追踪参数匹配

如果关联不上（某些链接在 Archer 中没有对应数据），
会单独显示 Archer 数据，不显示 Google Ads 花费。
