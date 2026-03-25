"""
Database dependency injection for FastAPI

Provides database session management with proper cleanup
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import os
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Import Base for ORM models
from .base import Base

__all__ = ["Base", "engine", "SessionLocal", "get_db", "get_db_transaction", "get_db_readonly", "init_db", "healthcheck_db"]

# Database configuration
# Support both SQLite (local development) and PostgreSQL (production)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///petpooja_retail_db.sqlite3"  # Changed to SQLite for local dev
)

# Create engine with connection pooling
# SQLite needs different settings than PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=40,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False
    )

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    connection_record.info['checkout_time'] = time.time()

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    checkout_time = connection_record.info.get('checkout_time')
    if checkout_time:
        duration = time.time() - checkout_time
        if duration > 1.0:
            logger.warning(f"Long database connection hold explicitly detected: {duration:.2f}s")

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
    from app.api.db.models import Base as Phase1Base
    from app.api.db.phase2_models import Base as Phase2Base
    
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
