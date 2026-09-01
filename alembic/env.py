"""
alembic/env.py
Alembic environment — reads DATABASE_URL from env and uses the project Base metadata
for migrations.

IMPORTANT: Alembic migrations must run SYNCHRONOUSLY (blocking).
This file converts async driver URLs to sync for migration execution.
"""

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, create_engine
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
for env_file in (project_root / '.env', project_root / 'backend' / '.env'):
    if env_file.exists():
        load_dotenv(env_file)

sys.path.insert(0, str(project_root / 'backend'))

# Try to import models, but if it fails, use a simple declarative base
# This is important for Docker migration containers where dependencies might not be available
try:
    from app.models import Base
    target_metadata = Base.metadata
except (ImportError, ModuleNotFoundError) as exc:
    print(f"[Alembic] Warning: could not import app.models: {exc}")
    print("[Alembic] Using empty declarative base for migrations")
    from sqlalchemy.orm import declarative_base
    target_metadata = declarative_base().metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def build_sync_database_url() -> str:
    """
    Build a synchronous database URL for migrations.
    
    Migrations must run synchronously. This function constructs a psycopg2
    (synchronous) URL from environment variables, bypassing any async drivers.
    
    Raises:
        RuntimeError: If required database configuration is missing
    """
    # Try to get DATABASE_URL first (preferred method)
    database_url = os.getenv('DATABASE_URL', '').strip()
    
    if database_url:
        # Convert async URL to sync URL
        # Replace postgresql+asyncpg:// with postgresql://
        if 'postgresql+asyncpg://' in database_url:
            sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
            print(f"[Alembic] Using DATABASE_URL (converted from asyncpg to psycopg2)")
            print(f"[Alembic] Sync URL: postgresql://***:***@{sync_url.split('@')[1]}")
            return sync_url
        elif database_url.startswith('postgresql://'):
            print(f"[Alembic] Using DATABASE_URL (already synchronous)")
            print(f"[Alembic] Sync URL: postgresql://***:***@{database_url.split('@')[1]}")
            return database_url
        else:
            raise RuntimeError(
                f"Invalid DATABASE_URL format: {database_url[:50]}... "
                "Must start with 'postgresql://' or 'postgresql+asyncpg://'"
            )
    
    # Fallback: Build from individual POSTGRES_* variables
    print("[Alembic] DATABASE_URL not found, building from POSTGRES_* variables")
    
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB')
    
    # Validate required variables
    missing = []
    if not db_user:
        missing.append('POSTGRES_USER')
    if not db_password:
        missing.append('POSTGRES_PASSWORD')
    if not db_name:
        missing.append('POSTGRES_DB')
    
    if missing:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "ALEMBIC CONFIGURATION ERROR\n"
            "=" * 70 + "\n"
            "DATABASE_URL environment variable is not set AND required POSTGRES_* "
            "variables are missing.\n\n"
            f"Missing variables: {', '.join(missing)}\n\n"
            "Required configuration:\n"
            "  Option 1 (preferred): Set DATABASE_URL\n"
            "    DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE\n\n"
            "  Option 2: Set individual variables\n"
            "    POSTGRES_USER=your_user\n"
            "    POSTGRES_PASSWORD=your_password\n"
            "    POSTGRES_DB=your_database\n"
            "    POSTGRES_HOST=localhost (default)\n"
            "    POSTGRES_PORT=5432 (default)\n\n"
            "Set these in your .env file or environment variables.\n"
            "=" * 70 + "\n"
        )
        raise RuntimeError(error_msg)
    
    # Construct synchronous URL (uses psycopg2 by default)
    sync_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    print(f"[Alembic] Constructed URL from POSTGRES_* variables")
    print(f"[Alembic] User: {db_user}, Host: {db_host}, Port: {db_port}, DB: {db_name}")
    
    return sync_url


def get_database_url() -> str:
    """
    Get database URL for migrations (synchronous).
    
    Prioritizes DATABASE_URL, falls back to constructing from POSTGRES_* variables.
    Raises explicit error if configuration is missing.
    """
    return build_sync_database_url()


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode - uses SQL scripts without database connection.
    Used for generating migration scripts for review.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode - connects to database and applies migrations.
    This is the default mode used by 'alembic upgrade head'.
    
    CRITICAL: Uses synchronous engine (psycopg2), not async (asyncpg)
    """
    url = get_database_url()
    
    print(f"[Alembic] Starting migrations...")
    
    # Create synchronous engine for migrations
    # Use connect_args to avoid any async-specific options
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        echo=False,  # Set to True for SQL debugging
    )

    print(f"[Alembic] Connecting to database...")
    with connectable.connect() as connection:
        print(f"[Alembic] Connected! Configuring context...")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        print(f"[Alembic] Running migrations...")
        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()
    print(f"[Alembic] Migrations complete!")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


