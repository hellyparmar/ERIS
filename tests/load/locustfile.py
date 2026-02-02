"""
Locust Load Testing Configuration
Test R-DIOS API under load (100-1000 concurrent users)
"""

from locust import HttpUser, task, between, events
import json
import random
from datetime import datetime

class RDIOSUser(HttpUser):
    """Simulates a typical R-DIOS user"""
    
    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get auth token"""
        # Register and login
        username = f"loadtest_user_{random.randint(1, 100000)}"
        
        # Try to register (may fail if user exists)
        self.client.post(
            "/auth/register",
            json={
                "username": username,
                "email": f"{username}@loadtest.com",
                "password": "LoadTest123!"
            }
        )
        
        # Login
        response = self.client.post(
            "/auth/login",
            data={"username": username, "password": "LoadTest123!"}
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Use without auth for public endpoints
            self.token = None
            self.headers = {}
    
    # ==================== PUBLIC ENDPOINTS (No Auth) ====================
    
    @task(10)
    def check_health(self):
        """Check health endpoint - high frequency"""
        self.client.get("/health")
    
    @task(5)
    def check_ready(self):
        """Check readiness endpoint"""
        self.client.get("/ready")
    
    @task(3)
    def get_metrics(self):
        """Get Prometheus metrics"""
        self.client.get("/monitoring/metrics/prometheus")
    
    # ==================== ANALYTICS ENDPOINTS ====================
    
    @task(8)
    def get_analytics_overview(self):
        """Get analytics dashboard data"""
        self.client.get("/api/v1/analytics/overview", headers=self.headers)
    
    @task(5)
    def get_sales_trends(self):
        """Get sales trends"""
        self.client.get("/api/v1/analytics/trends?period=30", headers=self.headers)
    
    @task(3)
    def get_inventory_alerts(self):
        """Get inventory alerts"""
        self.client.get("/inventory/alerts", headers=self.headers)
    
    # ==================== INVOICE ENDPOINTS ====================
    
    @task(6)
    def get_invoice_stats(self):
        """Get invoice statistics"""
        self.client.get("/api/invoices/stats/summary", headers=self.headers)
    
    @task(4)
    def get_overdue_invoices(self):
        """Get overdue invoices"""
        self.client.get("/api/invoices/overdue", headers=self.headers)
    
    @task(2)
    def create_invoice(self):
        """Create new invoice (write operation)"""
        if self.token:
            self.client.post(
                "/api/invoices/create",
                json={
                    "sale_id": random.randint(1, 10000),
                    "payment_terms_days": 30,
                    "send_whatsapp_receipt": False
                },
                headers=self.headers
            )
    
    # ==================== MESSAGE ENDPOINTS ====================
    
    @task(4)
    def get_unread_count(self):
        """Get unread message count"""
        self.client.get(
            "/api/messages/unread-count?user_type=staff&user_id=1",
            headers=self.headers
        )
    
    @task(3)
    def search_messages(self):
        """Search messages"""
        search_terms = ["invoice", "payment", "order", "urgent", "reminder"]
        self.client.get(
            f"/api/messages/search?user_type=staff&user_id=1&q={random.choice(search_terms)}",
            headers=self.headers
        )
    
    # ==================== COMMUNITY ENDPOINTS ====================
    
    @task(4)
    def browse_listings(self):
        """Browse stock swap listings"""
        self.client.get("/api/community/listings", headers=self.headers)
    
    @task(3)
    def browse_bulk_buy(self):
        """Browse bulk buy groups"""
        self.client.get("/api/community/bulk-buy", headers=self.headers)
    
    @task(2)
    def get_marketplace_stats(self):
        """Get marketplace statistics"""
        self.client.get("/api/community/stats", headers=self.headers)
    
    # ==================== CIRCUIT BREAKER CHECK ====================
    
    @task(1)
    def check_circuit_status(self):
        """Check circuit breaker status"""
        self.client.get("/api/circuit-breakers/status", headers=self.headers)


class AdminUser(HttpUser):
    """Simulates admin operations (lower frequency)"""
    
    wait_time = between(5, 10)
    weight = 1  # Lower weight = fewer admin users
    
    def on_start(self):
        """Login as admin"""
        # Login as admin
        response = self.client.post(
            "/auth/login",
            data={"username": "admin", "password": "AdminPass123!"}
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(3)
    def mark_overdue(self):
        """Admin: Mark invoices as overdue"""
        if self.headers:
            self.client.post("/api/invoices/mark-overdue", headers=self.headers)
    
    @task(2)
    def get_dashboard_stats(self):
        """Admin: Get monitoring dashboard"""
        self.client.get("/monitoring/dashboard/stats", headers=self.headers)
    
    @task(1)
    def check_circuit_health(self):
        """Admin: Check system resilience"""
        self.client.get("/api/circuit-breakers/health", headers=self.headers)


class HeavyUser(HttpUser):
    """Simulates power users with intensive operations"""
    
    wait_time = between(0.5, 1)
    weight = 1  # Few heavy users
    
    def on_start(self):
        """Login"""
        username = f"heavy_user_{random.randint(1, 1000)}"
        self.client.post(
            "/auth/register",
            json={
                "username": username,
                "email": f"{username}@loadtest.com",
                "password": "HeavyUser123!"
            }
        )
        
        response = self.client.post(
            "/auth/login",
            data={"username": username, "password": "HeavyUser123!"}
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(10)
    def rapid_health_check(self):
        """Rapid health checks (stress test)"""
        self.client.get("/health")
    
    @task(5)
    def bulk_invoice_lookup(self):
        """Lookup multiple invoices rapidly"""
        for i in range(5):
            self.client.get(f"/api/invoices/{random.randint(1, 1000)}/summary", headers=self.headers)


# ==================== EVENT HOOKS ====================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║       R-DIOS Load Testing Starting                ║
    ║                                                   ║
    ║   Target: 1000 concurrent users                   ║
    ║   Duration: 10 minutes                            ║
    ║   Ramp-up: 100 users/second                       ║
    ╚═══════════════════════════════════════════════════╝
    """)

@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """Called when load test ends"""
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║       Load Testing Complete!                      ║
    ║                                                   ║
    ║   Check the Locust web UI for detailed stats      ║
    ║   http://localhost:8089                           ║
    ╚═══════════════════════════════════════════════════╝
    """)
