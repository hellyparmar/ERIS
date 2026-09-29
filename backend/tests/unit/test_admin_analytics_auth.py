"""
Test Authentication on Admin and Analytics Routers

Verifies that both admin.py and analytics.py correctly resolve authenticated
users via app.api.deps.get_current_user using the JWT username 'sub' claim,
returning 200 OK (not 401 Unauthorized).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from tests.conftest import _TEST_ADMIN_PW

@pytest.fixture
def auth_headers(client, seed_users):
    login_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": _TEST_ADMIN_PW})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    data = login_res.json()
    token = data.get("access_token")
    assert token, "No access_token received"
    return {"Authorization": f"Bearer {token}"}

def test_admin_users_endpoint_authenticated(client, auth_headers):
    """Admin /users endpoint should return 200 with valid admin token"""
    res = client.get("/api/v1/admin/users", headers=auth_headers)
    assert res.status_code == 200
    users = res.json()
    assert isinstance(users, list)
    assert len(users) > 0

def test_analytics_dashboard_summary_authenticated(client, auth_headers):
    """Analytics /dashboard/summary endpoint should return 200 with valid token"""
    res = client.get("/api/v1/analytics/dashboard/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "summary_text" in data

def test_unauthenticated_requests_fail(client, seed_users):
    """Requests without authorization header must fail with 401"""
    res_admin = client.get("/api/v1/admin/users")
    assert res_admin.status_code == 401
    res_analytics = client.get("/api/v1/analytics/dashboard/summary")
    assert res_analytics.status_code == 401
