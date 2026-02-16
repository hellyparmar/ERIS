#!/usr/bin/env python3
"""
STEP 2.5 + STEP 3: Integrated Authentication & Frontend Verification
Tests the full stack: Auth, API, and Frontend integration

Run with: python test_integrated_stack.py
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegratedStackTester:
    """Test complete R-DIOS stack: Auth -> API -> Frontend"""
    
    def __init__(self, api_url: str = "http://localhost:8000", 
                 frontend_url: str = "http://localhost:5173"):
        self.api_url = api_url
        self.frontend_url = frontend_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "api_url": api_url,
            "frontend_url": frontend_url,
            "authentication": {},
            "api_integration": {},
            "frontend_status": {},
            "summary": {}
        }
    
    def test_api_health(self) -> bool:
        """Test API health status"""
        logger.info("\n🏥 Testing API Health...")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("  ✅ API is healthy")
                self.results["api_integration"]["health"] = "online"
                return True
            else:
                logger.error(f"  ❌ API returned {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"  ❌ API unreachable: {e}")
            return False
    
    def test_authentication_system(self) -> bool:
        """Test authentication system status"""
        logger.info("\n🔐 Testing Authentication System...")
        
        try:
            response = requests.get(f"{self.api_url}/auth/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  ✅ Auth service is {data.get('status')}")
                logger.info(f"  ℹ️  Test credentials: {data.get('test_credentials')}")
                self.results["authentication"]["status"] = "active"
                self.results["authentication"]["service"] = data.get("service")
                return True
            else:
                logger.error(f"  ❌ Auth status check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"  ❌ Auth check failed: {e}")
            return False
    
    def test_core_endpoints(self) -> Dict[str, Any]:
        """Test core API endpoints (no auth required)"""
        logger.info("\n📊 Testing Core API Endpoints...")
        
        endpoints = {
            "dashboard": ("/api/v1/dashboard/realtime", "Dashboard Data"),
            "inventory": ("/api/v1/inventory/list", "Inventory List"),
            "forecast": ("/api/forecasting/forecast/1/1?days=7", "Sales Forecast"),
            "menu": ("/api/petpooja/menu", "Restaurant Menu"),
            "ai_status": ("/api/v1/ai/status", "AI System Status")
        }
        
        results = {}
        for key, (endpoint, name) in endpoints.items():
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    logger.info(f"  ✅ {name}: {response.status_code}")
                    results[key] = "working"
                else:
                    logger.warning(f"  ⚠️  {name}: {response.status_code}")
                    results[key] = f"status_{response.status_code}"
            except Exception as e:
                logger.error(f"  ❌ {name}: {e}")
                results[key] = "error"
        
        return results
    
    def test_frontend_connectivity(self) -> bool:
        """Test frontend server"""
        logger.info("\n🖥️  Testing Frontend Connectivity...")
        
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"  ✅ Frontend running at {self.frontend_url}")
                self.results["frontend_status"]["connectivity"] = "online"
                return True
            else:
                logger.warning(f"  ⚠️  Frontend returned {response.status_code}")
                return False
        except requests.ConnectionError:
            logger.warning(f"  ⚠️  Frontend not running at {self.frontend_url}")
            logger.info("     To start: npm run dev")
            self.results["frontend_status"]["connectivity"] = "offline"
            return False
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            return False
    
    def test_cors_configuration(self) -> bool:
        """Test CORS is properly configured"""
        logger.info("\n🔗 Testing CORS Configuration...")
        
        try:
            headers = {"Origin": self.frontend_url}
            response = requests.options(f"{self.api_url}/api", headers=headers, timeout=5)
            
            if "access-control-allow-origin" in response.headers:
                allowed_origin = response.headers.get("access-control-allow-origin")
                logger.info(f"  ✅ CORS enabled for: {allowed_origin}")
                self.results["api_integration"]["cors"] = "configured"
                return True
            else:
                logger.warning("  ⚠️  CORS headers not found")
                self.results["api_integration"]["cors"] = "not_configured"
                return False
        except Exception as e:
            logger.error(f"  ❌ CORS test failed: {e}")
            return False
    
    def test_api_response_times(self) -> Dict[str, float]:
        """Measure API response times"""
        logger.info("\n⚡ Testing API Response Times...")
        
        endpoints = {
            "dashboard": "/api/v1/dashboard/realtime",
            "inventory": "/api/v1/inventory/list",
            "forecast": "/api/forecasting/forecast/1/1?days=7"
        }
        
        timings = {}
        for name, endpoint in endpoints.items():
            try:
                start = time.time()
                response = requests.get(f"{self.api_url}{endpoint}", timeout=5)
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    logger.info(f"  ⚡ {name}: {elapsed:.0f}ms")
                    timings[name] = elapsed
            except Exception as e:
                logger.error(f"  ❌ {name}: {e}")
                timings[name] = -1
        
        return timings
    
    def test_data_integration(self) -> Dict[str, Any]:
        """Test data flow from API to frontend"""
        logger.info("\n📊 Testing Data Integration...")
        
        integration_results = {}
        
        # Test dashboard data
        try:
            response = requests.get(f"{self.api_url}/api/v1/dashboard/realtime", timeout=5)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["today_revenue", "total_revenue", "active_orders", "top_products"]
                if all(field in data for field in required_fields):
                    logger.info("  ✅ Dashboard data complete and structured")
                    integration_results["dashboard"] = "complete"
                else:
                    logger.warning("  ⚠️  Dashboard data incomplete")
                    integration_results["dashboard"] = "incomplete"
        except Exception as e:
            logger.error(f"  ❌ Dashboard data error: {e}")
            integration_results["dashboard"] = "error"
        
        # Test inventory data
        try:
            response = requests.get(f"{self.api_url}/api/v1/inventory/list", timeout=5)
            if response.status_code == 200:
                logger.info("  ✅ Inventory data accessible")
                integration_results["inventory"] = "accessible"
        except Exception as e:
            logger.error(f"  ❌ Inventory data error: {e}")
            integration_results["inventory"] = "error"
        
        # Test forecast data
        try:
            response = requests.get(f"{self.api_url}/api/forecasting/forecast/1/1?days=7", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "forecast" in data and "metrics" in data:
                    logger.info("  ✅ Forecast data with metrics")
                    integration_results["forecast"] = "complete"
        except Exception as e:
            logger.error(f"  ❌ Forecast data error: {e}")
            integration_results["forecast"] = "error"
        
        return integration_results
    
    def test_full_workflow(self) -> bool:
        """Test a complete user workflow"""
        logger.info("\n🔄 Testing Complete User Workflow...")
        
        workflow_steps = []
        
        # Step 1: Load dashboard
        try:
            response = requests.get(f"{self.api_url}/api/v1/dashboard/realtime", timeout=5)
            if response.status_code == 200:
                workflow_steps.append("✅ Dashboard loads with KPIs")
            else:
                workflow_steps.append("❌ Dashboard load failed")
        except Exception as e:
            workflow_steps.append(f"❌ Dashboard error: {e}")
        
        # Step 2: Load inventory
        try:
            response = requests.get(f"{self.api_url}/api/v1/inventory/list", timeout=5)
            if response.status_code == 200:
                workflow_steps.append("✅ Inventory page loads with products")
            else:
                workflow_steps.append("❌ Inventory load failed")
        except Exception as e:
            workflow_steps.append(f"❌ Inventory error: {e}")
        
        # Step 3: Get forecast
        try:
            response = requests.get(f"{self.api_url}/api/forecasting/forecast/1/1?days=7", timeout=5)
            if response.status_code == 200:
                workflow_steps.append("✅ Forecast data retrieved")
            else:
                workflow_steps.append("❌ Forecast retrieval failed")
        except Exception as e:
            workflow_steps.append(f"❌ Forecast error: {e}")
        
        # Step 4: Get menu
        try:
            response = requests.get(f"{self.api_url}/api/petpooja/menu", timeout=5)
            if response.status_code == 200:
                workflow_steps.append("✅ Petpooja menu loaded")
            else:
                workflow_steps.append("❌ Menu load failed")
        except Exception as e:
            workflow_steps.append(f"❌ Menu error: {e}")
        
        for step in workflow_steps:
            logger.info(f"  {step}")
        
        return all("✅" in step for step in workflow_steps)
    
    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        
        print("\n" + "="*80)
        print(" INTEGRATED STACK TESTING: AUTH + API + FRONTEND")
        print("="*80)
        
        logger.info(f"\n🔗 API URL: {self.api_url}")
        logger.info(f"🔗 Frontend URL: {self.frontend_url}")
        
        # Critical: API must be running
        if not self.test_api_health():
            logger.error("\n❌ CRITICAL: API is not running")
            return False
        
        # Test authentication
        self.test_authentication_system()
        
        # Test core endpoints
        self.results["api_integration"]["endpoints"] = self.test_core_endpoints()
        
        # Test CORS
        self.test_cors_configuration()
        
        # Test response times
        self.results["api_integration"]["response_times"] = self.test_api_response_times()
        
        # Test data integration
        self.results["api_integration"]["data_integration"] = self.test_data_integration()
        
        # Test frontend
        frontend_online = self.test_frontend_connectivity()
        
        # Test complete workflow
        self.results["summary"]["workflow_functional"] = self.test_full_workflow()
        
        return True
    
    def print_summary(self):
        """Print detailed summary"""
        
        print("\n" + "="*80)
        print(" INTEGRATION TEST RESULTS")
        print("="*80 + "\n")
        
        # API Status
        print("🔗 API Status:")
        api_endpoints = self.results["api_integration"].get("endpoints", {})
        working = sum(1 for v in api_endpoints.values() if v == "working")
        total = len(api_endpoints)
        print(f"   Core Endpoints: {working}/{total} working")
        for endpoint, status in api_endpoints.items():
            symbol = "✅" if status == "working" else "❌"
            print(f"     {symbol} {endpoint}")
        
        # Response Times
        print("\n⚡ Response Times:")
        timings = self.results["api_integration"].get("response_times", {})
        for endpoint, time_ms in timings.items():
            if time_ms > 0:
                symbol = "✅" if time_ms < 500 else "⚠️"
                print(f"   {symbol} {endpoint}: {time_ms:.0f}ms")
        
        # Data Integration
        print("\n📊 Data Integration:")
        data_int = self.results["api_integration"].get("data_integration", {})
        for service, status in data_int.items():
            symbol = "✅" if "complete" in status else "⚠️" if "incomplete" in status else "❌"
            print(f"   {symbol} {service}: {status}")
        
        # Workflow
        workflow = self.results["summary"].get("workflow_functional", False)
        symbol = "✅" if workflow else "❌"
        print(f"\n🔄 Complete Workflow: {symbol}")
        
        print("\n" + "="*80)
        print(" RECOMMENDATIONS")
        print("="*80 + "\n")
        
        print("✅ Ready for STEP 3 Frontend Verification if:")
        print("   1. All core API endpoints are working")
        print("   2. Response times are < 500ms")
        print("   3. Data structures are complete")
        
        print("\n📋 Next Steps:")
        print("   1. Start frontend: npm run dev")
        print("   2. Run frontend verification: python test_frontend_verification.py")
        print("   3. Test dashboard with live data")
        print("   4. Verify all charts render correctly")
        
        print("\n" + "="*80 + "\n")
    
    def save_results(self):
        """Save test results"""
        with open("test_results_integrated_stack.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"✅ Results saved to: test_results_integrated_stack.json")


def main():
    tester = IntegratedStackTester()
    tester.run_all_tests()
    tester.print_summary()
    tester.save_results()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Testing interrupted")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
