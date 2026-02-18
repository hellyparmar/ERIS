"""
Database dependency injection for FastAPI

Provides database session management with proper cleanup
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import os
from contextlib import contextmanager

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://retail_user:retail_pass@localhost:5432/enterprise_retail"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session
    
    Yields a database session and ensures proper cleanup
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_transaction():
    """
    Context manager for database transactions with automatic rollback
    
    Usage:
        with get_db_transaction() as db:
            invoice = Invoice(...)
            db.add(invoice)
            # Automatically commits or rolls back
    
    Yields:
        Session: SQLAlchemy session object
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@contextmanager
def get_db_readonly():
    """
    Context manager for read-only database operations
    
    Usage:
        with get_db_readonly() as db:
            invoices = db.query(Invoice).all()
    
    Yields:
        Session: SQLAlchemy session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables (create all tables)
    
    Should be called once during application startup
    """
    from api.db.models import Base as Phase1Base
    from api.db.phase2_models import Base as Phase2Base
    
    # Create all Phase 1 and Phase 2 tables
    Phase1Base.metadata.create_all(bind=engine)
    Phase2Base.metadata.create_all(bind=engine)
    print("✓ Database tables initialized")


def healthcheck_db() -> bool:
    """
    Check database connectivity
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return result is not None
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False
