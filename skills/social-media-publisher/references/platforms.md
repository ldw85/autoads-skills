# 各社交媒体平台配置指南

## Reddit

### API配置
- 需要Reddit开发者账号
- 创建应用获取：`client_id`, `client_secret`, `user_agent`
- 授权获取：`username`, `password`

### 发布规则
- 子版块规则差异大，需遵守各版块规则
- 每天发布数量有限制
- 支持：链接帖子、文本帖子

### API端点
```
POST /api/submit
```

## Medium

### API配置
- 使用Medium的OAuth或集成令牌
- 获取`integration_token`

### 发布规则
- 支持Markdown
- 可设置是否为付费内容
- 可添加标签（最多5个）

### API端点
```
POST https://api.medium.com/v1/users/{userId}/posts
```

## X (Twitter)

### API配置
- 需要Twitter开发者账号
- 创建应用获取：`API_KEY`, `API_SECRET`
- 获取`ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`

### 发布规则
- 每条推文<280字符
- 每天限制依账号类型不同
- 支持：文字、图片、链接、视频

### API端点
```
POST https://api.twitter.com/2/tweets
```

## 凭证存储

建议将凭证存储在环境变量或安全的配置文件中：
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `MEDIUM_INTEGRATION_TOKEN`
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`
