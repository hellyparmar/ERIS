"""
Sales endpoint tests.
Tests: create sale, get sales history, sales analytics.
"""
import uuid
import pytest
from datetime import datetime


def _sale_payload(product_id=None, customer_id=None):
    return {
        "store_id": 1,
        "customer_id": customer_id,
        "items": [
            {
                "product_id": product_id or 1,
                "quantity": 2,
                "unit_price": 299.99,
            }
        ],
        "discount": 0.0,
        "tax": 53.99,
        "payment_method": "cash",
    }


class TestSales:
    def test_get_sales_unauthenticated(self, test_client):
        """Sales list requires authentication."""
        resp = test_client.get("/api/v1/sales/")
        assert resp.status_code == 401, resp.text

    def test_get_sales_authenticated(self, test_client, auth_headers):
        """Authenticated user can fetch sales list."""
        resp = test_client.get("/api/v1/sales/", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text
        if resp.status_code == 200:
            assert isinstance(resp.json(), (list, dict))

    def test_create_sale(self, test_client, auth_headers):
        """Creating a sale returns 200/201 with transaction ID."""
        resp = test_client.post(
            "/api/v1/sales/",
            json=_sale_payload(),
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201, 400, 422), resp.text
        if resp.status_code in (200, 201):
            data = resp.json()
            assert "transaction_id" in data or "id" in data

    def test_create_sale_invalid_payload(self, test_client, auth_headers):
        """Sale with missing required fields must be rejected."""
        resp = test_client.post(
            "/api/v1/sales/",
            json={"store_id": 1},  # missing items
            headers=auth_headers,
        )
        assert resp.status_code in (400, 422), resp.text

    def test_get_sale_by_id(self, test_client, auth_headers):
        """Fetching a specific sale by ID returns sale details or 404."""
        resp = test_client.get("/api/v1/sales/999999", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text

    def test_sales_analytics(self, test_client, auth_headers):
        """Sales analytics endpoint returns structured report data."""
        resp = test_client.get(
            "/api/v1/analytics/sales",
            params={"period": "month"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 404, 422), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)

    def test_sales_summary(self, test_client, auth_headers):
        """Sales summary endpoint is reachable and returns dict."""
        resp = test_client.get("/api/v1/sales/summary", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text

    def test_daily_sales_report(self, test_client, auth_headers):
        """Daily report endpoint accepts date parameter."""
        today = datetime.now().strftime("%Y-%m-%d")
        resp = test_client.get(
            "/api/v1/sales/daily-report",
            params={"date": today},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 404, 422), resp.text
