"""Database engine and session management (SQLAlchemy 2.0, synchronous)."""
from collections.abc import Iterator
from pathlib import Path

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
        engine = create_engine(url, connect_args={"check_same_thread": False})

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
            conn.exec_driver_sql("BEGIN")

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


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    from app import models  # noqa: F401  (register models)

    Base.metadata.create_all(engine)
