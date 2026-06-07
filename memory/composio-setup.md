# Composio API Key 更新配置指南

## Composio 邮件监控配置步骤

### Step 1: 登录 Composio
```
https://app.composio.dev
```

### Step 2: 切换到 Platform 版本
- 界面右上角切换到 "for platform" 版本

### Step 3: 进入 Auth Configs
- 侧边栏选择 **Auth Configs**

### Step 4: 连接/刷新账户
1. 找到 USERID: `pb_asin_stt_mon@outlook.com` 的配置
2. 点击 **Connect Account** 连接 `pb_asin_stt_mon@outlook.com`
3. 如果没有配置，就在 Auth Configs 新建一个，选择刚才的 userid

### Step 5: 获取 Connected Account ID
- 连接成功后，记录显示的 connected_account_id（格式: ca_xxx）
- 当前有效ID: ca_h6jrQTnP0cPT（截至 2026-06-03）

### Step 6: 更新脚本配置
编辑文件: `/root/.openclaw/workspace/scripts/composio_email_monitor.py`

```python
# 第27行左右
API_KEY = os.environ.get('COMPOSIO_API_KEY', 'ak__6l6HT0MCX-Rvxg9DsFj')

# 第29-30行  
CONNECTED_ACCOUNT_ID = 'ca_h6jrQTnP0cPT'
USER_ID = 'pb_asin_stt_mon@outlook.com'
```

### Step 7: 测试运行
```bash
COMPOSIO_API_KEY='ak__6l6HT0MCX-Rvxg9DsFj' python3 /root/.openclaw/workspace/scripts/composio_email_monitor.py --check
```

## 当前配置（2026-06-03）
- API Key: ak__6l6HT0MCX-Rvxg9DsFj
- Connected Account: ca_h6jrQTnP0cPT
- User: pb_asin_stt_mon@outlook.com

## 常见问题
1. "No connected account found" → 需要在 Auth Configs 重新连接 Outlook
2. "status is INITIATED not ACTIVE" → OAuth 未完成，需要在界面完成授权
3. "API key invalid" → API key 过期，需要获取新的 key