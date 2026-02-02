"""
R-DIOS Load Testing Script
Uses Locust for performance testing

Installation:
    pip install locust

Usage:
    locust -f scripts/load_test.py --host http://localhost:8000

Then open http://localhost:8089 in browser to configure and run tests.
"""

from locust import HttpUser, task, between
import random
import json


class RDIOSUser(HttpUser):
    """
    Simulates a typical R-DIOS user session.
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.session_id = f"loadtest_{random.randint(1000, 9999)}"
    
    # =========================================================================
    # Dashboard Endpoints (High Frequency)
    # =========================================================================
    
    @task(10)
    def get_dashboard_stats(self):
        """Most common request - dashboard KPIs"""
        self.client.get("/api/v1/dashboard/stats")
    
    @task(8)
    def get_sales_trend(self):
        """Sales trend chart data"""
        self.client.get("/api/v1/analytics/sales-trend?days=30")
    
    @task(5)
    def get_top_products(self):
        """Top products list"""
        self.client.get("/api/v1/analytics/top-products?limit=10")
    
    # =========================================================================
    # Forecasting Endpoints (Medium Frequency)
    # =========================================================================
    
    @task(3)
    def get_forecast(self):
        """Prophet forecast request"""
        self.client.post(
            "/prophet/predict",
            json={
                "history_days": 365,
                "forecast_days": 30,
                "growth_rate": 0
            }
        )
    
    @task(2)
    def get_forecast_metrics(self):
        """Forecast model metrics"""
        self.client.get("/api/v1/forecasts/metrics")
    
    # =========================================================================
    # Inventory Endpoints (Medium Frequency)
    # =========================================================================
    
    @task(4)
    def get_inventory_list(self):
        """Inventory list with pagination"""
        page = random.randint(1, 5)
        self.client.get(f"/api/v1/inventory?page={page}&limit=20")
    
    @task(2)
    def get_low_stock_alerts(self):
        """Low stock alerts"""
        self.client.get("/api/v1/inventory/low-stock")
    
    # =========================================================================
    # AI Assistant Endpoints (Lower Frequency - Expensive)
    # =========================================================================
    
    @task(1)
    def ai_assistant_query(self):
        """AI Assistant chat query"""
        queries = [
            "What were sales last week?",
            "Top 5 products by revenue",
            "Show me inventory status",
            "Compare this month to last month"
        ]
        
        self.client.post(
            "/api/v1/ai/chat",
            json={
                "message": {
                    "text": random.choice(queries),
                    "language": "english",
                    "script": "native"
                },
                "session_id": self.session_id
            }
        )
    
    @task(1)
    def get_ai_status(self):
        """AI service status check"""
        self.client.get("/api/v1/ai/status")
    
    # =========================================================================
    # Reports Endpoints (Low Frequency)
    # =========================================================================
    
    @task(1)
    def get_sales_report(self):
        """Generate sales report"""
        self.client.get("/api/v1/reports/sales?period=monthly")
    
    @task(1)
    def get_tax_summary(self):
        """Tax compliance summary"""
        self.client.get("/api/v1/tax/summary")


class HealthCheckUser(HttpUser):
    """
    Lightweight user that only checks health endpoints.
    Useful for baseline testing.
    """
    wait_time = between(0.5, 1)
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task
    def root_check(self):
        self.client.get("/")



class PetpoojaUser(HttpUser):
    """
    Simulates Petpooja POS and KDS users.
    Focuses on high-frequency polling and order management.
    """
    wait_time = between(5, 15)  # Polling is every 10-30s real world, we stress it more
    
    def on_start(self):
        self.order_ids = []

    @task(10)
    def poll_orders(self):
        """KDS Auto-refresh polling"""
        with self.client.get("/api/petpooja/orders/today", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "orders" in data and data["orders"]:
                    # Store some IDs for status updates
                    self.order_ids = [o["order_id"] for o in data["orders"]]

    @task(3)
    def check_analytics(self):
        """Dashboard polling"""
        self.client.get("/api/petpooja/analytics/daily-summary")

    @task(2)
    def create_order(self):
        """Simulate POS creating an order"""
        items = [
            {"category": "Main Course", "name": "Butter Chicken", "quantity": 1, "unit_price": 350.0, "amount": 350.0},
            {"category": "Breads", "name": "Butter Naan", "quantity": 2, "unit_price": 40.0, "amount": 80.0}
        ]
        response = self.client.post("/api/petpooja/orders/create", json={
            "order_type": random.choice(["Dine-in", "Takeaway", "Delivery"]),
            "table_number": random.randint(1, 10),
            "items": items
        })
        if response.status_code == 200:
            order_id = response.json().get("order", {}).get("order_id")
            if order_id:
                self.order_ids.append(order_id)

    @task(3)
    def update_kds_status(self):
        """Kitchen staff updating status"""
        if not self.order_ids:
            return
            
        order_id = random.choice(self.order_ids)
        status = random.choice(["Preparing", "Ready", "Completed"])
        
        self.client.put(f"/api/petpooja/orders/{order_id}/status", json={
            "status": status
        })

# ============================================================================
# Test Scenarios Configuration
# ============================================================================

"""
Recommended Test Scenarios:

1. SMOKE TEST (Quick validation)
   - Users: 5
   - Spawn rate: 1/sec
   - Duration: 1 minute
   
2. LOAD TEST (Normal traffic)
   - Users: 50
   - Spawn rate: 5/sec
   - Duration: 5 minutes
   
3. STRESS TEST (Peak traffic)
   - Users: 200
   - Spawn rate: 10/sec
   - Duration: 10 minutes
   
4. SPIKE TEST (Sudden surge)
   - Start with 20 users
   - Spike to 500 users
   - Return to 20 users
   
5. ENDURANCE TEST (Long-running)
   - Users: 30
   - Duration: 1 hour
   
Target Metrics:
- Response time p95 < 500ms
- Error rate < 1%
- Requests/sec > 100

Command examples:
    # Smoke test
    locust -f scripts/load_test.py --host http://localhost:8000 \\
           --users 5 --spawn-rate 1 --run-time 1m --headless
    
    # Load test
    locust -f scripts/load_test.py --host http://localhost:8000 \\
           --users 50 --spawn-rate 5 --run-time 5m --headless
    
    # Generate HTML report
    locust -f scripts/load_test.py --host http://localhost:8000 \\
           --users 50 --spawn-rate 5 --run-time 5m --headless \\
           --html=load_test_report.html
"""
