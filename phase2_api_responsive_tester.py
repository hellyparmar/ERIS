#!/usr/bin/env python3
"""
Phase 2: Responsive Design Testing (API-based)
Tests all 7 pages' API responsiveness at different payload sizes
Simulates responsive behavior through API response times
Total: 42 tests across 7 pages at 6 response complexity levels
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List
import statistics
import jwt
from datetime import timedelta

class ResponsiveAPITester:
    """Test API responsiveness across different data loads"""
    
    # Response complexity levels (simulating different viewport requirements)
    COMPLEXITY_LEVELS = {
        "minimal": {"limit": 5, "device": "Mobile (375px) - Minimal Load"},
        "light": {"limit": 10, "device": "Mobile (480px) - Light Load"},
        "medium": {"limit": 25, "device": "Tablet (768px) - Medium Load"},
        "heavy": {"limit": 50, "device": "Tablet (1024px) - Heavy Load"},
        "full": {"limit": 100, "device": "Desktop (1440px) - Full Load"},
        "ultra": {"limit": 200, "device": "Desktop (1920px) - Ultra Load"},
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
    
    # Performance targets for responsive design
    TARGETS = {
        "minimal": 0.1,      # 100ms for minimal load
        "light": 0.15,       # 150ms for light load
        "medium": 0.25,      # 250ms for medium load
        "heavy": 0.35,       # 350ms for heavy load
        "full": 0.45,        # 450ms for full load
        "ultra": 0.5,        # 500ms for ultra load
    }
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.start_time = None
        self.results = {}
        self.errors = []
        self.auth_token = None
        self.session = requests.Session()
        self._setup_auth()
        
    def _setup_auth(self):
        """Setup authentication token for protected endpoints"""
        try:
            # Create token manually using PyJWT
            secret_key = "your-secret-key-here"  # Default for testing
            payload = {
                "user_id": "admin123",
                "email": "admin@example.com",
                "role": "super_admin",
                "outlet_id": None,
                "exp": datetime.utcnow() + timedelta(hours=24),
            }
            self.auth_token = jwt.encode(payload, secret_key, algorithm="HS256")
            if self.auth_token:
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log(f"✅ Authentication token created successfully", "INFO")
        except Exception as e:
            self.log(f"⚠️  Authentication setup failed: {str(e)[:50]}", "WARN")
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level}]"
        print(f"{prefix} {message}")
    
    def test_endpoint_responsive(self, endpoint_name: str, endpoint_url: str) -> Dict:
        """Test endpoint performance at different complexity levels"""
        results = {
            "name": endpoint_name,
            "url": endpoint_url,
            "tests": {},
            "passed": 0,
            "failed": 0,
        }
        
        self.log(f"\nTesting {endpoint_name} responsiveness...", "PERF")
        
        for complexity_name, complexity_info in self.COMPLEXITY_LEVELS.items():
            try:
                # Add limit parameter for responsive testing
                test_url = f"{self.base_url}{endpoint_url}?limit={complexity_info['limit']}"
                
                # Measure response time
                start = time.time()
                response = self.session.get(test_url, timeout=5)
                elapsed = time.time() - start
                
                # Check if response is acceptable (200-500 status)
                passed = (200 <= response.status_code < 500) and (elapsed <= self.TARGETS[complexity_name])
                
                results["tests"][complexity_name] = {
                    "device": complexity_info["device"],
                    "status_code": response.status_code,
                    "response_time": elapsed,
                    "target": self.TARGETS[complexity_name],
                    "passed": passed,
                }
                
                if passed:
                    results["passed"] += 1
                    self.passed_count += 1
                    self.log(f"  ✅ {complexity_name:10} ({complexity_info['device']:35}) {elapsed:.3f}s", "PERF")
                else:
                    results["failed"] += 1
                    self.failed_count += 1
                    reason = "timeout" if elapsed > self.TARGETS[complexity_name] else f"status {response.status_code}"
                    self.log(f"  ❌ {complexity_name:10} ({complexity_info['device']:35}) {elapsed:.3f}s ({reason})", "PERF")
                
                self.test_count += 1
                
            except requests.exceptions.Timeout:
                results["tests"][complexity_name] = {
                    "device": complexity_info["device"],
                    "status_code": "TIMEOUT",
                    "response_time": 5.0,
                    "target": self.TARGETS[complexity_name],
                    "passed": False,
                }
                results["failed"] += 1
                self.failed_count += 1
                self.test_count += 1
                self.log(f"  ❌ {complexity_name:10} ({complexity_info['device']:35}) TIMEOUT", "PERF")
            except Exception as e:
                results["tests"][complexity_name] = {
                    "device": complexity_info["device"],
                    "status_code": "ERROR",
                    "error": str(e)[:50],
                    "target": self.TARGETS[complexity_name],
                    "passed": False,
                }
                results["failed"] += 1
                self.failed_count += 1
                self.test_count += 1
                self.log(f"  ❌ {complexity_name:10} ({complexity_info['device']:35}) ERROR: {str(e)[:40]}", "PERF")
        
        return results
    
    def run_all_tests(self):
        """Execute all responsive design tests"""
        self.start_time = datetime.now()
        self.log("=" * 90, "START")
        self.log("PHASE 2: RESPONSIVE DESIGN TESTING (API-Based)", "START")
        self.log("Testing all 7 pages at 6 complexity levels (42 tests total)", "START")
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
        
        # Test all endpoints
        for endpoint_name, endpoint_url in self.ENDPOINTS:
            result = self.test_endpoint_responsive(endpoint_name, endpoint_url)
            self.results[endpoint_name] = result
        
        self.generate_report()
        return True
    
    def generate_report(self):
        """Generate test report"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        self.log("\n\n" + "=" * 90, "REPORT")
        self.log("PHASE 2 RESPONSIVE DESIGN TESTING - FINAL REPORT", "REPORT")
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
        self.log("\n📋 DETAILED ENDPOINT RESULTS", "REPORT")
        self.log("-" * 90, "REPORT")
        
        for endpoint_name, result in self.results.items():
            status = "✅" if result["failed"] == 0 else "❌"
            self.log(f"{status} {endpoint_name:20} - Passed: {result['passed']}/6, Failed: {result['failed']}/6", "REPORT")
        
        # Complexity level summary
        self.log("\n📊 COMPLEXITY LEVEL SUMMARY", "REPORT")
        self.log("-" * 90, "REPORT")
        
        for complexity_name, complexity_info in self.COMPLEXITY_LEVELS.items():
            complexity_passed = sum(
                1 for result in self.results.values()
                if result["tests"].get(complexity_name, {}).get("passed", False)
            )
            self.log(f"  {complexity_name:10} ({complexity_info['device']:40}) - {complexity_passed}/7 endpoints ✅", "REPORT")
        
        # Performance targets
        self.log("\n🎯 PERFORMANCE TARGETS", "REPORT")
        self.log("-" * 90, "REPORT")
        for complexity_name, target in self.TARGETS.items():
            self.log(f"  {complexity_name:10} - Target: ≤ {target*1000:.0f}ms", "REPORT")
        
        # Success determination
        self.log("\n" + "=" * 90, "REPORT")
        if pass_rate >= 85:
            self.log("✅ RESPONSIVE DESIGN TESTS - PASSING", "REPORT")
            self.log(f"   {pass_rate:.1f}% pass rate meets success criteria (≥85%)", "REPORT")
        else:
            self.log("❌ RESPONSIVE DESIGN TESTS - NEEDS IMPROVEMENT", "REPORT")
            self.log(f"   {pass_rate:.1f}% pass rate below success criteria (≥85%)", "REPORT")
        self.log("=" * 90, "REPORT")
        
        # Save results to JSON
        report_data = {
            "phase": "Phase 2: Responsive Design Testing",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_tests": self.test_count,
                "passed": self.passed_count,
                "failed": self.failed_count,
                "pass_rate": pass_rate,
            },
            "endpoints": self.results,
        }
        
        with open("phase2_responsive_test_results.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"\n📄 Report saved to phase2_responsive_test_results.json\n", "REPORT")

if __name__ == "__main__":
    tester = ResponsiveAPITester()
    tester.run_all_tests()
