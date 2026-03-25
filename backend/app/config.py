from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/enterprise_retail"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI/ML
    USE_OLLAMA: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # WhatsApp (MSG91)
    MSG91_API_KEY: Optional[str] = None
    MSG91_SENDER_ID: str = "RDIOS_MSG"
    
    # JWT
    JWT_SECRET_KEY: str = "change_me_in_production_extremely_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Feature Flags
    ENABLE_AI_ASSISTANT: bool = True
    ENABLE_EMAIL: bool = True
    ENABLE_WHATSAPP: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
