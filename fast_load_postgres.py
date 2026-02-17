#!/usr/bin/env python3
"""
Fast PostgreSQL data loader - generates 100K sales transactions
"""

import random
from datetime import datetime, timedelta
from sqlalchemy import text
import sys

sys.path.insert(0, "/home/petpooja/Enterprise Retail Intelligence System")
from api.db import engine

print("\n" + "="*60)
print(" R-DIOS Fast PostgreSQL Loader")
print("="*60 + "\n")

# Get default organization
with engine.connect() as conn:
    org_id = conn.execute(text("SELECT id FROM organizations LIMIT 1")).scalar()
    if not org_id:
        from uuid import uuid4
        org_id = str(uuid4())
        conn.execute(text("""
            INSERT INTO organizations (id, name, gstin, is_active, created_at)
            VALUES (:id, 'Default Org', '18AABCT1234H1Z5', TRUE, NOW())
        """), {"id": org_id})
        conn.commit()

print("📊 Generating test data...")

with engine.connect() as conn:
    # Clear
    conn.execute(text("TRUNCATE TABLE sales CASCADE"))
    conn.execute(text("TRUNCATE TABLE sale_items CASCADE"))
    conn.execute(text("TRUNCATE TABLE inventory CASCADE"))
    conn.execute(text("TRUNCATE TABLE products CASCADE"))
    conn.execute(text("TRUNCATE TABLE customers CASCADE"))
    
    # Create test products (simplified menu)
    products = [
        ("Butter Chicken", 350, 12),
        ("Paneer Tikka", 280, 5),
        ("Chicken Biryani", 320, 5),
        ("Masala Dosa", 140, 12),
        ("Idli Sambar", 80, 0),
        ("Hakka Noodles", 180, 12),
        ("Manchurian Chicken", 200, 5),
        ("Masala Chai", 40, 0),
        ("Mango Lassi", 80, 0),
        ("Gulab Jamun", 80, 12),
    ]
    
    for sku, (name, price, gst) in enumerate(products):
        conn.execute(text("""
            INSERT INTO products (sku, name, unit_price, cost_price, gst_rate, organization_id, created_at)
            VALUES (:sku, :name, :price, :cost, :gst, :org_id, NOW())
        """), {
            "sku": f"SKU-{sku:04d}",
            "name": name,
            "price": price,
            "cost": price * 0.4,
            "gst": gst,
            "org_id": org_id
        })
    
    conn.commit()
    print(f"  ✅ Created {len(products)} products")
    
    # Create test customers
    customer_names = ["Rajesh Kumar", "Priya Singh", "Amit Patel", "Deepika Sharma", "Vikram Reddy",
                     "Ananya Gupta", "Rohan Desai", "Neha Verma", "Arjun Nair", "Divya Chatterjee"]
    
    for i in range(5000):
        name = random.choice(customer_names) + f" {i//500}"
        conn.execute(text("""
            INSERT INTO customers (name, email, phone, city, customer_segment, organization_id, created_at)
            VALUES (:name, :email, :phone, :city, :segment, :org_id, NOW())
        """), {
            "name": name,
            "email": f"cust{i:05d}@example.com",
            "phone": f"9{random.randint(100000000, 999999999)}",
            "city": random.choice(["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad"]),
            "segment": random.choice(["regular", "occasional"]),
            "org_id": org_id
        })
        
        if (i + 1) % 1000 == 0:
            conn.commit()
    
    conn.commit()
    print(f"  ✅ Created 5,000 customers")
    
    # Get created customer IDs
    customer_ids = conn.execute(text("SELECT id FROM customers ORDER BY id")).fetchall()
    customer_ids = [row[0] for row in customer_ids]
    print(f"  Found customer IDs: {min(customer_ids)} to {max(customer_ids)}")
    
    # Create 100K sales transactions
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 6, 30)
    date_range = (end_date - start_date).days
    
    print(f"  💳 Creating 100,000 sales...")
    
    for txn_idx in range(100000):
        random_days = random.randint(0, date_range)
        txn_date = start_date + timedelta(days=random_days, hours=random.randint(8, 22))
        
        customer_id = random.choice(customer_ids)
        bill_amount = sum(random.choice(products)[1] for _ in range(random.randint(1, 6)))
        
        discount = 0
        if random.random() < 0.15:
            discount = int(bill_amount * random.choice([0.05, 0.10, 0.15, 0.20]))
            bill_amount -= discount
        
        tax = int(bill_amount * 0.05)
        total_amount = bill_amount + tax
        
        payment_method = random.choices(["cash", "card", "upi", "wallet"], weights=[0.40, 0.26, 0.24, 0.10])[0]
        
        conn.execute(text("""
            INSERT INTO sales (transaction_id, customer_id, transaction_date, discount, tax, total_amount, payment_method, source)
            VALUES (:txn_id, :cust_id, :date, :discount, :tax, :total, :payment, 'auto-generated')
        """), {
            "txn_id": f"TXN-{txn_idx:08d}",
            "cust_id": customer_id,
            "date": txn_date,
            "discount": discount,
            "tax": tax,
            "total": total_amount,
            "payment": payment_method
        })
        
        if (txn_idx + 1) % 10000 == 0:
            conn.commit()
            print(f"    {txn_idx+1:,} transactions...")
    
    conn.commit()
    print(f"  ✅ Created 100,000 sales transactions")

# ==================== VERIFY ====================
print("\n" + "="*60)
print(" VERIFICATION")
print("="*60)

with engine.connect() as conn:
    for table in ["products", "customers", "sales", "inventory"]:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"  {table:15s}: {count:>10,} rows")
    
    total_revenue = conn.execute(text("SELECT COALESCE(SUM(total_amount), 0) FROM sales")).scalar()
    print(f"\n  Total Revenue:    ₹{total_revenue:>10,.0f}")

print(f"\n{'='*60}")
print(" ✅ COMPLETE")
print(f"{'='*60}\n")
