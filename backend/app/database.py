from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url
from contextlib import contextmanager
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

__all__ = ["engine", "AsyncSessionLocal", "SessionLocal", "get_db", "get_sync_session", "get_db_sync", "get_db_readonly", "healthcheck_db", "init_db", "get_db_dependency", "get_db_sync_dependency"]

# Module-level synchronous session factory for sync-only tasks
from sqlalchemy import create_engine as _create_engine
_sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite://", "sqlite://")
if "ssl=" in _sync_url:
    _sync_url = _sync_url.replace("ssl=", "sslmode=")
_sync_engine = _create_engine(_sync_url, pool_pre_ping=True)
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

from fastapi import Request, HTTPException

async def get_db(request: Request = None):
    """
    Async dependency for FastAPI endpoints.
    Provides an AsyncSession with proper error handling and RLS context.
    Fails closed if setting the tenant context fails on PostgreSQL.
    """
    async_session = AsyncSessionLocal()
    try:
        # Enforce RLS if tenant context is available from middleware
        if request and hasattr(request.state, "tenant_context") and request.state.tenant_context:
            context = request.state.tenant_context
            try:
                await async_session.execute(
                    text("SELECT set_config('app.current_tenant', :tenant, false), set_config('app.current_tenant_id', :tenant, false)"),
                    {"tenant": str(context.tenant_id)}
                )
            except Exception as e:
                # Check if sqlite (e.g. unit test environment without postgres set_config)
                bind = async_session.bind
                if bind and hasattr(bind, 'dialect') and bind.dialect.name == "sqlite":
                    logger.debug("Skipping PostgreSQL set_config on SQLite session")
                else:
                    logger.error(f"Failed to set tenant context for tenant {context.tenant_id}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to initialize tenant security context"
                    )
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
def get_db_sync(tenant_id=None):
    """
    Get synchronous database session for sync-only operations.
    WARNING: Do NOT use this with async/await code - causes greenlet errors!
    Only use in sync tasks, migrations, or CLI operations.
    Fails closed if setting the tenant context fails on PostgreSQL.
    """
    db = None
    try:
        db = get_sync_session()
        if tenant_id:
            from sqlalchemy import text
            try:
                db.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"), {"tenant_id": str(tenant_id)})
            except Exception as e:
                bind = db.bind
                if bind and hasattr(bind, 'dialect') and bind.dialect.name == "sqlite":
                    logger.debug("Skipping PostgreSQL set_config on SQLite sync session")
                else:
                    logger.error(f"Failed to set tenant context in sync session for tenant {tenant_id}: {e}")
                    raise
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

def get_db_sync_dependency():
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
            User, Outlet, Product, Inventory, SaleTransaction,
            Supplier, PurchaseOrder, Invoice, Alert, Forecast, ChatMessage
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

