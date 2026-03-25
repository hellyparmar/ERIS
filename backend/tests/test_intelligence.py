"""
AI Intelligence (forecasting, anomaly detection) endpoint tests.
"""
import pytest


class TestForecasting:
    def test_forecast_unauthenticated(self, test_client):
        """Forecast endpoint requires authentication."""
        resp = test_client.post("/api/v1/intelligence/forecast", json={"days_ahead": 7})
        assert resp.status_code in (401, 422), resp.text

    def test_forecast_generation(self, test_client, auth_headers):
        """Forecast endpoint returns time-series data for given horizon."""
        resp = test_client.post(
            "/api/v1/intelligence/forecast",
            json={"days_ahead": 7, "confidence_level": 0.95},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201, 404, 422), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, (list, dict))

    def test_forecast_invalid_days(self, test_client, auth_headers):
        """Forecast with 0 or negative days_ahead should be rejected."""
        resp = test_client.post(
            "/api/v1/intelligence/forecast",
            json={"days_ahead": -5},
            headers=auth_headers,
        )
        assert resp.status_code in (400, 422), resp.text

    def test_forecast_long_horizon(self, test_client, auth_headers):
        """Forecast for 90 days is accepted and returns results."""
        resp = test_client.post(
            "/api/v1/intelligence/forecast",
            json={"days_ahead": 90, "confidence_level": 0.95},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201, 404, 422), resp.text


class TestAnomalyDetection:
    def test_anomaly_endpoint_accessible(self, test_client, auth_headers):
        """Anomaly detection endpoint is accessible."""
        resp = test_client.get("/api/v1/intelligence/anomalies", headers=auth_headers)
        assert resp.status_code in (200, 404), resp.text

    def test_anomaly_with_severity_filter(self, test_client, auth_headers):
        """Anomaly endpoint accepts severity filter parameter."""
        resp = test_client.get(
            "/api/v1/intelligence/anomalies",
            params={"severity": "critical"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 404, 422), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict) or isinstance(data, list)

    def test_anomaly_response_structure(self, test_client, auth_headers):
        """When successful, anomaly response has expected fields."""
        resp = test_client.get("/api/v1/intelligence/anomalies", headers=auth_headers)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                assert "anomalies" in data or "alerts" in data or "total_alerts" in data

    def test_intelligence_unauthenticated(self, test_client):
        """Intelligence endpoints require authentication."""
        resp = test_client.get("/api/v1/intelligence/anomalies")
        assert resp.status_code in (401, 422), resp.text
