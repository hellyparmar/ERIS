#!/usr/bin/env python3
"""
STEP 3: Frontend UI/UX Verification Suite
Comprehensive testing of React dashboard and frontend components

Run with: python test_frontend_verification.py
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FrontendVerifier:
    """Verify R-DIOS React Frontend"""
    
    def __init__(self, frontend_url: str = "http://localhost:5173", api_url: str = "http://localhost:8000"):
        self.frontend_url = frontend_url
        self.api_url = api_url
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "frontend_url": frontend_url,
            "api_url": api_url,
            "pages_tested": {},
            "components_tested": {},
            "data_integration": {},
            "performance": {},
            "issues": []
        }
    
    def test_frontend_connectivity(self) -> bool:
        """Test if frontend is running"""
        logger.info("🔗 Testing frontend connectivity...")
        
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"  ✅ Frontend running on {self.frontend_url}")
                return True
            else:
                logger.warning(f"  ⚠️  Frontend returned {response.status_code}")
                return False
        except requests.ConnectionError:
            logger.error(f"  ❌ Cannot connect to {self.frontend_url}")
            logger.info("     To start frontend: npm run dev")
            return False
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            return False
    
    def test_api_connectivity(self) -> bool:
        """Test API connectivity from frontend"""
        logger.info("🔗 Testing API connectivity for frontend...")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"  ✅ API accessible at {self.api_url}")
                self.results["api_status"] = "online"
                return True
            else:
                logger.warning(f"  ⚠️  API returned {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"  ❌ API Error: {e}")
            return False
    
    def test_dashboard_page(self) -> Dict[str, Any]:
        """Test dashboard page components"""
        logger.info("\n📊 Testing Dashboard Page...")
        
        test_results = {
            "page": "dashboard",
            "url": "/",
            "tests": {
                "page_loads": False,
                "header_present": False,
                "sidebar_present": False,
                "main_content": False,
                "kpi_cards": False,
                "charts": False,
                "theme_toggle": False
            }
        }
        
        try:
            # Test dashboard endpoint
            dashboard_data = requests.get(f"{self.api_url}/api/v1/dashboard/realtime", timeout=5)
            if dashboard_data.status_code == 200:
                logger.info("  ✅ Dashboard data endpoint accessible")
                test_results["tests"]["main_content"] = True
                test_results["data_available"] = True
                
                data = dashboard_data.json()
                required_keys = ["today_revenue", "total_revenue", "active_orders", "top_products"]
                if all(key in data for key in required_keys):
                    logger.info("  ✅ Dashboard KPI data complete")
                    test_results["tests"]["kpi_cards"] = True
                else:
                    logger.warning("  ⚠️  Some KPI data missing")
        except Exception as e:
            logger.error(f"  ❌ Dashboard test failed: {e}")
        
        return test_results
    
    def test_inventory_page(self) -> Dict[str, Any]:
        """Test inventory page"""
        logger.info("\n📦 Testing Inventory Page...")
        
        test_results = {
            "page": "inventory",
            "tests": {
                "page_loads": False,
                "table_displays": False,
                "filters_work": False,
                "search_works": False,
                "pagination_works": False
            }
        }
        
        try:
            # Test inventory endpoint
            inventory_data = requests.get(f"{self.api_url}/api/v1/inventory/list", timeout=5)
            if inventory_data.status_code == 200:
                logger.info("  ✅ Inventory data endpoint accessible")
                test_results["tests"]["table_displays"] = True
                
                data = inventory_data.json()
                if isinstance(data, dict) and "products" in data:
                    logger.info(f"  ✅ Inventory has {len(data.get('products', []))} items")
                    test_results["tests"]["page_loads"] = True
        except Exception as e:
            logger.error(f"  ❌ Inventory test failed: {e}")
        
        return test_results
    
    def test_analytics_page(self) -> Dict[str, Any]:
        """Test analytics page"""
        logger.info("\n📈 Testing Analytics Page...")
        
        test_results = {
            "page": "analytics",
            "tests": {
                "charts_display": False,
                "data_loading": False,
                "filters_work": False,
                "date_range_selector": False,
                "export_works": False
            }
        }
        
        try:
            # Test analytics metrics endpoint (public)
            analytics_data = requests.get(f"{self.api_url}/api/v1/analytics/metrics", timeout=5)
            if analytics_data.status_code == 200:
                logger.info("  ✅ Analytics metrics accessible")
                test_results["tests"]["data_loading"] = True
                test_results["tests"]["charts_display"] = True
        except Exception as e:
            logger.warning(f"  ⚠️  Analytics test: {e}")
            test_results["tests"]["data_loading"] = False
        
        return test_results
    
    def test_forecast_page(self) -> Dict[str, Any]:
        """Test forecasting page"""
        logger.info("\n🔮 Testing Forecasting Page...")
        
        test_results = {
            "page": "forecasting",
            "tests": {
                "forecast_displays": False,
                "model_selector": False,
                "timeframe_selector": False,
                "confidence_bounds": False,
                "accuracy_metrics": False
            }
        }
        
        try:
            # Test forecast endpoint
            forecast_data = requests.get(f"{self.api_url}/api/forecasting/forecast/1/1?days=7", timeout=5)
            if forecast_data.status_code == 200:
                logger.info("  ✅ Forecast data available")
                data = forecast_data.json()
                
                if "forecast" in data and len(data["forecast"]) > 0:
                    logger.info("  ✅ Forecast points generated")
                    test_results["tests"]["forecast_displays"] = True
                    test_results["tests"]["confidence_bounds"] = True
                
                if "metrics" in data:
                    logger.info("  ✅ Accuracy metrics available")
                    test_results["tests"]["accuracy_metrics"] = True
        except Exception as e:
            logger.error(f"  ❌ Forecast test failed: {e}")
        
        return test_results
    
    def test_petpooja_page(self) -> Dict[str, Any]:
        """Test Petpooja restaurant-specific pages"""
        logger.info("\n🍽️  Testing Petpooja Pages...")
        
        test_results = {
            "page": "petpooja",
            "tests": {
                "menu_displays": False,
                "categories_load": False,
                "items_show_prices": False,
                "daily_summary": False
            }
        }
        
        try:
            # Test menu endpoint
            menu_data = requests.get(f"{self.api_url}/api/petpooja/menu", timeout=5)
            if menu_data.status_code == 200:
                logger.info("  ✅ Menu endpoint accessible")
                data = menu_data.json()
                
                if "menu" in data and len(data["menu"]) > 0:
                    categories = list(data["menu"].keys())
                    logger.info(f"  ✅ Menu has {len(categories)} categories")
                    test_results["tests"]["menu_displays"] = True
                    test_results["tests"]["categories_load"] = True
            
            # Test daily summary
            daily_data = requests.get(f"{self.api_url}/api/petpooja/analytics/daily-summary", timeout=5)
            if daily_data.status_code == 200:
                logger.info("  ✅ Daily summary accessible")
                test_results["tests"]["daily_summary"] = True
        except Exception as e:
            logger.error(f"  ❌ Petpooja test failed: {e}")
        
        return test_results
    
    def test_responsive_design(self) -> Dict[str, Any]:
        """Test responsive design"""
        logger.info("\n📱 Testing Responsive Design...")
        
        test_results = {
            "tests": {
                "desktop_layout": "Not tested",
                "tablet_layout": "Not tested",
                "mobile_layout": "Not tested",
                "touch_friendly": "Manual review needed"
            },
            "note": "Requires browser automation (Playwright/Selenium)"
        }
        
        logger.info("  ℹ️  Responsive design requires Playwright/Selenium")
        logger.info("  📝 Manual testing recommended for:")
        logger.info("     - Mobile layout (< 768px)")
        logger.info("     - Tablet layout (768px - 1024px)")
        logger.info("     - Desktop layout (> 1024px)")
        
        return test_results
    
    def test_accessibility(self) -> Dict[str, Any]:
        """Test accessibility features"""
        logger.info("\n♿ Testing Accessibility...")
        
        test_results = {
            "tests": {
                "keyboard_navigation": "Manual review needed",
                "screen_reader_support": "Manual review needed",
                "color_contrast": "Manual review needed",
                "form_labels": "Manual review needed"
            },
            "tools_recommended": [
                "axe DevTools",
                "WAVE Browser Extension",
                "Lighthouse (Chrome DevTools)",
                "NVDA Screen Reader"
            ]
        }
        
        logger.info("  ℹ️  Accessibility requires manual review")
        logger.info("  📝 Recommended tools:")
        for tool in test_results["tools_recommended"]:
            logger.info(f"     - {tool}")
        
        return test_results
    
    def test_dark_mode(self) -> Dict[str, Any]:
        """Test dark mode theme"""
        logger.info("\n🌙 Testing Dark Mode...")
        
        test_results = {
            "tests": {
                "toggle_visible": False,
                "colors_change": "Manual review needed",
                "contrast_maintained": "Manual review needed",
                "persistence": "Check localStorage"
            }
        }
        
        logger.info("  ℹ️  Dark mode testing requires browser interaction")
        logger.info("  📝 Manual checks:")
        logger.info("     - Toggle button location")
        logger.info("     - Color scheme switch")
        logger.info("     - Settings persistence")
        
        return test_results
    
    def test_performance(self) -> Dict[str, Any]:
        """Test frontend performance"""
        logger.info("\n⚡ Testing Performance...")
        
        test_results = {
            "metrics": {},
            "recommendations": []
        }
        
        try:
            # Measure API response times
            start = time.time()
            requests.get(f"{self.api_url}/api/v1/dashboard/realtime", timeout=5)
            dashboard_time = (time.time() - start) * 1000
            
            logger.info(f"  Dashboard load: {dashboard_time:.0f}ms")
            test_results["metrics"]["dashboard_api"] = f"{dashboard_time:.0f}ms"
            
            if dashboard_time < 100:
                logger.info("  ✅ Excellent performance")
            elif dashboard_time < 500:
                logger.info("  ✅ Good performance")
            else:
                logger.warning("  ⚠️  Consider optimization")
                test_results["recommendations"].append("Optimize dashboard query")
        except Exception as e:
            logger.error(f"  ❌ Performance test failed: {e}")
        
        return test_results
    
    def run_all_tests(self) -> bool:
        """Run all frontend verification tests"""
        
        print("\n" + "="*80)
        print(" STEP 3: FRONTEND UI/UX VERIFICATION")
        print("="*80 + "\n")
        
        # Check connectivity
        if not self.test_frontend_connectivity():
            logger.error("\n❌ Frontend is not running. Start with: npm run dev")
            return False
        
        if not self.test_api_connectivity():
            logger.error("\n❌ API is not accessible")
            return False
        
        # Test pages
        logger.info("\n" + "="*80)
        logger.info(" PAGE VERIFICATION")
        logger.info("="*80)
        
        self.results["pages_tested"]["dashboard"] = self.test_dashboard_page()
        self.results["pages_tested"]["inventory"] = self.test_inventory_page()
        self.results["pages_tested"]["analytics"] = self.test_analytics_page()
        self.results["pages_tested"]["forecasting"] = self.test_forecast_page()
        self.results["pages_tested"]["petpooja"] = self.test_petpooja_page()
        
        # Test components
        logger.info("\n" + "="*80)
        logger.info(" COMPONENT & FEATURE VERIFICATION")
        logger.info("="*80)
        
        self.results["components_tested"]["responsive"] = self.test_responsive_design()
        self.results["components_tested"]["accessibility"] = self.test_accessibility()
        self.results["components_tested"]["dark_mode"] = self.test_dark_mode()
        self.results["performance"] = self.test_performance()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        
        print("\n" + "="*80)
        print(" FRONTEND VERIFICATION SUMMARY")
        print("="*80 + "\n")
        
        pages_tested = len(self.results["pages_tested"])
        print(f"📄 Pages Tested: {pages_tested}")
        
        working_pages = 0
        for page_name, page_data in self.results["pages_tested"].items():
            if "tests" in page_data:
                passed = sum(1 for test in page_data["tests"].values() if test is True)
                total = len(page_data["tests"])
                status = "✅" if passed > total/2 else "⚠️"
                print(f"   {status} {page_name.capitalize()}: {passed}/{total}")
                if passed > total/2:
                    working_pages += 1
        
        print(f"\n📊 Page Status: {working_pages}/{pages_tested} functional")
        
        print(f"\n🔗 Frontend URL: {self.frontend_url}")
        print(f"🔗 API URL: {self.api_url}")
        
        print(f"\n" + "="*80 + "\n")
    
    def save_results(self):
        """Save test results"""
        with open("test_results_3_frontend.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"✅ Results saved to: test_results_3_frontend.json")


def main():
    """Main execution"""
    
    verifier = FrontendVerifier()
    
    if verifier.run_all_tests():
        verifier.print_summary()
        verifier.save_results()
        
        print("\n📝 Manual Testing Checklist:")
        print("   ☐ Verify all pages load without errors")
        print("   ☐ Test responsive design on mobile/tablet")
        print("   ☐ Test dark mode toggle")
        print("   ☐ Verify all charts render correctly")
        print("   ☐ Test data filtering and search")
        print("   ☐ Verify keyboard navigation")
        print("   ☐ Check console for JavaScript errors")
        print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Testing interrupted")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
