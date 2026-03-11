"""
一键启动 Lab Manager + ngrok 隧道
适用于 Copilot Studio REST API 集成

用法:
    python start_copilot.py              # 启动 Flask + ngrok
    python start_copilot.py --no-tunnel  # 仅启动 Flask（手动管理隧道）
    python start_copilot.py --port 5001  # 指定端口
"""

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

FLASK_PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 5001
processes = []
ngrok_url = None


def _log(tag, msg, color=""):
    colors = {"green": "\033[92m", "blue": "\033[94m", "yellow": "\033[93m",
              "red": "\033[91m", "cyan": "\033[96m", "bold": "\033[1m", "reset": "\033[0m"}
    c = colors.get(color, "")
    r = colors["reset"] if c else ""
    print(f"{c}[{tag}]{r} {msg}")


def _stream_output(proc, tag, color):
    try:
        for line in iter(proc.stdout.readline, ""):
            if line.strip():
                _log(tag, line.strip(), color)
    except (ValueError, OSError):
        pass


def start_flask():
    _log("Flask", f"启动 Web Dashboard & API on http://localhost:{FLASK_PORT}", "green")
    env = os.environ.copy()
    env["FLASK_RUN_PORT"] = str(FLASK_PORT)
    p = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, cwd=BASE_DIR, env=env,
    )
    processes.append(("Flask", p))
    threading.Thread(target=_stream_output, args=(p, "Flask", "green"), daemon=True).start()
    return p


def start_ngrok():
    global ngrok_url
    _log("ngrok", f"启动 ngrok 隧道 → http://localhost:{FLASK_PORT}", "cyan")
    p = subprocess.Popen(
        ["ngrok", "http", str(FLASK_PORT), "--log", "stdout", "--log-format", "json"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, cwd=BASE_DIR,
    )
    processes.append(("ngrok", p))

    def _read_ngrok():
        global ngrok_url
        try:
            for line in iter(p.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                try:
                    log = json.loads(line)
                    url = log.get("url", "")
                    if url and url.startswith("https://"):
                        ngrok_url = url
                        print()
                        _log("ngrok", "=" * 60, "bold")
                        _log("ngrok", f"🌐 公网 URL: {ngrok_url}", "cyan")
                        _log("ngrok", f"🤖 Copilot Studio API 端点: {ngrok_url}/api/chat", "cyan")
                        _log("ngrok", f"❤️  健康检查: {ngrok_url}/api/health", "cyan")
                        _log("ngrok", "=" * 60, "bold")
                        print()
                        _update_openapi(ngrok_url)
                except json.JSONDecodeError:
                    if "https://" in line:
                        m = re.search(r"(https://[^\s\"]+\.ngrok[^\s\"]*)", line)
                        if m:
                            ngrok_url = m.group(1)
                            _log("ngrok", f"🌐 公网 URL: {ngrok_url}", "cyan")
                            _update_openapi(ngrok_url)
        except (ValueError, OSError):
            pass

    threading.Thread(target=_read_ngrok, daemon=True).start()
    return p


def _update_openapi(public_url):
    """自动更新 openapi.yaml 中的 servers URL"""
    spec_path = os.path.join(BASE_DIR, "openapi.yaml")
    if not os.path.exists(spec_path):
        return
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(
            r'(url:\s*)https?://[^\s]+',
            rf'\g<1>{public_url}',
            content,
            count=1,
        )
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(content)
        _log("ngrok", f"✅ openapi.yaml 已更新 servers.url → {public_url}", "green")
    except Exception as e:
        _log("ngrok", f"⚠ 更新 openapi.yaml 失败: {e}", "yellow")


def get_ngrok_url():
    """通过 ngrok API 获取公网 URL（备用方案）"""
    for _ in range(15):
        time.sleep(2)
        try:
            req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                for t in data.get("tunnels", []):
                    if t.get("proto") == "https":
                        return t["public_url"]
        except Exception:
            continue
    return None


def cleanup(*_):
    _log("System", "正在关闭所有服务...", "yellow")
    for name, p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
            _log("System", f"  ✓ {name} 已关闭", "yellow")
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    sys.exit(0)


def main():
    no_tunnel = "--no-tunnel" in sys.argv

    print()
    print("=" * 64)
    print("  🚀 Lab Manager — Copilot Studio 集成启动器")
    print("=" * 64)
    print()
    print(f"  📦 Web Dashboard  → http://localhost:{FLASK_PORT}")
    print(f"  🤖 API Endpoint   → http://localhost:{FLASK_PORT}/api/chat")
    if not no_tunnel:
        print("  🔗 ngrok Tunnel   → 自动启动 (等待公网 URL...)")
    print()
    print("  📄 OpenAPI 规范   → openapi.yaml")
    print("  按 Ctrl+C 关闭所有服务")
    print("=" * 64)
    print()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    start_flask()
    time.sleep(2)

    if not no_tunnel:
        start_ngrok()
        time.sleep(3)

        # 如果日志没抓到 URL，用 API 获取
        global ngrok_url
        if not ngrok_url:
            _log("ngrok", "从 API 获取公网 URL...", "cyan")
            url = get_ngrok_url()
            if url:
                ngrok_url = url
                _log("ngrok", "=" * 60, "bold")
                _log("ngrok", f"🌐 公网 URL: {ngrok_url}", "cyan")
                _log("ngrok", f"🤖 Copilot Studio API: {ngrok_url}/api/chat", "cyan")
                _log("ngrok", "=" * 60, "bold")
                _update_openapi(ngrok_url)
            else:
                _log("ngrok", "⚠ 未获取到公网 URL，请检查 ngrok 状态", "red")
                _log("ngrok", "  访问 http://127.0.0.1:4040 查看 ngrok 面板", "yellow")
    else:
        _log("提示", "Tunnel 未启动，请手动提供公网 HTTPS URL", "yellow")

    print()
    _log("Copilot Studio", "━" * 56, "bold")
    _log("Copilot Studio", "📋 配置步骤:", "bold")
    _log("Copilot Studio", "  1. 打开 https://copilotstudio.microsoft.com", "blue")
    _log("Copilot Studio", "  2. 创建新 Agent → 添加 Action → REST API", "blue")
    _log("Copilot Studio", "  3. 上传项目中的 openapi.yaml 文件", "blue")
    _log("Copilot Studio", "  4. 发布 Agent 到 Teams 频道", "blue")
    _log("Copilot Studio", "━" * 56, "bold")
    print()

    # 守护进程
    try:
        while True:
            for name, p in processes:
                if p.poll() is not None:
                    _log("System", f"⚠ {name} 已退出 (code={p.returncode})", "red")
                    cleanup()
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
