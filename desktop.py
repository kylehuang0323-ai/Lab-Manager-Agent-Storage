"""
Lab Manager 桌面版入口
使用 flaskwebgui 将 Flask 应用包装为原生桌面窗口
双击运行即可，无需浏览器手动打开
"""

import sys
import os
import shutil

# --------------------------------------------------
# 路径处理：PyInstaller 打包后的资源迁移
# --------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    INTERNAL = os.path.join(BASE_DIR, "_internal")

    # 首次运行：将 _internal 里的用户数据复制到 .exe 同级目录
    # 后续更新不会覆盖，确保用户数据持久化
    for folder in ("data",):
        src = os.path.join(INTERNAL, folder)
        dst = os.path.join(BASE_DIR, folder)
        if os.path.isdir(src) and not os.path.exists(dst):
            shutil.copytree(src, dst)

    # 首次运行：复制 .env 配置到 .exe 同级（方便用户修改 API Key）
    env_src = os.path.join(INTERNAL, ".env")
    env_dst = os.path.join(BASE_DIR, ".env")
    if os.path.isfile(env_src) and not os.path.exists(env_dst):
        shutil.copy2(env_src, env_dst)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

# 桌面模式禁用 Flask debug（避免 reloader 线程冲突）
os.environ["FLASK_DEBUG"] = "false"

from flaskwebgui import FlaskUI
from app import app
import alert_service


def main():
    alert_service.start_alert_scheduler(interval_seconds=300)
    print("=" * 50)
    print("📦 Lab Manager — Desktop Mode")
    print(f"   Base: {BASE_DIR}")
    print("=" * 50)

    FlaskUI(
        app=app,
        server="flask",
        port=5001,
        width=1280,
        height=860,
    ).run()


if __name__ == "__main__":
    main()
