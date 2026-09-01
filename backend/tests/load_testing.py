"""
load_testing.py – Locust load test for the Enterprise Retail Intelligence System API.

Usage:
    locust -f tests/load_testing.py --host=http://localhost:8000
    # Or headless:
    locust -f tests/load_testing.py --host=http://localhost:8000 \
           --users=50 --spawn-rate=5 --run-time=60s --headless \
           --html=tests/reports/load_report.html
"""

from locust import HttpUser, task, between, events
import random
import json


class RetailSystemUser(HttpUser):
    """
    Simulates a typical retail staff user hitting the API.
    Wait time: 1–5 seconds between requests (simulates human interaction).
    """

    wait_time = between(1, 5)
    token: str = ""

    def on_start(self):
        """Authenticate before running tasks."""
        resp = self.client.post("/api/v1/auth/login", json={
            "email": "admin@store.com",
            "password": "Admin123!",
        }, catch_response=True)

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

    # ------------------------------------------------------------------
    # High frequency tasks (weighted higher)
    # ------------------------------------------------------------------

    @task(5)
    def view_dashboard(self):
        """Most common action — view store dashboard."""
        self.client.get("/api/v1/dashboard/summary", headers=self._auth, name="/dashboard/summary")

    @task(4)
    def list_inventory(self):
        self.client.get("/api/v1/inventory/list?limit=20&offset=0", headers=self._auth, name="/inventory/list")

    @task(4)
    def low_stock_alert(self):
        self.client.get("/api/v1/inventory/low-stock", headers=self._auth, name="/inventory/low-stock")

    @task(3)
    def list_employees(self):
        self.client.get("/api/v1/employees/", headers=self._auth, name="/employees/list")

    @task(3)
    def today_attendance(self):
        self.client.get("/api/v1/employees/today-status", headers=self._auth, name="/employees/today-status")

    @task(2)
    def list_suppliers(self):
        self.client.get("/api/v1/suppliers/", headers=self._auth, name="/suppliers/list")

    @task(2)
    def list_purchase_orders(self):
        self.client.get("/api/v1/suppliers/purchase-orders/all", headers=self._auth, name="/purchase-orders/all")

    @task(2)
    def sales_analytics(self):
        self.client.get("/api/v1/sales/analytics?period=month", headers=self._auth, name="/sales/analytics")

    # ------------------------------------------------------------------
    # Medium frequency tasks
    # ------------------------------------------------------------------

    @task(1)
    def employee_performance(self):
        self.client.get("/api/v1/employees/performance", headers=self._auth, name="/employees/performance")

    @task(1)
    def clock_in_random(self):
        """Simulate an employee clock-in."""
        emp_id = random.randint(1, 20)
        self.client.post("/api/v1/employees/clock-in", json={"employee_id": emp_id},
                         headers=self._auth, name="/employees/clock-in")

    @task(1)
    def create_sale(self):
        """Simulate creating a POS sale."""
        payload = {
            "items": [{"product_id": random.randint(1, 50), "quantity": random.randint(1, 5)}],
            "payment_method": random.choice(["cash", "upi", "card"]),
            "customer_id": None,
        }
        self.client.post("/api/v1/pos/sale", json=payload, headers=self._auth, name="/pos/sale")


class StoreManagerUser(HttpUser):
    """
    Heavy-analysis user profile (manager).
    Hits report and forecasting endpoints more.
    """

    wait_time = between(3, 10)
    weight = 1  # 1 manager per 5 staff
    token: str = ""

    def on_start(self):
        resp = self.client.post("/api/v1/auth/login", json={
            "email": "manager@store.com",
            "password": "Manager123!",
        }, catch_response=True)
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")

    @property
    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def sales_report(self):
        self.client.get("/api/v1/reports/sales?period=month", headers=self._auth, name="/reports/sales")

    @task(3)
    def forecast_demand(self):
        self.client.get("/api/v1/forecast/sales?horizon=7", headers=self._auth, name="/forecast/sales")

    @task(2)
    def supplier_performance(self):
        sid = random.randint(1, 10)
        self.client.get(f"/api/v1/suppliers/{sid}/performance", headers=self._auth, name="/suppliers/id/performance")

    @task(2)
    def inventory_analytics(self):
        self.client.get("/api/v1/inventory/analytics", headers=self._auth, name="/inventory/analytics")

    @task(1)
    def generate_gstr1(self):
        self.client.get("/api/v1/gst/gstr1?month=3&year=2026", headers=self._auth, name="/gst/gstr1")


# ------------------------------------------------------------------
# Event hooks for reporting
# ------------------------------------------------------------------

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n🚀 Load test started — Enterprise Retail Intelligence System")
    print("   Target: >100 RPS, p95 < 500ms\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print(f"\n📊 Load test complete:")
    print(f"   Total requests  : {stats.num_requests}")
    print(f"   Failure rate    : {stats.fail_ratio * 100:.1f}%")
    print(f"   Avg response    : {stats.avg_response_time:.0f}ms")
    print(f"   p95 latency     : {stats.get_response_time_percentile(0.95):.0f}ms")
    print(f"   RPS             : {stats.total_rps:.1f}\n")
