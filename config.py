import os
from dotenv import load_dotenv

load_dotenv()

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
AI_MODEL = "llama-3.3-70b-versatile"

# Flask
SECRET_KEY = os.getenv("SECRET_KEY", "lab-manager-secret-key-change-me")
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

# Data paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.xlsx")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.xlsx")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
