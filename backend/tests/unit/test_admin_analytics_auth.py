"""
Test Authentication on Admin and Analytics Routers

Verifies that both admin.py and analytics.py correctly resolve authenticated
users via app.api.deps.get_current_user using the JWT username 'sub' claim,
returning 200 OK (not 401 Unauthorized).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import _TEST_ADMIN_PW

class TestAdminAnalyticsAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Authenticate as real seeded admin user
        login_res = cls.client.post("/api/v1/auth/login", data={"username": "admin", "password": _TEST_ADMIN_PW})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        data = login_res.json()
        cls.token = data.get("access_token")
        assert cls.token, "No access_token received"
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def test_admin_users_endpoint_authenticated(self):
        """Admin /users endpoint should return 200 with valid admin token"""
        res = self.client.get("/api/v1/admin/users", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        users = res.json()
        self.assertIsInstance(users, list)
        self.assertGreater(len(users), 0)

    def test_analytics_dashboard_summary_authenticated(self):
        """Analytics /dashboard/summary endpoint should return 200 with valid token"""
        res = self.client.get("/api/v1/analytics/dashboard/summary", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("summary_text", data)

    def test_unauthenticated_requests_fail(self):
        """Requests without authorization header must fail with 401"""
        res_admin = self.client.get("/api/v1/admin/users")
        self.assertEqual(res_admin.status_code, 401)
        res_analytics = self.client.get("/api/v1/analytics/dashboard/summary")
        self.assertEqual(res_analytics.status_code, 401)

if __name__ == "__main__":
    unittest.main()
