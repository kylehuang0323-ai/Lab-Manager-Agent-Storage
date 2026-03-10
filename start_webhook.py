"""
一键启动 Lab Manager + Teams Outgoing Webhook
无需 Azure 订阅，自动启动 Flask + Webhook + Dev Tunnel

用法:
    python start_webhook.py
    python start_webhook.py --no-tunnel   # 不启动 Dev Tunnel（手动管理）
"""

import os
import sys
import signal
import subprocess
import time
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

FLASK_PORT = 5001
WEBHOOK_PORT = 3978
processes = []


def _log(tag, msg, color=""):
    colors = {"green": "\033[92m", "blue": "\033[94m", "yellow": "\033[93m",
              "red": "\033[91m", "cyan": "\033[96m", "reset": "\033[0m"}
    c = colors.get(color, "")
    r = colors["reset"] if c else ""
    print(f"{c}[{tag}]{r} {msg}")


def _stream_output(proc, tag, color):
    """流式打印子进程输出"""
    try:
        for line in iter(proc.stdout.readline, ""):
            if line.strip():
                _log(tag, line.strip(), color)
    except (ValueError, OSError):
        pass


def start_flask():
    _log("Flask", f"启动 Web Dashboard on http://localhost:{FLASK_PORT}", "green")
    p = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, cwd=BASE_DIR,
    )
    processes.append(("Flask", p))
    threading.Thread(target=_stream_output, args=(p, "Flask", "green"), daemon=True).start()
    return p


def start_webhook():
    _log("Webhook", f"启动 Teams Webhook Bot on http://localhost:{WEBHOOK_PORT}", "blue")
    p = subprocess.Popen(
        [sys.executable, "webhook_bot.py"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, cwd=BASE_DIR,
    )
    processes.append(("Webhook", p))
    threading.Thread(target=_stream_output, args=(p, "Webhook", "blue"), daemon=True).start()
    return p


def start_tunnel():
    _log("Tunnel", f"启动 Dev Tunnel (port {WEBHOOK_PORT})...", "cyan")
    p = subprocess.Popen(
        ["devtunnel", "host", "--port-numbers", str(WEBHOOK_PORT), "--allow-anonymous"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, cwd=BASE_DIR,
    )
    processes.append(("Tunnel", p))
    threading.Thread(target=_stream_output, args=(p, "Tunnel", "cyan"), daemon=True).start()
    return p


def cleanup(*_):
    _log("System", "正在关闭所有服务...", "yellow")
    for name, p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
            _log("System", f"  ✓ {name} 已关闭", "yellow")
        except Exception:
            p.kill()
    sys.exit(0)


def main():
    no_tunnel = "--no-tunnel" in sys.argv

    print()
    print("=" * 60)
    print("🚀 Lab Manager — 一键启动 (Outgoing Webhook 模式)")
    print("=" * 60)
    print()
    print("  📦 Web Dashboard  → http://localhost:5001")
    print(f"  🤖 Webhook Bot    → http://localhost:{WEBHOOK_PORT}/api/messages")
    if not no_tunnel:
        print("  🔗 Dev Tunnel     → 自动启动 (查看日志获取 HTTPS URL)")
    print()
    print("  按 Ctrl+C 关闭所有服务")
    print("=" * 60)
    print()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    start_flask()
    time.sleep(1)
    start_webhook()

    if not no_tunnel:
        time.sleep(1)
        start_tunnel()
        print()
        _log("提示", "📋 复制 Dev Tunnel 日志中的 HTTPS URL", "yellow")
        _log("提示", "   然后在 Teams 频道中创建 Outgoing Webhook，填入:", "yellow")
        _log("提示", "   URL: https://<tunnel-id>.devtunnels.ms/api/messages", "yellow")
    else:
        print()
        _log("提示", "Tunnel 未启动，请手动提供 HTTPS URL", "yellow")

    # 守护进程
    try:
        while True:
            for name, p in processes:
                if p.poll() is not None:
                    _log("System", f"⚠️ {name} 已退出 (code={p.returncode})", "red")
                    processes.remove((name, p))
            if not processes:
                _log("System", "所有服务已退出", "red")
                break
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
