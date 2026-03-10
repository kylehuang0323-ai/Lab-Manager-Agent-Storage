"""
Teams Bot 部署配置向导
用法: python setup_teams_bot.py

引导你完成 Azure Bot 注册和本地环境配置
"""

import os
import sys
import subprocess

from dotenv import load_dotenv, set_key

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(PROJECT_DIR, ".env")


def check_devtunnel():
    """检查 devtunnel 是否可用"""
    try:
        result = subprocess.run(
            ["devtunnel", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            ver = result.stdout.strip()
            print(f"  ✅ Dev Tunnel: {ver}")
            return True
    except FileNotFoundError:
        pass
    print("  ❌ Dev Tunnel 未安装")
    print("     运行: winget install Microsoft.devtunnel")
    return False


def check_devtunnel_login():
    """检查 devtunnel 登录状态"""
    try:
        result = subprocess.run(
            ["devtunnel", "user", "show"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and "Logged in" in result.stdout:
            print(f"  ✅ Dev Tunnel 已登录")
            return True
    except Exception:
        pass
    print("  ⚠️ Dev Tunnel 未登录")
    print("     运行: devtunnel user login")
    return False


def check_bot_credentials():
    """检查 Bot 凭证"""
    load_dotenv(ENV_FILE, override=True)
    app_id = os.getenv("BOT_APP_ID", "").strip()
    app_pw = os.getenv("BOT_APP_PASSWORD", "").strip()

    if app_id and app_pw:
        print(f"  ✅ Bot App ID: {app_id[:8]}...")
        print(f"  ✅ Bot Password: {'*' * 8} (已配置)")
        return True
    else:
        if not app_id:
            print("  ❌ BOT_APP_ID 未配置")
        if not app_pw:
            print("  ❌ BOT_APP_PASSWORD 未配置")
        return False


def configure_credentials():
    """交互式配置 Bot 凭证"""
    print()
    print("=" * 55)
    print("📝 Azure Bot 注册指南")
    print("=" * 55)
    print()
    print("请在浏览器中完成以下步骤:")
    print()
    print("  1️⃣  打开 https://portal.azure.com/#create/Microsoft.AzureBot")
    print()
    print("  2️⃣  填写创建表单:")
    print("     • Bot handle: LabManagerBot")
    print("     • 订阅: 选择你的订阅")
    print("     • 资源组: 新建或选择已有")
    print("     • 定价层: F0 (免费)")
    print("     • Microsoft App ID: 创建新的")
    print("     • 应用类型: 多租户 (Multi Tenant)")
    print("     • 创建类型: 创建新的 Microsoft App ID")
    print()
    print("  3️⃣  创建完成后:")
    print("     • 进入 Bot 资源 → 配置 (Configuration)")
    print("     • 复制 'Microsoft App ID'")
    print("     • 点击 '管理密码' → 新建客户端密码 → 复制密码值")
    print()
    print("  4️⃣  添加 Teams 频道:")
    print("     • 进入 Bot 资源 → 频道 (Channels)")
    print("     • 点击 'Microsoft Teams' → 保存")
    print()
    print("-" * 55)

    app_id = input("\n请输入 Microsoft App ID: ").strip()
    if not app_id:
        print("❌ App ID 不能为空")
        return False

    app_pw = input("请输入 App Password (客户端密码): ").strip()
    if not app_pw:
        print("❌ Password 不能为空")
        return False

    # 写入 .env
    set_key(ENV_FILE, "BOT_APP_ID", app_id)
    set_key(ENV_FILE, "BOT_APP_PASSWORD", app_pw)

    print(f"\n✅ 已保存到 .env")
    print(f"   BOT_APP_ID={app_id[:8]}...")
    print(f"   BOT_APP_PASSWORD={'*' * 8}")
    return True


def create_tunnel():
    """创建并启动 Dev Tunnel，打印公网 URL"""
    print()
    print("🔗 创建 Dev Tunnel...")
    print("   运行以下命令获取公网 URL:")
    print()
    print("   devtunnel host --port-numbers 3978 --allow-anonymous")
    print()
    print("   复制输出中的 HTTPS URL，例如:")
    print("   https://xxxxxxxx-3978.asse.devtunnels.ms")
    print()
    print("   然后回到 Azure Portal → Bot 配置 → 消息终结点:")
    print("   填写: https://xxxxxxxx-3978.asse.devtunnels.ms/api/messages")
    print()


def main():
    print()
    print("=" * 55)
    print("🤖 Lab Manager — Teams Bot 部署向导")
    print("=" * 55)
    print()

    # 1. 环境检查
    print("📋 环境检查:")
    dt_ok = check_devtunnel()
    dt_login = check_devtunnel_login() if dt_ok else False
    cred_ok = check_bot_credentials()

    if dt_ok and dt_login and cred_ok:
        print()
        print("🎉 所有配置已就绪！")
        print()
        print("启动步骤:")
        print("  1. python bot_app.py          # 启动 Bot 服务")
        print("  2. devtunnel host --port-numbers 3978 --allow-anonymous")
        print("  3. python pack_teams_app.py    # 打包 Teams App")
        print("  4. 在 Teams 中上传自定义应用")
        print()
        print("或一键启动:")
        print("  python start_all.py")
        return

    # 2. 缺少 devtunnel login
    if dt_ok and not dt_login:
        print()
        ans = input("是否现在登录 Dev Tunnel? (y/n): ").strip().lower()
        if ans == 'y':
            subprocess.run(["devtunnel", "user", "login"])

    # 3. 缺少 Bot 凭证
    if not cred_ok:
        print()
        ans = input("是否现在配置 Azure Bot 凭证? (y/n): ").strip().lower()
        if ans == 'y':
            if configure_credentials():
                create_tunnel()
                print("接下来:")
                print("  1. 配置好 Azure Bot 消息终结点后")
                print("  2. 运行: python pack_teams_app.py")
                print("  3. 运行: python start_all.py")
            return

    create_tunnel()


if __name__ == "__main__":
    main()
