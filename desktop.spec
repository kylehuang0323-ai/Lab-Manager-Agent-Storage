# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置
运行: pyinstaller desktop.spec
输出: dist/LabManager/LabManager.exe

首次运行 .exe 时会自动在同级目录创建 data/, exports/, uploads/ 文件夹
将 .env 文件放在 .exe 同级目录即可配置 API Key
"""

import os

BASE = os.path.abspath(".")

a = Analysis(
    ["desktop.py"],
    pathex=[BASE],
    datas=[
        ("templates", "templates"),
        ("static", "static"),
        ("data", "data"),
        (".env", "."),
    ],
    hiddenimports=[
        # Flask & web
        "flask",
        "flask.json",
        "flaskwebgui",
        "waitress",
        "waitress.task",
        "waitress.channel",
        "engineio.async_drivers.threading",
        # Excel
        "openpyxl",
        "openpyxl.styles",
        "openpyxl.utils",
        "openpyxl.cell",
        # AI / LLM
        "openai",
        # Date
        "dateutil",
        "dateutil.relativedelta",
        # Env
        "dotenv",
    ],
    excludes=[
        # 全局安装但项目不使用的大型包 — 排除以减小体积
        "torch", "torchvision", "torchaudio",
        "numpy", "pandas", "scipy", "matplotlib",
        "pytest", "py", "_pytest",
        "tkinter", "unittest",
        "PIL", "cv2",
        "IPython", "notebook", "jupyter",
        "sphinx", "docutils",
        "pyinstaller", "PyInstaller",
        "tensorboard", "tensorflow",
        "botbuilder",
        "aiohttp",
        "uvicorn", "uvloop",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LabManager",
    console=False,          # 无控制台黑窗口
    icon=None,              # 可替换为 .ico 图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="LabManager",
)
