import requests
import json

BASE_URL = "http://localhost:8000"

users = {
    "super_admin": {
        "username": "super_admin_test@rdios.com",
        "password": "password123"
    },
    "area_manager": {
        "username": "area_manager_test@rdios.com",
        "password": "password123"
    },
    "outlet_manager": {
        "username": "outlet_manager_test@rdios.com",
        "password": "password123"
    }
}

def get_token(username, password):
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={
        "username": username,
        "password": password
    })
    if resp.status_code != 200:
        print(f"Failed to login {username}: {resp.status_code} - {resp.text}")
        return None
    return resp.json()["access_token"]

def main():
    tokens = {}
    for role, creds in users.items():
        token = get_token(creds["username"], creds["password"])
        if token:
            tokens[role] = token
            print(f"Logged in as {role} successfully.")
            
    print("\n" + "="*50)
    print("TESTING ENDPOINT: /api/v1/dashboard/summary")
    print("="*50)
    for role, token in tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/api/v1/dashboard/summary", headers=headers)
        print(f"[{role}] Status: {resp.status_code}")
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        else:
            print(resp.text)
            
    print("\n" + "="*50)
    print("TESTING ENDPOINT: /api/v1/inventory/summary")
    print("="*50)
    for role, token in tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/api/v1/inventory/summary", headers=headers)
        print(f"[{role}] Status: {resp.status_code}")
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        else:
            print(resp.text)

    print("\n" + "="*50)
    print("TESTING ENDPOINT: /api/v1/inventory (Row counts)")
    print("="*50)
    for role, token in tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/api/v1/inventory", headers=headers)
        print(f"[{role}] Status: {resp.status_code}")
        if resp.status_code == 200:
            items = resp.json()
            print(f"[{role}] Total Inventory items returned: {len(items)}")
            if items:
                outlets_seen = set(item.get("outlet_name") for item in items)
                print(f"[{role}] Outlets present in response: {outlets_seen}")
        else:
            print(resp.text)

    print("\n" + "="*50)
    print("TESTING ENDPOINT: /api/analytics/sales/summary")
    print("="*50)
    for role, token in tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/api/analytics/sales/summary?start_date=2020-01-01&end_date=2026-12-31", headers=headers)
        print(f"[{role}] Status: {resp.status_code}")
        if resp.status_code == 200:
            metrics = resp.json().get("metrics", {})
            print(f"[{role}] Total Orders: {metrics.get('total_orders')}, Total Revenue: {metrics.get('total_revenue')}")
        else:
            print(resp.text)

if __name__ == '__main__':
    main()
