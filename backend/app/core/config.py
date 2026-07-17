import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, ValidationInfo, field_validator


class Settings(BaseSettings):
    # Application Config
    PROJECT_NAME: str = "Social AI Agent API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"

    # Database Config
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="social_ai")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/social_ai")

    # Database Connection Pool Settings
    POSTGRES_POOL_SIZE: int = Field(default=20)
    POSTGRES_MAX_OVERFLOW: int = Field(default=10)
    POSTGRES_POOL_TIMEOUT: int = Field(default=30)
    POSTGRES_POOL_RECYCLE: int = Field(default=1800)

    # JWT Security Settings
    SECRET_KEY: str = Field(default="super-secret-development-jwt-signing-key-keep-safe")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # n8n Integration Settings
    N8N_WEBHOOK_URL: str = Field(default="http://localhost:5678/webhook/publish")
    N8N_SHARED_SECRET: str = Field(default="n8n-shared-secret-key-keep-safe")

    # SMTP Email Settings
    SMTP_HOST: str = Field(default="smtp.resend.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="resend")
    SMTP_PASSWORD: str = Field(default="")
    EMAILS_FROM_EMAIL: str = Field(default="info@socialagent.ai")
    EMAILS_FROM_NAME: str = Field(default="Social AI Agent")
    
    # Resend API Settings
    RESEND_API_KEY: str = Field(default="")
    
    # Frontend Redirect URL
    FRONTEND_URL: str = Field(default="http://localhost:3000")

    # MinIO S3 Settings
    MINIO_ENDPOINT: str = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minio_admin")
    MINIO_SECRET_KEY: str = Field(default="minio_secret_key")
    MINIO_BUCKET_NAME: str = Field(default="proposals")

    # API Config
    API_V1_STR: str = "/api/v1"

    # We read from .env if present.
    # We use model_config to instruct Pydantic to read from a .env file located at the root of the project.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # ignores extra fields in the env file not declared here
    )


# Instantiate the Settings object as a singleton for the app
settings = Settings()
