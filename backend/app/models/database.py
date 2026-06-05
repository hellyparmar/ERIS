"""
database.py - Database Connection & Session Management
MSc Data Science Project - Enterprise Retail Intelligence System

Supports PostgreSQL only.
"""

import os
import logging
import time
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .base import Base

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://eris_admin:JnCSXvJLgIY7V8KtUd2TT26QXkbgvuwv@localhost:5434/eris_production"
)

# ── Engine ────────────────────────────────────────────────────────────────────

def _build_engine(url: str):
    """Build the SQLAlchemy engine for PostgreSQL only."""
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False,
    )


engine = _build_engine(DATABASE_URL)


# ── Connection-hold monitoring ────────────────────────────────────────────────

@event.listens_for(engine, "checkout")
def on_checkout(dbapi_conn, conn_record, conn_proxy):
    conn_record.info["checkout_time"] = time.monotonic()


@event.listens_for(engine, "checkin")
def on_checkin(dbapi_conn, conn_record):
    start = conn_record.info.get("checkout_time")
    if start:
        duration = time.monotonic() - start
        if duration > 2.0:
            logger.warning("Slow DB connection: held for %.2fs", duration)


# ── Session factory ───────────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session, ensuring teardown after each request.

    Usage in a FastAPI route:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Transaction helper (for services / background tasks) ─────────────────────

@contextmanager
def get_db_transaction():
    """
    Context manager that wraps work in a single transaction.

    Commits on success, rolls back on any exception.

    Usage:
        with get_db_transaction() as db:
            db.add(some_object)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Read-only helper ─────────────────────────────────────────────────────────

@contextmanager
def get_db_readonly():
    """Yield a session for read-only queries (no commit)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Table initialisation ─────────────────────────────────────────────────────

def init_db(drop_first: bool = False) -> None:
    """
    Create all tables defined across the models package.

    Args:
        drop_first: If True, drops all existing tables first (dev use only).
    """
    # Import all model modules to ensure they are registered with Base.metadata
    import app.models.organization  # noqa: F401
    import app.models.users         # noqa: F401
    import app.models.product       # noqa: F401
    import app.models.customers     # noqa: F401
    import app.models.invoicing     # noqa: F401
    import app.models.sale          # noqa: F401
    import app.models.alert         # noqa: F401

    if drop_first:
        logger.warning("Dropping all tables — this is destructive!")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables initialised")


# ── Health check ─────────────────────────────────────────────────────────────

def healthcheck_db() -> bool:
    """Return True if the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        return False


__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_transaction",
    "get_db_readonly",
    "init_db",
    "healthcheck_db",
]
