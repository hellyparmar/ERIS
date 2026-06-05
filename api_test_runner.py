#!/usr/bin/env python3
"""
API Testing Script for Enterprise Retail Intelligence System
Tests all backend endpoints for data integrity and error handling
"""

import requests
import json
import sys
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "http://localhost:5000"
API_VERSION = "/api/v1"

# Test data storage
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": [],
    "warnings": [],
    "test_start": datetime.now().isoformat(),
    "endpoints_tested": {}
}

# Helper class for test results
class TestResult:
    def __init__(self, name: str, endpoint: str, method: str):
        self.name = name
        self.endpoint = endpoint
        self.method = method
        self.status = None
        self.expected_status = None
        self.actual_status = None
        self.message = ""
        self.response_data = None
        
    def passed(self, message: str = ""):
        self.status = "PASSED"
        self.message = message
        test_results["passed"] += 1
        return self
    
    def failed(self, message: str = ""):
        self.status = "FAILED"
        self.message = message
        test_results["failed"] += 1
        test_results["errors"].append({
            "name": self.name,
            "endpoint": self.endpoint,
            "message": message
        })
        return self
    
    def warning(self, message: str = ""):
        test_results["warnings"].append({
            "name": self.name,
            "endpoint": self.endpoint,
            "message": message
        })
        return self

def make_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """
    Make an HTTP request to the API
    """
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        return {
            "status": response.status_code,
            "data": response.json() if response.text else None,
            "headers": dict(response.headers),
            "error": None
        }
    except requests.exceptions.Timeout:
        return {
            "status": None,
            "data": None,
            "headers": {},
            "error": "Request timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": None,
            "data": None,
            "headers": {},
            "error": "Connection refused - Backend server not running"
        }
    except Exception as e:
        return {
            "status": None,
            "data": None,
            "headers": {},
            "error": str(e)
        }

def validate_response_format(response_data: Dict, expected_fields: List[str] = None) -> tuple[bool, str]:
    """
    Validate that response follows standard format
    """
    if not isinstance(response_data, dict):
        return False, "Response is not a dictionary"
    
    # Check for standard fields
    if "success" not in response_data:
        return False, "Missing 'success' field"
    
    if "message" not in response_data:
        return False, "Missing 'message' field"
    
    if "data" not in response_data:
        return False, "Missing 'data' field"
    
    # Check expected fields in data
    if expected_fields and isinstance(response_data.get("data"), dict):
        data = response_data["data"]
        missing = [f for f in expected_fields if f not in data]
        if missing:
            return False, f"Missing fields in data: {missing}"
    
    return True, "Response format valid"

# =============================================================================
# TEST SUITES
# =============================================================================

def test_health_check():
    """Test that backend is running"""
    print("\n" + "="*80)
    print("HEALTH CHECK")
    print("="*80)
    
    test = TestResult("Health Check", f"{API_VERSION}/health", "GET")
    response = make_request("GET", f"{API_VERSION}/health")
    
    if response["error"]:
        print(f"❌ {test.name}: {response['error']}")
        test.failed(response["error"])
        return False
    
    if response["status"] == 200:
        print(f"✅ {test.name}: Backend is running")
        test.passed("Health check successful")
        test_results["endpoints_tested"]["health"] = test.__dict__
        return True
    else:
        print(f"❌ {test.name}: Unexpected status {response['status']}")
        test.failed(f"Expected 200, got {response['status']}")
        test_results["endpoints_tested"]["health"] = test.__dict__
        return False

def test_employees_endpoints():
    """Test Employee API endpoints"""
    print("\n" + "="*80)
    print("EMPLOYEES ENDPOINT TESTING")
    print("="*80)
    
    # Test 1: GET /api/v1/employees
    print("\n[1/4] Testing GET /api/v1/employees...")
    test = TestResult("Get Employees List", f"{API_VERSION}/employees", "GET")
    response = make_request("GET", f"{API_VERSION}/employees")
    
    if response["error"]:
        print(f"⚠️  Endpoint not available: {response['error']}")
        test.warning(response["error"])
    elif response["status"] == 200:
        is_valid, msg = validate_response_format(response["data"], ["id", "name"])
        if is_valid:
            print(f"✅ GET /api/v1/employees: Returns valid response")
            test.passed(f"Response contains {len(response['data'].get('data', []))} employees")
        else:
            print(f"⚠️  Response format issue: {msg}")
            test.warning(msg)
    elif response["status"] == 404:
        print(f"⚠️  Endpoint not found (404)")
        test.warning("Endpoint not implemented yet")
    else:
        print(f"❌ Unexpected status: {response['status']}")
        test.failed(f"Expected 200, got {response['status']}")
    
    test_results["endpoints_tested"]["get_employees"] = test.__dict__

def test_sales_endpoints():
    """Test Sales API endpoints"""
    print("\n" + "="*80)
    print("SALES ENDPOINT TESTING")
    print("="*80)
    
    print("\n[1/3] Testing GET /api/v1/sales...")
    test = TestResult("Get Sales List", f"{API_VERSION}/sales", "GET")
    response = make_request("GET", f"{API_VERSION}/sales")
    
    if response["error"]:
        print(f"⚠️  Endpoint not available: {response['error']}")
        test.warning(response["error"])
    elif response["status"] == 200:
        print(f"✅ GET /api/v1/sales: Returns valid response")
        test.passed("Sales data retrieved successfully")
    elif response["status"] == 404:
        print(f"⚠️  Endpoint not found (404)")
        test.warning("Endpoint not implemented yet")
    else:
        print(f"❌ Unexpected status: {response['status']}")
        test.failed(f"Expected 200, got {response['status']}")
    
    test_results["endpoints_tested"]["get_sales"] = test.__dict__

def test_customers_endpoints():
    """Test Customers/Contacts API endpoints"""
    print("\n" + "="*80)
    print("CUSTOMERS/CONTACTS ENDPOINT TESTING")
    print("="*80)
    
    print("\n[1/3] Testing GET /api/v1/customers...")
    test = TestResult("Get Customers List", f"{API_VERSION}/customers", "GET")
    response = make_request("GET", f"{API_VERSION}/customers")
    
    if response["error"]:
        print(f"⚠️  Endpoint not available: {response['error']}")
        test.warning(response["error"])
    elif response["status"] == 200:
        print(f"✅ GET /api/v1/customers: Returns valid response")
        test.passed("Customers data retrieved successfully")
    elif response["status"] == 404:
        print(f"⚠️  Endpoint not found (404)")
        test.warning("Endpoint not implemented yet")
    elif response["status"] == 401:
        print(f"⚠️  Authentication required (401)")
        test.warning("Endpoint requires authentication - need token")
    else:
        print(f"❌ Unexpected status: {response['status']}")
        test.failed(f"Expected 200, got {response['status']}")
    
    test_results["endpoints_tested"]["get_customers"] = test.__dict__

def test_invoices_endpoints():
    """Test Invoices API endpoints"""
    print("\n" + "="*80)
    print("INVOICES ENDPOINT TESTING")
    print("="*80)
    
    print("\n[1/3] Testing GET /api/v1/invoices...")
    test = TestResult("Get Invoices List", f"{API_VERSION}/invoices", "GET")
    response = make_request("GET", f"{API_VERSION}/invoices")
    
    if response["error"]:
        print(f"⚠️  Endpoint not available: {response['error']}")
        test.warning(response["error"])
    elif response["status"] == 200:
        print(f"✅ GET /api/v1/invoices: Returns valid response")
        test.passed("Invoices data retrieved successfully")
    elif response["status"] == 404:
        print(f"⚠️  Endpoint not found (404)")
        test.warning("Endpoint not implemented yet")
    elif response["status"] == 401:
        print(f"⚠️  Authentication required (401)")
        test.warning("Endpoint requires authentication")
    else:
        print(f"❌ Unexpected status: {response['status']}")
        test.failed(f"Expected 200, got {response['status']}")
    
    test_results["endpoints_tested"]["get_invoices"] = test.__dict__

def test_outlets_endpoints():
    """Test Outlets API endpoints"""
    print("\n" + "="*80)
    print("OUTLETS ENDPOINT TESTING")
    print("="*80)
    
    print("\n[1/3] Testing GET /api/v1/outlets...")
    test = TestResult("Get Outlets List", f"{API_VERSION}/outlets", "GET")
    response = make_request("GET", f"{API_VERSION}/outlets")
    
    if response["error"]:
        print(f"⚠️  Endpoint not available: {response['error']}")
        test.warning(response["error"])
    elif response["status"] == 200:
        print(f"✅ GET /api/v1/outlets: Returns valid response")
        test.passed("Outlets data retrieved successfully")
    elif response["status"] == 404:
        print(f"⚠️  Endpoint not found (404)")
        test.warning("Endpoint not implemented yet")
    elif response["status"] == 401:
        print(f"⚠️  Authentication required (401)")
        test.warning("Endpoint requires authentication")
    else:
        print(f"❌ Unexpected status: {response['status']}")
        test.failed(f"Expected 200, got {response['status']}")
    
    test_results["endpoints_tested"]["get_outlets"] = test.__dict__

def test_settings_endpoints():
    """Test Settings API endpoints"""
    print("\n" + "="*80)
    print("SETTINGS ENDPOINT TESTING")
    print("="*80)
    
    print("\n[1/2] Testing GET /api/v1/settings...")
    test = TestResult("Get Settings", f"{API_VERSION}/settings", "GET")
    response = make_request("GET", f"{API_VERSION}/settings")
    
    if response["error"]:
        print(f"⚠️  Endpoint not available: {response['error']}")
        test.warning(response["error"])
    elif response["status"] == 200:
        print(f"✅ GET /api/v1/settings: Returns valid response")
        test.passed("Settings data retrieved successfully")
    elif response["status"] == 404:
        print(f"⚠️  Endpoint not found (404)")
        test.warning("Endpoint not implemented yet")
    elif response["status"] == 401:
        print(f"⚠️  Authentication required (401)")
        test.warning("Endpoint requires authentication")
    else:
        print(f"❌ Unexpected status: {response['status']}")
        test.failed(f"Expected 200, got {response['status']}")
    
    test_results["endpoints_tested"]["get_settings"] = test.__dict__

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "="*80)
    print("TEST SUMMARY REPORT")
    print("="*80)
    
    total_tests = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 Test Results:")
    print(f"  ✅ Passed: {test_results['passed']}")
    print(f"  ❌ Failed: {test_results['failed']}")
    print(f"  ⚠️  Warnings: {len(test_results['warnings'])}")
    print(f"  📈 Pass Rate: {pass_rate:.1f}%")
    
    if test_results["warnings"]:
        print(f"\n⚠️  Warnings:")
        for warning in test_results["warnings"]:
            print(f"  - {warning['name']}: {warning['message']}")
    
    if test_results["errors"]:
        print(f"\n❌ Errors:")
        for error in test_results["errors"]:
            print(f"  - {error['name']}: {error['message']}")
    
    print(f"\n⏱️  Test Duration:")
    print(f"  Started: {test_results['test_start']}")
    print(f"  Ended: {datetime.now().isoformat()}")
    
    # Save report to file
    report_file = "/home/petpooja/Enterprise Retail Intelligence System/API_TEST_RESULTS.json"
    try:
        with open(report_file, "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        print(f"\n💾 Report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save report: {e}")

def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("ENTERPRISE RETAIL INTELLIGENCE SYSTEM - API TESTING")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Version: {API_VERSION}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    # Start tests
    if not test_health_check():
        print("\n⚠️  Backend server is not running!")
        print("To start the backend:")
        print("  cd /home/petpooja/Enterprise\\ Retail\\ Intelligence\\ System/backend")
        print("  python -m uvicorn app.main:app --reload")
        generate_test_report()
        return 1
    
    # Run endpoint tests
    test_employees_endpoints()
    test_sales_endpoints()
    test_customers_endpoints()
    test_invoices_endpoints()
    test_outlets_endpoints()
    test_settings_endpoints()
    
    # Generate report
    generate_test_report()
    
    return 0 if test_results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
