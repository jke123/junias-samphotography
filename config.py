import os
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_url():
    url = os.getenv("DATABASE_URL", "")
    # Neon / Render fournissent parfois postgres:// → on corrige
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # psycopg3 driver
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if not url:
        url = "sqlite:///" + os.path.join(BASE_DIR, "portfolio.db")
        print("[WARNING] DATABASE_URL manquant — SQLite local utilisé")
    else:
        print("[DB] PostgreSQL connecté ✓")
    return url


class Config:
    SECRET_KEY              = os.getenv("SECRET_KEY", "change-this-in-production")
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # NullPool = obligatoire pour Vercel serverless (pas de connexions persistantes)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool,
    }
    UPLOAD_FOLDER   = os.path.join(BASE_DIR, "static", "uploads")
    PROFILE_FOLDER  = os.path.join(BASE_DIR, "static", "uploads", "profile")
    PHOTOS_FOLDER   = os.path.join(BASE_DIR, "static", "uploads", "photos")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024   # 4 MB (limite Vercel)
    ALLOWED_EXTENSIONS  = {"png", "jpg", "jpeg", "gif", "webp"}
    ADMIN_USERNAME  = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD  = os.getenv("ADMIN_PASSWORD", "admin123")
