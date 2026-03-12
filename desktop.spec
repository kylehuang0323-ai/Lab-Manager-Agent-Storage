# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置
运行: pyinstaller desktop.spec
输出: dist/LabManager/LabManager.exe
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
        "flask",
        "openpyxl",
        "openai",
        "dotenv",
        "dateutil",
        "pandas",
        "flaskwebgui",
        "engineio.async_drivers.threading",
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
