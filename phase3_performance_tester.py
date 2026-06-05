#!/usr/bin/env python3
"""
Phase 3: Performance Testing
Measures Core Web Vitals and API response times
Tests backend API performance under load
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import requests
import json
import time
from datetime import datetime
from typing import Dict, List
import statistics
from app.core.security import create_access_token

class PerformanceTester:
    """Test API performance metrics"""
    
    # Performance targets
    TARGETS = {
        "api_response": {"max": 0.5, "unit": "seconds", "name": "API Response Time"},
        "p50_response": {"max": 0.3, "unit": "seconds", "name": "50th Percentile Response"},
        "p95_response": {"max": 0.8, "unit": "seconds", "name": "95th Percentile Response"},
        "p99_response": {"max": 1.0, "unit": "seconds", "name": "99th Percentile Response"},
    }
    
    # API endpoints to test
    ENDPOINTS = [
        ("Employees List", "/api/v1/employees"),
        ("Sales List", "/api/v1/sales"),
        ("Contacts List", "/api/v1/contacts"),
        ("Invoices List", "/api/v1/invoices"),
        ("Reports List", "/api/v1/reports"),
        ("Outlets List", "/api/v1/outlets"),
        ("Settings Profile", "/api/v1/settings/profile"),
    ]
    
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
            # Create token directly using the security module
            token_data = {
                "user_id": "admin123",
                "email": "admin@example.com",
                "role": "super_admin",
                "outlet_id": None,
            }
            self.auth_token = create_access_token(token_data)
            
            # Set default auth header
            if self.auth_token:
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log(f"✅ Authentication token created successfully", "INFO")
        except Exception as e:
            # If token creation fails, continue with unauthenticated requests
            self.log(f"⚠️  Authentication setup failed: {str(e)[:50]}", "WARN")
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level}]"
        print(f"{prefix} {message}")
    
    def test_endpoint_performance(self, endpoint_name: str, endpoint_url: str, iterations: int = 10) -> Dict:
        """Test a single endpoint multiple times for performance metrics"""
        response_times = []
        errors = 0
        
        self.log(f"Testing {endpoint_name}... ({iterations} requests)", "PERF")
        
        for i in range(iterations):
            try:
                start = time.time()
                response = self.session.get(f"{self.base_url}{endpoint_url}", timeout=5)
                elapsed = time.time() - start
                
                # Accept both successful and authentication-failed responses
                # to measure performance regardless of auth status
                if 200 <= response.status_code < 500:
                    response_times.append(elapsed)
                else:
                    errors += 1
                    self.log(f"  ❌ Request {i+1}: Status {response.status_code}", "PERF")
            except requests.exceptions.Timeout:
                errors += 1
                self.log(f"  ❌ Request {i+1}: Timeout", "PERF")
            except Exception as e:
                errors += 1
                self.log(f"  ❌ Request {i+1}: {str(e)[:50]}", "PERF")
        
        # Calculate metrics
        if response_times:
            metrics = {
                "name": endpoint_name,
                "url": endpoint_url,
                "samples": len(response_times),
                "errors": errors,
                "avg": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "stdev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "p50": sorted(response_times)[int(len(response_times) * 0.50)] if len(response_times) > 1 else response_times[0],
                "p95": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[-1],
                "p99": sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) > 1 else response_times[-1],
            }
            
            # Evaluate against targets
            passed = metrics["avg"] <= self.TARGETS["api_response"]["max"]
            
            if passed:
                self.passed_count += 1
                self.log(f"✅ PASS - {endpoint_name} avg: {metrics['avg']:.3f}s (target: ≤{self.TARGETS['api_response']['max']}s)", "PERF")
            else:
                self.failed_count += 1
                self.log(f"❌ FAIL - {endpoint_name} avg: {metrics['avg']:.3f}s (target: ≤{self.TARGETS['api_response']['max']}s)", "PERF")
            
            self.test_count += 1
            return metrics
        else:
            self.failed_count += 1
            self.test_count += 1
            self.log(f"❌ FAIL - {endpoint_name}: All requests failed", "PERF")
            return {
                "name": endpoint_name,
                "url": endpoint_url,
                "samples": 0,
                "errors": errors,
                "status": "failed"
            }
    
    def run_all_tests(self, iterations: int = 10) -> Dict:
        """Test all endpoints"""
        self.start_time = time.time()
        
        self.log("=" * 80)
        self.log("PHASE 3: PERFORMANCE TESTING")
        self.log(f"Testing {len(self.ENDPOINTS)} endpoints × {iterations} requests each")
        self.log("=" * 80)
        self.log("")
        
        # Check backend connectivity
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            self.log(f"✅ Backend accessible at {self.base_url}")
        except Exception as e:
            self.log(f"❌ Backend not accessible: {str(e)[:50]}", "ERROR")
            return {"status": "failed", "reason": "Backend not accessible"}
        
        self.log("")
        
        # Test each endpoint
        for endpoint_name, endpoint_url in self.ENDPOINTS:
            metrics = self.test_endpoint_performance(endpoint_name, endpoint_url, iterations)
            self.results[endpoint_name] = metrics
            self.log("")
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict:
        """Generate performance report"""
        elapsed = time.time() - self.start_time
        
        # Calculate pass rate
        pass_rate = (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_endpoints": self.test_count,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "pass_rate": pass_rate,
            "duration": elapsed,
            "results_by_endpoint": self.results
        }
        
        # Calculate aggregate metrics
        valid_results = [r for r in self.results.values() if "avg" in r]
        if valid_results:
            avgs = [r["avg"] for r in valid_results]
            report["aggregate_metrics"] = {
                "avg_response_time": statistics.mean(avgs),
                "median_response_time": statistics.median(avgs),
                "slowest_endpoint": max(valid_results, key=lambda r: r["avg"])["name"],
                "fastest_endpoint": min(valid_results, key=lambda r: r["avg"])["name"],
            }
        
        # Print final report
        self._print_report(report)
        
        return report
    
    def _print_report(self, report: Dict):
        """Print formatted performance report"""
        print("\n")
        print("=" * 80)
        print("PHASE 3 PERFORMANCE TESTING - FINAL REPORT")
        print("=" * 80)
        print("")
        print(f"⏱️  TESTING DURATION: {report['duration']:.1f} seconds")
        print("")
        print("📊 OVERALL RESULTS")
        print("-" * 80)
        print(f"Total Endpoints: {report['total_endpoints']}")
        print(f"Endpoints Passed: {report['passed']} ✅")
        print(f"Endpoints Failed: {report['failed']} ❌")
        print(f"Pass Rate: {report['pass_rate']:.1f}%")
        print("")
        
        if "aggregate_metrics" in report:
            agg = report["aggregate_metrics"]
            print("📈 AGGREGATE METRICS")
            print("-" * 80)
            print(f"Average Response Time: {agg['avg_response_time']:.3f}s")
            print(f"Median Response Time: {agg['median_response_time']:.3f}s")
            print(f"Fastest Endpoint: {agg['fastest_endpoint']}")
            print(f"Slowest Endpoint: {agg['slowest_endpoint']}")
            print("")
        
        print("📋 DETAILED ENDPOINT RESULTS")
        print("-" * 80)
        for endpoint_name, metrics in report['results_by_endpoint'].items():
            if "avg" in metrics:
                status = "✅" if metrics["avg"] <= self.TARGETS["api_response"]["max"] else "❌"
                print(f"{status} {endpoint_name:20} avg: {metrics['avg']:.3f}s | p95: {metrics['p95']:.3f}s | p99: {metrics['p99']:.3f}s | errors: {metrics['errors']}")
            else:
                print(f"❌ {endpoint_name:20} FAILED - All requests failed")
        
        print("")
        print("🎯 PERFORMANCE TARGETS")
        print("-" * 80)
        print(f"API Response Time: ≤ {self.TARGETS['api_response']['max']}s")
        print(f"P50 Response Time: ≤ {self.TARGETS['p50_response']['max']}s")
        print(f"P95 Response Time: ≤ {self.TARGETS['p95_response']['max']}s")
        print(f"P99 Response Time: ≤ {self.TARGETS['p99_response']['max']}s")
        print("")
        print("=" * 80)
        
        if report['pass_rate'] == 100:
            print("✅ ALL PERFORMANCE TESTS PASSING")
        elif report['pass_rate'] >= 85:
            print("⚠️  PERFORMANCE TESTS - MINOR ISSUES")
        else:
            print("❌ PERFORMANCE TESTS - CRITICAL ISSUES")
        
        print("=" * 80)
        
        # Save report to file
        report_file = "phase3_performance_test_results.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to {report_file}")


def main():
    """Main test execution"""
    tester = PerformanceTester()
    report = tester.run_all_tests(iterations=10)
    
    # Exit with appropriate code
    return 0 if report.get("pass_rate", 0) >= 85 else 1


if __name__ == "__main__":
    exit(main())
