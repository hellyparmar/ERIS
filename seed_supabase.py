"""
Seed Supabase Database with Test Data
Creates minimal test data for POS transaction testing
"""
from api.db import SessionLocal
from api.db.models import Product, Inventory
from datetime import datetime

db = SessionLocal()

try:
    print("🌱 Seeding Supabase database...")
    
    # Create test products
    products = [
        Product(
            name="Test Product 1",
            sku="TEST001",
            category="Electronics",
            unit_price=100.0,
            created_at=datetime.now()
        ),
        Product(
            name="Test Product 2",
            sku="TEST002",
            category="Electronics",
            unit_price=50.0,
            created_at=datetime.now()
        )
    ]
    
    for p in products:
        db.add(p)
    db.flush()
    
    # Create inventory
    for p in products:
        inv = Inventory(
            product_id=p.id,
            current_stock=100,
            reserved_stock=0,
            available_stock=100,
            reorder_point=10,
            stock_status='high',
            last_updated=datetime.now()
        )
        db.add(inv)
    
    db.commit()
    
    print(f"✅ Seeded Supabase database:")
    print(f"   - {len(products)} products")
    print(f"   - {len(products)} inventory records")
    print("\n✅ Ready to test POS transactions!")

except Exception as e:
    db.rollback()
    print(f"❌ Error seeding database: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
