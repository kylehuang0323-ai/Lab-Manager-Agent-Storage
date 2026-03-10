"""
Teams Outgoing Webhook 设置向导
无需 Azure 订阅！只需在 Teams 频道中创建 Outgoing Webhook

运行: python setup_webhook.py
"""

import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ANSI Colors
G = "\033[92m"   # green
B = "\033[94m"   # blue
Y = "\033[93m"   # yellow
C = "\033[96m"   # cyan
R = "\033[0m"    # reset
BOLD = "\033[1m"


def banner():
    print(f"""
{C}╔══════════════════════════════════════════════════════════╗
║  🤖 Lab Manager — Teams Outgoing Webhook 设置向导       ║
║  无需 Azure 订阅！                                       ║
╚══════════════════════════════════════════════════════════╝{R}
""")


def check_prereqs():
    print(f"{BOLD}📋 Step 1: 检查前置条件{R}\n")
    ok = True

    # Python
    print(f"  Python ............ {G}✓ {sys.version.split()[0]}{R}")

    # Flask
    try:
        import flask
        print(f"  Flask ............. {G}✓ {flask.__version__}{R}")
    except ImportError:
        print(f"  Flask ............. {Y}✗ 未安装 (pip install flask){R}")
        ok = False

    # Groq API Key
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    if os.getenv("GROQ_API_KEY"):
        print(f"  Groq API Key ...... {G}✓ 已配置{R}")
    else:
        print(f"  Groq API Key ...... {Y}✗ 未配置{R}")
        ok = False

    # Dev Tunnel
    if shutil.which("devtunnel"):
        print(f"  Dev Tunnel ........ {G}✓ 已安装{R}")
    else:
        print(f"  Dev Tunnel ........ {Y}✗ 未安装{R}")
        print(f"    安装: winget install Microsoft.devtunnel")
        ok = False

    print()
    return ok


def check_devtunnel_login():
    print(f"{BOLD}📋 Step 2: Dev Tunnel 登录{R}\n")
    try:
        r = subprocess.run(["devtunnel", "user", "show"], capture_output=True, text=True)
        if "Logged in" in r.stdout or r.returncode == 0:
            print(f"  {G}✓ Dev Tunnel 已登录{R}")
            return True
    except Exception:
        pass

    print(f"  {Y}⚠ Dev Tunnel 未登录{R}")
    print(f"\n  请运行以下命令登录 (使用你的 Microsoft 账号):\n")
    print(f"    {C}devtunnel user login{R}")
    print()
    ans = input("  已登录? [y/N]: ").strip().lower()
    return ans == "y"


def setup_secret():
    print(f"\n{BOLD}📋 Step 3: 创建 Teams Outgoing Webhook{R}\n")
    print(f"""  请按以下步骤在 Teams 中创建 Outgoing Webhook:

  {B}1.{R} 打开 Microsoft Teams
  {B}2.{R} 进入你要使用的{BOLD}频道{R} (建议创建一个 "Lab Manager" 频道)
  {B}3.{R} 点击频道名称旁的 {BOLD}⋯{R} → {BOLD}管理频道{R}
  {B}4.{R} 切换到 {BOLD}"应用"{R} 标签页
  {B}5.{R} 点击右下角 {BOLD}"创建传出 Webhook"{R} 按钮
  {B}6.{R} 填写:
     • 名称: {C}LabManager{R}
     • 回调 URL: {C}(先留空，下一步获取){R}
     • 描述: {C}Lab 智能库存管理助手{R}
  {B}7.{R} 点击 "创建" 后，Teams 会显示一个{BOLD}安全令牌{R} (密钥)
  {B}8.{R} {Y}⚠ 务必复制此令牌！{R} 关闭后无法再查看
""")
    secret = input("  粘贴 Teams 给出的安全令牌 (或直接回车跳过): ").strip()
    return secret


def save_env(secret):
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        with open(env_path, "r") as f:
            pass

    # 读取现有 .env
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TEAMS_WEBHOOK_SECRET="):
                    lines.append(f"TEAMS_WEBHOOK_SECRET={secret}\n")
                    found = True
                else:
                    lines.append(line)

    if not found:
        lines.append(f"\n# Teams Outgoing Webhook\n")
        lines.append(f"TEAMS_WEBHOOK_SECRET={secret}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"\n  {G}✓ 安全令牌已保存到 .env{R}")


def show_final_steps():
    print(f"""
{BOLD}📋 Step 4: 启动服务{R}

  运行一键启动脚本:

    {C}python start_webhook.py{R}

  这会同时启动:
    • Flask Web Dashboard (http://localhost:5001)
    • Webhook Bot (http://localhost:3978)
    • Dev Tunnel (HTTPS 公网转发)

{BOLD}📋 Step 5: 更新 Webhook URL{R}

  1. 在 Dev Tunnel 日志中找到 HTTPS URL，类似:
     {C}https://xxxxxxxx.devtunnels.ms{R}

  2. 回到 Teams 频道 → 管理频道 → 应用 → 编辑 LabManager Webhook
     将回调 URL 更新为: {C}https://xxxxxxxx.devtunnels.ms/api/messages{R}

{BOLD}📋 Step 6: 开始使用！{R}

  在频道中输入:
    {C}@LabManager 查一下库存{R}
    {C}@LabManager 入库 10 个鼠标{R}
    {C}@LabManager 帮助{R}

{Y}💡 注意:{R}
  • 使用时需要 @LabManager 提及 Bot
  • Dev Tunnel 每次重启可能会变 URL，需要更新 Teams 中的 Webhook URL
  • 可以创建持久化 tunnel: devtunnel create --allow-anonymous
""")


def main():
    banner()

    ok = check_prereqs()
    if not ok:
        print(f"  {Y}⚠ 有前置条件未满足，请先安装/配置后重试{R}\n")
        return

    if not check_devtunnel_login():
        print(f"\n  {Y}请先登录 Dev Tunnel 后重新运行此脚本{R}\n")
        return

    secret = setup_secret()
    if secret:
        save_env(secret)
    else:
        print(f"\n  {Y}⚠ 跳过令牌配置 (可稍后手动添加到 .env){R}")

    show_final_steps()
    print(f"{G}✅ 设置完成！{R}\n")


if __name__ == "__main__":
    main()
