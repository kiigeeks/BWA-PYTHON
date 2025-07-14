# config.py
import os
from dotenv import load_dotenv

# Memuat variabel dari file .env ke environment
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
# --- Pengaturan Database ---
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Pengaturan Otentikasi ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# --- Pengaturan Aplikasi ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(',')