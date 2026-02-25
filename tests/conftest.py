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
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from api.main import app
from api.db.database import get_db
from api.auth.password import hash_password

# Simple User model for testing (to avoid relationship issues)
Base = declarative_base()

class User(Base):
    """Simple user model for testing"""
    __tablename__ = "test_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    is_active = Column(Boolean, default=True)


class MockUser:
    """Mock user object for dependency injection"""
    def __init__(self, id=1, username="testuser", email="test@example.com", role="user", is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.is_active = is_active

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
    
    # Don't mock authentication by default
    # Let endpoints fail with 401 if no auth headers provided
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
        password_hash=hash_password("TestPass123"),
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
        password_hash=hash_password("AdminPass123"),
        role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    # Mock the current user dependency to return a regular user
    try:
        from api.auth.dependencies import get_current_active_user
        def mock_get_current_user():
            return MockUser(id=1, username="testuser", role="user")
        client.app.dependency_overrides[get_current_active_user] = mock_get_current_user
    except ImportError:
        pass
    
    return {"Authorization": "Bearer test-token-user"}

@pytest.fixture(scope="function")
def admin_headers(client, admin_user):
    """Get authentication headers for admin user"""
    # Mock the current user dependency to return admin role
    try:
        from api.auth.dependencies import get_current_active_user
        def mock_get_current_admin():
            return MockUser(id=2, username="admin", role="admin")
        client.app.dependency_overrides[get_current_active_user] = mock_get_current_admin
    except ImportError:
        pass
    
    return {"Authorization": "Bearer test-token-admin"}
