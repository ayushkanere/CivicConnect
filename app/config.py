import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-secret-key-change-in-prod-civicconnect")
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'civicconnect.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 2 * 1024 * 1024))  # 2 MB limit
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    
    # Security & Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Rate Limiting
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "True").lower() in ("true", "1")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_STRATEGY = "fixed-window"
    
    # Feature Flags
    ENABLE_MAP = os.getenv("ENABLE_MAP", "False").lower() in ("true", "1")
    
    # Civic Domain Constants
    CATEGORIES = [
        "Garbage/Waste",
        "Water Leakage/Drainage",
        "Damaged Road/Unsafe Infrastructure",
        "Broken Streetlight",
        "Community Cleanliness/Awareness",
        "Other"
    ]
    
    STATUSES = [
        "Submitted",
        "Under Review",
        "In Progress",
        "Resolved"
    ]


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # Disabled in unit tests for convenience where needed
    RATELIMIT_ENABLED = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
