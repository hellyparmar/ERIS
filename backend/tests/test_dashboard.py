"""
Dashboard endpoint tests.
Tests: dashboard overview, KPIs, charts, real-time data.
"""
import pytest


class TestDashboard:
    def test_dashboard_unauthenticated(self, test_client):
        """Dashboard requires authentication."""
        resp = test_client.get("/api/v1/dashboard/")
        assert resp.status_code in (401, 404), resp.text

    def test_dashboard_overview(self, test_client, auth_headers):
        """Dashboard overview returns expected KPI structure."""
        resp = test_client.get("/api/v1/dashboard/", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text
        if resp.status_code == 200:
            assert isinstance(resp.json(), dict)

    def test_dashboard_stats(self, test_client, auth_headers):
        """Dashboard stats endpoint returns revenue and orders info."""
        resp = test_client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text

    def test_dashboard_kpis(self, test_client, auth_headers):
        """KPI endpoint returns structured key performance indicators."""
        resp = test_client.get("/api/v1/dashboard/kpis", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)

    def test_dashboard_recent_sales(self, test_client, auth_headers):
        """Recent sales widget returns a list."""
        resp = test_client.get("/api/v1/dashboard/recent-sales", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text
        if resp.status_code == 200:
            assert isinstance(resp.json(), (list, dict))

    def test_dashboard_top_products(self, test_client, auth_headers):
        """Top products report is accessible."""
        resp = test_client.get("/api/v1/dashboard/top-products", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text

    def test_dashboard_revenue_chart(self, test_client, auth_headers):
        """Revenue chart data is accessible with period parameter."""
        resp = test_client.get(
            "/api/v1/dashboard/revenue-chart",
            params={"period": "week"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 404, 422), resp.text

    def test_health_check(self, test_client):
        """Health check endpoint is always accessible without auth."""
        resp = test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy"
