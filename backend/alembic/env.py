"""
alembic/env.py
Alembic environment — reads DATABASE_URL from env and uses the project Base metadata
for autogenerate (`alembic revision --autogenerate`).

DATABASE_URL is REQUIRED at runtime. Must be set in environment or .env file.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# ── Load environment variables ────────────────────────────────────────────────
# Load from multiple possible locations for flexibility
for env_file in ['.env', '../.env', '../../.env']:
    env_path = os.path.join(os.path.dirname(__file__), env_file)
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

# ── Make the app importable ───────────────────────────────────────────────────
# Resolve the "backend/" directory so imports like `app.models` work.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Import models so that Base.metadata knows about every table ───────────────
from app.models.models import Base   # noqa: F401 - must import after sys.path patch
# Individual imports ensure all mapper classes are registered
# import app.models.organization  # noqa: F401
# import app.models.users         # noqa: F401  # Commented out to avoid duplicate User table
# import app.models.product       # noqa: F401  # Commented out to avoid duplicate Product table
# import app.models.customers     # noqa: F401
# import app.models.invoicing     # noqa: F401  # Commented out to avoid duplicate Invoice table
# import app.models.sale          # noqa: F401  # Commented out to avoid duplicate Sale table
# import app.models.alert         # noqa: F401

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Get DATABASE_URL from environment and validate it is set.
    
    Raises:
        RuntimeError: If DATABASE_URL is not set or has invalid format
    """
    database_url = os.getenv("DATABASE_URL", "").strip()
    
    if not database_url:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "ALEMBIC CONFIGURATION ERROR\n"
            "=" * 70 + "\n"
            "DATABASE_URL environment variable is not set.\n"
            "This is REQUIRED for Alembic migrations to run.\n\n"
            "Set DATABASE_URL in your .env file or environment variables:\n"
            "  DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE\n\n"
            "Note: For migrations, asyncpg URLs will be converted to psycopg2 (sync).\n"
            "=" * 70 + "\n"
        )
        raise RuntimeError(error_msg)
    
    # Validate format (should start with postgresql:// or postgresql+asyncpg://)
    if not database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        raise RuntimeError(
            f"Invalid DATABASE_URL format. Must start with 'postgresql://' or "
            f"'postgresql+asyncpg://', got: {database_url[:50]}..."
        )
    
    # Convert asyncpg to psycopg2 for migrations (must be synchronous)
    if 'postgresql+asyncpg://' in database_url:
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    return database_url


# Set the DATABASE_URL at configuration time
# This fails fast if DATABASE_URL is not set
try:
    sqlalchemy_url = get_database_url()
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)
except RuntimeError as e:
    print(str(e), file=sys.stderr)
    raise


# ── Offline mode (generate SQL script without a live connection) ──────────────
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (apply directly to the database) ─────────────────────────────
def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
