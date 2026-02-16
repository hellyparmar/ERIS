#!/usr/bin/env python3
import requests
import json

API = "http://localhost:8000"

print("\n" + "="*80)
print("TESTING FIXES")
print("="*80)

# Test 1: Security Headers
print("\n✅ TEST 1: Security Headers")
r = requests.get(f"{API}/health")
headers_to_check = [
    "X-Content-Type-Options",
    "X-Frame-Options", 
    "Content-Security-Policy",
    "Strict-Transport-Security"
]

for header in headers_to_check:
    if header in r.headers:
        print(f"   ✅ {header}: {r.headers[header][:50]}...")
    else:
        print(f"   ❌ {header}: Missing")

# Test 2: Authentication  
print("\n✅ TEST 2: Authentication Login")
test_cases = [
    ("admin@rdios.local", "secret", "Email-based"),
    ("admin", "secret", "Username-based")
]

token = None
for username, password, label in test_cases:
    try:
        r = requests.post(
            f"{API}/auth/login",
            data={"username": username, "password": password}
        )
        
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            print(f"   ✅ {label} login SUCCESS")
            print(f"      Token: {token[:30]}...")
            break
        else:
            print(f"   ❌ {label} login: {r.status_code}")
    except Exception as e:
        print(f"   ❌ {label} error: {e}")

# Test 3: Analytics Endpoints
print("\n✅ TEST 3: Analytics Endpoints")
if token:
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/v1/analytics/metrics",
        "/api/v1/analytics/alerts",
        "/api/v1/analytics/chart-data"
    ]
    
    for endpoint in endpoints:
        try:
            r = requests.get(f"{API}{endpoint}", headers=headers, timeout=5)
            print(f"   {endpoint}: {r.status_code}")
        except:
            print(f"   {endpoint}: timeout")
else:
    print("   ⚠️  Skipping (no token obtained)")

# Test 4: Forecast (no auth)
print("\n✅ TEST 4: Core Endpoints (No Auth)")
endpoints = {
    "Dashboard": "/api/v1/dashboard/realtime",
    "Inventory": "/api/v1/inventory/list",
    "Forecast": "/api/forecasting/forecast/1/1?days=7"
}

for name, endpoint in endpoints.items():
    try:
        r = requests.get(f"{API}{endpoint}")
        symbol = "✅" if r.status_code == 200 else "❌"
        print(f"   {symbol} {name}: {r.status_code}")
    except:
        print(f"   ❌ {name}: timeout")

print("\n" + "="*80 + "\n")
