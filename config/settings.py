from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
import os
import json
from typing import Optional, List, Dict, Any

class Settings(BaseSettings):

    # Project Configuration
    PROJECT_NAME: str = "MeraKia"
    LOG_LEVEL: str
    
    # Directories
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR: str = os.path.join(BASE_DIR, "logs", "api")
    CACHE_DIR: str = os.path.join(BASE_DIR, "cache")
    IMAGES_DIR: str = os.path.join(CACHE_DIR, "images")

    # Relational Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    DATABASE_URL: Optional[str] = None

    @property
    def POSTGRES_URL(self):
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+psycopg2://", 1)
            return url
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI / AI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_TEXT_MODEL: str = "gpt-4o-mini"
    OPENAI_IMAGE_MODEL: str = "gpt-image-2"
    OPENAI_IMAGE_SIZE: str = "1024x1024"
    OPENAI_TIMEOUT_SECONDS: int = 60
    # Quando True, geracao de imagem retorna placeholder verde (sem chamar OpenAI)
    AI_PLACEHOLDER_MODE: bool = False

    # Development Configuration
    DEV_MODE: bool = False

    # AI Iterations Limit Configuration
    AI_ITERATIONS_LIMIT_ENABLED: bool = False
    AI_ITERATIONS_DAILY_LIMIT: int = 5

    # SMTP / Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    EMAIL_FROM: str = ""
    EMAIL_FROM_NAME: str = "MeraKia"

    # Storage Configuration (local | s3)
    STORAGE_BACKEND: str = "local"
    # URL publica base para servir imagens locais (ex.: http://localhost:8000/images)
    STORAGE_PUBLIC_URL_BASE: str = "/images"
    # Limite de upload em MB
    STORAGE_MAX_UPLOAD_MB: int = 10

    # S3 / DigitalOcean Spaces / MinIO
    S3_ENDPOINT_URL: Optional[str] = None  # https://nyc3.digitaloceanspaces.com (Spaces) ou None (AWS)
    S3_REGION: str = "us-east-1"
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    # URL publica base do bucket/CDN (ex.: https://cdn.example.com)
    S3_PUBLIC_URL_BASE: str = ""
    # ACL padrao ('public-read' ou 'private')
    S3_DEFAULT_ACL: str = "public-read"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()