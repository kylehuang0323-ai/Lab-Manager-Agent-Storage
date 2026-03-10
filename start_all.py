"""
一键启动脚本 — 同时运行 Flask Dashboard + Teams Bot + Dev Tunnel
用法: python start_all.py
"""

import os
import sys
import subprocess
import time
import signal

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

# 加载 .env
from dotenv import load_dotenv
load_dotenv()

processes = []


def cleanup(sig=None, frame=None):
    print("\n🛑 正在停止所有服务...")
    for name, proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
            print(f"  ✅ {name} 已停止")
        except Exception:
            proc.kill()
            print(f"  ⚠️ {name} 强制停止")
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def start():
    print("=" * 55)
    print("🚀 Lab Manager — All Services Launcher")
    print("=" * 55)

    # 1. Flask Dashboard (port 5001)
    print("\n[1/3] 启动 Flask Dashboard (port 5001)...")
    flask_proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=PROJECT_DIR,
        env={**os.environ},
    )
    processes.append(("Flask Dashboard", flask_proc))
    time.sleep(2)

    # 2. Teams Bot (port 3978)
    bot_id = os.getenv("BOT_APP_ID", "")
    if not bot_id:
        print("\n[2/3] ⚠️  BOT_APP_ID 未配置，跳过 Teams Bot")
        print("      请先在 Azure Portal 注册 Bot 并填写 .env")
    else:
        print(f"\n[2/3] 启动 Teams Bot (port 3978, App ID: {bot_id[:8]}...)...")
        bot_proc = subprocess.Popen(
            [sys.executable, "bot_app.py"],
            cwd=PROJECT_DIR,
            env={**os.environ},
        )
        processes.append(("Teams Bot", bot_proc))
        time.sleep(2)

    # 3. Dev Tunnel
    if not bot_id:
        print("\n[3/3] ⚠️  跳过 Dev Tunnel (需要先配置 Bot)")
    else:
        print("\n[3/3] 启动 Dev Tunnel (tunnel → port 3978)...")
        print("      ⏳ 首次使用需要 `devtunnel user login` 登录")
        tunnel_proc = subprocess.Popen(
            ["devtunnel", "host", "--port-numbers", "3978", "--allow-anonymous"],
            cwd=PROJECT_DIR,
        )
        processes.append(("Dev Tunnel", tunnel_proc))
        time.sleep(3)

    print("\n" + "=" * 55)
    print("✅ 服务已启动:")
    print(f"   🌐 Web Dashboard: http://localhost:5001")
    if bot_id:
        print(f"   🤖 Teams Bot:     http://localhost:3978/api/messages")
        print(f"   🔗 Dev Tunnel:    查看上方 tunnel URL")
    print("=" * 55)
    print("按 Ctrl+C 停止所有服务\n")

    # 等待所有进程
    try:
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"⚠️ {name} 已退出 (code {ret})")
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    start()
