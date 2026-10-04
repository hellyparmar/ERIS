"""Database engine and session management (SQLAlchemy 2.0, synchronous)."""
from collections.abc import Iterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    if url.startswith("sqlite"):
        db_path = url.split("///", 1)[-1]
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # timeout: how long a writer waits for SQLite's single write lock before giving up
        engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _):
            # Let SQLAlchemy control transactions (pysqlite's implicit BEGIN breaks SAVEPOINTs).
            dbapi_conn.isolation_level = None
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.close()

        @event.listens_for(engine, "begin")
        def _sqlite_begin(conn):
            # Write requests take the write lock when their transaction starts (BEGIN IMMEDIATE) and queue for it.
            # A plain BEGIN would read first and then fail with "database is locked" when another request wrote
            # in between (SQLite cannot upgrade a stale read snapshot in WAL mode).
            immediate = conn.get_execution_options().get("sqlite_immediate")
            conn.exec_driver_sql("BEGIN IMMEDIATE" if immediate else "BEGIN")

        return engine
    _register_numpy_adapters()
    return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20, insertmanyvalues_page_size=5000)


def _register_numpy_adapters() -> None:
    """Let psycopg2 accept NumPy scalars (pandas/NumPy results flow into inserts and filters)."""
    try:
        import numpy as np
        from psycopg2.extensions import AsIs, register_adapter
    except ImportError:
        return
    for t in (np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64):
        register_adapter(t, lambda v: AsIs(int(v)))
    for t in (np.float16, np.float32, np.float64):
        register_adapter(t, lambda v: AsIs(repr(float(v))))
    register_adapter(np.bool_, lambda v: AsIs(bool(v)))


engine = _make_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
_write_engine = engine.execution_options(sqlite_immediate=True)


# POSTs that mostly read: sign-in only records the last-login time (best effort) and the assistant computes an answer
# (possibly via a slow local LLM) before saving it in a short write_session(), so neither may hold the write lock
READ_MOSTLY_POSTS = {"/api/auth/login", "/api/auth/refresh", "/api/assistant/chat"}


def write_engine():
    """Engine whose transactions take SQLite's write lock up front (BEGIN IMMEDIATE)."""
    return _write_engine


def write_session() -> Session:
    """A separate short write transaction for a request that otherwise only reads (e.g. saving a forecast run).

    On SQLite a read transaction cannot be upgraded to a write once another request has written, so writes made
    while serving a read go through their own session that takes the write lock up front."""
    return SessionLocal(bind=_write_engine)


def get_db(request: Request) -> Iterator[Session]:
    """Session for one request. Requests that change data use write transactions from the start on SQLite."""
    writes = request.method not in ("GET", "HEAD", "OPTIONS") and request.url.path not in READ_MOSTLY_POSTS
    db = SessionLocal(bind=_write_engine) if writes and settings.is_sqlite else SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables directly (tests / throwaway databases). Normal startup uses `migrate()`."""
    from app import models  # noqa: F401  (register models)

    Base.metadata.create_all(engine)


def migrate() -> None:
    """Bring the database schema to the latest Alembic revision (one migration tree for SQLite & PostgreSQL).

    Databases created by ERIS v2 (before migrations existed) are detected: an untouched synthetic demo is simply
    rebuilt; a database containing user data stops with instructions instead of being modified.
    """
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect, text

    from app import models  # noqa: F401

    api_dir = Path(__file__).resolve().parent.parent
    cfg = Config(str(api_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_dir / "migrations"))
    tables = set(inspect(engine).get_table_names())
    if tables and "alembic_version" not in tables:
        with engine.connect() as conn:
            sources = {r[0] for r in conn.execute(text("SELECT DISTINCT source FROM sales"))} if "sales" in tables else set()
        if sources - {"demo", "synthetic"}:
            raise RuntimeError(
                "This database was created by an older ERIS version and contains your own data. Export it "
                "(Sales/Products/Customers -> Export), point DATABASE_URL at a new database and import the CSVs.")
        Base.metadata.drop_all(engine)
        with engine.begin() as conn:
            for t in tables - set(Base.metadata.tables):
                conn.execute(text(f'DROP TABLE IF EXISTS "{t}"'))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")
