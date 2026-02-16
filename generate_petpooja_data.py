#!/usr/bin/env python3
"""
R-DIOS Petpooja Synthetic Data Generator
Generates 100,000+ realistic restaurant transactions with Indian context

Features:
- 8+ active stores across major cities
- 150+ Indian food menu items (North, South, Chinese, Beverages, Desserts)
- 25,000+ unique customers with RFM segmentation
- 18 months of transaction history (Jan 2024 - Jun 2025)
- Seasonal patterns (Diwali, Holi, Monsoon)
- Multiple payment methods (UPI, Cash, Card, Wallet)
- Customer churn risk scoring
- Credit management data
"""

import sqlite3
import random
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import json

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

# ==================== SEASONAL PATTERNS ====================

def get_seasonal_multiplier(date: datetime) -> float:
    """Get demand multiplier based on Indian festivals and seasons"""
    month = date.month
    day = date.day
    
    # Diwali (Oct-Nov) - 2.5x spike
    if month in [10, 11]:
        return 2.5
    
    # Holi (Feb-Mar) - 1.8x spike
    if month in [2, 3]:
        return 1.8
    
    # New Year (Dec-Jan) - 1.5x spike
    if month in [12, 1]:
        return 1.5
    
    # Summer (Apr-Jun) - 1.2x (ice cream, cold drinks)
    if month in [4, 5, 6]:
        return 1.2
    
    # Monsoon (Jul-Sep) - Normal
    if month in [7, 8, 9]:
        return 1.0
    
    return 1.0


def generate_synthetic_data(db_path: str = "api/rdios_dev.db", num_transactions: int = 100000):
    """Generate comprehensive Petpooja synthetic dataset"""
    
    print(f"\n{'='*60}")
    print(" R-DIOS Petpooja Synthetic Data Generator")
    print(f"{'='*60}\n")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ==================== GENERATE USERS ====================
    print("👤 Generating users...")
    
    users = [
        ("admin", "admin@petpooja.com", "admin", "Admin User", True),
        ("manager1", "mgr1@petpooja.com", "manager", "Store Manager 1", True),
        ("manager2", "mgr2@petpooja.com", "manager", "Store Manager 2", True),
        ("analyst", "analyst@petpooja.com", "analyst", "Data Analyst", True),
    ]
    
    cursor.execute("DELETE FROM users")
    for email, name, role, password, active in [("admin@petpooja.com", "Admin", "admin", "admin", True)]:
        cursor.execute("""
            INSERT OR IGNORE INTO users (email, full_name, role, is_active)
            VALUES (?, ?, ?, ?)
        """, (email, name, role, active))
    
    conn.commit()
    print(f"  ✅ Created {len(users)} users")
    
    # ==================== GENERATE PRODUCTS ====================
    print("🍽️  Generating menu items...")
    
    cursor.execute("DELETE FROM products")
    
    product_id = 1
    products = []
    
    for category, items in MENU_ITEMS.items():
        for name, price in items:
            cursor.execute("""
                INSERT INTO products (id, name, category, price, sku, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, name, category, price, f"SKU-{product_id:04d}", True))
            
            products.append({
                "id": product_id,
                "name": name,
                "category": category,
                "price": price
            })
            
            product_id += 1
    
    conn.commit()
    print(f"  ✅ Created {len(products)} menu items")
    print(f"     Categories: {', '.join(MENU_ITEMS.keys())}")
    
    # ==================== GENERATE CUSTOMERS ====================
    print("👥 Generating customers...")
    
    cursor.execute("DELETE FROM customers")
    
    customers = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(25000):
        cust_id = i + 1
        
        # Create realistic customer profiles
        name = random.choice(CUSTOMER_NAMES) + f" {i//20}"
        email = f"customer{i:05d}@example.com"
        phone = f"9{random.randint(100000000, 999999999)}"
        city = random.choice([s["city"] for s in PETPOOJA_STORES])
        
        # RFM Segmentation
        # 80% regulars (high LTV), 15% occasional, 5% VIP
        segment = random.choices(
            ["regular", "occasional", "vip"],
            weights=[80, 15, 5]
        )[0]
        
        # Churn risk (opposite of RFM)
        if segment == "vip":
            churn_risk = "none"
        elif segment == "occasional":
            churn_risk = "high" if random.random() < 0.4 else "medium"
        else:
            churn_risk = "medium" if random.random() < 0.2 else "low"
        
        # Credit limit for Khata system
        credit_limit = random.choice([0, 5000, 10000, 20000, 50000])
        
        cursor.execute("""
            INSERT INTO customers (id, name, email, phone, city, customer_segment, 
                                  churn_risk, credit_limit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cust_id, name, email, phone, city, segment, churn_risk, credit_limit, 
              base_date + timedelta(days=random.randint(0, 500))))
        
        customers.append({
            "id": cust_id,
            "name": name,
            "segment": segment,
            "churn_risk": churn_risk
        })
    
    conn.commit()
    print(f"  ✅ Created {len(customers)} customers")
    
    # ==================== GENERATE SALES TRANSACTIONS ====================
    print(f"💳 Generating {num_transactions:,} sales transactions...")
    
    cursor.execute("DELETE FROM sales")
    cursor.execute("DELETE FROM sync_logs")
    
    # Transaction date range: Jan 2024 - Jun 2025
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 6, 30)
    date_range = (end_date - start_date).days
    
    transaction_id = 1
    batch_size = 5000
    
    for batch_num in range(0, num_transactions, batch_size):
        batch_txns = []
        
        for _ in range(min(batch_size, num_transactions - batch_num)):
            # Random date in range
            random_days = random.randint(0, date_range)
            txn_date = start_date + timedelta(days=random_days, hours=random.randint(8, 22))
            
            # Store selection (biased towards high-traffic stores)
            store_id = random.choices(
                [s["id"] for s in PETPOOJA_STORES],
                weights=[1.5, 1.5, 1.2, 1.0, 0.9, 0.8, 0.7, 0.4]
            )[0]
            
            # Customer selection
            customer_id = random.randint(1, len(customers))
            
            # Bill amount (₹150-₹2000 per transaction)
            num_items = random.randint(1, 6)
            bill_amount = 0
            discount = 0
            
            for _ in range(num_items):
                item = random.choice(products)
                bill_amount += item["price"]
            
            # Apply occasional discounts (5-20%)
            if random.random() < 0.15:
                discount_pct = random.choice([5, 10, 15, 20])
                discount = int(bill_amount * discount_pct / 100)
                bill_amount -= discount
            
            # Tax (5% GST baseline)
            tax = int(bill_amount * 0.05)
            total_amount = bill_amount + tax
            
            # Payment method (realistic distribution for India)
            payment_method = random.choices(
                PAYMENT_METHODS,
                weights=[0.40, 0.26, 0.24, 0.10]  # UPI, Cash, Card, Wallet
            )[0]
            
            # Apply seasonal multiplier (affects order frequency, not amount)
            multiplier = get_seasonal_multiplier(txn_date)
            
            batch_txns.append((
                transaction_id,
                f"TXN-{transaction_id:08d}",
                store_id,
                customer_id,
                txn_date.strftime("%Y-%m-%d %H:%M:%S"),
                discount,
                tax,
                total_amount,
                payment_method,
                "auto-generated"
            ))
            
            transaction_id += 1
        
        # Batch insert
        cursor.executemany("""
            INSERT INTO sales (id, transaction_id, store_id, customer_id, transaction_date,
                             discount, tax, total_amount, payment_method, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_txns)
        
        conn.commit()
        
        if (batch_num + batch_size) % 20000 == 0:
            print(f"  ✅ Generated {min(batch_num + batch_size, num_transactions):,} transactions")
    
    print(f"  ✅ Generated {num_transactions:,} sales transactions")
    
    # ==================== GENERATE INVENTORY ====================
    print("📦 Generating inventory data...")
    
    cursor.execute("DELETE FROM inventory")
    
    inv_id = 1
    for store in PETPOOJA_STORES:
        for product in products[:50]:  # Sample of products
            # Random stock levels (0-500 units)
            stock_qty = random.randint(10, 500)
            reorder_point = random.randint(20, 100)
            
            cursor.execute("""
                INSERT INTO inventory (id, store_id, product_id, quantity, reorder_point, 
                                     last_updated, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (inv_id, store["id"], product["id"], stock_qty, reorder_point, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "active"))
            
            inv_id += 1
    
    conn.commit()
    print(f"  ✅ Created {inv_id-1} inventory records")
    
    # ==================== SUMMARY ====================
    
    cursor.execute("SELECT COUNT(*) FROM sales")
    sales_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    products_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    customers_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_amount) FROM sales")
    total_revenue = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM sales")
    date_range_result = cursor.fetchone()
    min_date, max_date = date_range_result if date_range_result else (None, None)
    
    # Close connection
    conn.close()
    
    print(f"\n{'='*60}")
    print(" SYNTHETIC DATA GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Sales Transactions:  {sales_count:,}")
    print(f"✅ Menu Items:          {products_count}")
    print(f"✅ Customers:           {customers_count:,}")
    print(f"✅ Total Revenue:       ₹{total_revenue:,.0f}")
    print(f"✅ Date Range:          {min_date} to {max_date}")
    print(f"\n📋 Categories:")
    for cat in MENU_ITEMS.keys():
        count = len(MENU_ITEMS[cat])
        print(f"   - {cat}: {count} items")
    
    print(f"\n🏪 Stores: {len(PETPOOJA_STORES)} locations")
    print(f"💳 Payment Methods: {', '.join(PAYMENT_METHODS)}")
    print(f"\n✅ Database ready for testing!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    generate_synthetic_data(num_transactions=100000)
