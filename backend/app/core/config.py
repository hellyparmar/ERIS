from pydantic_settings import BaseSettings
from pydantic import field_validator
import os
from typing import Optional


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # PostgreSQL configuration - DATABASE_URL is REQUIRED
    # PostgreSQL configuration - DATABASE_URL is REQUIRED
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # Redis configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # JWT - JWT_SECRET_KEY is REQUIRED
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

    # Encryption - ENCRYPTION_KEY is REQUIRED
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # CORS
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:4173"
    )
    
    # AI/ML
    USE_OLLAMA: bool = os.getenv("USE_OLLAMA", "true").lower() == "true"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Feature Flags
    ENABLE_AI_ASSISTANT: bool = os.getenv("ENABLE_AI_ASSISTANT", "true").lower() == "true"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate that DATABASE_URL is set, not a placeholder, and properly formatted.
        """
        if not v or not v.strip():
            raise RuntimeError(
                "DATABASE_URL environment variable is not set. "
                "This is a REQUIRED configuration at startup. "
                "Provide a PostgreSQL async URL or a SQLite URL."
            )
        cleaned = v.strip().lower()
        if cleaned.startswith("change_me") or cleaned in {"changeme", "placeholder", "dummy"}:
            raise RuntimeError(
                f"DATABASE_URL contains a placeholder value ({v!r}). "
                "A real database connection string must be configured."
            )
        
        # Basic format validation (support postgresql and sqlite for testing)
        if not v.startswith(("postgresql+", "postgresql://", "sqlite://", "sqlite+")):
            raise RuntimeError(
                f"DATABASE_URL has an invalid format: {v[:50]}... "
                "Must start with 'postgresql+asyncpg://', 'postgresql://', or 'sqlite://'"
            )
        
        return v

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        """
        Validate that JWT_SECRET_KEY is set and not a placeholder.
        """
        if not v or not v.strip():
            raise RuntimeError(
                "JWT_SECRET_KEY / JWT_SECRET environment variable is not set. "
                "This is a REQUIRED configuration at startup."
            )
        cleaned = v.strip().lower()
        if cleaned.startswith("change_me") or cleaned in {
            "changeme", "your_secret_key", "your-secret-key",
            "your-super-secret-key", "placeholder", "dummy", "dev_secret", "secret"
        }:
            raise RuntimeError(
                f"JWT_SECRET_KEY contains a placeholder value ({v!r}). "
                "A secure secret key must be configured."
            )
        return v

    @field_validator("ENCRYPTION_KEY", mode="before")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """
        Validate that ENCRYPTION_KEY is set and not a placeholder.
        """
        if not v or not v.strip():
            raise RuntimeError(
                "ENCRYPTION_KEY environment variable is not set. "
                "This is a REQUIRED configuration at startup."
            )
        cleaned = v.strip().lower()
        if cleaned.startswith("change_me") or cleaned in {"changeme", "placeholder", "dummy"}:
            raise RuntimeError(
                f"ENCRYPTION_KEY contains a placeholder value ({v!r}). "
                "A valid 32-byte Fernet key must be configured."
            )
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"


# Initialize settings at module import time
# This ensures DATABASE_URL validation happens at application startup
try:
    settings = Settings()
except (ValueError, RuntimeError) as e:
    # Provide clear error message on startup
    import sys
    error_msg = (
        "\n" + "=" * 70 + "\n"
        "FATAL: CONFIGURATION ERROR AT STARTUP\n"
        "=" * 70 + "\n"
        f"{str(e)}\n"
        "=" * 70 + "\n"
    )
    print(error_msg, file=sys.stderr)
    raise

