"""
Seed Supabase with minimal test data using direct SQL
Bypasses model constraints for quick testing
"""
from api.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("🌱 Seeding Supabase with test data...")
    
    # Insert products directly (bypassing organization_id constraint for testing)
    db.execute(text("""
        INSERT INTO products (id, sku, name, category, unit_price, source, is_dead_stock, created_at)
        VALUES 
            (1, 'TEST001', 'Test Product 1', 'Electronics', 100.00, 'manual', false, NOW()),
            (2, 'TEST002', 'Test Product 2', 'Electronics', 50.00, 'manual', false, NOW())
        ON CONFLICT (id) DO NOTHING
    """))
    
    # Insert inventory
    db.execute(text("""
        INSERT INTO inventory (product_id, current_stock, reserved_stock, available_stock, reorder_point, stock_status, last_updated)
        VALUES 
            (1, 100, 0, 100, 10, 'high', NOW()),
            (2, 100, 0, 100, 10, 'high', NOW())
        ON CONFLICT (product_id) DO NOTHING
    """))
    
    db.commit()
    
    # Verify
    result = db.execute(text("SELECT COUNT(*) FROM products"))
    product_count = result.scalar()
    
    result = db.execute(text("SELECT COUNT(*) FROM inventory"))
    inventory_count = result.scalar()
    
    print(f"✅ Seeded Supabase database:")
    print(f"   - {product_count} products")
    print(f"   - {inventory_count} inventory records")
    print("\n✅ Ready to test POS transactions!")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()
