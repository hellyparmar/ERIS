#!/usr/bin/env python3
"""
R-DIOS Comprehensive System Test Suite
Tests database, API endpoints, and system functionality
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_endpoint():
    """Test 1: Health Check"""
    print("TEST 1: Health Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Status: {data.get('status')}, Version: {data.get('version')}")
            return True
        else:
            print(f"❌ FAIL - Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_auth_login():
    """Test 2: Authentication"""
    print("\nTEST 2: Authentication (Login)")
    try:
        # Try multiple possible credentials
        credentials = [
            ("admin@petpooja.com", "admin123"),
            ("admin", "admin123"),
            ("test@test.com", "test123")
        ]
        
        for email, password in credentials:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                data={"username": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                print(f"✅ PASS - Logged in as: {email}")
                print(f"   Token: {token[:50]}...")
                return True, token
            
        print(f"❌ FAIL - No valid credentials found")
        print(f"   Last response: {response.text[:200]}")
        return False, None
        
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False, None

def test_enterprise_endpoint(token=None):
    """Test 3: Enterprise Overview Endpoint"""
    print("\nTEST 3: Enterprise Overview API")
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        response = requests.get(f"{BASE_URL}/api/enterprise/overview", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Retrieved {len(data)} stores")
            if data:
                print(f"   Sample: {data[0].get('name')} - Revenue: ₹{data[0].get('revenue', 0):,.0f}")
            return True
        elif response.status_code == 401:
            print(f"⚠️  SKIP - Authentication required (expected without token)")
            return None
        else:
            print(f"❌ FAIL - Status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_customer_rfm_endpoint(token=None):
    """Test 4: Customer RFM Summary"""
    print("\nTEST 4: Customer RFM Summary API")
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        response = requests.get(f"{BASE_URL}/api/analytics/customers/rfm/summary", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total_customers", 0)
            revenue = data.get("total_revenue", 0)
            print(f"✅ PASS - Total Customers: {total:,}, Revenue: ₹{revenue:,.0f}")
            segments = data.get("segments", [])
            if segments:
                print(f"   Segments: {len(segments)} found")
            return True
        elif response.status_code == 401:
            print(f"⚠️  SKIP - Authentication required")
            return None
        else:
            print(f"❌ FAIL - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_database_connection():
    """Test 5: Database Connection (via Python)"""
    print("\nTEST 5: Database Connection")
    try:
        import sys
        sys.path.insert(0, '/home/petpooja/Enterprise Retail Intelligence System')
        from api.db.database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        result = db.execute(text("SELECT COUNT(*) FROM stores")).scalar()
        print(f"✅ PASS - Database connected, {result} stores found")
        db.close()
        return True
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def main():
    print_section("R-DIOS SYSTEM TEST SUITE")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # Test 1: Health
    print_section("BACKEND HEALTH")
    result = test_health_endpoint()
    results["total"] += 1
    if result:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 2: Auth
    print_section("AUTHENTICATION")
    auth_result, token = test_auth_login()
    results["total"] += 1
    if auth_result:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 3-4: API Endpoints
    print_section("API ENDPOINTS")
    
    for test_func in [test_enterprise_endpoint, test_customer_rfm_endpoint]:
        result = test_func(token)
        results["total"] += 1
        if result is True:
            results["passed"] += 1
        elif result is False:
            results["failed"] += 1
        else:
            results["skipped"] += 1
    
    # Test 5: Database
    print_section("DATABASE")
    result = test_database_connection()
    results["total"] += 1
    if result:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⚠️  Skipped: {results['skipped']}")
    
    pass_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"\nPass Rate: {pass_rate:.1f}%")
    
    if pass_rate >= 80:
        print("\n🎉 SYSTEM STATUS: READY")
    elif pass_rate >= 50:
        print("\n⚠️  SYSTEM STATUS: PARTIALLY READY")
    else:
        print("\n❌ SYSTEM STATUS: NOT READY")

if __name__ == "__main__":
    main()
