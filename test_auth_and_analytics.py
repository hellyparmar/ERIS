#!/usr/bin/env python3
"""Test authentication and analytics endpoints"""

import requests
import json

API = "http://localhost:8000"

print("="*80)
print("AUTHENTICATION & ANALYTICS VERIFICATION")
print("="*80)

# Test 1: Get auth status
print("\n1. Testing Auth Status Endpoint...")
try:
    r = requests.get(f"{API}/auth/status", timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print(f"   ✅ Auth service active")
        data = r.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Test login with hardcoded users
print("\n2. Testing Login Endpoint...")
test_credentials = [
    ("admin", "secret"),
    ("user", "secret")
]

token = None
for username, password in test_credentials:
    try:
        r = requests.post(
            f"{API}/auth/login",
            data={"username": username, "password": password},
            timeout=5
        )
        print(f"   Login {username}: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            print(f"   ✅ Token received: {token[:20]}...")
            break
        else:
            print(f"   ❌ Response: {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Test 3: Test analytics endpoints without auth (should fail)
print("\n3. Testing Analytics Endpoints (NO AUTH - should fail)...")
analytics_endpoints = [
    "/api/v1/analytics/sales",
    "/api/v1/analytics/customers",
    "/api/v1/reports/revenue"
]

for endpoint in analytics_endpoints:
    try:
        r = requests.get(f"{API}{endpoint}", timeout=5)
        print(f"   {endpoint}: {r.status_code}")
        if r.status_code == 401:
            print(f"      ✅ Correctly requires auth (401)")
        elif r.status_code == 200:
            print(f"      ⚠️  Returns data without auth!")
        else:
            print(f"      ❓ Unexpected status")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Test 4: Test analytics with token (if we got one)
if token:
    print(f"\n4. Testing Analytics Endpoints WITH AUTH TOKEN...")
    headers = {"Authorization": f"Bearer {token}"}
    
    for endpoint in analytics_endpoints:
        try:
            r = requests.get(f"{API}{endpoint}", headers=headers, timeout=5)
            print(f"   {endpoint}: {r.status_code}")
            if r.status_code == 200:
                print(f"      ✅ Success with token")
            elif r.status_code == 401:
                print(f"      ❌ Still requires auth")
            else:
                print(f"      ⚠️  Status {r.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

# Test 5: Check weather endpoints
print(f"\n5. Testing Weather Endpoints...")
weather_endpoints = [
    "/api/weather/current",
    "/api/weather/forecast",
    "/api/openweather/current"
]

for endpoint in weather_endpoints:
    try:
        # Try with location parameter
        r = requests.get(f"{API}{endpoint}?location=New+York", timeout=5)
        print(f"   {endpoint}: {r.status_code}")
        if r.status_code == 200:
            print(f"      ✅ Working")
        elif r.status_code == 422:
            print(f"      ⚠️  Parameter validation error")
        elif r.status_code == 404:
            print(f"      ❌ Endpoint not found")
    except Exception as e:
        pass  # Endpoint may not exist

# Test 6: Check prediction endpoints
print(f"\n6. Testing Prediction Endpoints...")
prediction_endpoints = [
    ("/api/v1/forecast/predict", "POST"),
    ("/api/forecasting/forecast/1/1", "GET")
]

for endpoint, method in prediction_endpoints:
    try:
        if method == "GET":
            r = requests.get(f"{API}{endpoint}?days=7", timeout=5)
        else:
            r = requests.post(f"{API}{endpoint}", json={}, timeout=5)
        print(f"   {endpoint} ({method}): {r.status_code}")
        if r.status_code in [200, 201]:
            print(f"      ✅ Working")
        else:
            print(f"      Status: {r.status_code}")
    except Exception as e:
        pass

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)

