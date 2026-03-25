"""
Test fixtures for the ERIS backend test suite.
Uses SQLite in-memory for isolation — no live database or external services required.
"""
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
print("--- PRE-IMPORT CONFTEST ---")

import pytest
import pytest_asyncio
from typing import Generator

# ── Override DATABASE_URL BEFORE any app code imports ──────────────────────
os.environ["DATABASE_URL"] = "sqlite:///./test.db?check_same_thread=False"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-only-for-testing-purposes-32chars"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient
from app.models import Base
from app.models import get_db
from app.main import app

# ── In-memory SQLite engine (shared across the whole test session) ──────────
TEST_DATABASE_URL = "sqlite:///./test.db?check_same_thread=False"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the test session, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_db():
    """Provide a transactional DB session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def test_client(test_db) -> Generator:
    """FastAPI TestClient with the DB dependency overridden."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    from app.middleware.rate_limiter import limiter
    # Fix rate limits in tests
    limiter.enabled = False
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
    app.dependency_overrides.clear()
    limiter.enabled = True


@pytest.fixture()
def registered_user(test_client) -> dict:
    """Register a fresh user unique to this test."""
    import uuid
    uid = uuid.uuid4().hex[0:6]
    payload = {
        "email": f"test_{uid}@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "organization_name": f"Test Org {uid}",
        "role": "ADMIN",
    }
    resp = test_client.post("/api/v1/auth/register", json=payload)
    return {"payload": payload, "response": resp}


@pytest.fixture()
def auth_headers(test_client, registered_user) -> dict:
    """
    Log in with the registered user and return Bearer auth headers.
    Uses OAuth2 form-style login (username/password).
    """
    payload = registered_user["payload"]
    resp = test_client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    if resp.status_code == 200:
        token = resp.json().get("access_token", "")
        return {"Authorization": f"Bearer {token}"}
    # Fallback: try JSON login
    resp2 = test_client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = resp2.json().get("access_token", "") if resp2.status_code == 200 else ""
    return {"Authorization": f"Bearer {token}"}
