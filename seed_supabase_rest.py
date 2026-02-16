"""
Seed Supabase using REST API (faster than SQL connection)
Bypasses SQLAlchemy for direct API calls
"""
import os
import requests
import uuid
from dotenv import load_dotenv

load_dotenv('backend/.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    exit(1)

headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation,resolution=merge-duplicates'
}

print("🌱 Seeding Supabase via REST API...")

try:
    # 1. Create organization with client-generated UUID
    print("   Creating organization...")
    org_id = str(uuid.uuid4())
    
    org_response = requests.post(
        f'{SUPABASE_URL}/rest/v1/organizations',
        headers=headers,
        json={'id': org_id, 'name': 'Test Organization'}
    )
    
    if org_response.status_code in [200, 201]:
        print(f"   ✅ Organization created: {org_id}")
    else:
        print(f"   ❌ Organization creation failed: {org_response.status_code}")
        print(f"   Response: {org_response.text}")
        exit(1)
    
    # 2. Create store with UUID
    print("   Creating store...")
    store_id = str(uuid.uuid4())
    
    store_response = requests.post(
        f'{SUPABASE_URL}/rest/v1/stores',
        headers=headers,
        json={
            'id': store_id,
            'organization_id': org_id,
            'name': 'Main Store'
        }
    )
    
    if store_response.status_code in [200, 201]:
        print(f"   ✅ Store created: {store_id}")
    else:
        print(f"   ❌ Store creation failed: {store_response.status_code}")
        print(f"   Response: {store_response.text}")
        exit(1)
    
    # 3. Create products
    print("   Creating products...")
    products_response = requests.post(
        f'{SUPABASE_URL}/rest/v1/products',
        headers=headers,
        json=[
            {
                'id': 1,
                'sku': 'TEST001',
                'name': 'Test Product 1',
                'category': 'Electronics',
                'unit_price': 100.00,
                'organization_id': org_id
            },
            {
                'id': 2,
                'sku': 'TEST002',
                'name': 'Test Product 2',
                'category': 'Electronics',
                'unit_price': 50.00,
                'organization_id': org_id
            }
        ]
    )
    
    if products_response.status_code in [200, 201]:
        products = products_response.json()
        print(f"   ✅ Created {len(products)} products")
    else:
        print(f"   ❌ Products creation failed: {products_response.status_code}")
        print(f"   Response: {products_response.text}")
        exit(1)
    
    # 4. Create inventory with store_id
    print("   Creating inventory...")
    inventory_response = requests.post(
        f'{SUPABASE_URL}/rest/v1/inventory',
        headers=headers,
        json=[
            {
                'product_id': 1,
                'store_id': store_id,
                'current_stock': 100,
                'reorder_point': 10
            },
            {
                'product_id': 2,
                'store_id': store_id,
                'current_stock': 100,
                'reorder_point': 10
            }
        ]
    )
    
    if inventory_response.status_code in [200, 201]:
        inventory = inventory_response.json()
        print(f"   ✅ Created {len(inventory)} inventory records")
    else:
        print(f"   ❌ Inventory creation failed: {inventory_response.status_code}")
        print(f"   Response: {inventory_response.text}")
        exit(1)
    
    # 4. Verify data
    print("\n🔍 Verifying data...")
    
    products_count = requests.get(
        f'{SUPABASE_URL}/rest/v1/products?select=count',
        headers={**headers, 'Prefer': 'count=exact'}
    )
    
    inventory_count = requests.get(
        f'{SUPABASE_URL}/rest/v1/inventory?select=count',
        headers={**headers, 'Prefer': 'count=exact'}
    )
    
    print(f"   Products: {products_count.headers.get('Content-Range', '0').split('/')[-1]}")
    print(f"   Inventory: {inventory_count.headers.get('Content-Range', '0').split('/')[-1]}")
    
    print("\n✅ Supabase seeded successfully via REST API!")
    print("🎉 Ready to test POS transactions!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
