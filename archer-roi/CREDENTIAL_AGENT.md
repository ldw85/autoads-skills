# Credential Agent - 安全凭证存储

## 工作原理

1. **加密存储**: 凭证用 master 密码加密后保存在磁盘 (`/tmp/openclaw-cred-agent.enc`)
2. **内存运行**: 守护进程将解密后的凭证保存在内存中
3. **Socket 通信**: 通过 Unix socket (`/tmp/openclaw-cred-agent.sock`) 提供服务

## 使用步骤

### 1. 首次设置（只需一次）

在终端执行以下命令，会交互式要求你输入 master 密码和凭证：

```bash
python3 /root/.openclaw/workspace/scripts/cred-agent.py --init
```

交互示例：
```
=== Credential Agent 设置 ===
提示: 输入 master 密码来加密你的凭证

设置 master 密码: ********
确认 master 密码: ********

输入要存储的凭证（格式: NAME=value），输入空行结束:
> ARCHER_USERNAME=your_username
> ARCHER_PASSWORD=your_password
>
已存储: 2 个凭证

运行 --daemon 启动服务
```

### 2. 启动守护进程

```bash
python3 /root/.openclaw/workspace/scripts/cred-agent.py --daemon
```

启动后会提示输入 master 密码（用于解密已存储的凭证）。

### 3. 验证

```bash
python3 /root/.openclaw/workspace/scripts/cred-agent.py --list
```

### 4. Cron 任务使用

定时任务会自动通过 socket 获取凭证，无需额外配置。

## 常用命令

```bash
# 设置凭证
python3 cred-agent.py --set ARCHER_USERNAME=user ARCHER_PASSWORD=pass

# 获取凭证
python3 cred-agent.py --get ARCHER_PASSWORD

# 列出所有凭证名
python3 cred-agent.py --list

# 关闭守护进程
python3 cred-agent.py --shutdown

# 重新初始化
python3 cred-agent.py --init
```

## 安全说明

- Master 密码不会存储在任何地方，每次启动守护进程时需要输入
- 加密凭证保存在 `/tmp/openclaw-cred-agent.enc`，权限 600
- Unix socket 权限 600，仅 root 可访问
- 守护进程重启后需要重新输入 master 密码
