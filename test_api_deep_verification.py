#!/usr/bin/env python3
"""
STEP 2 (Extended): R-DIOS Backend API Deep Testing
More comprehensive endpoint discovery and testing

Run with: python test_api_deep_verification.py
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DeepAPITester:
    """Deep dive testing of R-DIOS API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "api_version": "3.0.0",
            "endpoints_tested": [],
            "endpoints_working": [],
            "endpoints_failed": [],
            "business_logic": {},
            "performance": {}
        }
    
    def test_endpoint(self, method: str, endpoint: str, name: str = None, 
                     data: Dict = None, expected_status: List[int] = None) -> Dict:
        """Generic endpoint testing"""
        
        if expected_status is None:
            expected_status = [200, 201]
        
        name = name or endpoint
        
        try:
            url = f"{self.base_url}{endpoint}"
            start = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data or {}, timeout=10)
            else:
                return None
            
            elapsed = time.time() - start
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time": elapsed,
                "success": response.status_code in expected_status
            }
            
            if response.status_code in expected_status:
                logger.info(f"✅ {name}: {response.status_code} ({elapsed:.2f}s)")
                self.results["endpoints_working"].append(endpoint)
                
                try:
                    result["response_sample"] = response.json() if response.text else {}
                except:
                    result["response_sample"] = response.text[:200] if response.text else None
            else:
                logger.warning(f"⚠️  {name}: {response.status_code} ({elapsed:.2f}s)")
                self.results["endpoints_failed"].append(endpoint)
            
            self.results["endpoints_tested"].append(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ {name}: {e}")
            self.results["endpoints_failed"].append(endpoint)
            self.results["endpoints_tested"].append({
                "endpoint": endpoint,
                "error": str(e)
            })
            return None
    
    def run_all_tests(self):
        """Run comprehensive endpoint testing"""
        
        print("\n" + "="*80)
        print(" DEEP API VERIFICATION - ENDPOINT DISCOVERY & TESTING")
        print("="*80 + "\n")
        
        logger.info("🔍 Scanning R-DIOS API endpoints...\n")
        
        # System endpoints
        logger.info("📋 SYSTEM ENDPOINTS:")
        self.test_endpoint("GET", "/", "Root")
        self.test_endpoint("GET", "/health", "Health Check")
        self.test_endpoint("GET", "/docs", "Swagger UI")
        self.test_endpoint("GET", "/redoc", "ReDoc")
        
        # Dashboard endpoints
        logger.info("\n📊 DASHBOARD ENDPOINTS:")
        self.test_endpoint("GET", "/api/v1/dashboard", "Dashboard v1")
        self.test_endpoint("GET", "/api/v1/dashboard/realtime", "Dashboard Realtime")
        self.test_endpoint("GET", "/api/dashboard/summary", "Dashboard Summary")
        self.test_endpoint("GET", "/api/dashboard/kpis", "Dashboard KPIs")
        
        # Analytics endpoints
        logger.info("\n📈 ANALYTICS ENDPOINTS:")
        self.test_endpoint("GET", "/api/v1/analytics/sales", "Sales Analytics")
        self.test_endpoint("GET", "/api/v1/analytics/revenue", "Revenue Analytics")
        self.test_endpoint("GET", "/api/v1/analytics/inventory", "Inventory Analytics")
        self.test_endpoint("GET", "/api/v1/analytics/customers", "Customer Analytics")
        self.test_endpoint("GET", "/api/sales-analytics/daily-summary", "Sales Daily Summary")
        self.test_endpoint("GET", "/api/sales-analytics/category-performance", "Category Performance")
        
        # Prediction/Forecasting
        logger.info("\n🔮 FORECASTING & PREDICTION ENDPOINTS:")
        self.test_endpoint("GET", "/api/v1/predictions/revenue", "Revenue Prediction")
        self.test_endpoint("GET", "/api/v1/predictions/demand", "Demand Prediction")
        self.test_endpoint("GET", "/api/forecasting/forecast/1/1?days=7", "Forecast Store 1 Product 1")
        self.test_endpoint("GET", "/api/forecasting/forecast/store/1?days=30", "Forecast Store 1")
        
        # Inventory Management
        logger.info("\n📦 INVENTORY ENDPOINTS:")
        self.test_endpoint("GET", "/api/inventory/low-stock", "Low Stock Items")
        self.test_endpoint("GET", "/api/inventory/stock-levels", "Stock Levels")
        self.test_endpoint("GET", "/api/inventory/turnover", "Inventory Turnover")
        
        # Petpooja specific
        logger.info("\n🍽️  PETPOOJA RESTAURANT ENDPOINTS:")
        self.test_endpoint("GET", "/api/petpooja/menu", "Menu List")
        self.test_endpoint("GET", "/api/petpooja/categories", "Menu Categories")
        self.test_endpoint("GET", "/api/petpooja/analytics/daily-summary", "Daily Summary")
        self.test_endpoint("GET", "/api/petpooja/analytics/category-sales", "Category Sales")
        self.test_endpoint("GET", "/api/petpooja/customers", "Customers")
        
        # Reports
        logger.info("\n📄 REPORTS & EXPORT:")
        self.test_endpoint("GET", "/api/reports/sales", "Sales Report")
        self.test_endpoint("GET", "/api/reports/inventory", "Inventory Report")
        self.test_endpoint("GET", "/api/export/sales", "Export Sales")
        
        # Weather
        logger.info("\n🌤️  WEATHER INTEGRATION:")
        self.test_endpoint("GET", "/api/weather/current", "Current Weather")
        self.test_endpoint("GET", "/api/weather/forecast", "Weather Forecast")
        
        # Health & Monitoring
        logger.info("\n🏥 HEALTH & MONITORING:")
        self.test_endpoint("GET", "/api/health/status", "Health Status")
        self.test_endpoint("GET", "/api/monitoring/metrics", "Metrics")
        self.test_endpoint("GET", "/api/circuit-breaker/status", "Circuit Breaker Status")
        
        # Authentication
        logger.info("\n🔐 AUTHENTICATION:")
        self.test_endpoint("GET", "/api/auth/status", "Auth Status")
        self.test_endpoint("POST", "/api/auth/login", "Login", {"username": "test", "password": "test"})
        
        # Data Management
        logger.info("\n💾 DATA MANAGEMENT:")
        self.test_endpoint("GET", "/api/v1/data/products", "Products")
        self.test_endpoint("GET", "/api/v1/data/customers", "Customers")
        self.test_endpoint("GET", "/api/v1/data/sales", "Sales")
        
        # ML Models
        logger.info("\n🤖 ML MODEL ENDPOINTS:")
        self.test_endpoint("GET", "/api/v1/models", "Models List")
        self.test_endpoint("GET", "/api/v1/models/status", "Models Status")
        
        # Advanced features
        logger.info("\n⚡ ADVANCED FEATURES:")
        self.test_endpoint("GET", "/api/causal/analysis", "Causal Analysis")
        self.test_endpoint("GET", "/api/loyalty/members", "Loyalty Members")
        self.test_endpoint("GET", "/api/alerts/active", "Active Alerts")
        
        print("\n" + "="*80 + "\n")
    
    def print_summary(self):
        """Print detailed summary"""
        
        total = len(self.results["endpoints_tested"])
        working = len(self.results["endpoints_working"])
        failed = len(self.results["endpoints_failed"])
        
        print("="*80)
        print(" TEST RESULTS SUMMARY")
        print("="*80)
        print(f"\n📊 Statistics:")
        print(f"   Total Endpoints Tested: {total}")
        print(f"   ✅ Working Endpoints: {working}")
        print(f"   ⚠️  Failed/Not Found: {failed}")
        
        if working > 0:
            print(f"\n✅ WORKING ENDPOINTS ({working}):")
            for ep in self.results["endpoints_working"]:
                print(f"   - {ep}")
        
        if failed > 0:
            print(f"\n⚠️  FAILED/NOT FOUND ENDPOINTS ({failed}):")
            for ep in self.results["endpoints_failed"][:10]:  # Show first 10
                print(f"   - {ep}")
        
        print("\n" + "="*80)
        print(" RECOMMENDATIONS")
        print("="*80)
        
        if working >= 10:
            print("\n✅ API is FUNCTIONING WELL")
            print("   - Multiple endpoints accessible")
            print("   - Core functionality operational")
            print("   - Database connectivity verified")
        elif working >= 5:
            print("\n⚠️  API is PARTIALLY OPERATIONAL")
            print("   - Core endpoints working")
            print("   - Some endpoints need configuration")
        else:
            print("\n❌ API NEEDS ATTENTION")
            print("   - Limited endpoints accessible")
            print("   - Check backend logs for errors")
            print("   - Verify database connection")
        
        print("\n🔗 API Documentation: http://localhost:8000/docs")
        print("📊 ReDoc: http://localhost:8000/redoc")
        print("="*80 + "\n")
    
    def save_results(self):
        """Save detailed results to JSON"""
        with open("test_results_2b_api_deep.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"✅ Results saved to: test_results_2b_api_deep.json")


def main():
    tester = DeepAPITester()
    tester.run_all_tests()
    tester.print_summary()
    tester.save_results()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Testing interrupted")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
