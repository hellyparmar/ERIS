from sqlalchemy import create_engine as _create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url
from contextlib import contextmanager
from fastapi import Request
import logging
import os

from app.core.config import settings
from app.models.base import Base

logger = logging.getLogger(__name__)

configured_database_url = settings.DATABASE_URL

# Convert local SQLite URLs to the async-compatible aiosqlite driver
if configured_database_url.startswith("sqlite://") and not configured_database_url.startswith("sqlite+aiosqlite://"):
    database_url = configured_database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
elif configured_database_url.startswith(("postgresql://", "postgres://", "postgresql+asyncpg://")):
    postgres_url = make_url(configured_database_url.replace("postgres://", "postgresql://", 1))
    query = dict(postgres_url.query)
    ssl_mode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    if ssl_mode:
        query["ssl"] = ssl_mode
    database_url = postgres_url.set(drivername="postgresql+asyncpg", query=query).render_as_string(hide_password=False)
else:
    database_url = configured_database_url

url = make_url(database_url)
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
}

# Handle PostgreSQL async engine
if url.drivername.startswith("postgresql"):
    engine_kwargs.update(
        {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "5")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Verify connections before using them
        }
    )

    # Add echo for SQL debugging
    if os.getenv("DEBUG", "false").lower() == "true":
        engine_kwargs["echo"] = True
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

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "SessionLocal",
    "get_db",
    "get_sync_session",
    "get_db_sync",
    "get_db_readonly",
    "healthcheck_db",
    "init_db",
    "get_db_dependency",
    "get_db_sync_dependency",
]

# Module-level synchronous session factory for sync-only tasks

_sync_url = (
    configured_database_url.replace("postgres://", "postgresql://", 1)
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("sqlite+aiosqlite://", "sqlite://")
)
if "ssl=" in _sync_url:
    _sync_url = _sync_url.replace("ssl=", "sslmode=")
_sync_engine_kwargs = {"pool_pre_ping": True}
if _sync_url.startswith("sqlite:"):
    _sync_engine_kwargs["connect_args"] = {"check_same_thread": False}
_sync_engine = _create_engine(_sync_url, **_sync_engine_kwargs)
SessionLocal = sessionmaker(
    bind=_sync_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
AsyncSessionLocal_alias = AsyncSessionLocal


def get_sync_session():
    """Get synchronous session - only use for sync-only contexts (tasks, CLI, etc.)"""
    return SessionLocal()


async def get_db(request: Request = None):
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
    """
    async with AsyncSessionLocal() as session:
        return session


@contextmanager
def get_db_sync():
    """
    Get synchronous database session for sync-only operations (tasks, migrations, CLI).
    WARNING: Do NOT use this with async/await code.
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


async def get_db_sync_dependency(request: Request = None):
    """Dependency for synchronous FastAPI endpoints"""
    db = get_sync_session()
    try:
        yield db
    finally:
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
    try:
        from app.models import (  # noqa
            User,
            Outlet,
            Product,
            Inventory,
            SaleTransaction,
            Supplier,
            Invoice,
            Alert,
            ForecastResult,
            ChatMessage,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    except Exception as e:
        if "already exists" in str(e):
            logger.warning("Some indexes already exist (idempotent startup)")
        else:
            logger.error(f"Failed to initialize database: {e}")
            raise
