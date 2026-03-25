import httpx
import asyncio
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"

async def test_priority_endpoints():
    print("\n=== STARTING PRIORITY ENDPOINT VERIFICATION ===\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Auth: Register
        email = f"test_user_{uuid.uuid4().hex[0:4]}@example.com"
        reg_payload = {
            "email": email,
            "full_name": "Test User",
            "password": "password123",
            "organization_name": f"Test Org {uuid.uuid4().hex[0:4]}",
            "role": "ADMIN"
        }
        res = await client.post(f"{BASE_URL}/auth/register", json=reg_payload)
        if res.status_code in [200, 201]:
            print("✅ Auth Register: Success")
        else:
            print(f"❌ Auth Register: Failed ({res.status_code}): {res.text}")
            return

        # 2. Auth: Login
        login_payload = {"email": email, "password": "password123"}
        res = await client.post(f"{BASE_URL}/auth/login", json=login_payload)
        if res.status_code == 200:
            token = res.json()["access_token"]
            print("✅ Auth Login: Success")
        else:
            print(f"❌ Auth Login: Failed ({res.status_code})")
            return
            
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Inventory: Fetch Store and Create Product
        # First get organization_id from /me
        me_res = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        org_id = me_res.json()["organization_id"]

        # Get real Store ID
        store_res = await client.get(f"{BASE_URL}/inventory/stores", headers=headers)
        if store_res.status_code == 200 and len(store_res.json()) > 0:
            store_id = store_res.json()[0]["id"]
            print(f"✅ Store Found: {store_id}")
        else:
            print(f"❌ Store Fetch: Failed ({store_res.status_code})")
            return

        prod_payload = {
            "sku": f"SKU-{uuid.uuid4().hex[0:4].upper()}",
            "name": "Test Product",
            "category": "Electronics",
            "unit_price": 99.99,
            "organization_id": org_id,
            "initial_stock": 50,
            "store_id": store_id
        }
        
        res = await client.post(f"{BASE_URL}/inventory/products", json=prod_payload, headers=headers)
        if res.status_code == 201:
            product_id = res.json()["id"]
            print("✅ Inventory Create: Success")
        else:
            print(f"❌ Inventory Create: Failed ({res.status_code}): {res.text}")

        # 4. Sales: Create Sale
        sale_payload = {
            "store_id": store_id,
            "items": [{"product_id": product_id, "quantity": 2, "unit_price": 99.99}],
            "payment_method": "upi"
        }
        res = await client.post(f"{BASE_URL}/sales/", json=sale_payload, headers=headers)
        if res.status_code == 201:
            print("✅ Sales Create: Success")
        else:
            print(f"❌ Sales Create: Failed ({res.status_code}): {res.text}")

        # 5. Customers: Create Customer
        cust_payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "9876543210",
            "organization_id": org_id
        }
        res = await client.post(f"{BASE_URL}/customers/", json=cust_payload, headers=headers)
        if res.status_code == 201:
            print("✅ Customer Create: Success")
        else:
            print(f"❌ Customer Create: Failed ({res.status_code})")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_priority_endpoints())
