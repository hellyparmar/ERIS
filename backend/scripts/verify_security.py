import requests
import time
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def test_security():
    print("--- Starting Security Verification ---")
    
    # 1. Register a new user
    u_hex = uuid.uuid4().hex
    user_email = f"test_{u_hex[0:8]}@example.com"
    reg_payload = {
        "email": user_email,
        "password": "SecurePassword123!",
        "full_name": "Test User",
        "organization_id": 1,
        "role": "admin"
    }
    
    print(f"\n1. Testing Registration for {user_email}...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            return
    except Exception as e:
        print(f"Server connection failed: {e}")
        return

    # 2. Test Rate Limiting on Login
    print("\n2. Testing Rate Limiting (Login attempts)...")
    for i in range(7):
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": user_email, "password": "wrong"})
        print(f"Attempt {i+1}: {resp.status_code}")
        if resp.status_code == 429:
            print("✅ Rate limiting caught excessive login attempts!")
            break
    
    # 3. Successful Login
    print("\n3. Testing Successful Login...")
    login_data = {"username": user_email, "password": "SecurePassword123!"}
    resp = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if resp.status_code == 200:
        tokens = resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        print("✅ Login successful, tokens received.")
    else:
        print(f"❌ Login failed: {resp.text}")
        return

    # 4. Access Protected Route
    print("\n4. Testing Protected Route (/auth/me)...")
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if resp.status_code == 200:
        print(f"✅ Success: {resp.json()['email']}")
    else:
        print(f"❌ Protected route access failed: {resp.text}")

    # 5. Token Refresh
    print("\n5. Testing Token Refresh...")
    refresh_payload = {"refresh_token": refresh_token}
    resp = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_payload)
    if resp.status_code == 200:
        new_tokens = resp.json()
        new_access_token = new_tokens["access_token"]
        print("✅ Token refresh successful.")
    else:
        print(f"❌ Token refresh failed: {resp.text}")
        return

    # 6. Logout / Blacklisting
    print("\n6. Testing Logout (Blacklisting)...")
    headers = {"Authorization": f"Bearer {new_access_token}"}
    resp = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    if resp.status_code == 200:
        print("✅ Logout successful.")
    else:
        print(f"❌ Logout failed: {resp.text}")

    # 7. Access with Blacklisted Token
    print("\n7. Verifying Blacklisted Token...")
    resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if resp.status_code == 401:
        print("✅ Success: Blacklisted token rejected!")
    else:
        print(f"❌ Error: Blacklisted token still allowed! ({resp.status_code})")

    # 8. Test Error Format (404)
    print("\n[8] Testing Error Format (404)...")
    resp = requests.get(f"{BASE_URL}/api/v1/non-existent")
    if resp.status_code == 404:
        data = resp.json()
        if "error" in data and "code" in data["error"] and "timestamp" in data["error"]:
            print("  - SUCCESS: Error format is consistent JSON")
        else:
            print(f"  - FAILURE: Error format mismatch: {data}")
    else:
        print(f"  - FAILURE: Expected 404, got {resp.status_code}")

    # 9. Test Metrics Endpoint
    print("\n[9] Testing Metrics Endpoint...")
    resp = requests.get(f"{BASE_URL}/metrics")
    if resp.status_code == 200 and "api_requests_total" in resp.text:
        print("  - SUCCESS: Metrics endpoint is working")
    else:
        print(f"  - FAILURE: Metrics endpoint returned {resp.status_code}")

    print("\nAll security and monitoring tests completed!")

if __name__ == "__main__":
    test_security()
