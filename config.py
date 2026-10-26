import os
from dotenv import load_dotenv

# Path direktori utama
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Muat konfigurasi dari file .env jika ada
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

# Konfigurasi Token Bot Telegram
TOKEN = os.getenv("BOT_TOKEN", "8971959851:AAEWs90buIdzaRff2SmjzS4GsYAaN9D89JY")

# Daftar Administrator Bot (ID Telegram)
admin_ids_raw = os.getenv("ADMIN_IDS", "8523165108")
ADMIN_IDS = [int(i.strip()) for i in admin_ids_raw.split(",") if i.strip().isdigit()]
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@aibarokah")

# Daftar Channel yang wajib diikuti
CHANNELS = [
    {
        "id": "@aibarokahstore",
        "name": "1. 📢 Store AI Barokah",
        "link": "https://t.me/aibarokahstore"
    },
    {
        "id": "@notifikasiAiBarokah",
        "name": "2. 🔔 Channel Notifikasi",
        "link": "https://t.me/notifikasiAiBarokah"
    }
]

# Channel untuk log notifikasi verifikasi
NOTIF_CHANNEL_ID = os.getenv("NOTIF_CHANNEL_ID", "@notifikasiAiBarokah")

# Konfigurasi QRIS GoPay Merchant
GOPAY_QRIS_STRING = os.getenv("GOPAY_QRIS_STRING", "").strip()

# Folder data terpusat
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Path file-file data di dalam folder data/
DATA_FILE = os.path.join(DATA_DIR, "registered_users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")
USERS_PROFILE_FILE = os.path.join(DATA_DIR, "users_profile.json")
BLOCKED_USERS_FILE = os.path.join(DATA_DIR, "blocked_users.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
