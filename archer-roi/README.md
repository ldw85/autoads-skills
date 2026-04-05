# Archer × Google Ads ROI 计算器

## 功能
- **ROI 报告**：计算 Google Ads 广告系列在 Archer 联盟平台上的收益率
- **产品监控**：每隔2小时检测 Archer 中的被删产品，自动暂停对应广告系列

---

## 🚀 快速上手（3步完成设置）

### 步骤1：初始化凭证（只需一次）

```bash
cd /root/.openclaw/workspace/archer-roi
python3 cred-agent.py --init
```

交互式输入：
- Master 密码（至少8位，用于加密存储）
- Archer 用户名和密码

### 步骤2：启动守护进程

```bash
python3 cred-agent.py --daemon
```

输入步骤1设置的 master 密码即可启动。

### 步骤3：验证

```bash
python3 cred-agent.py --list
```

看到 `ARCHER_USERNAME` 和 `ARCHER_PASSWORD` 即表示成功。

---

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

### Credential Agent 安全机制

凭证通过以下方式保护：
- **Master 密码不存储** - 每次启动守护进程时输入
- **AES 加密存储** - 凭证加密保存在 `/tmp/openclaw-cred-agent.enc`
- **内存运行** - 解密后的凭证仅存在内存
- **Unix Socket** - 仅 root 可通过 socket 访问

详见 [CREDENTIAL_AGENT.md](CREDENTIAL_AGENT.md)

## 常用命令

```bash
# 启动/重启守护进程
python3 cred-agent.py --daemon

# 查看所有凭证名
python3 cred-agent.py --list

# 获取单个凭证值
python3 cred-agent.py --get ARCHER_PASSWORD

# 更新凭证
python3 cred-agent.py --set ARCHER_USERNAME=newuser ARCHER_PASSWORD=newpass

# 关闭守护进程
python3 cred-agent.py --shutdown

# 重新初始化（更换master密码）
python3 cred-agent.py --init
```

## ROI 报告

```bash
# 生成最近30天报告
python3 main.py --report

# 指定日期范围
python3 main.py --report --start 20260301 --end 20260331

# 输出 JSON
python3 main.py --report --format json --output report.json
```

### 输出指标

| 指标 | 说明 |
|------|------|
| ROAS | 广告支出回报率 = 销售额 / 广告花费 |
| ROI% | 投资回报率 = (销售额 - 花费) / 花费 × 100% |
| CPA | 每次转化成本 = 花费 / 转化数 |
| RPC | 每次点击收入 = 销售额 / 点击数 |
| 佣金率 | Archer 佣金 / 销售额 |

## 产品监控

### 工作流程
1. 从 `/get_all_links` 获取当前所有已创建的 ASIN
2. 对每个 ASIN 调用 `/check_product` 实时验证是否仍然有效
3. 无效的 ASIN → 在 Google Ads 中搜索 `final_url` 包含该 ASIN 的广告
4. 自动暂停对应的广告系列

### 手动命令
```bash
# 执行一次监控
python3 monitor_main.py --run

# 查看监控状态
python3 monitor_main.py --status

# 列出所有无效产品
python3 monitor_main.py --list-removed

# 手动暂停指定 ASIN 的广告
python3 monitor_main.py --pause-asin B08DL8WH9V
```

### 数据文件
- 无效记录：`logs/removed_products.json`
- 日志：`logs/monitor_result_YYYYMMDD_HHMMSS.json`

## Archer API 字段映射

```json
// /link_data
{
  "pagination_info": { "total_pages": 1, "current_page": 1, ... },
  "Links_Data": [{
    "totalClickThroughs": 123,
    "totalAttributedSales14d": 456.78,
    "totalUnitsSold14d": 5,
    "commission_amount": 25.00,
    "link_info": {
      "link_name": "...",
      "asin": "B08DL8WH9V"
    }
  }]
}
```

---

## 关联逻辑

由于 Archer API 返回的 `link_data` 按 `link_name` 组织，
而 Google Ads 数据按 `campaign_id` 组织，关联方式如下：

1. **直接匹配**：Archer `link_name` ≈ Google Ads `campaign_name`
2. **ASIN 匹配**：两者都有 ASIN 时按 ASIN 关联
3. **参数匹配**：从 Archer 获取所有 link 后，按 URL 中的追踪参数匹配

如果关联不上，会单独显示 Archer 数据，不显示 Google Ads 花费。
