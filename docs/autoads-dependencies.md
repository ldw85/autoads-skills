# AutoAds 依赖配置清单

> 生成时间: 2026-03-30

---

## 🐍 Python 环境

| 依赖 | 版本 | 用途 |
|------|------|------|
| `PyYAML` | ≥6.0 | 配置文件解析 |
| `python-dotenv` | ≥1.0.0 | .env 环境变量读取 |
| `google-ads` | ≥22.0.0 | Google Ads API |
| `requests` | ≥2.31.0 | HTTP 请求 |
| `openai` | ≥1.12.0 | OpenAI 兼容接口 |
| `Pillow` | ≥10.0.0 | 图片处理 |
| `google-cloud-secret-manager` | (optional) | GCP 密钥管理 |

---

## 🔑 Google Ads API

### 方式一：直接环境变量（本地开发）

| 环境变量 | 说明 |
|----------|------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads API 开发者 Token |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | MCC 账户 ID（无连字符）|
| `GOOGLE_ADS_CUSTOMER_ID` | 目标广告账户 ID（无连字符）|
| `GOOGLE_ADS_SERVICE_ACCOUNT_JSON` | Service Account JSON 文件路径 |

### 方式二：GCP Secret Manager（生产环境/VPS）

| 环境变量 | 说明 |
|----------|------|
| `USE_SECRET_MANAGER` | 设为 `true` 启用 |
| `GCP_PROJECT_ID` | GCP 项目 ID |
| Secret Manager 中的 Secret IDs： | |
| `google-ads-developer-token` | Developer Token |
| `google-ads-login-customer-id` | Login Customer ID |
| `google-ads-customer-id` | Customer ID |
| `google-ads-client-id` | OAuth2 Client ID |
| `google-ads-client-secret` | OAuth2 Client Secret |
| `google-ads-refresh-token` | OAuth2 Refresh Token |

---

## 📡 Decodo Scraper

| 环境变量 | 说明 |
|----------|------|
| `DECODO_AUTH_TOKEN` | Decodo API Base64 Token（来自 Decodo Dashboard） |

**Decodo Scraper 路径**：`/root/.openclaw/workspace/skills/decodo-scraper/tools/scrape.py`

调用示例：
```bash
python3 /root/.openclaw/workspace/skills/decodo-scraper/tools/scrape.py \
  --target amazon \
  --url "https://www.amazon.com/dp/XXX"
```

---

## 🤖 AI 调用（新版 `AdResearcher`）

| 工具 | 说明 |
|------|------|
| `claude` (Claude Code CLI) | 通过 `claude --print --output-format json` 调用 |

**路径**：`/root/.nvm/versions/node/v22.22.1/bin/claude`

无需额外环境变量，使用当前系统已登录的 Claude 账号。

---

## 🤖 MiniMax API（旧版 `research_flow`）

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MINIMAX_API_KEY` | — | MiniMax API 密钥 |
| `MINIMAX_API_BASE_URL` | `https://api.minimaxi.com/anthropic/v1/chat/completions` | API 端点 |

> ⚠️ 旧版流程使用，新版 AI 调研（`--use-ai-research`）已改用 `claude --print`，不需要 MiniMax API。

---

## 💬 飞书 Bot

| 环境变量 | 说明 |
|----------|------|
| `FEISHU_APP_ID` | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret |
| `FEISHU_VERIFICATION_TOKEN` | 飞书 Verification Token |

---

## 🌐 代理（可选）

| 环境变量 | 说明 |
|----------|------|
| `HTTP_PROXY` | HTTP 代理地址 |
| `HTTPS_PROXY` | HTTPS 代理地址 |

用于 Google Ads API gRPC 连接。

---

## 📁 配置文件

| 文件 | 说明 |
|------|------|
| `config/config.yaml` | 主配置文件（包含默认值）|
| `.env` | 环境变量配置文件 |
| `.env.example` | 环境变量配置模板 |

---

## 🔗 依赖关系图

```
AutoAds
  ├── google-ads API
  │     ├── GOOGLE_ADS_DEVELOPER_TOKEN
  │     ├── GOOGLE_ADS_LOGIN_CUSTOMER_ID
  │     ├── GOOGLE_ADS_CUSTOMER_ID
  │     └── (GOOGLE_ADS_SERVICE_ACCOUNT_JSON | OAuth2 credentials)
  │
  ├── Decodo Scraper
  │     └── DECODO_AUTH_TOKEN
  │
  ├── Claude CLI (新版 AI 调研)
  │     └── claude --print（无需 token）
  │
  ├── MiniMax API (旧版调研流程)
  │     ├── MINIMAX_API_KEY
  │     └── MINIMAX_API_BASE_URL
  │
  ├── GCP Secret Manager (可选，生产环境)
  │     ├── USE_SECRET_MANAGER=true
  │     ├── GCP_PROJECT_ID
  │     └── Secret Manager 中的 6 个 Secret
  │
  ├── 飞书 Bot
  │     ├── FEISHU_APP_ID
  │     ├── FEISHU_APP_SECRET
  │     └── FEISHU_VERIFICATION_TOKEN
  │
  └── 代理（可选）
        ├── HTTP_PROXY
        └── HTTPS_PROXY
```

---

## ✅ 最小依赖（仅创建广告）

只需：
1. `DECODO_AUTH_TOKEN` — Decodo 爬取 Amazon
2. `claude` CLI — AI 生成文案和关键词
3. Google Ads API 凭证（Token / Service Account）
