"""
Database Configuration - Supabase Cloud & Local PostgreSQL Support
Automatically detects and configures for:
- Supabase cloud database (production)
- Local PostgreSQL (development)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use local default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://petpooja:password@localhost:5432/rdios_db"
)

# Supabase configuration (optional - for direct Supabase client usage)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Auto-detect cloud database and add SSL requirement
if "supabase" in DATABASE_URL or "neon.tech" in DATABASE_URL:
    # Cloud database detected - ensure SSL mode
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"
    
    print(f"🌐 Using cloud database: {DATABASE_URL.split('@')[1].split('/')[0]}")
else:
    print(f"💻 Using local database: localhost:5432/rdios_db")

# SQLAlchemy Engine Configuration
engine_args = {
    "pool_pre_ping": True,  # Verify connections before using
    "pool_recycle": 3600,   # Recycle connections every hour
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",  # SQL logging
}

# Connection pooling for production (cloud databases)
if "supabase" in DATABASE_URL or "neon.tech" in DATABASE_URL:
    engine_args.update({
        "pool_size": 5,
        "max_overflow": 10,
    })

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, **engine_args)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    """
    Database session dependency for FastAPI.
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Supabase client (optional - for advanced features)
supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized")
    except ImportError:
        print("⚠️  Supabase client not available (install: pip install supabase)")
    except Exception as e:
        print(f"⚠️  Could not initialize Supabase client: {e}")

# Health check function
def check_database_connection():
    """
    Check if database connection is healthy.
    Returns: (bool, str) - (success, message)
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            return True, f"Connected to PostgreSQL: {version.split(',')[0]}"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

# Export configuration
__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "supabase_client",
    "check_database_connection",
    "DATABASE_URL",
]
