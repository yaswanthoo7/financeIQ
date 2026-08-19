"""
FinanceIQ Backend Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "FinanceIQ"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://invoiceiq:invoiceiq@localhost:5432/invoiceiq"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://invoiceiq:invoiceiq@localhost:5432/invoiceiq"
    
    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: str = ".pdf,.png,.jpg,.jpeg,.tiff,.webp"
    
    # Extraction
    CONFIDENCE_THRESHOLD: float = 0.7
    MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
