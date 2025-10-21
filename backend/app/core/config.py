"""
Application configuration and environment variables
"""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@db:5432/bizcard_crm"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    APP_NAME: str = "FastAPI Business Card CRM"
    APP_VERSION: str = os.getenv("APP_VERSION", "v2.12")
    APP_MESSAGE: str = os.getenv("APP_MESSAGE", "")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Upload directories
    UPLOAD_DIR: str = "uploads"
    CARDS_DIR: str = "uploads/cards"
    TEMP_DIR: str = "uploads/temp"
    
    # OCR Settings
    TESSERACT_CMD: Optional[str] = os.getenv("TESSERACT_CMD")
    OCR_LANGUAGES: str = "rus+eng"
    
    # Security
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://ibbase.ru",
        "http://ibbase.ru"
    ]
    
    # Duplicate Detection
    DEFAULT_DUPLICATE_THRESHOLD: float = 0.75


settings = Settings()


