# Scripts

## run-monitor.sh

Archer 产品监控定时任务包装脚本。

通过 Unix socket 从 cred-agent 获取加密存储的 Archer 凭证，然后执行监控。

**依赖：**
- socat
- cred-agent.py 守护进程

**使用：**
```bash
bash scripts/run-monitor.sh
```
