from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url
from contextlib import asynccontextmanager, contextmanager
import logging
import os

from app.core.config import settings
from app.models.base import Base

logger = logging.getLogger(__name__)

database_url = settings.DATABASE_URL

# Convert local SQLite URLs to the async-compatible aiosqlite driver
if database_url.startswith("sqlite://") and not database_url.startswith("sqlite+aiosqlite://"):
    database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

url = make_url(database_url)
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
}

# Handle PostgreSQL async engine
if url.drivername.startswith("postgresql"):
    # Add asyncpg-specific SSL handling for local development
    if os.getenv("ENVIRONMENT", "development") == "development":
        # Disable SSL for local development unless explicitly enabled
        if not database_url.endswith("?ssl=prefer"):
            database_url = database_url.split("?")[0] + "?ssl=prefer" if "sslmode" not in database_url else database_url
    
    engine_kwargs.update({
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Verify connections before using them
    })
    
    # Add echo for SQL debugging
    if os.getenv("DEBUG", "false").lower() == "true":
        engine_kwargs["echo"] = True
else:
    # SQLite configuration
    pass

# Create async engine for PostgreSQL with asyncpg driver or SQLite for tests
engine: AsyncEngine = create_async_engine(
    database_url,
    **engine_kwargs,
)

# Create async session factory with proper async context
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # Prevent attribute expiration in async contexts
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
)

# Provide a synchronous session factory for sync-only tasks (avoid mixing with async code)
def get_sync_session():
    """Get synchronous session - only use for sync-only contexts (tasks, CLI, etc.)"""
    from sqlalchemy import create_engine
    # Create synchronous engine from URL
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(
        bind=sync_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    return SessionLocal()

async def get_db():
    """
    Async dependency for FastAPI endpoints.
    Provides an AsyncSession with proper error handling.
    """
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    except Exception as e:
        await async_session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await async_session.close()


async def get_db_dependency() -> AsyncSession:
    """
    Async dependency function for FastAPI endpoints.
    Provides an AsyncSession for database operations.
    
    Usage in endpoints:
        async def endpoint(session: AsyncSession = Depends(get_db_dependency)):
            await session.execute(...)
    """
    async with AsyncSessionLocal() as session:
        return session

@contextmanager
def get_db_sync():
    """
    Get synchronous database session for sync-only operations.
    WARNING: Do NOT use this with async/await code - causes greenlet errors!
    Only use in sync tasks, migrations, or CLI operations.
    """
    db = None
    try:
        db = get_sync_session()
        yield db
        db.commit()
    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"Sync database error: {e}")
        raise
    finally:
        if db:
            db.close()

@contextmanager
def get_db_readonly():
    """Get synchronous read-only session"""
    db = None
    try:
        db = get_sync_session()
        yield db
    finally:
        if db:
            db.close()

async def healthcheck_db() -> bool:
    """
    Check database connectivity using async connection.
    Verifies that PostgreSQL is accessible and responsive.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def init_db():
    """
    Initialize database by importing all models.
    This registers models with SQLAlchemy metadata.
    
    NOTE: For schema management, use Alembic migrations:
    - Create migration: alembic revision --autogenerate -m "description"
    - Apply migrations: alembic upgrade head
    - Downgrade: alembic downgrade -1
    """
    try:
        # Import models to register them with SQLAlchemy Base
        from app.models import (  # noqa
            User, Outlet, Product, Inventory, SaleTransaction,
            Supplier, PurchaseOrder, Invoice, Alert, Forecast, ChatMessage
        )
        logger.info("Database models initialized")
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        raise
