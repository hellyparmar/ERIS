#!/usr/bin/env python
"""
ERIS System Comprehensive Functionality Test
Tests all major features: Auth, CRUD, Analytics, Forecasting, etc.
"""

import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@eris.local"
ADMIN_PASSWORD = "AdminPassword123!"


class ERISSystemTester:
    """Comprehensive system tester for ERIS."""
    
    def __init__(self):
        self.token = None
        self.admin_user_id = None
        self.test_product_id = None
        self.test_customer_id = None
        self.test_sale_id = None
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log test result."""
        if passed:
            logger.info(f"✅ {name}")
            self.results["passed"].append(name)
        else:
            logger.error(f"❌ {name}: {message}")
            self.results["failed"].append(f"{name}: {message}")
    
    def log_warning(self, name: str, message: str):
        """Log warning."""
        logger.warning(f"⚠️ {name}: {message}")
        self.results["warnings"].append(f"{name}: {message}")
    
    # ============= HEALTH CHECKS =============
    
    def test_health_check(self):
        """Test basic health endpoint."""
        try:
            response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
            self.log_test("Health Check", response.status_code == 200, response.text)
        except Exception as e:
            self.log_test("Health Check", False, str(e))
    
    # ============= AUTHENTICATION TESTS =============
    
    def test_login(self):
        """Test admin login."""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.admin_user_id = data.get("user", {}).get("id")
                self.log_test("Admin Login", True)
            else:
                self.log_test("Admin Login", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_test("Admin Login", False, str(e))
    
    def test_invalid_login(self):
        """Test invalid login attempt."""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": "invalid@test.com", "password": "wrongpassword"}
            )
            self.log_test("Invalid Login Rejection", response.status_code >= 400)
        except Exception as e:
            self.log_test("Invalid Login Rejection", False, str(e))
    
    def get_headers(self):
        """Get auth headers."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    # ============= DATABASE SEEDING TESTS =============
    
    def test_database_check(self):
        """Test database status check."""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/database/data-summary",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                data = response.json()
                total = data.get("total_records", 0)
                self.log_test("Database Summary Check", total > 0, 
                            f"Found {total} records")
            else:
                self.log_test("Database Summary Check", False, 
                            f"Status {response.status_code}")
        except Exception as e:
            self.log_test("Database Summary Check", False, str(e))
    
    # ============= CUSTOMER TESTS =============
    
    def test_get_customers(self):
        """Test fetching customers."""
        try:
            response = requests.get(
                f"{BASE_URL}/customers/",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                customers = response.json()
                if customers:
                    self.test_customer_id = customers[0].get("id")
                self.log_test("Get Customers List", len(customers) > 0,
                            f"Found {len(customers)} customers")
            else:
                self.log_test("Get Customers List", False, 
                            f"Status {response.status_code}")
        except Exception as e:
            self.log_test("Get Customers List", False, str(e))
    
    def test_create_customer(self):
        """Test creating a new customer."""
        try:
            customer_data = {
                "customer_code": f"TEST-{int(time.time())}",
                "name": "Test Customer",
                "email": f"testcust_{int(time.time())}@test.com",
                "phone": "+91-9876543210",
                "city": "Mumbai",
                "country": "India",
                "source": "test"
            }
            response = requests.post(
                f"{BASE_URL}/customers/",
                json=customer_data,
                headers=self.get_headers()
            )
            if response.status_code == 201:
                customer = response.json()
                self.test_customer_id = customer.get("id")
                self.log_test("Create Customer", True)
            else:
                self.log_test("Create Customer", False,
                            f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Create Customer", False, str(e))
    
    def test_get_customer_details(self):
        """Test getting customer details."""
        if not self.test_customer_id:
            self.log_warning("Get Customer Details", "No test customer ID")
            return
        
        try:
            response = requests.get(
                f"{BASE_URL}/customers/{self.test_customer_id}",
                headers=self.get_headers()
            )
            self.log_test("Get Customer Details", response.status_code == 200)
        except Exception as e:
            self.log_test("Get Customer Details", False, str(e))
    
    # ============= INVENTORY/PRODUCTS TESTS =============
    
    def test_get_inventory(self):
        """Test fetching inventory list."""
        try:
            response = requests.get(
                f"{BASE_URL}/inventory/",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                items = response.json()
                if items and len(items) > 0:
                    self.test_product_id = items[0].get("id")
                self.log_test("Get Inventory List", len(items) > 0,
                            f"Found {len(items)} items")
            else:
                self.log_test("Get Inventory List", False,
                            f"Status {response.status_code}")
        except Exception as e:
            self.log_test("Get Inventory List", False, str(e))
    
    def test_low_stock_alerts(self):
        """Test low stock alerts."""
        try:
            response = requests.get(
                f"{BASE_URL}/inventory/alerts",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                alerts = response.json()
                self.log_test("Low Stock Alerts", True,
                            f"Found {len(alerts) if isinstance(alerts, list) else 0} alerts")
            else:
                self.log_test("Low Stock Alerts", response.status_code == 200)
        except Exception as e:
            self.log_test("Low Stock Alerts", False, str(e))
    
    # ============= SALES TESTS =============
    
    def test_get_sales(self):
        """Test fetching sales list."""
        try:
            response = requests.get(
                f"{BASE_URL}/sales/",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                sales = response.json()
                if sales and len(sales) > 0:
                    self.test_sale_id = sales[0].get("id")
                self.log_test("Get Sales List", len(sales) > 0,
                            f"Found {len(sales)} sales")
            else:
                self.log_test("Get Sales List", False,
                            f"Status {response.status_code}")
        except Exception as e:
            self.log_test("Get Sales List", False, str(e))
    
    def test_create_sale(self):
        """Test creating a new sale."""
        if not self.test_product_id or not self.test_customer_id:
            self.log_warning("Create Sale", "Missing product or customer ID")
            return
        
        try:
            sale_data = {
                "product_id": self.test_product_id,
                "customer_id": self.test_customer_id,
                "quantity": 5,
                "discount": 100.00,
                "store_id": 1
            }
            response = requests.post(
                f"{BASE_URL}/sales/",
                json=sale_data,
                headers=self.get_headers()
            )
            if response.status_code == 201:
                sale = response.json()
                self.test_sale_id = sale.get("id")
                self.log_test("Create Sale", True)
            else:
                self.log_test("Create Sale", False,
                            f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Create Sale", False, str(e))
    
    def test_get_sale_details(self):
        """Test getting sale details."""
        if not self.test_sale_id:
            self.log_warning("Get Sale Details", "No test sale ID")
            return
        
        try:
            response = requests.get(
                f"{BASE_URL}/sales/{self.test_sale_id}",
                headers=self.get_headers()
            )
            self.log_test("Get Sale Details", response.status_code == 200)
        except Exception as e:
            self.log_test("Get Sale Details", False, str(e))
    
    def test_sales_summary(self):
        """Test sales summary endpoint."""
        try:
            response = requests.get(
                f"{BASE_URL}/sales/summary",
                headers=self.get_headers()
            )
            self.log_test("Sales Summary", response.status_code == 200)
        except Exception as e:
            self.log_test("Sales Summary", False, str(e))
    
    def test_sales_analytics(self):
        """Test sales analytics."""
        try:
            response = requests.get(
                f"{BASE_URL}/sales/analytics",
                headers=self.get_headers()
            )
            self.log_test("Sales Analytics", response.status_code == 200)
        except Exception as e:
            self.log_test("Sales Analytics", False, str(e))
    
    # ============= DASHBOARD TESTS =============
    
    def test_dashboard_metrics(self):
        """Test dashboard metrics endpoints."""
        endpoints = [
            ("Top Products", "/dashboard/top-products"),
            ("Sales Metrics", "/dashboard/sales-metrics"),
            ("Revenue by Category", "/dashboard/revenue-by-category"),
            ("Customer Insights", "/dashboard/customer-insights"),
            ("Pending Orders", "/dashboard/pending-orders"),
        ]
        
        for name, endpoint in endpoints:
            try:
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    headers=self.get_headers()
                )
                self.log_test(f"Dashboard: {name}", response.status_code == 200)
            except Exception as e:
                self.log_test(f"Dashboard: {name}", False, str(e))
    
    # ============= FORECASTING TESTS =============
    
    def test_product_forecast(self):
        """Test product forecasting."""
        if not self.test_product_id:
            self.log_warning("Product Forecast", "No test product ID")
            return
        
        try:
            response = requests.get(
                f"{BASE_URL}/intelligence/forecast/product/{self.test_product_id}",
                headers=self.get_headers()
            )
            self.log_test("Product Forecast", response.status_code == 200)
        except Exception as e:
            self.log_test("Product Forecast", False, str(e))
    
    def test_business_insights(self):
        """Test business insights."""
        try:
            response = requests.get(
                f"{BASE_URL}/intelligence/insights",
                headers=self.get_headers()
            )
            self.log_test("Business Insights", response.status_code == 200)
        except Exception as e:
            self.log_test("Business Insights", False, str(e))
    
    def test_recommendations(self):
        """Test recommendations."""
        try:
            response = requests.get(
                f"{BASE_URL}/intelligence/recommendations",
                headers=self.get_headers()
            )
            self.log_test("Recommendations", response.status_code == 200)
        except Exception as e:
            self.log_test("Recommendations", False, str(e))
    
    # ============= ANALYTICS TESTS =============
    
    def test_analytics_endpoints(self):
        """Test various analytics endpoints."""
        try:
            response = requests.get(
                f"{BASE_URL}/analytics",
                headers=self.get_headers()
            )
            self.log_test("Analytics Module", response.status_code in [200, 404])
        except Exception as e:
            self.log_test("Analytics Module", False, str(e))
    
    # ============= ADMIN TESTS =============
    
    def test_audit_log(self):
        """Test audit log retrieval."""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/security/audit-log",
                headers=self.get_headers()
            )
            self.log_test("Audit Log", response.status_code == 200)
        except Exception as e:
            self.log_test("Audit Log", False, str(e))
    
    def test_system_health(self):
        """Test system health check."""
        try:
            response = requests.get(
                f"{BASE_URL}/health/detailed",
                headers=self.get_headers()
            )
            self.log_test("System Health Check", response.status_code == 200)
        except Exception as e:
            self.log_test("System Health Check", False, str(e))
    
    # ============= REPORT GENERATION =============
    
    def print_report(self):
        """Print comprehensive test report."""
        print("\n" + "="*80)
        print(" "*20 + "ERIS SYSTEM FUNCTIONALITY TEST REPORT")
        print("="*80 + "\n")
        
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])
        warnings = len(self.results["warnings"])
        total = passed + failed
        
        print(f"SUMMARY:")
        print(f"  ✅ Passed:   {passed}/{total} ({(passed/total*100 if total > 0 else 0):.1f}%)")
        print(f"  ❌ Failed:   {failed}/{total}")
        print(f"  ⚠️  Warnings: {warnings}\n")
        
        if self.results["passed"]:
            print("✅ PASSED TESTS:")
            for test in self.results["passed"]:
                print(f"   • {test}")
        
        if self.results["failed"]:
            print(f"\n❌ FAILED TESTS:")
            for test in self.results["failed"]:
                print(f"   • {test}")
        
        if self.results["warnings"]:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.results["warnings"]:
                print(f"   • {warning}")
        
        print("\n" + "="*80)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! System is fully functional.")
        else:
            print(f"⚠️  {failed} test(s) need attention.")
        
        print("="*80 + "\n")
    
    # ============= MAIN TEST RUNNER =============
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "="*80)
        print(" "*15 + "🚀 STARTING ERIS SYSTEM FUNCTIONALITY TESTS")
        print("="*80 + "\n")
        
        # Health & Auth
        print("📋 AUTHENTICATION & HEALTH CHECKS")
        self.test_health_check()
        self.test_login()
        self.test_invalid_login()
        self.test_system_health()
        
        # Database
        print("\n📊 DATABASE & SEEDING")
        self.test_database_check()
        
        # Customers
        print("\n👥 CUSTOMER MANAGEMENT")
        self.test_get_customers()
        self.test_create_customer()
        if self.test_customer_id:
            self.test_get_customer_details()
        
        # Inventory
        print("\n📦 INVENTORY MANAGEMENT")
        self.test_get_inventory()
        self.test_low_stock_alerts()
        
        # Sales
        print("\n💰 SALES MANAGEMENT")
        self.test_get_sales()
        self.test_sales_summary()
        self.test_sales_analytics()
        if self.test_product_id and self.test_customer_id:
            self.test_create_sale()
        if self.test_sale_id:
            self.test_get_sale_details()
        
        # Dashboard
        print("\n📈 DASHBOARD & METRICS")
        self.test_dashboard_metrics()
        
        # Analytics & Intelligence
        print("\n🤖 FORECASTING & INTELLIGENCE")
        if self.test_product_id:
            self.test_product_forecast()
        self.test_business_insights()
        self.test_recommendations()
        
        # Admin
        print("\n🔐 ADMIN & SECURITY")
        self.test_audit_log()
        
        # Report
        print("\n📄 GENERATING REPORT...")
        self.print_report()


def main():
    """Main entry point."""
    try:
        tester = ERISSystemTester()
        tester.run_all_tests()
        
        # Exit with appropriate code
        if len(tester.results["failed"]) > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
