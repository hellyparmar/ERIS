#!/usr/bin/env python3
"""
Phase 4: Cross-Browser Testing
Tests API compatibility and reliability across different "browser" scenarios
Simulates different user agents and browser-specific requirements
Total: 28 tests across 7 pages × 4 browser types
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List

class CrossBrowserTester:
    """Test API compatibility with different browser requirements"""
    
    # Simulated browsers with their characteristics
    BROWSERS = {
        "chrome": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "name": "Chrome 124 (Windows)",
            "requirements": {"json": True, "compression": True, "cache": True},
        },
        "firefox": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "name": "Firefox 124 (Windows)",
            "requirements": {"json": True, "compression": True, "cache": True},
        },
        "safari": {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "name": "Safari 17 (macOS)",
            "requirements": {"json": True, "compression": True, "cache": True},
        },
        "edge": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
            "name": "Edge 124 (Windows)",
            "requirements": {"json": True, "compression": True, "cache": True},
        },
    }
    
    # API endpoints to test
    ENDPOINTS = [
        ("Employees", "/api/v1/employees"),
        ("Sales", "/api/v1/sales"),
        ("Contacts", "/api/v1/contacts"),
        ("Invoices", "/api/v1/invoices"),
        ("Reports", "/api/v1/reports"),
        ("Outlets", "/api/v1/outlets"),
        ("Settings", "/api/v1/settings/profile"),
    ]
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.start_time = None
        self.results = {}
        self.errors = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level}]"
        print(f"{prefix} {message}")
    
    def test_endpoint_browser(self, endpoint_name: str, endpoint_url: str, browser_name: str, browser_config: Dict) -> Dict:
        """Test endpoint with specific browser"""
        result = {
            "endpoint": endpoint_name,
            "browser": browser_config["name"],
            "status_code": None,
            "response_time": None,
            "content_type": None,
            "passed": False,
            "issues": [],
        }
        
        try:
            # Create session with browser-specific headers
            session = requests.Session()
            session.headers.update({
                "User-Agent": browser_config["user_agent"],
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "max-age=0",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            })
            
            # Make request
            start = time.time()
            response = session.get(f"{self.base_url}{endpoint_url}?limit=10", timeout=5)
            elapsed = time.time() - start
            
            result["status_code"] = response.status_code
            result["response_time"] = elapsed
            result["content_type"] = response.headers.get("content-type", "unknown")
            
            # Check requirements
            passed = True
            
            # Requirement 1: HTTP status 200-500
            if not (200 <= response.status_code < 500):
                result["issues"].append(f"Status {response.status_code} outside expected range")
                passed = False
            
            # Requirement 2: JSON response for successful requests
            if 200 <= response.status_code < 300:
                if "application/json" not in response.headers.get("content-type", ""):
                    result["issues"].append(f"Content-Type is {response.headers.get('content-type', 'unknown')}, expected application/json")
                    passed = False
                else:
                    try:
                        response.json()
                    except:
                        result["issues"].append("Response is not valid JSON")
                        passed = False
            
            # Requirement 3: Response time reasonable
            if elapsed > 1.0:
                result["issues"].append(f"Slow response: {elapsed:.2f}s")
                passed = False
            
            result["passed"] = passed and len(result["issues"]) == 0
            return result
            
        except requests.exceptions.Timeout:
            result["issues"].append("Request timeout (>5s)")
            return result
        except Exception as e:
            result["issues"].append(str(e)[:50])
            return result
    
    def run_all_tests(self):
        """Execute all cross-browser tests"""
        self.start_time = datetime.now()
        self.log("=" * 90, "START")
        self.log("PHASE 4: CROSS-BROWSER TESTING", "START")
        self.log("Testing API compatibility with Chrome, Firefox, Safari, Edge (28 tests total)", "START")
        self.log("=" * 90, "START")
        self.log("")
        
        # Test connectivity
        self.log("🔍 Testing connectivity to backend...", "INFO")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log(f"✅ Backend accessible at {self.base_url}", "INFO")
            else:
                self.log(f"⚠️  Backend returned status {response.status_code}", "WARN")
        except Exception as e:
            self.log(f"❌ Cannot connect to backend: {e}", "ERROR")
            return False
        
        self.log("")
        
        # Test all combinations
        for endpoint_name, endpoint_url in self.ENDPOINTS:
            self.log(f"\nTesting {endpoint_name} across browsers...", "PERF")
            
            for browser_name, browser_config in self.BROWSERS.items():
                result = self.test_endpoint_browser(endpoint_name, endpoint_url, browser_name, browser_config)
                
                self.test_count += 1
                
                if result["passed"]:
                    self.passed_count += 1
                    self.log(f"  ✅ {browser_config['name']:30} - {result['status_code']} - {result['response_time']:.3f}s", "PERF")
                else:
                    self.failed_count += 1
                    issues = ", ".join(result["issues"])
                    self.log(f"  ❌ {browser_config['name']:30} - {issues}", "PERF")
                
                # Store result
                if endpoint_name not in self.results:
                    self.results[endpoint_name] = {}
                self.results[endpoint_name][browser_name] = result
        
        self.generate_report()
        return True
    
    def generate_report(self):
        """Generate test report"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        self.log("\n\n" + "=" * 90, "REPORT")
        self.log("PHASE 4 CROSS-BROWSER TESTING - FINAL REPORT", "REPORT")
        self.log("=" * 90, "REPORT")
        
        self.log(f"\n⏱️  TESTING DURATION: {duration:.1f} seconds\n", "REPORT")
        
        # Overall results
        pass_rate = (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        
        self.log("📊 OVERALL RESULTS", "REPORT")
        self.log("-" * 90, "REPORT")
        self.log(f"Total Tests: {self.test_count}", "REPORT")
        self.log(f"Tests Passed: {self.passed_count} ✅", "REPORT")
        self.log(f"Tests Failed: {self.failed_count} ❌", "REPORT")
        self.log(f"Pass Rate: {pass_rate:.1f}%", "REPORT")
        
        # Endpoint summary
        self.log("\n📋 ENDPOINT BROWSER COMPATIBILITY", "REPORT")
        self.log("-" * 90, "REPORT")
        
        for endpoint_name, browsers in self.results.items():
            passed_browsers = sum(1 for result in browsers.values() if result["passed"])
            status = "✅" if passed_browsers == 4 else "⚠️" if passed_browsers >= 3 else "❌"
            self.log(f"{status} {endpoint_name:20} - {passed_browsers}/4 browsers compatible", "REPORT")
        
        # Browser summary
        self.log("\n🌐 BROWSER COMPATIBILITY SUMMARY", "REPORT")
        self.log("-" * 90, "REPORT")
        
        for browser_name, browser_config in self.BROWSERS.items():
            browser_passed = sum(
                1 for result in self.results.values()
                if result.get(browser_name, {}).get("passed", False)
            )
            self.log(f"  {browser_config['name']:30} - {browser_passed}/7 endpoints ✅", "REPORT")
        
        # Success determination
        self.log("\n" + "=" * 90, "REPORT")
        if pass_rate >= 85:
            self.log("✅ CROSS-BROWSER TESTS - PASSING", "REPORT")
            self.log(f"   {pass_rate:.1f}% pass rate meets success criteria (≥85%)", "REPORT")
        else:
            self.log("❌ CROSS-BROWSER TESTS - NEEDS IMPROVEMENT", "REPORT")
            self.log(f"   {pass_rate:.1f}% pass rate below success criteria (≥85%)", "REPORT")
        self.log("=" * 90, "REPORT")
        
        # Save results to JSON
        report_data = {
            "phase": "Phase 4: Cross-Browser Testing",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_tests": self.test_count,
                "passed": self.passed_count,
                "failed": self.failed_count,
                "pass_rate": pass_rate,
            },
            "browsers_tested": list(self.BROWSERS.keys()),
            "endpoints": self.results,
        }
        
        with open("phase4_crossbrowser_test_results.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"\n📄 Report saved to phase4_crossbrowser_test_results.json\n", "REPORT")

if __name__ == "__main__":
    tester = CrossBrowserTester()
    tester.run_all_tests()
