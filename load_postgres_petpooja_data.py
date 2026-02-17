#!/usr/bin/env python3
"""
Load Petpooja synthetic data directly into PostgreSQL
Generates 100,000+ realistic restaurant transactions
"""

import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

sys.path.insert(0, "/home/petpooja/Enterprise Retail Intelligence System")
from api.db import Base, get_db

# ==================== INDIAN RESTAURANT DATA ====================

PETPOOJA_STORES = [
    {"id": 1, "name": "Petpooja - Mumbai Central", "city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"id": 2, "name": "Petpooja - Delhi NCR", "city": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"id": 3, "name": "Petpooja - Bangalore", "city": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"id": 4, "name": "Petpooja - Hyderabad", "city": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"id": 5, "name": "Petpooja - Chennai", "city": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"id": 6, "name": "Petpooja - Pune", "city": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"id": 7, "name": "Petpooja - Kolkata", "city": "Kolkata", "lat": 22.5726, "lon": 88.3639},
    {"id": 8, "name": "Petpooja - Ahmedabad", "city": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
]

MENU_ITEMS = {
    "North Indian": [
        ("Butter Chicken", 350),
        ("Paneer Tikka", 280),
        ("Chicken Biryani", 320),
        ("Lamb Rogan Josh", 400),
        ("Tandoori Chicken", 300),
        ("Naan (Plain)", 40),
        ("Garlic Naan", 60),
        ("Butter Naan", 60),
        ("Paneer Naan", 80),
        ("Roti", 20),
        ("Dal Makhani", 180),
        ("Paneer Butter Masala", 300),
        ("Chole Bhature", 150),
        ("Aloo Paratha", 100),
        ("Goat Curry", 380),
        ("Shahi Tukda", 120),
        ("Haleem", 280),
        ("Seekh Kebab", 200),
    ],
    "South Indian": [
        ("Masala Dosa", 140),
        ("Idli Sambar", 80),
        ("Vada Sambar", 90),
        ("Uttapam", 120),
        ("Chole Puri", 100),
        ("Appam with Curry", 110),
        ("Puttu Curry", 100),
        ("Sambar", 60),
        ("Rasam", 50),
        ("Coconut Chutney", 30),
        ("Mint Chutney", 30),
        ("Fish Curry Kerala", 320),
        ("Avial", 140),
        ("Vegetable Stew", 130),
        ("Payasam", 80),
    ],
    "Chinese": [
        ("Hakka Noodles", 180),
        ("Fried Rice", 160),
        ("Chow Mein", 170),
        ("Manchurian (Veg)", 150),
        ("Manchurian (Chicken)", 200),
        ("Spring Rolls", 120),
        ("Sweet & Sour Pork", 250),
        ("Chicken Manchurian", 200),
        ("Vegetable Soup", 80),
        ("Hot & Sour Soup", 90),
    ],
    "Beverages": [
        ("Masala Chai", 40),
        ("Ginger Chai", 50),
        ("Coffee", 60),
        ("Cold Coffee", 100),
        ("Mango Lassi", 80),
        ("Buttermilk", 50),
        ("Lemonade", 40),
        ("Fresh Orange Juice", 120),
        ("Sugarcane Juice", 60),
        ("Iced Tea", 70),
        ("Mineral Water (500ml)", 30),
        ("Soft Drink (Cola)", 50),
        ("Mango Shake", 90),
        ("Strawberry Shake", 90),
    ],
    "Desserts": [
        ("Gulab Jamun", 80),
        ("Kheer", 100),
        ("Jalebi", 60),
        ("Rasgulla", 70),
        ("Barfi", 90),
        ("Laddu", 60),
        ("Ice Cream", 100),
        ("Flan", 110),
        ("Brownie", 120),
        ("Cake Slice", 130),
    ],
}

PAYMENT_METHODS = ["cash", "card", "upi", "wallet"]
CUSTOMER_NAMES = [
    "Rajesh Kumar", "Priya Singh", "Amit Patel", "Deepika Sharma", "Vikram Reddy",
    "Ananya Gupta", "Rohan Desai", "Neha Verma", "Arjun Nair", "Divya Chatterjee",
    "Sanjay Menon", "Pooja Rao", "Aditya Bhat", "Shreya Joshi", "Nikhil Kapoor",
    "Isha Malhotra", "Varun Chopra", "Sneha Bhandari", "Karan Singh", "Manvi Nanda",
]

def get_seasonal_multiplier(date):
    """Get demand multiplier based on Indian festivals and seasons"""
    month = date.month
    if month in [10, 11]:
        return 2.5
    if month in [2, 3]:
        return 1.8
    if month in [12, 1]:
        return 1.5
    if month in [4, 5, 6]:
        return 1.2
    return 1.0

def generate_data(num_transactions=100000):
    """Generate and load Petpooja synthetic dataset into PostgreSQL"""
    
    print(f"\n{'='*60}")
    print(" R-DIOS PostgreSQL Data Loader")
    print(f"{'='*60}\n")
    
    from api.db import engine
    
    db = next(get_db())
    
    # ==================== CLEAR EXISTING DATA ====================
    print("🧹 Clearing existing data...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE sales CASCADE"))
        conn.execute(text("TRUNCATE TABLE sale_items CASCADE"))
        conn.execute(text("TRUNCATE TABLE inventory CASCADE"))
        conn.execute(text("TRUNCATE TABLE products CASCADE"))
        conn.execute(text("TRUNCATE TABLE customers CASCADE"))
        conn.commit()
    print("  ✅ Cleared old data")
    
    # ==================== CREATE PRODUCTS ====================
    print("🍽️  Creating menu items...")
    product_id = 1
    products = []
    with engine.connect() as conn:
        for category, items in MENU_ITEMS.items():
            for name, price in items:
                conn.execute(text("""
                    INSERT INTO products (id, name, category, price, sku, is_active, created_at)
                    VALUES (:id, :name, :category, :price, :sku, TRUE, NOW())
                """), {
                    "id": product_id,
                    "name": name,
                    "category": category,
                    "price": price,
                    "sku": f"SKU-{product_id:04d}"
                })
                products.append({"id": product_id, "name": name, "price": price})
                product_id += 1
        conn.commit()
    print(f"  ✅ Created {len(products)} menu items")
    
    # ==================== CREATE CUSTOMERS ====================
    print("👥 Creating customers...")
    customers = []
    with engine.connect() as conn:
        for i in range(25000):
            cust_id = i + 1
            name = random.choice(CUSTOMER_NAMES) + f" {i//20}"
            email = f"customer{i:05d}@example.com"
            phone = f"9{random.randint(100000000, 999999999)}"
            city = random.choice([s["city"] for s in PETPOOJA_STORES])
            segment = random.choices(["regular", "occasional", "vip"], weights=[80, 15, 5])[0]
            
            conn.execute(text("""
                INSERT INTO customers (id, name, email, phone, city, customer_segment, created_at)
                VALUES (:id, :name, :email, :phone, :city, :segment, NOW())
            """), {
                "id": cust_id,
                "name": name,
                "email": email,
                "phone": phone,
                "city": city,
                "segment": segment
            })
            customers.append(cust_id)
            
            if (i + 1) % 5000 == 0:
                conn.commit()
                print(f"    {i+1:,} customers created...")
    
    with engine.connect() as conn:
        conn.commit()
    print(f"  ✅ Created {len(customers)} customers")
    
    # ==================== CREATE SALES TRANSACTIONS ====================
    print(f"💳 Creating {num_transactions:,} sales transactions...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 6, 30)
    date_range = (end_date - start_date).days
    
    with engine.connect() as conn:
        for txn_idx in range(num_transactions):
            random_days = random.randint(0, date_range)
            txn_date = start_date + timedelta(days=random_days, hours=random.randint(8, 22))
            
            store_id = random.choices(
                [s["id"] for s in PETPOOJA_STORES],
                weights=[1.5, 1.5, 1.2, 1.0, 0.9, 0.8, 0.7, 0.4]
            )[0]
            
            customer_id = random.choice(customers)
            
            num_items = random.randint(1, 6)
            bill_amount = sum(random.choice(products)["price"] for _ in range(num_items))
            
            discount = 0
            if random.random() < 0.15:
                discount_pct = random.choice([5, 10, 15, 20])
                discount = int(bill_amount * discount_pct / 100)
                bill_amount -= discount
            
            tax = int(bill_amount * 0.05)
            total_amount = bill_amount + tax
            payment_method = random.choices(PAYMENT_METHODS, weights=[0.40, 0.26, 0.24, 0.10])[0]
            
            conn.execute(text("""
                INSERT INTO sales (transaction_id, store_id, customer_id, transaction_date,
                                 discount, tax, total_amount, payment_method, source)
                VALUES (:txn_id, :store_id, :cust_id, :date, :discount, :tax, :total, :payment, 'auto-generated')
            """), {
                "txn_id": f"TXN-{txn_idx:08d}",
                "store_id": store_id,
                "cust_id": customer_id,
                "date": txn_date,
                "discount": discount,
                "tax": tax,
                "total": total_amount,
                "payment": payment_method
            })
            
            if (txn_idx + 1) % 10000 == 0:
                conn.commit()
                print(f"    {txn_idx+1:,} transactions created...")
        
        conn.commit()
    print(f"  ✅ Created {num_transactions:,} sales transactions")
    
    # ==================== CREATE INVENTORY ====================
    print("📦 Creating inventory data...")
    with engine.connect() as conn:
        inv_id = 1
        for store in PETPOOJA_STORES:
            for product_idx in range(50):
                stock_qty = random.randint(10, 500)
                conn.execute(text("""
                    INSERT INTO inventory (store_id, product_id, quantity, reorder_point, status)
                    VALUES (:store_id, :product_id, :qty, :reorder, 'active')
                """), {
                    "store_id": store["id"],
                    "product_id": (product_idx % len(products)) + 1,
                    "qty": stock_qty,
                    "reorder": random.randint(20, 100)
                })
                inv_id += 1
        conn.commit()
    print(f"  ✅ Created {inv_id-1} inventory records")
    
    # ==================== FINAL VERIFICATION ====================
    print("\n" + "="*60)
    print(" FINAL VERIFICATION")
    print("="*60)
    
    with engine.connect() as conn:
        for table in ["products", "customers", "sales", "inventory"]:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table:15s}: {count:>10,} rows")
        
        total_revenue = conn.execute(text("SELECT COALESCE(SUM(total_amount), 0) FROM sales")).scalar()
        print(f"\n  Total Revenue:    ₹{total_revenue:>10,.0f}")
    
    print(f"\n{'='*60}")
    print(" ✅ DATA LOAD COMPLETE")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    generate_data(num_transactions=100000)
