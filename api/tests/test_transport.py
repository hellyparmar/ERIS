"""Connections to the database are encrypted in production."""
from app.db import require_tls


def test_production_postgres_requires_tls():
    assert require_tls("postgresql+psycopg2://u:p@db:5432/eris", "production") == \
        "postgresql+psycopg2://u:p@db:5432/eris?sslmode=require"
    assert require_tls("postgresql+psycopg2://u:p@db/eris?connect_timeout=5", "production").endswith("&sslmode=require")


def test_an_explicit_sslmode_is_kept():
    url = "postgresql+psycopg2://u:p@db/eris?sslmode=verify-full"
    assert require_tls(url, "production") == url


def test_development_and_sqlite_are_unchanged():
    assert require_tls("postgresql+psycopg2://u:p@localhost/eris", "development") == \
        "postgresql+psycopg2://u:p@localhost/eris"
    assert require_tls("sqlite:///x.db", "production") == "sqlite:///x.db"
