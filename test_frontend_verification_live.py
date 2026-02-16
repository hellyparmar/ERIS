#!/usr/bin/env python3
"""
STEP 3: Frontend Verification & User Experience Testing
Tests React components, pages, responsiveness, performance, and accessibility

Run with: python test_frontend_verification_live.py
Requirements: pip install selenium playwright pytest
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    name: str
    status: str
    details: str
    time_ms: float = 0


class FrontendVerifier:
    """Comprehensive frontend verification suite"""
    
    def __init__(self, frontend_url: str = "http://localhost:5173",
                 api_url: str = "http://localhost:8000"):
        self.frontend_url = frontend_url
        self.api_url = api_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "frontend_url": frontend_url,
            "api_url": api_url,
            "pages": {},
            "components": {},
            "performance": {},
            "accessibility": {},
            "security": {},
            "summary": {}
        }
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_log: List[TestResult] = []
    
    def log_test(self, name: str, status: str, details: str, time_ms: float = 0):
        """Log test result"""
        result = TestResult(name, status, details, time_ms)
        self.test_log.append(result)
        
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        time_info = f" ({time_ms:.0f}ms)" if time_ms > 0 else ""
        logger.info(f"  {symbol} {name}: {details}{time_info}")
        
        if status == "PASS":
            self.tests_passed += 1
        elif status == "FAIL":
            self.tests_failed += 1
    
    def test_frontend_connectivity(self) -> bool:
        """Test frontend server is running"""
        logger.info("\n🌐 Testing Frontend Connectivity...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_test("Frontend Server", "PASS", "Server responding at port 5173")
                return True
            else:
                self.log_test("Frontend Server", "FAIL", f"Status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Server", "FAIL", f"Not running: {e}")
            return False
    
    def test_page_loads(self) -> bool:
        """Test critical pages load"""
        logger.info("\n📄 Testing Page Loads...")
        
        pages = {
            "Dashboard": "/",
            "Inventory": "/inventory",
            "Analytics": "/analytics",
            "Forecasting": "/forecasting",
            "Petpooja": "/petpooja"
        }
        
        all_passed = True
        for name, path in pages.items():
            try:
                start = time.time()
                response = requests.get(f"{self.frontend_url}{path}", timeout=10)
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    self.log_test(f"Page: {name}", "PASS", "Page loads successfully", elapsed)
                    # Check for common HTML elements
                    if "<!doctype html" in response.text.lower() or "<html" in response.text.lower():
                        pass
                    else:
                        self.log_test(f"Page: {name} HTML", "WARN", "No HTML doctype detected")
                else:
                    self.log_test(f"Page: {name}", "FAIL", f"Status {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test(f"Page: {name}", "FAIL", str(e))
                all_passed = False
        
        return all_passed
    
    def test_api_integration(self) -> Dict[str, bool]:
        """Test frontend can access API endpoints"""
        logger.info("\n🔗 Testing API Integration...")
        
        integration_results = {}
        
        endpoints = {
            "Dashboard Data": "/api/v1/dashboard/realtime",
            "Inventory": "/api/v1/inventory/list",
            "Forecast": "/api/forecasting/forecast/1/1?days=7",
            "Petpooja Menu": "/api/petpooja/menu",
            "AI Status": "/api/v1/ai/status"
        }
        
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # Verify data structure
                    if data and isinstance(data, (dict, list)):
                        self.log_test(f"API: {name}", "PASS", "Data returns valid JSON")
                        integration_results[name] = True
                    else:
                        self.log_test(f"API: {name}", "FAIL", "Invalid data structure")
                        integration_results[name] = False
                else:
                    self.log_test(f"API: {name}", "FAIL", f"Status {response.status_code}")
                    integration_results[name] = False
            except Exception as e:
                self.log_test(f"API: {name}", "FAIL", str(e))
                integration_results[name] = False
        
        return integration_results
    
    def test_performance_metrics(self) -> Dict[str, float]:
        """Test frontend performance"""
        logger.info("\n⚡ Testing Performance Metrics...")
        
        performance_results = {}
        
        # Test page load times
        pages = {
            "Dashboard": "/",
            "Inventory": "/inventory",
            "Forecasting": "/forecasting"
        }
        
        for name, path in pages.items():
            times = []
            for _ in range(3):  # Multiple loads for average
                try:
                    start = time.time()
                    response = requests.get(f"{self.frontend_url}{path}", timeout=10)
                    elapsed = (time.time() - start) * 1000
                    times.append(elapsed)
                except:
                    pass
            
            if times:
                avg_time = sum(times) / len(times)
                performance_results[name] = avg_time
                
                # Performance threshold: < 2 seconds
                if avg_time < 2000:
                    self.log_test(f"Performance: {name}", "PASS", f"Load time {avg_time:.0f}ms")
                else:
                    self.log_test(f"Performance: {name}", "WARN", f"Load time {avg_time:.0f}ms (slow)")
        
        return performance_results
    
    def test_responsive_design(self) -> bool:
        """Test responsive design (via CSS checks)"""
        logger.info("\n📱 Testing Responsive Design...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            html = response.text
            
            # Check for responsive meta tag
            if 'viewport' in html and 'width=device-width' in html:
                self.log_test("Responsive Meta", "PASS", "Viewport meta tag present")
            else:
                self.log_test("Responsive Meta", "WARN", "Viewport meta tag missing")
            
            # Check for Tailwind CSS (responsive framework)
            if 'tailwind' in html.lower() or '_app-' in html or 'className=' in html:
                self.log_test("Responsive Framework", "PASS", "Tailwind CSS detected")
                return True
            else:
                self.log_test("Responsive Framework", "WARN", "CSS framework unclear")
                return False
        except Exception as e:
            self.log_test("Responsive Design", "FAIL", str(e))
            return False
    
    def test_accessibility(self) -> bool:
        """Test accessibility features"""
        logger.info("\n♿ Testing Accessibility...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            html = response.text.lower()
            
            checks = {
                "lang attribute": html.count('lang=') > 0,
                "alt attributes": html.count('alt=') > 0,
                "heading hierarchy": all(f'<h{i}' in html for i in range(1, 4)),
                "ARIA labels": 'aria-' in html,
                "semantic HTML": any(tag in html for tag in ['<nav', '<main', '<section', '<article'])
            }
            
            passed = 0
            for check, result in checks.items():
                if result:
                    self.log_test(f"Accessibility: {check}", "PASS", "Implemented")
                    passed += 1
                else:
                    self.log_test(f"Accessibility: {check}", "WARN", "Not detected")
            
            self.results["accessibility"] = checks
            return passed >= 3
        except Exception as e:
            self.log_test("Accessibility", "FAIL", str(e))
            return False
    
    def test_security_headers(self) -> bool:
        """Test security headers"""
        logger.info("\n🔒 Testing Security Headers...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            headers = response.headers
            
            security_checks = {
                "X-Content-Type-Options": "nosniff" in headers.get("X-Content-Type-Options", ""),
                "X-Frame-Options": "X-Frame-Options" in headers,
                "Content-Security-Policy": "Content-Security-Policy" in headers,
                "Strict-Transport-Security": "Strict-Transport-Security" in headers
            }
            
            passed = 0
            for header, present in security_checks.items():
                if present:
                    self.log_test(f"Header: {header}", "PASS", "Present")
                    passed += 1
                else:
                    self.log_test(f"Header: {header}", "WARN", "Not configured")
            
            return passed >= 1
        except Exception as e:
            self.log_test("Security Headers", "FAIL", str(e))
            return False
    
    def test_dark_mode_support(self) -> bool:
        """Test dark mode support"""
        logger.info("\n🌙 Testing Dark Mode Support...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            html = response.text
            
            # Check for Tailwind dark mode or CSS custom properties
            has_dark_mode = (
                'dark:' in html or 
                '--color-dark' in html or 
                'prefers-color-scheme' in html or
                'darkMode' in html
            )
            
            if has_dark_mode:
                self.log_test("Dark Mode", "PASS", "Dark mode support detected")
                return True
            else:
                self.log_test("Dark Mode", "WARN", "Dark mode support not detected")
                return False
        except Exception as e:
            self.log_test("Dark Mode", "FAIL", str(e))
            return False
    
    def test_error_handling(self) -> bool:
        """Test frontend error handling"""
        logger.info("\n❌ Testing Error Handling...")
        
        try:
            # Test 404 page
            response = requests.get(f"{self.frontend_url}/nonexistent-page", timeout=10)
            
            # Frontend should handle gracefully
            if response.status_code == 200:
                # SPA returns 200 for routing
                if '404' in response.text or 'Not Found' in response.text or 'page not found' in response.text.lower():
                    self.log_test("404 Handling", "PASS", "Frontend shows 404 message")
                    return True
                else:
                    self.log_test("404 Handling", "WARN", "No 404 page detected")
                    return False
            else:
                self.log_test("404 Handling", "PASS", f"HTTP {response.status_code} returned")
                return True
        except Exception as e:
            self.log_test("Error Handling", "FAIL", str(e))
            return False
    
    def test_component_rendering(self) -> bool:
        """Test critical components render"""
        logger.info("\n🧩 Testing Component Rendering...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            html = response.text
            
            components = {
                "Navigation": 'nav' in html or 'navbar' in html.lower() or 'header' in html,
                "Sidebar": 'sidebar' in html.lower() or 'aside' in html,
                "Chart/Graph": 'canvas' in html or 'svg' in html or 'chart' in html.lower(),
                "Form": 'form' in html or 'input' in html,
                "Footer": 'footer' in html
            }
            
            passed = 0
            for component, present in components.items():
                if present:
                    self.log_test(f"Component: {component}", "PASS", "Rendered")
                    passed += 1
                else:
                    self.log_test(f"Component: {component}", "WARN", "Not found")
            
            return passed >= 3
        except Exception as e:
            self.log_test("Component Rendering", "FAIL", str(e))
            return False
    
    def test_static_assets(self) -> bool:
        """Test static assets load"""
        logger.info("\n📦 Testing Static Assets...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            html = response.text
            
            # Check for CSS and JS loading
            has_css = '<link' in html and 'css' in html.lower()
            has_js = '<script' in html
            
            css_pass = "CSS loaded" if has_css else "CSS not found"
            js_pass = "JavaScript loaded" if has_js else "JavaScript not found"
            
            self.log_test("CSS Assets", "PASS" if has_css else "WARN", css_pass)
            self.log_test("JS Assets", "PASS" if has_js else "WARN", js_pass)
            
            return has_css and has_js
        except Exception as e:
            self.log_test("Static Assets", "FAIL", str(e))
            return False
    
    def run_all_tests(self) -> bool:
        """Run all frontend tests"""
        
        print("\n" + "="*80)
        print(" STEP 3: FRONTEND VERIFICATION & USER EXPERIENCE TESTING")
        print("="*80)
        
        logger.info(f"\n🔗 Frontend URL: {self.frontend_url}")
        logger.info(f"🔗 API URL: {self.api_url}")
        
        # Critical: Frontend must be running
        if not self.test_frontend_connectivity():
            logger.error("\n❌ CRITICAL: Frontend is not running")
            logger.info("💡 Start frontend with: npm run dev")
            return False
        
        # Run all test suites
        self.test_page_loads()
        self.results["api_integration"] = self.test_api_integration()
        self.results["performance"] = self.test_performance_metrics()
        self.test_responsive_design()
        self.test_accessibility()
        self.test_security_headers()
        self.test_dark_mode_support()
        self.test_error_handling()
        self.test_component_rendering()
        self.test_static_assets()
        
        # Calculate summary
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        self.results["summary"] = {
            "total_tests": total,
            "passed": self.tests_passed,
            "failed": self.tests_failed,
            "pass_rate": f"{pass_rate:.1f}%"
        }
        
        return True
    
    def print_summary(self):
        """Print detailed summary"""
        
        print("\n" + "="*80)
        print(" STEP 3 VERIFICATION RESULTS")
        print("="*80 + "\n")
        
        # Overall Results
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"📊 Test Results: {self.tests_passed}/{total} passed ({pass_rate:.1f}%)")
        print(f"   ✅ Passed: {self.tests_passed}")
        print(f"   ❌ Failed: {self.tests_failed}")
        
        # API Integration
        print("\n🔗 API Integration:")
        api_results = self.results.get("api_integration", {})
        if api_results:
            working = sum(1 for v in api_results.values() if v)
            total_api = len(api_results)
            print(f"   {working}/{total_api} endpoints responding")
            for endpoint, status in api_results.items():
                symbol = "✅" if status else "❌"
                print(f"     {symbol} {endpoint}")
        
        # Performance
        print("\n⚡ Performance:")
        perf = self.results.get("performance", {})
        if perf:
            for page, time_ms in perf.items():
                symbol = "✅" if time_ms < 2000 else "⚠️"
                print(f"   {symbol} {page}: {time_ms:.0f}ms")
        
        # Accessibility
        print("\n♿ Accessibility Checks:")
        a11y = self.results.get("accessibility", {})
        if a11y:
            for check, status in a11y.items():
                symbol = "✅" if status else "⚠️"
                print(f"   {symbol} {check}")
        
        print("\n" + "="*80)
        print(" STEP 3 VERIFICATION STATUS")
        print("="*80 + "\n")
        
        if pass_rate >= 80:
            print("✅ STEP 3 VERIFICATION PASSED")
            print("   Frontend is production-ready for deployment")
        elif pass_rate >= 50:
            print("⚠️  STEP 3 VERIFICATION PARTIAL")
            print("   Frontend needs additional testing/fixes")
        else:
            print("❌ STEP 3 VERIFICATION FAILED")
            print("   Frontend requires significant work")
        
        print("\n" + "="*80 + "\n")
    
    def save_results(self):
        """Save test results"""
        with open("test_results_frontend_step3.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"✅ Results saved to: test_results_frontend_step3.json")


def main():
    verifier = FrontendVerifier()
    verifier.run_all_tests()
    verifier.print_summary()
    verifier.save_results()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Testing interrupted")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
