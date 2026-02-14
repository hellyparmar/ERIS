"""
Backend Configuration Module
Loads all configuration from environment variables
"""

import os
from dotenv import load_dotenv
from typing import List

# Load .env file
load_dotenv()

class Config:
    """
    Application Configuration
    Loads all settings from environment variables
    """
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/enterprise_retail"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    
    # API Server
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("API_DEBUG", "False").lower() == "true"
    WORKERS: int = int(os.getenv("API_WORKERS", "4"))
    
    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    ]
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    CORS_ALLOW_METHODS: List[str] = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    CORS_ALLOW_HEADERS: List[str] = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRY_MINUTES: int = int(os.getenv("JWT_EXPIRY_MINUTES", "30"))
    JWT_REFRESH_EXPIRY_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7"))
    
    # External APIs
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    
    # Feature Flags
    ENABLE_INVOICING: bool = os.getenv("ENABLE_INVOICING", "True").lower() == "true"
    ENABLE_BILL_MANAGEMENT: bool = os.getenv("ENABLE_BILL_MANAGEMENT", "True").lower() == "true"
    ENABLE_FORECASTING: bool = os.getenv("ENABLE_FORECASTING", "True").lower() == "true"
    ENABLE_WEATHER_INTEGRATION: bool = os.getenv("ENABLE_WEATHER_INTEGRATION", "True").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE: str = os.getenv("LOG_FILE", "/var/log/enterprise_retail.log")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate critical configuration values
        Returns True if all required values are set
        """
        required_vars = [
            'DATABASE_URL',
            'JWT_SECRET_KEY',
            'OPENROUTER_API_KEY'
        ]
        
        for var in required_vars:
            if not getattr(cls, var):
                print(f"❌ Missing required environment variable: {var}")
                return False
        
        # Validate JWT_SECRET_KEY length
        if len(cls.JWT_SECRET_KEY) < 32:
            print("❌ JWT_SECRET_KEY must be at least 32 characters")
            return False
        
        # Validate DATABASE_URL
        if not cls.DATABASE_URL.startswith("postgresql://"):
            print("❌ DATABASE_URL must be a PostgreSQL connection string")
            return False
        
        print("✅ All configuration values are valid")
        return True

# Create singleton config instance
config = Config()

# Example usage in main.py:
"""
from config import config, Config
from sqlalchemy import create_engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Validate configuration
if not Config.validate():
    exit(1)

# Create database engine
engine = create_engine(
    config.DATABASE_URL,
    pool_size=config.DATABASE_POOL_SIZE,
    max_overflow=config.DATABASE_MAX_OVERFLOW,
    pool_recycle=config.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True
)

# Create FastAPI app
app = FastAPI(
    debug=config.DEBUG,
    title="Enterprise Retail Intelligence"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

# Run app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        workers=config.WORKERS,
        reload=config.DEBUG
    )
"""
