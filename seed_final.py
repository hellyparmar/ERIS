"""Final working seed script for Supabase"""
from api.db import SessionLocal
from sqlalchemy import text

print("🌱 Seeding Supabase...")

db = SessionLocal()

try:
    # Insert organization with UUID using gen_random_uuid()
    result = db.execute(text("""
        INSERT INTO organizations (id, name, created_at) 
        VALUES (gen_random_uuid(), 'Test Org', NOW()) 
        RETURNING id
    """))
    org_id = result.scalar()
    print(f"✅ Created organization: {org_id}")
    
    # Insert products with organization UUID
    db.execute(text(f"""
        INSERT INTO products (id, sku, name, category, unit_price, organization_id, created_at) 
        VALUES 
            (1, 'TEST001', 'Product 1', 'Electronics', 100, '{org_id}', NOW()),
            (2, 'TEST002', 'Product 2', 'Electronics', 50, '{org_id}', NOW())
        ON CONFLICT (id) DO NOTHING
    """))
    print("✅ Created 2 products")
    
    # Insert inventory
    db.execute(text("""
        INSERT INTO inventory (product_id, current_stock, reorder_point, last_updated) 
        VALUES 
            (1, 100, 10, NOW()),
            (2, 100, 10, NOW())
        ON CONFLICT (product_id) DO NOTHING
    """))
    print("✅ Created 2 inventory records")
    
    db.commit()
    print("✅ Committed to Supabase")
    
    # Verify
    r = db.execute(text("SELECT COUNT(*) FROM products"))
    print(f"✅ Products: {r.scalar()}")
    r = db.execute(text("SELECT COUNT(*) FROM inventory"))
    print(f"✅ Inventory: {r.scalar()}")
    
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
