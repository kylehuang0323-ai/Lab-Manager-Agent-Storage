import os
import sys
from dotenv import load_dotenv

# PyInstaller frozen 模式下，__file__ 指向临时解压目录
# 数据文件应存放在 .exe 同级目录，确保持久可写
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
AI_MODEL = "llama-3.3-70b-versatile"

# Flask
SECRET_KEY = os.getenv("SECRET_KEY", "lab-manager-secret-key-change-me")
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

# Data paths — 始终在 BASE_DIR 下，打包后数据跟 .exe 同级
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.xlsx")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.xlsx")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
