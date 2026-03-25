import os
from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
_root_env = Path(__file__).parent.parent / ".env"
load_dotenv(_root_env)

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "R-DIOS"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # AI/ML Configuration
    USE_OLLAMA: bool = os.getenv("USE_OLLAMA", "true").lower() == "true"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    AI_PROVIDER_PRIORITY: List[str] = ["ollama", "anthropic", "openai"]
    
    # Email Configuration (SMTP/Gmail)
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@rdios.com")
    
    # WhatsApp Configuration (MSG91)
    WHATSAPP_ENABLED: bool = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"
    MSG91_AUTH_KEY: Optional[str] = os.getenv("MSG91_AUTH_KEY")
    MSG91_SENDER_ID: str = os.getenv("MSG91_SENDER_ID", "RDIOS")
    
    # Integration Feature Flags
    ENABLE_TALLY_EXPORT: bool = True
    ENABLE_GST_REPORTS: bool = True
    ENABLE_AI_ASSISTANT: bool = True

    class Config:
        case_sensitive = True

settings = Settings()
