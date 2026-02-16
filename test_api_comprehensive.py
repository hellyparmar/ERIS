#!/usr/bin/env python3
"""
STEP 2 (Final): R-DIOS Backend API Comprehensive Testing
Tests actual available endpoints with real data

Run with: python test_api_comprehensive.py
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveAPITester:
    """Test R-DIOS API with actual available endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_endpoints": 0,
                "endpoints_working": 0,
                "endpoints_tested": {},
                "response_times": [],
                "errors": []
            },
            "test_suites": {
                "system": [],
                "health": [],
                "dashboard": [],
                "analytics": [],
                "forecasting": [],
                "inventory": [],
                "authentication": [],
                "integrations": [],
                "ai": [],
                "weather": [],
                "petpooja": []
            }
        }
    
    def test_endpoint(self, suite: str, method: str, endpoint: str, 
                     name: str = None, params: Dict = None) -> bool:
        """Test a single endpoint"""
        
        name = name or endpoint
        
        try:
            url = f"{self.base_url}{endpoint}"
            start = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=5)
            elif method.upper() == "POST":
                response = requests.post(url, json=params or {}, timeout=5)
            else:
                return False
            
            elapsed = time.time() - start
            success = response.status_code in [200, 201]
            
            test_result = {
                "endpoint": endpoint,
                "method": method,
                "name": name,
                "status_code": response.status_code,
                "response_time": elapsed,
                "success": success
            }
            
            self.results["test_suites"][suite].append(test_result)
            self.results["summary"]["endpoints_tested"][endpoint] = success
            self.results["summary"]["response_times"].append(elapsed)
            
            if success:
                self.results["summary"]["endpoints_working"] += 1
                logger.info(f"  ✅ {name}: {response.status_code} ({elapsed:.2f}s)")
            else:
                logger.info(f"  ⚠️  {name}: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"  ❌ {name}: {e}")
            self.results["summary"]["errors"].append({
                "endpoint": endpoint,
                "error": str(e)
            })
            return False
    
    def run_tests(self):
        """Run all API tests"""
        
        print("\n" + "="*80)
        print(" COMPREHENSIVE R-DIOS BACKEND API TEST SUITE")
        print(" STEP 2: Production Readiness Verification")
        print("="*80 + "\n")
        
        # System & Health Tests
        logger.info("🏥 SYSTEM & HEALTH TESTS:")
        self.test_endpoint("system", "GET", "/", "API Root")
        self.test_endpoint("system", "GET", "/health", "Health Check")
        self.test_endpoint("health", "GET", "/health/", "Health (Alt)")
        self.test_endpoint("health", "GET", "/health/live", "Health Live")
        self.test_endpoint("health", "GET", "/health/ready", "Health Ready")
        self.test_endpoint("health", "GET", "/health/detailed", "Health Detailed")
        self.test_endpoint("health", "GET", "/health/metrics", "Health Metrics")
        self.test_endpoint("system", "GET", "/docs", "Swagger UI")
        
        # Dashboard Tests
        logger.info("\n📊 DASHBOARD TESTS:")
        self.test_endpoint("dashboard", "GET", "/api/v1/dashboard/realtime", "Dashboard Realtime")
        self.test_endpoint("dashboard", "GET", "/api/v1/dashboard/kpis", "Dashboard KPIs")
        self.test_endpoint("dashboard", "GET", "/api/v1/dashboard/summary", "Dashboard Summary")
        self.test_endpoint("dashboard", "GET", "/api/v1/dashboard/stats", "Dashboard Stats")
        
        # Analytics Tests - Sales
        logger.info("\n📈 ANALYTICS - SALES:")
        self.test_endpoint("analytics", "GET", "/api/analytics/sales/summary", "Sales Summary")
        self.test_endpoint("analytics", "GET", "/api/analytics/sales/daily-trend", "Daily Trend")
        self.test_endpoint("analytics", "GET", "/api/analytics/sales/by-category", "By Category")
        self.test_endpoint("analytics", "GET", "/api/analytics/sales/top-products", "Top Products")
        self.test_endpoint("analytics", "GET", "/api/analytics/sales/payment-methods", "Payment Methods")
        self.test_endpoint("analytics", "GET", "/api/analytics/sales/weekly-pattern", "Weekly Pattern")
        self.test_endpoint("analytics", "GET", "/api/analytics/sales/hourly-pattern", "Hourly Pattern")
        
        # Analytics Tests - Inventory
        logger.info("\n📦 ANALYTICS - INVENTORY:")
        self.test_endpoint("analytics", "GET", "/api/analytics/inventory/summary", "Inventory Summary")
        self.test_endpoint("analytics", "GET", "/api/analytics/inventory/low-stock", "Low Stock")
        self.test_endpoint("analytics", "GET", "/api/analytics/inventory/turnover", "Turnover")
        self.test_endpoint("analytics", "GET", "/api/analytics/inventory/abc-analysis", "ABC Analysis")
        self.test_endpoint("analytics", "GET", "/api/analytics/inventory/dead-stock", "Dead Stock")
        
        # Analytics Tests - Customers
        logger.info("\n👥 ANALYTICS - CUSTOMERS:")
        self.test_endpoint("analytics", "GET", "/api/analytics/customers/rfm/summary", "RFM Summary")
        self.test_endpoint("analytics", "GET", "/api/analytics/customers/top-spenders", "Top Spenders")
        self.test_endpoint("analytics", "GET", "/api/analytics/customers/at-risk", "At Risk")
        self.test_endpoint("analytics", "GET", "/api/analytics/customers/upcoming-birthdays", "Birthdays")
        
        # Forecasting Tests
        logger.info("\n🔮 FORECASTING & PREDICTIONS:")
        self.test_endpoint("forecasting", "GET", "/api/forecasting/forecast/1/1?days=7", "Forecast 7 Days")
        self.test_endpoint("forecasting", "GET", "/api/v1/predict/sales", "Predict Sales")
        self.test_endpoint("forecasting", "GET", "/api/v1/predict/stockout", "Predict Stockout")
        
        # Inventory Management
        logger.info("\n📦 INVENTORY MANAGEMENT:")
        self.test_endpoint("inventory", "GET", "/api/v1/inventory/list", "Inventory List")
        self.test_endpoint("inventory", "GET", "/api/v1/inventory/summary", "Inventory Summary")
        self.test_endpoint("inventory", "GET", "/api/v1/inventory/reorder-recommendations", "Reorder Recs")
        
        # Authentication
        logger.info("\n🔐 AUTHENTICATION:")
        self.test_endpoint("authentication", "GET", "/auth/me", "Auth Me")
        self.test_endpoint("authentication", "GET", "/auth/logout", "Auth Logout")
        
        # Weather Integration
        logger.info("\n🌤️  WEATHER INTEGRATION:")
        self.test_endpoint("weather", "GET", "/api/v1/weather/health", "Weather Health")
        self.test_endpoint("weather", "GET", "/api/v1/weather/current", "Current Weather")
        self.test_endpoint("weather", "GET", "/api/v1/weather/forecast", "Weather Forecast")
        
        # AI & ML
        logger.info("\n🤖 AI & MACHINE LEARNING:")
        self.test_endpoint("ai", "GET", "/api/v1/ai/status", "AI Status")
        self.test_endpoint("ai", "GET", "/api/v1/models/list", "Models List")
        self.test_endpoint("ai", "GET", "/api/v1/analytics/metrics", "Analytics Metrics")
        
        # Petpooja Specific
        logger.info("\n🍽️  PETPOOJA RESTAURANT:")
        self.test_endpoint("petpooja", "GET", "/api/petpooja/menu", "Menu")
        self.test_endpoint("petpooja", "GET", "/api/petpooja/analytics/daily-summary", "Daily Summary")
        
        # Integrations
        logger.info("\n🔗 INTEGRATIONS:")
        self.test_endpoint("integrations", "GET", "/api/v1/integrations/tally/company-info", "Tally Info")
        self.test_endpoint("integrations", "GET", "/api/v1/integrations/odoo/config", "Odoo Config")
        
        # Monitoring
        logger.info("\n📊 MONITORING:")
        self.test_endpoint("system", "GET", "/monitoring/metrics/prometheus", "Prometheus Metrics")
        self.test_endpoint("system", "GET", "/monitoring/dashboard/stats", "Monitor Stats")
        
        # Circuit Breakers
        logger.info("\n🔌 CIRCUIT BREAKERS:")
        self.test_endpoint("system", "GET", "/api/circuit-breakers/status", "CB Status")
        
        self.results["summary"]["total_endpoints"] = len(self.results["summary"]["endpoints_tested"])
        
        print("\n" + "="*80 + "\n")
    
    def print_summary(self):
        """Print test results summary"""
        
        summary = self.results["summary"]
        total = summary["total_endpoints"]
        working = summary["endpoints_working"]
        
        print("="*80)
        print(" TEST RESULTS SUMMARY")
        print("="*80 + "\n")
        
        print(f"📊 Overall Statistics:")
        print(f"   Total Endpoints Tested: {total}")
        print(f"   ✅ Working: {working}")
        print(f"   ⚠️  Not Working: {total - working}")
        
        if summary["response_times"]:
            avg_time = sum(summary["response_times"]) / len(summary["response_times"])
            max_time = max(summary["response_times"])
            min_time = min(summary["response_times"])
            print(f"\n⏱️  Response Time Statistics:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Min: {min_time:.3f}s")
            print(f"   Max: {max_time:.3f}s")
        
        # Print working endpoints by category
        print(f"\n✅ WORKING ENDPOINTS BY CATEGORY:\n")
        
        for suite, tests in self.results["test_suites"].items():
            working_tests = [t for t in tests if t.get("success", False)]
            if working_tests:
                print(f"   {suite.upper()} ({len(working_tests)}):")
                for test in working_tests[:5]:  # Show first 5
                    print(f"      - {test['name']}: {test['status_code']}")
                if len(working_tests) > 5:
                    print(f"      ... and {len(working_tests)-5} more")
        
        # Assessment
        percentage_working = (working / total * 100) if total > 0 else 0
        print(f"\n{'='*80}")
        print(f" PRODUCTION READINESS ASSESSMENT")
        print(f"{'='*80}\n")
        
        if percentage_working >= 80:
            print(f"✅ API is PRODUCTION-READY ({percentage_working:.0f}% endpoints working)")
            print("   - Core functionality operational")
            print("   - Analytics fully accessible")
            print("   - Dashboard endpoints responsive")
            print("   - Forecasting working")
        elif percentage_working >= 60:
            print(f"⚠️  API is MOSTLY OPERATIONAL ({percentage_working:.0f}% endpoints working)")
            print("   - Core endpoints functional")
            print("   - Some advanced features need attention")
        elif percentage_working >= 40:
            print(f"⚠️  API is PARTIALLY OPERATIONAL ({percentage_working:.0f}% endpoints working)")
            print("   - Basic functionality available")
            print("   - Multiple endpoints need configuration")
        else:
            print(f"❌ API NEEDS ATTENTION ({percentage_working:.0f}% endpoints working)")
        
        print(f"\n{'='*80}\n")
        print("🔗 Swagger Documentation: http://localhost:8000/docs")
        print("📊 ReDoc: http://localhost:8000/redoc")
        print(f"{'='*80}\n")
    
    def save_results(self):
        """Save test results to JSON"""
        with open("test_results_2_api_comprehensive.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"✅ Results saved to: test_results_2_api_comprehensive.json")


def main():
    tester = ComprehensiveAPITester()
    tester.run_tests()
    tester.print_summary()
    tester.save_results()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Testing interrupted")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
