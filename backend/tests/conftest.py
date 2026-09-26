"""
Pytest configuration and fixtures for R-DIOS tests.
Uses SQLite in-memory database for fast, isolated tests.
"""
import sys
import os
from typing import Generator

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test database before any app imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test_secret"
os.environ["ENVIRONMENT"] = "test"

# ---------------------------------------------------------------------------
# TEST-ONLY passwords — these are NOT real credentials.
# They are used exclusively to seed an in-memory SQLite DB for automated tests.
# ---------------------------------------------------------------------------
_TEST_ADMIN_PW    = "test-admin-pw"
_TEST_MANAGER_PW  = "test-manager-pw"
_TEST_ANALYST_PW  = "test-analyst-pw"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Import app components only after DATABASE_URL is set  
try:
    from app.main import app
except ImportError as e:
    print(f"WARNING: Could not import app.main: {e}")
    app = None

from app.models.schema import Base
from app.models.users import User
from app.core.security import hash_password
from app.database import get_db

# Use in-memory SQLite — no file written to disk, fully isolated.
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test function."""
    from app.models import (
        User, Outlet, Product, Inventory, SaleTransaction,
        Supplier, PurchaseOrder, Invoice, Alert, Forecast, ChatMessage
    )
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with the test database injected."""
    if app is None:
        pytest.skip("FastAPI app not available")
    
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_users(db):
    """Seed test users with properly hashed passwords."""
    from app.models.users import Role
    from app.models.organization import Organization
    
    # Create a test organization if it doesn't exist
    org = Organization(name="Test Organization")
    db.add(org)
    db.commit()
    
    # Create roles
    admin_role = Role(name="admin", description="Administrator")
    manager_role = Role(name="manager", description="Manager")
    analyst_role = Role(name="analyst", description="Analyst")
    db.add(admin_role)
    db.add(manager_role)
    db.add(analyst_role)
    db.commit()
    
    users = [
        User(
            email="admin@test.com",
            username="admin",
            first_name="Test",
            last_name="Admin",
            password_hash=hash_password(_TEST_ADMIN_PW),
            role_id=admin_role.id,
            organization_id=org.id,
        ),
        User(
            email="manager@test.com",
            username="manager",
            first_name="Test",
            last_name="Manager",
            password_hash=hash_password(_TEST_MANAGER_PW),
            role_id=manager_role.id,
            organization_id=org.id,
        ),
        User(
            email="analyst@test.com",
            username="analyst",
            first_name="Test",
            last_name="Analyst",
            password_hash=hash_password(_TEST_ANALYST_PW),
            role_id=analyst_role.id,
            organization_id=org.id,
        ),
    ]
    for u in users:
        db.add(u)
    db.commit()
    return users


@pytest.fixture
def admin_token(client, seed_users):
    """Get a valid JWT for the admin user."""
    res = client.post("/api/v1/auth/login", data={"username": "admin@test.com", "password": _TEST_ADMIN_PW})
    assert res.status_code == 200, f"Login failed: {res.json()}"
    return res.json()["access_token"]


@pytest.fixture
def manager_token(client, seed_users):
    """Get a valid JWT for the manager user."""
    res = client.post("/api/v1/auth/login", data={"username": "manager@test.com", "password": _TEST_MANAGER_PW})
    assert res.status_code == 200
    return res.json()["access_token"]
