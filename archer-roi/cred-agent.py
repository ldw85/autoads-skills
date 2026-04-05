#!/usr/bin/env python3
"""
Credential Agent - 安全凭证存储服务
===================================
- 凭证加密存储在内存中
- 通过 Unix socket 通信
- 使用 Fernet (AES-128-CBC + HMAC) 加密

使用方式:
  # 启动为守护进程（交互式输入master密码）
  python3 cred-agent.py --daemon

  # 设置凭证（需要先启动守护进程）
  python3 cred-agent.py --set ARCHER_USERNAME=user ARCHER_PASSWORD=pass

  # 读取凭证
  python3 cred-agent.py --get ARCHER_PASSWORD

  # 列出所有凭证名
  python3 cred-agent.py --list

  # 关闭守护进程
  python3 cred-agent.py --shutdown
"""

import os
import sys
import json
import socket
import argparse
import hashlib
import base64
import threading
from pathlib import Path

# 尝试导入加密库，不存在则提示安装
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("需要安装加密库: pip install cryptography")
    sys.exit(1)

# 配置
SOCKET_PATH = "/tmp/openclaw-cred-agent.sock"
CREDENTIALS_FILE = "/tmp/openclaw-cred-agent.enc"  # 加密后的凭证文件（重启后需重新设置）
SOCKET_BACKLOG = 5
BUFFER_SIZE = 4096


class CredentialAgent:
    def __init__(self, master_password: str = None):
        self.lock = threading.Lock()
        self.credentials = {}  # {"NAME": "VALUE", ...}
        self.fernet = None
        
        if master_password:
            self._init_crypto(master_password)
        elif Path(CREDENTIALS_FILE).exists():
            # 如果有加密文件但没有master password，无法解密
            pass

    def _derive_key(self, password: str, salt: bytes = b"openclaw-cred-agent-v1") -> bytes:
        """从master密码派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _init_crypto(self, master_password: str):
        """初始化加密器"""
        key = self._derive_key(master_password)
        self.fernet = Fernet(key)
        self._load_from_disk()

    def _load_from_disk(self):
        """从加密文件加载凭证"""
        if not Path(CREDENTIALS_FILE).exists():
            return
        
        try:
            with open(CREDENTIALS_FILE, "rb") as f:
                encrypted_data = f.read()
            
            if encrypted_data:
                decrypted = self.fernet.decrypt(encrypted_data)
                self.credentials = json.loads(decrypted)
                print(f"已从磁盘加载 {len(self.credentials)} 个凭证")
        except Exception as e:
            print(f"警告: 无法从磁盘加载凭证: {e}")
            self.credentials = {}

    def _save_to_disk(self):
        """加密保存凭证到磁盘"""
        if not self.fernet:
            return
        
        try:
            data = json.dumps(self.credentials).encode()
            encrypted = self.fernet.encrypt(data)
            with open(CREDENTIALS_FILE, "wb") as f:
                f.write(encrypted)
            os.chmod(CREDENTIALS_FILE, 0o600)  # 仅root可读写
        except Exception as e:
            print(f"警告: 无法保存凭证到磁盘: {e}")

    def set_credential(self, name: str, value: str):
        """设置凭证"""
        with self.lock:
            self.credentials[name.upper()] = value
            self._save_to_disk()
            return True

    def get_credential(self, name: str) -> str:
        """获取凭证"""
        with self.lock:
            return self.credentials.get(name.upper())

    def list_credentials(self) -> list:
        """列出所有凭证名（不显示值）"""
        with self.lock:
            return list(self.credentials.keys())

    def clear_all(self):
        """清除所有凭证"""
        with self.lock:
            self.credentials = {}
            if Path(CREDENTIALS_FILE).exists():
                os.remove(CREDENTIALS_FILE)


def handle_client(client_sock, agent: CredentialAgent):
    """处理客户端请求"""
    try:
        data = client_sock.recv(BUFFER_SIZE).decode().strip()
        
        if not data:
            return

        # 解析命令
        parts = data.split(maxsplit=1)
        cmd = parts[0].upper()
        
        if cmd == "GET" and len(parts) > 1:
            name = parts[1]
            value = agent.get_credential(name)
            if value is not None:
                client_sock.sendall(value.encode())
            # else: 发送空响应，表示不存在
            
        elif cmd == "SET" and len(parts) > 1:
            # SET NAME=VALUE
            try:
                name, value = parts[1].split("=", 1)
                agent.set_credential(name.strip(), value.strip())
                client_sock.sendall(b"OK")
            except ValueError:
                client_sock.sendall(b"ERROR: Invalid SET format, use NAME=VALUE")
                
        elif cmd == "LIST":
            names = agent.list_credentials()
            client_sock.sendall(json.dumps(names).encode())
            
        elif cmd == "SHUTDOWN":
            agent.clear_all()
            client_sock.sendall(b"OK")
            client_sock.close()
            raise KeyboardInterrupt  # 退出服务器循环
            
        else:
            client_sock.sendall(b"ERROR: Unknown command")
            
    except Exception as e:
        try:
            client_sock.sendall(f"ERROR: {e}".encode())
        except:
            pass
    finally:
        client_sock.close()


def run_server(agent: CredentialAgent):
    """运行Unix socket服务器"""
    # 清理旧的socket文件
    if Path(SOCKET_PATH).exists():
        os.remove(SOCKET_PATH)
    
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(SOCKET_PATH)
    server.listen(SOCKET_BACKLOG)
    os.chmod(SOCKET_PATH, 0o600)  # 仅root可访问
    
    print(f"Credential Agent 已启动，监听 {SOCKET_PATH}")
    
    try:
        while True:
            client, _ = server.accept()
            handle_client(client, agent)
    except KeyboardInterrupt:
        print("\n正在关闭...")
    finally:
        server.close()
        if Path(SOCKET_PATH).exists():
            os.remove(SOCKET_PATH)


def client_request(command: str, timeout: float = 2.0) -> str:
    """发送请求到服务器并返回响应"""
    if not Path(SOCKET_PATH).exists():
        return None
        
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(timeout)
        client.connect(SOCKET_PATH)
        client.sendall(command.encode())
        
        # 接收响应
        chunks = []
        while True:
            try:
                chunk = client.recv(BUFFER_SIZE)
                if not chunk:
                    break
                chunks.append(chunk)
            except socket.timeout:
                break
        response = b"".join(chunks)
        client.close()
        return response.decode() if response else None
    except Exception as e:
        return None


def ensure_daemon_running() -> bool:
    """确保守护进程正在运行，不在则自动启动"""
    if Path(SOCKET_PATH).exists():
        # 尝试通信测试
        if client_request("LIST") is not None:
            return True
    
    # 需要启动
    import getpass
    print("Credential Agent 未运行，正在启动...")
    
    # 需要master密码解密
    if not Path(CREDENTIALS_FILE).exists():
        print("错误: 凭证文件不存在，请先运行 --init")
        return False
    
    try:
        master_password = getpass.getpass("Master 密码: ")
    except EOFError:
        print("需要master密码来启动")
        return False
    
    # 启动守护进程
    import subprocess
    import tempfile
    
    # 用master密码启动（通过环境变量传递会有安全问题，这里用文件）
    # 实际上更好的方式是让守护进程自己提示输入
    print("请手动启动守护进程: python3 cred-agent.py --daemon")
    print("或在另一个终端运行: python3 /root/.openclaw/workspace/scripts/cred-agent.py --daemon")
    return False


def get_passwords_from_stdin() -> dict:
    """从stdin读取密码对（用于管道输入）"""
    passwords = {}
    for line in sys.stdin:
        line = line.strip()
        if "=" in line:
            key, value = line.split("=", 1)
            passwords[key.strip().upper()] = value.strip()
    return passwords


def interactive_set(agent: CredentialAgent):
    """交互式设置master密码和凭证"""
    import getpass
    
    print("\n=== Credential Agent 设置 ===")
    print("提示: 输入 master 密码来加密你的凭证")
    print()
    
    # 读取master密码
    while True:
        master1 = getpass.getpass("设置 master 密码: ")
        if len(master1) < 8:
            print("密码至少8位")
            continue
        master2 = getpass.getpass("确认 master 密码: ")
        if master1 != master2:
            print("密码不匹配")
            continue
        break
    
    # 初始化加密
    agent._init_crypto(master1)
    
    # 读取凭证
    print("\n输入要存储的凭证（格式: NAME=value），输入空行结束:")
    while True:
        try:
            line = input("> ").strip()
            if not line:
                break
            if "=" in line:
                name, value = line.split("=", 1)
                agent.set_credential(name.strip(), value.strip())
                print(f"  已存储: {name.strip()}")
        except EOFError:
            break
    
    print(f"\n已存储 {len(agent.credentials)} 个凭证")
    print("运行 --daemon 启动服务")
    
    # 保持凭证在内存中（以便后续--daemon使用同一个对象）
    return agent


def main():
    parser = argparse.ArgumentParser(description="Credential Agent - 安全凭证存储")
    parser.add_argument("--daemon", action="store_true", help="启动为守护进程")
    parser.add_argument("--set", metavar="NAME=VALUE", nargs="+", help="设置凭证")
    parser.add_argument("--get", metavar="NAME", help="获取凭证")
    parser.add_argument("--list", action="store_true", help="列出所有凭证名")
    parser.add_argument("--shutdown", action="store_true", help="关闭守护进程")
    parser.add_argument("--init", action="store_true", help="初始化（交互式设置）")
    
    args = parser.parse_args()
    
    # 交互式初始化
    if args.init:
        agent = CredentialAgent()
        agent = interactive_set(agent)
        return
    
    # 如果有加密文件，需要master密码才能解密
    has_encrypted_file = Path(CREDENTIALS_FILE).exists()
    master_password = None
    
    if has_encrypted_file and (args.set or args.get or args.list or args.daemon):
        import getpass
        master_password = getpass.getpass("Master 密码: ")
    
    # 创建agent实例
    if master_password:
        agent = CredentialAgent(master_password)
    else:
        agent = CredentialAgent()
    
    # 守护进程模式
    if args.daemon:
        if not has_encrypted_file:
            print("错误: 需要先使用 --init 初始化凭证")
            sys.exit(1)
        run_server(agent)
        return
    
    # 设置凭证
    if args.set:
        for item in args.set:
            if "=" in item:
                name, value = item.split("=", 1)
                agent.set_credential(name.strip(), value.strip())
        # 保存到磁盘
        # 注意: 需要先初始化加密才能保存
        if agent.fernet:
            agent._save_to_disk()
            print(f"已保存 {len(args.set)} 个凭证")
        else:
            print("错误: 需要master密码才能保存")
        return
    
    # 获取凭证
    if args.get:
        value = agent.get_credential(args.get)
        if value is not None:
            print(value)
        # else: 尝试通过socket查询运行中的守护进程
        else:
            response = client_request(f"GET {args.get}")
            if response:
                print(response)
            else:
                print(f"凭证 {args.get} 不存在")
        return
    
    # 列出凭证
    if args.list:
        names = agent.list_credentials()
        if not names and has_encrypted_file:
            # 尝试通过socket查询
            response = client_request("LIST")
            if response:
                names = json.loads(response)
        
        if names:
            print("已存储的凭证:")
            for name in names:
                print(f"  {name}")
        else:
            print("没有存储的凭证")
        return
    
    # 关闭守护进程
    if args.shutdown:
        response = client_request("SHUTDOWN")
        if response == "OK":
            print("已关闭守护进程")
        else:
            print("守护进程未运行")
        return
    
    # 默认显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
