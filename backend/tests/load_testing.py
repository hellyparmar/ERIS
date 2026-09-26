"""
load_testing.py – Locust load test for the Enterprise Retail Intelligence System API.
"""

from locust import HttpUser, task, between, events
import random
import json
import os


class RetailSystemUser(HttpUser):
    """
    Simulates a typical retail staff user hitting the API.
    Wait time: 1–5 seconds between requests (simulates human interaction).
    """

    wait_time = between(1, 5)
    token: str = ""

    def on_start(self):
        """Authenticate before running tasks."""
        with self.client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": os.getenv("TEST_ADMIN_PASSWORD", "testpass"),
        }, catch_response=True) as resp:
            if resp.status_code == 200:
                body = resp.json()
                self.token = body.get("access_token", "")
                resp.success()
            else:
                self.token = ""
                resp.failure(f"Login failed: {resp.status_code}")

    @property
    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def view_dashboard(self):
        self.client.get("/api/v1/analytics/metrics", headers=self._auth, name="/analytics/metrics")

    @task(4)
    def list_inventory(self):
        self.client.get("/api/v1/inventory", headers=self._auth, name="/inventory")

    @task(4)
    def low_stock_alert(self):
        self.client.get("/api/v1/inventory?low_stock_only=true", headers=self._auth, name="/inventory/low-stock")

    @task(3)
    def list_sales(self):
        self.client.get("/api/v1/sales", headers=self._auth, name="/sales")

    @task(2)
    def sales_summary(self):
        self.client.get("/api/v1/sales/summary?period=monthly", headers=self._auth, name="/sales/summary")


class StoreManagerUser(HttpUser):
    """
    Heavy-analysis user profile (manager).
    """
    wait_time = between(3, 10)
    weight = 1  # 1 manager per 5 staff
    token: str = ""

    def on_start(self):
        with self.client.post("/api/v1/auth/login", data={
            "username": "manager",
            "password": os.getenv("TEST_MANAGER_PASSWORD", "testpass"),
        }, catch_response=True) as resp:
            if resp.status_code == 200:
                self.token = resp.json().get("access_token", "")
                resp.success()
            else:
                self.token = ""
                resp.failure(f"Login failed: {resp.status_code}")

    @property
    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def sales_summary(self):
        self.client.get("/api/v1/sales/summary?period=monthly", headers=self._auth, name="/sales/summary")

    @task(2)
    def inventory_analytics(self):
        self.client.get("/api/v1/inventory", headers=self._auth, name="/inventory/analytics")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n[Load test started] — Enterprise Retail Intelligence System")
    print("   Target: >100 RPS, p95 < 500ms\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print(f"\n[Load test complete]:")
    print(f"   Total requests  : {stats.num_requests}")
    print(f"   Failure rate    : {stats.fail_ratio * 100:.1f}%")
    print(f"   Avg response    : {stats.avg_response_time:.0f}ms")
    print(f"   p95 latency     : {stats.get_response_time_percentile(0.95):.0f}ms")
    print(f"   RPS             : {stats.total_rps:.1f}\n")
