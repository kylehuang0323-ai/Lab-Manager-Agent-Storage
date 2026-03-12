"""
Lab Manager 桌面版入口
使用 flaskwebgui 将 Flask 应用包装为原生桌面窗口
双击运行即可，无需浏览器手动打开
"""

import sys
import os

# PyInstaller 打包后，资源文件解压到临时目录
# 需要将工作目录切换到实际资源所在位置
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
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
