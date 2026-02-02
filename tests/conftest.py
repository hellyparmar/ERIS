"""
Test Configuration and Fixtures
Shared test utilities, database setup, and authentication helpers
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.db.database import Base, get_db
from api.db.models import User
from api.auth.password import hash_password

# Test database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        password=hash_password("TestPass123!"),
        full_name="Test User",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user"""
    admin = User(
        username="admin",
        email="admin@example.com",
        password=hash_password("AdminPass123!"),
        full_name="Admin User",
        role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "TestPass123!"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def admin_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "AdminPass123!"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
