# AutoAds 执行超时说明

## 问题
广告创建等长时间任务默认exec超时30秒会被SIGKILL强制终止。

## 解决方案

### 方案1：使用后台exec（推荐用于>2分钟的任务）

```bash
# 启动后台执行
exec --command "cd /root/.openclaw/workspace/autoads && python3 -m src.main --command create --url '...' 2>&1" --background

# 然后用 process 工具轮询
process --action poll --sessionId <session_id> --timeout 300000
```

### 方案2：使用 yieldMs 参数

```bash
exec --command "cd /root/.openclaw/workspace/autoads && python3 -m src.main ..." --yieldMs 300000 --timeout 600
```

参数说明：
- `yieldMs=600000`: 10分钟后后台化，继续等待
- `timeout=900`: 总超时15分钟

### 方案3：使用 sessions_spawn 隔离session

```python
sessions_spawn(
  task="cd /root/.openclaw/workspace/autoads && python3 -m src.main --command create --url '...' --customer-id 6052559425",
  runTimeoutSeconds=900,
  mode="run"
)
```

## 推荐工作流

对于广告创建（通常需2-5分钟）：
1. 使用 sessions_spawn 隔离执行，设置 runTimeoutSeconds=900（15分钟）
2. 或使用后台exec + poll方式，设置 timeout=900

