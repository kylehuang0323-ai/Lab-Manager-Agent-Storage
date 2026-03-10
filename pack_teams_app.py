"""
打包 Teams App — 生成可上传到 Teams 的 .zip 文件
用法: python pack_teams_app.py

会自动读取 .env 中的 BOT_APP_ID 替换 manifest.json 中的占位符
"""

import json
import os
import sys
import zipfile
import shutil

from dotenv import load_dotenv
load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TEAMS_DIR = os.path.join(PROJECT_DIR, "teams_app")
OUTPUT_ZIP = os.path.join(PROJECT_DIR, "teams_app", "LabManager.zip")
TEMP_DIR = os.path.join(PROJECT_DIR, "teams_app", "_build")


def pack():
    bot_id = os.getenv("BOT_APP_ID", "").strip()
    if not bot_id:
        print("❌ 错误: BOT_APP_ID 未配置")
        print("   请先在 Azure Portal 注册 Bot，然后在 .env 中填写:")
        print("   BOT_APP_ID=your-app-id-here")
        print("   BOT_APP_PASSWORD=your-app-password-here")
        print()
        print("📖 Azure Bot 注册步骤:")
        print("   1. 打开 https://portal.azure.com")
        print("   2. 搜索 'Azure Bot' → 创建")
        print("   3. 填写: 名称=LabManagerBot, 定价=F0(免费)")
        print("   4. 创建类型选 '多租户'")
        print("   5. 创建完成后 → 配置 → 复制 Microsoft App ID")
        print("   6. 管理密码 → 新建客户端密码 → 复制值")
        print("   7. 频道 → 添加 Microsoft Teams 频道")
        print("   8. 配置 → 消息终结点填: <你的devtunnel URL>/api/messages")
        sys.exit(1)

    print(f"📦 打包 Teams App (Bot ID: {bot_id[:8]}...)")

    # 清理临时目录
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    # 处理 manifest.json — 替换占位符
    with open(os.path.join(TEAMS_DIR, "manifest.json"), "r", encoding="utf-8") as f:
        manifest = f.read()

    manifest = manifest.replace("{{BOT_APP_ID}}", bot_id)
    manifest_data = json.loads(manifest)

    with open(os.path.join(TEMP_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=4, ensure_ascii=False)

    # 复制图标
    for icon in ["color.png", "outline.png"]:
        src = os.path.join(TEAMS_DIR, icon)
        if os.path.exists(src):
            shutil.copy2(src, TEMP_DIR)
        else:
            print(f"⚠️ 缺少图标: {icon}")

    # 打包 zip
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(TEMP_DIR):
            fpath = os.path.join(TEMP_DIR, fname)
            zf.write(fpath, fname)

    # 清理
    shutil.rmtree(TEMP_DIR)

    print(f"✅ 打包成功: {OUTPUT_ZIP}")
    print()
    print("📤 上传到 Teams 的步骤:")
    print("   1. 打开 Microsoft Teams")
    print("   2. 左侧栏 → 应用 (Apps)")
    print("   3. 底部 → 管理你的应用 (Manage your apps)")
    print("   4. → 上传应用 (Upload an app)")
    print("   5. → 上传自定义应用 (Upload a custom app)")
    print(f"   6. 选择: {OUTPUT_ZIP}")
    print("   7. 在弹出的对话中点击 '添加' (Add)")


if __name__ == "__main__":
    pack()
