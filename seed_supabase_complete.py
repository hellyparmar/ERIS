"""
Complete Supabase Seed Script
Creates organization, products, and inventory with proper foreign keys
"""
from api.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("🌱 Seeding Supabase database with complete data...")
    
    # 1. Create organization
    db.execute(text("""
        INSERT INTO organizations (id, name, email, phone, address, created_at)
        VALUES (1, 'Test Retail Store', 'test@retail.com', '1234567890', '123 Test St', NOW())
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
    """))
    print("   ✅ Created organization")
    
    # 2. Create products with organization_id
    db.execute(text("""
        INSERT INTO products (id, sku, name, category, unit_price, source, is_dead_stock, organization_id, created_at)
        VALUES 
            (1, 'TEST001', 'Test Product 1', 'Electronics', 100.00, 'manual', false, 1, NOW()),
            (2, 'TEST002', 'Test Product 2', 'Electronics', 50.00, 'manual', false, 1, NOW())
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
    """))
    print("   ✅ Created 2 products")
    
    # 3. Create inventory
    db.execute(text("""
        INSERT INTO inventory (product_id, current_stock, reserved_stock, available_stock, reorder_point, stock_status, last_updated)
        VALUES 
            (1, 100, 0, 100, 10, 'high', NOW()),
            (2, 100, 0, 100, 10, 'high', NOW())
        ON CONFLICT (product_id) DO UPDATE SET current_stock = EXCLUDED.current_stock
    """))
    print("   ✅ Created 2 inventory records")
    
    db.commit()
    
    # Verify
    result = db.execute(text("SELECT COUNT(*) FROM organizations"))
    org_count = result.scalar()
    
    result = db.execute(text("SELECT COUNT(*) FROM products"))
    product_count = result.scalar()
    
    result = db.execute(text("SELECT COUNT(*) FROM inventory"))
    inventory_count = result.scalar()
    
    print(f"\n✅ Supabase database seeded successfully:")
    print(f"   - {org_count} organization(s)")
    print(f"   - {product_count} products")
    print(f"   - {inventory_count} inventory records")
    print("\n🎉 Ready to test POS transactions on Supabase!")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
