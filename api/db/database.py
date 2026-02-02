"""
Database Configuration for R-DIOS
Supports both SQLite (development) and PostgreSQL (production)
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Determine database type from environment
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    # SQLite for development (no installation required)
    DATABASE_URL = "sqlite:///./rdios_dev.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Required for SQLite
        echo=False
    )
else:
    # PostgreSQL for production
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://rdios_user:rdios_password@localhost/rdios_dev"
    )
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

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
    finally:
        db.close()

# Initialize database tables
def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database tables created using {'SQLite' if USE_SQLITE else 'PostgreSQL'}")

# Drop all tables (use with caution!)
def drop_tables():
    """Drop all tables from the database"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All tables dropped")
