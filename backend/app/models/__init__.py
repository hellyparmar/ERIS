"""
Database Configuration for R-DIOS
PostgreSQL setup with connection pooling
"""

import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load from backend/.env
env_path = Path("/home/petpooja/Enterprise Retail Intelligence System/backend/.env")
if env_path.exists():
    load_dotenv(env_path)
else:
    logger.warning(f".env not found at {env_path}")

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:EnterpriseRetail%402026@localhost:5433/enterprise_retail"
)

logger.info(f"Using DATABASE_URL: {DATABASE_URL[:40]}...")

# Create engine with connection pooling optimized for cloud (Supabase)
engine_args = {
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600,
    "pool_timeout": 30,
    "echo": False
}

# Add connection timeout for cloud databases (Supabase)
if "supabase" in DATABASE_URL or "neon.tech" in DATABASE_URL:
    engine_args["connect_args"] = {
        "connect_timeout": 30,
        "options": "-c statement_timeout=60000"
    }

engine = create_engine(DATABASE_URL, **engine_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    """
    Database session dependency
    Use with FastAPI's Depends()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"DB session error: {e}")
        raise
    finally:
        db.close()

# Import all models to ensure they are registered with Base
from . import multitenant_models
from . import models
