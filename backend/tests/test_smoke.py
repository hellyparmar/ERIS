"""
Golden smoke tests for core functionality in ERIS.
Verifies critical paths:
1. User authentication / login (JWT issuance)
2. Listing accessible outlets
3. Listing sales transactions
4. Forecasting request
5. Startup fail-fast validation for missing or placeholder secrets
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.main import validate_required_env_vars, is_placeholder_secret
from app.models.outlet import Outlet
from app.models.models_v6 import Sale
from app.models.users import UserOutletAccess

_TEST_ADMIN_PW = "test-admin-pw"


def test_login_success(client, seed_users):
    """Smoke test: Login with seeded admin credentials returns a valid JWT token."""
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": _TEST_ADMIN_PW}
    )
    assert res.status_code == 200, f"Login failed: {res.text}"
    body = res.json()
    assert "access_token" in body
    assert body.get("token_type", "").lower() == "bearer"
    assert len(body["access_token"]) > 20


def test_login_invalid_password_refused(client, seed_users):
    """Smoke test: Login with bad credentials is explicitly rejected with 401."""
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrong-password"}
    )
    assert res.status_code == 401


def test_list_outlets(client, admin_token, db, seed_users):
    """Smoke test: Authenticated user can list outlets."""
    admin_user = seed_users[0]
    # Create test outlet
    outlet = Outlet(name="Flagship Mumbai", city="Mumbai", is_active=True)
    db.add(outlet)
    db.commit()
    db.refresh(outlet)

    # Grant admin access to outlet
    access = UserOutletAccess(user_id=admin_user.id, outlet_id=outlet.id)
    db.add(access)
    db.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/outlets", headers=headers)
    assert res.status_code == 200, f"List outlets failed: {res.text}"
    outlets = res.json()
    assert isinstance(outlets, list)
    assert any(o.get("name") == "Flagship Mumbai" for o in outlets)


def test_list_sales(client, admin_token, db, seed_users):
    """Smoke test: Authenticated user can list sales records."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/sales/", headers=headers)
    assert res.status_code == 200, f"List sales failed: {res.text}"
    data = res.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_forecast_request(client, admin_token, db):
    """Smoke test: Forecast anomalies endpoint responds with success."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/forecasting/anomalies?store_id=1&lookback_days=90", headers=headers)
    assert res.status_code == 200, f"Forecast anomalies failed: {res.text}"
    body = res.json()
    assert body.get("success") is True
    assert "anomalies" in body


# ── Secret Validation & Fail-Fast Smoke Tests ─────────────────────────────────

def test_placeholder_detector():
    """Verify placeholder secret detection flags common dummy values."""
    assert is_placeholder_secret(None) is True
    assert is_placeholder_secret("") is True
    assert is_placeholder_secret("   ") is True
    assert is_placeholder_secret("CHANGE_ME") is True
    assert is_placeholder_secret("CHANGE_ME_OR_LEAVE_BLANK") is True
    assert is_placeholder_secret("changeme") is True
    assert is_placeholder_secret("your_secret_key") is True
    assert is_placeholder_secret("dev_secret") is True
    # Real-looking or explicit mock key for tests is not a generic placeholder
    assert is_placeholder_secret("real_random_entropy_secret_key_123456789") is False


def test_startup_refuses_placeholder_jwt_secret(monkeypatch):
    """App startup validation must raise RuntimeError if JWT_SECRET is a placeholder."""
    monkeypatch.setenv("JWT_SECRET_KEY", "CHANGE_ME")
    monkeypatch.setenv("JWT_SECRET", "CHANGE_ME")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("ENCRYPTION_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")
    with pytest.raises(RuntimeError, match="Missing or placeholder required environment variables"):
        validate_required_env_vars()


def test_startup_refuses_placeholder_database_url(monkeypatch):
    """App startup validation must raise RuntimeError if DATABASE_URL is a placeholder."""
    monkeypatch.setenv("DATABASE_URL", "CHANGE_ME")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-long-for-testing-only")
    monkeypatch.setenv("ENCRYPTION_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")
    with pytest.raises(RuntimeError, match="Missing or placeholder required environment variables"):
        validate_required_env_vars()


def test_startup_refuses_placeholder_encryption_key(monkeypatch):
    """App startup validation must raise RuntimeError if ENCRYPTION_KEY is a placeholder."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-long-for-testing-only")
    monkeypatch.setenv("ENCRYPTION_KEY", "CHANGE_ME")
    with pytest.raises(RuntimeError, match="Missing or placeholder required environment variables"):
        validate_required_env_vars()
