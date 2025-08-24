"""
Configuration management for Memorial Website.
Handles environment variables and application settings.
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Application
    APP_NAME: str = "Memorial Website"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    
    # API Configuration
    API_V1_STR: str = "/v1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Server Configuration
    SERVER_NAME: str = "Memorial Website"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"
    PROJECT_NAME: str = "Memorial Website"
    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:8000"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    CORS_ORIGINS: List[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = []
    CORS_ALLOW_HEADERS: List[str] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:memorial123@localhost:5432/memorial_website_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "memorial123"
    DB_NAME: str = "memorial_website_db"
    
    POSTGRES_SERVER: str = Field(default="localhost", env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="memorial123", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="memorial_website_db", env="POSTGRES_DB")
    POSTGRES_PORT: str = Field(default="5432", env="POSTGRES_PORT")
    
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=int(values.get("POSTGRES_PORT", 5432)),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )
    
    # Caching and Rate Limiting Configuration
    # Note: Currently using in-memory storage. Can be migrated to PostgreSQL if persistence is needed.
    
    # File Upload Configuration
    UPLOAD_FOLDER: str = Field(default="storage", env="UPLOAD_FOLDER")
    PHOTOS_FOLDER: str = Field(default="storage/photos", env="PHOTOS_FOLDER")
    VIDEOS_FOLDER: str = Field(default="storage/videos", env="VIDEOS_FOLDER")
    TEMP_FOLDER: str = Field(default="storage/temp", env="TEMP_FOLDER")
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, env="MAX_UPLOAD_SIZE_MB")
    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(default=["jpg", "jpeg", "png", "gif", "webp"], env="ALLOWED_IMAGE_EXTENSIONS")
    ALLOWED_VIDEO_EXTENSIONS: List[str] = Field(default=["mp4", "avi", "mov", "wmv"], env="ALLOWED_VIDEO_EXTENSIONS")
    MAX_PHOTOS_PER_MEMORIAL: int = Field(default=4, env="MAX_PHOTOS_PER_MEMORIAL")
    STATIC_URL: str = Field(default="/static", env="STATIC_URL")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    
    # Email Configuration
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    SMTP_PORT: Optional[int] = Field(default=587, env="SMTP_PORT")
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[EmailStr] = Field(default=None, env="EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = Field(default=None, env="EMAILS_FROM_NAME")
    
    # Security Configuration  
    BCRYPT_ROUNDS: int = 12
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_CALLS: int = Field(default=100, env="RATE_LIMIT_CALLS")
    RATE_LIMIT_PERIOD: int = Field(default=3600, env="RATE_LIMIT_PERIOD")  # 1 hour
    
    # Hebrew Calendar API Configuration
    HEBREW_CALENDAR_API_URL: str = Field(
        default="https://www.hebcal.com/converter/",
        env="HEBREW_CALENDAR_API_URL"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Development/Testing Configuration (already defined above)
    
    # Administrative Configuration
    FIRST_SUPERUSER: EmailStr = Field(default="admin@memorial.com", env="FIRST_SUPERUSER")
    FIRST_SUPERUSER_PASSWORD: str = Field(default="changeme", env="FIRST_SUPERUSER_PASSWORD")
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    
    # Additional fields to match .env file
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    CSRF_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    SESSION_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    SESSION_COOKIE_NAME: str = "memorial_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_LIFETIME_SECONDS: int = 86400
    
    EMAIL_ENABLED: bool = False
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM_ADDRESS: str = "noreply@memorial-website.com"
    EMAIL_FROM_NAME: str = "Memorial Website"
    EMAIL_USE_TLS: bool = True
    
    HEBREW_CALENDAR_API_KEY: Optional[str] = None
    
    WHATSAPP_ENABLED: bool = False
    WHATSAPP_API_URL: str = "https://api.whatsapp.com/"
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER: Optional[str] = None
    
    STRIPE_ENABLED: bool = False
    STRIPE_PUBLIC_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 600
    
    LOG_FILE: str = "logs/memorial.log"
    LOG_MAX_SIZE_MB: int = 10
    LOG_BACKUP_COUNT: int = 5
    
    FEATURE_WHATSAPP_GROUPS: bool = False
    FEATURE_VIDEO_UPLOAD: bool = True
    FEATURE_GPS_LOCATION: bool = True
    FEATURE_PAYMENT: bool = False
    
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = False
    TESTING: bool = False
    TEST_DATABASE_URL: Optional[str] = None
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


# Configuration for different environments
class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    model_config = {
        **Settings.model_config,
        "env_file": ".env.development"
    }


class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    BCRYPT_ROUNDS: int = 14  # More secure for production
    
    model_config = {
        **Settings.model_config,
        "env_file": ".env.production"
    }


class TestingSettings(Settings):
    """Testing environment settings."""
    TESTING: bool = True
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    POSTGRES_DB: str = "memorial_test_db"
    
    model_config = {
        **Settings.model_config,
        "env_file": ".env.testing"
    }


def get_settings_for_environment(environment: str = None) -> Settings:
    """Get settings based on environment variable."""
    environment = environment or os.getenv("ENVIRONMENT", "development")
    
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }
    
    settings_class = settings_map.get(environment.lower(), DevelopmentSettings)
    return settings_class()