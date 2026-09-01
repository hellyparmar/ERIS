#!/usr/bin/env python3
"""
Seeding script for Spice Route Hospitality Pvt Ltd.
Populates PostgreSQL with realistic Indian restaurant data for all ERIS features.
"""

import os
import sys
import random
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date, timedelta
from decimal import Decimal

# Connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'eris_user',
    'password': 'ErisDevPass2026Secure9',
    'dbname': 'eris_dev'
}

# Constants for restaurant seeding
CATEGORIES = ['Starters', 'Mains', 'Breads', 'Desserts', 'Beverages']

PRODUCTS_DATA = {
    'Starters': [
        ('Paneer Tikka', 280), ('Chicken Wings', 320), ('Veg Spring Rolls', 180),
        ('Crispy Corn', 160), ('Seekh Kebab', 350), ('Fish Fingers', 300),
        ('Hara Bhara Kebab', 220), ('Mushroom Pepper Dry', 240), ('Chicken Tikka', 340),
        ('Chilli Paneer', 260)
    ],
    'Mains': [
        ('Butter Chicken', 380), ('Dal Makhani', 280), ('Chicken Biryani', 420),
        ('Paneer Butter Masala', 320), ('Kadai Chicken', 360), ('Veg Biryani', 300),
        ('Mutton Rogan Josh', 480), ('Palak Paneer', 280), ('Fish Curry', 420),
        ('Chole Bhature', 220), ('Lamb Biryani', 480), ('Egg Curry', 260),
        ('Rajma Chawal', 200), ('Pav Bhaji', 180), ('Veg Thali', 350)
    ],
    'Breads': [
        ('Butter Naan', 50), ('Garlic Naan', 60), ('Tandoori Roti', 35),
        ('Laccha Paratha', 70), ('Puri', 30), ('Missi Roti', 45),
        ('Kulcha', 55)
    ],
    'Desserts': [
        ('Gulab Jamun', 100), ('Rasgulla', 90), ('Kheer', 120),
        ('Ice Cream', 150), ('Brownie Sundae', 180), ('Mango Kulfi', 130),
        ('Gajar Halwa', 110), ('Phirni', 100)
    ],
    'Beverages': [
        ('Masala Chai', 60), ('Cold Coffee', 140), ('Fresh Lime Soda', 80),
        ('Mango Lassi', 120), ('Sweet Lassi', 90), ('Soft Drink', 70),
        ('Mineral Water', 40), ('Jal Jeera', 70), ('Rose Sharbat', 80),
        ('Buttermilk', 60)
    ]
}

SUPPLIERS_INFO = [
    ('Metro Cash & Carry', 'Net 15', 0.97),
    ('Innovative Foods Pvt Ltd', 'Net 30', 0.94),
    ('Punjab Poultry Farms', 'Net 7', 0.91),
    ('Sea Fresh Exports', 'Net 7', 0.88),
    ('Amul Distribution', 'Net 15', 0.99),
    ('Kitchen Essentials Co', 'Net 30', 0.96)
]

CUSTOMER_FIRST_NAMES = ['Rajesh', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Aisha', 'Arjun', 'Divya', 
                        'Rohan', 'Neha', 'Sandeep', 'Pooja', 'Akshay', 'Kavya', 'Nitin', 'Riya', 
                        'Karan', 'Anjali', 'Varun', 'Shreya', 'Deepak', 'Meera', 'Vijay', 'Sunita',
                        'Rahul', 'Aarti', 'Manoj', 'Jyoti', 'Sanjay', 'Rekha']
CUSTOMER_LAST_NAMES = ['Sharma', 'Patel', 'Kumar', 'Singh', 'Gupta', 'Verma', 'Pandey', 'Iyer', 
                       'Nair', 'Desai', 'Joshi', 'Mehta', 'Rao', 'Reddy', 'Bose', 'Sen',
                       'Mukherjee', 'Kulkarni', 'Chawla']

EMPLOYEE_ROLES = [
    ('MANAGER', 'Front of House', 'FULL_TIME', 45000, 65000),
    ('OTHER', 'Kitchen', 'FULL_TIME', 40000, 55000),
    ('SALES_ASSOCIATE', 'Front of House', 'FULL_TIME', 18000, 25000),
    ('SALES_ASSOCIATE', 'Front of House', 'PART_TIME', 18000, 25000),
    ('CASHIER', 'Front of House', 'FULL_TIME', 20000, 28000)
]

SHIFTS = ['Morning', 'Evening', 'Night']
PAYMENT_METHODS = ['UPI', 'CASH', 'CARD', 'WALLET']
ORDER_TYPES = ['Dine-in', 'Takeaway', 'Delivery']

def check_table_columns(cur, table_name):
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s
    """, (table_name,))
    cols = [r[0] for r in cur.fetchall()]
    print(f"📋 Columns in {table_name}: {cols}")
    return cols

def get_realistic_combo(products_seeded):
    # Group products by category
    by_cat = {}
    for p in products_seeded:
        cat = p['category']
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(p)
        
    combo_type = random.choices(
        ['starter_main_bread_bev', 'main_bread', 'main_dessert', 'bev_only', 'random'],
        weights=[30, 40, 15, 10, 5]
    )[0]
    
    selected = []
    if combo_type == 'starter_main_bread_bev':
        if by_cat.get('Starters'):
            selected.append(random.choice(by_cat['Starters']))
        if by_cat.get('Mains'):
            selected.append(random.choice(by_cat['Mains']))
        if by_cat.get('Breads'):
            selected.append(random.choice(by_cat['Breads']))
        if by_cat.get('Beverages'):
            selected.append(random.choice(by_cat['Beverages']))
    elif combo_type == 'main_bread':
        if by_cat.get('Mains'):
            selected.append(random.choice(by_cat['Mains']))
        if by_cat.get('Breads'):
            selected.append(random.choice(by_cat['Breads']))
    elif combo_type == 'main_dessert':
        if by_cat.get('Mains'):
            selected.append(random.choice(by_cat['Mains']))
        if by_cat.get('Desserts'):
            selected.append(random.choice(by_cat['Desserts']))
    elif combo_type == 'bev_only':
        if by_cat.get('Beverages'):
            selected.append(random.choice(by_cat['Beverages']))
    else:
        # 1 to 4 random products
        num_items = random.randint(1, 4)
        selected = random.sample(products_seeded, min(num_items, len(products_seeded)))
        
    return selected

def main():
    print("🌱 Starting database seeding script...")
    
    # Try connecting using specified DB_CONFIG, fallback to admin1234 or .env if needed
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"⚠️ Failed connecting with default credentials ({e}). Trying fallback password...")
        alt_config = DB_CONFIG.copy()
        alt_config['password'] = 'admin1234'
        try:
            conn = psycopg2.connect(**alt_config)
        except Exception as ex:
            print(f"⚠️ Fallback password failed ({ex}). Trying environment DATABASE_URL...")
            from dotenv import load_dotenv
            load_dotenv("backend/.env")
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
                conn = psycopg2.connect(db_url)
            else:
                raise ex

    cur = conn.cursor()
    print("🚀 Connected to database successfully.")

    # TRUNCATE tables in order to clear old general-store data
    print("\n🧹 Truncating tables to prepare for seeding...")
    tables_to_truncate = [
        'sale_items', 'sales', 'inventory', 'products', 'product_categories', 'categories', 'suppliers',
        'purchase_order_items', 'purchase_orders', 'customers', 'employees', 'alerts', 'day_closes'
    ]
    for table in tables_to_truncate:
        cur.execute("SELECT exists(SELECT * FROM information_schema.tables WHERE table_name=%s)", (table,))
        exists = cur.fetchone()[0]
        if exists:
            cur.execute(f"TRUNCATE TABLE {table} CASCADE")
            print(f"   ✓ Truncated table: {table}")
    conn.commit()

    # Get system references
    cur.execute("SELECT id FROM organizations LIMIT 1")
    org_row = cur.fetchone()
    org_id = org_row[0] if org_row else 1
    print(f"🏢 Active Organization ID: {org_id}")

    cur.execute("SELECT id FROM outlets ORDER BY id")
    outlet_ids = [r[0] for r in cur.fetchall()]
    print(f"📍 Active Outlets: {outlet_ids}")

    cur.execute("SELECT id FROM users LIMIT 1")
    user_row = cur.fetchone()
    user_id = user_row[0] if user_row else 1
    print(f"👤 Active User ID for Day Close: {user_id}")

    # 1. PRODUCT CATEGORIES
    print("\n[1/10] Seeding Product Categories...")
    category_map = {}
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='product_categories'")
        pc_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in product_categories: {pc_cols}")
        
        category_table = 'product_categories'
        if not pc_cols:
            print("   (product_categories table doesn't exist, using 'categories' table)")
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='categories'")
            pc_cols = [r[0] for r in cur.fetchall()]
            print(f"Columns in categories: {pc_cols}")
            category_table = 'categories'
            
        for cat in CATEGORIES:
            insert_cols = []
            val_placeholders = []
            val_args = []
            
            if 'organization_id' in pc_cols:
                insert_cols.append('organization_id')
                val_placeholders.append('%s')
                val_args.append(org_id)
            if 'name' in pc_cols:
                insert_cols.append('name')
                val_placeholders.append('%s')
                val_args.append(cat)
            if 'description' in pc_cols:
                insert_cols.append('description')
                val_placeholders.append('%s')
                val_args.append(f"{cat} category")
            if 'code' in pc_cols:
                insert_cols.append('code')
                val_placeholders.append('%s')
                val_args.append(f"CAT-{cat.upper()[:4]}")
            if 'is_active' in pc_cols:
                insert_cols.append('is_active')
                val_placeholders.append('%s')
                val_args.append(True)
            if 'is_deleted' in pc_cols:
                insert_cols.append('is_deleted')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'created_at' in pc_cols:
                insert_cols.append('created_at')
                val_placeholders.append('NOW()')
            if 'updated_at' in pc_cols:
                insert_cols.append('updated_at')
                val_placeholders.append('NOW()')
                
            query = f"INSERT INTO {category_table} ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)}) RETURNING id"
            cur.execute(query, tuple(val_args))
            cat_id = cur.fetchone()[0]
            category_map[cat] = cat_id
            
        conn.commit()
        print(f"   ✓ Seeded {len(category_map)} categories successfully into '{category_table}'.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Product Categories seeding failed: {e}")
        raise e

    # 2. PRODUCTS
    print("\n[2/10] Seeding Products (50 items)...")
    products_seeded = []
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='products'")
        p_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in products: {p_cols}")
        
        sku_idx = 1
        for cat_name, items in PRODUCTS_DATA.items():
            cat_id = category_map[cat_name]
            for name, price in items:
                cost = round(price * 0.45, 2)
                gst = 18.0 if cat_name == 'Beverages' else 5.0
                sku = f"PROD-{cat_name[:3].upper()}-{sku_idx:03d}"
                sku_idx += 1
                
                insert_cols = []
                val_placeholders = []
                val_args = []
                
                if 'organization_id' in p_cols:
                    insert_cols.append('organization_id')
                    val_placeholders.append('%s')
                    val_args.append(org_id)
                if 'category_id' in p_cols:
                    insert_cols.append('category_id')
                    val_placeholders.append('%s')
                    val_args.append(cat_id)
                if 'category' in p_cols:
                    insert_cols.append('category')
                    val_placeholders.append('%s')
                    val_args.append(cat_name)
                if 'sku' in p_cols:
                    insert_cols.append('sku')
                    val_placeholders.append('%s')
                    val_args.append(sku)
                if 'sku_code' in p_cols:
                    insert_cols.append('sku_code')
                    val_placeholders.append('%s')
                    val_args.append(sku)
                if 'name' in p_cols:
                    insert_cols.append('name')
                    val_placeholders.append('%s')
                    val_args.append(name)
                if 'description' in p_cols:
                    insert_cols.append('description')
                    val_placeholders.append('%s')
                    val_args.append(f"Delicious {name}")
                if 'cost_price' in p_cols:
                    insert_cols.append('cost_price')
                    val_placeholders.append('%s')
                    val_args.append(cost)
                if 'selling_price' in p_cols:
                    insert_cols.append('selling_price')
                    val_placeholders.append('%s')
                    val_args.append(price)
                if 'base_price' in p_cols:
                    insert_cols.append('base_price')
                    val_placeholders.append('%s')
                    val_args.append(price)
                if 'mrp' in p_cols:
                    insert_cols.append('mrp')
                    val_placeholders.append('%s')
                    val_args.append(price)
                if 'current_stock' in p_cols:
                    insert_cols.append('current_stock')
                    val_placeholders.append('%s')
                    val_args.append(0)
                if 'reorder_level' in p_cols:
                    insert_cols.append('reorder_level')
                    val_placeholders.append('%s')
                    val_args.append(20)
                if 'reorder_point' in p_cols:
                    insert_cols.append('reorder_point')
                    val_placeholders.append('%s')
                    val_args.append(20)
                if 'max_stock' in p_cols:
                    insert_cols.append('max_stock')
                    val_placeholders.append('%s')
                    val_args.append(100)
                if 'shelf_life_days' in p_cols:
                    insert_cols.append('shelf_life_days')
                    val_placeholders.append('%s')
                    val_args.append(7)
                if 'reorder_quantity' in p_cols:
                    insert_cols.append('reorder_quantity')
                    val_placeholders.append('%s')
                    val_args.append(50)
                if 'unit' in p_cols:
                    insert_cols.append('unit')
                    val_placeholders.append('%s')
                    val_args.append('portion')
                if 'barcode' in p_cols:
                    insert_cols.append('barcode')
                    val_placeholders.append('%s')
                    val_args.append(sku)
                if 'is_perishable' in p_cols:
                    insert_cols.append('is_perishable')
                    val_placeholders.append('%s')
                    val_args.append(True)
                if 'is_active' in p_cols:
                    insert_cols.append('is_active')
                    val_placeholders.append('%s')
                    val_args.append(True)
                if 'is_deleted' in p_cols:
                    insert_cols.append('is_deleted')
                    val_placeholders.append('%s')
                    val_args.append(False)
                if 'gst_rate' in p_cols:
                    insert_cols.append('gst_rate')
                    val_placeholders.append('%s')
                    val_args.append(gst)
                if 'hsn_code' in p_cols:
                    insert_cols.append('hsn_code')
                    val_placeholders.append('%s')
                    val_args.append('22021010' if cat_name == 'Beverages' else '21069099')
                if 'created_at' in p_cols:
                    insert_cols.append('created_at')
                    val_placeholders.append('NOW()')
                if 'updated_at' in p_cols:
                    insert_cols.append('updated_at')
                    val_placeholders.append('NOW()')
                    
                query = f"INSERT INTO products ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)}) RETURNING id"
                cur.execute(query, tuple(val_args))
                prod_id = cur.fetchone()[0]
                
                products_seeded.append({
                    'id': prod_id,
                    'name': name,
                    'category': cat_name,
                    'selling_price': price,
                    'cost_price': cost,
                    'gst_rate': gst
                })
                
        conn.commit()
        print(f"   ✓ Seeded {len(products_seeded)} products successfully.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Products seeding failed: {e}")
        raise e

    # 3. INVENTORY
    print("\n[3/10] Seeding Inventory...")
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='inventory'")
        inv_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in inventory: {inv_cols}")
        
        inventory_tuples = []
        for outlet_id in outlet_ids:
            # Pick 2 products per outlet to be below reorder level (20)
            low_stock_products = random.sample(products_seeded, 2)
            
            for prod in products_seeded:
                is_low = prod in low_stock_products
                stock = random.randint(5, 18) if is_low else random.randint(40, 200)
                
                # Build tuple for batch execution
                val_args = []
                insert_cols = ['outlet_id', 'product_id', 'current_stock']
                val_args.extend([outlet_id, prod['id'], stock])
                
                if 'reserved_stock' in inv_cols:
                    insert_cols.append('reserved_stock')
                    val_args.append(0)
                if 'last_restocked_at' in inv_cols:
                    insert_cols.append('last_restocked_at')
                    val_args.append(datetime.now())
                if 'next_expiry_date' in inv_cols:
                    insert_cols.append('next_expiry_date')
                    val_args.append(datetime.now() + timedelta(days=30))
                    
                inventory_tuples.append(tuple(val_args))
                
        placeholders = ", ".join(["%s"] * len(insert_cols))
        query = f"INSERT INTO inventory ({', '.join(insert_cols)}) VALUES %s"
        execute_values(cur, query, inventory_tuples)
        
        conn.commit()
        print(f"   ✓ Seeded inventory for {len(outlet_ids)} outlets successfully.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Inventory seeding failed: {e}")
        raise e

    # 4. SUPPLIERS
    print("\n[4/10] Seeding Suppliers...")
    supplier_map = {}
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='suppliers'")
        sup_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in suppliers: {sup_cols}")
        
        for name, terms, rate in SUPPLIERS_INFO:
            insert_cols = []
            val_placeholders = []
            val_args = []
            
            if 'organization_id' in sup_cols:
                insert_cols.append('organization_id')
                val_placeholders.append('%s')
                val_args.append(org_id)
            if 'name' in sup_cols:
                insert_cols.append('name')
                val_placeholders.append('%s')
                val_args.append(name)
            if 'contact_person' in sup_cols:
                insert_cols.append('contact_person')
                val_placeholders.append('%s')
                val_args.append(f"{name} Manager")
            if 'email' in sup_cols:
                insert_cols.append('email')
                val_placeholders.append('%s')
                val_args.append(f"contact@{name.lower().replace(' ', '').replace('&', 'and')}.com")
            if 'phone' in sup_cols:
                insert_cols.append('phone')
                val_placeholders.append('%s')
                val_args.append(f"+91-9{random.randint(100000000, 999999999)}")
            if 'address' in sup_cols:
                insert_cols.append('address')
                val_placeholders.append('%s')
                val_args.append(f"Plot {random.randint(1,100)}, Industrial Area")
            if 'city' in sup_cols:
                insert_cols.append('city')
                val_placeholders.append('%s')
                val_args.append(random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai']))
            if 'state' in sup_cols:
                insert_cols.append('state')
                val_placeholders.append('%s')
                val_args.append(random.choice(['MH', 'DL', 'KA', 'TN']))
            if 'country' in sup_cols:
                insert_cols.append('country')
                val_placeholders.append('%s')
                val_args.append('India')
            if 'postal_code' in sup_cols:
                insert_cols.append('postal_code')
                val_placeholders.append('%s')
                val_args.append(f"{random.randint(110001, 600001)}")
            if 'tax_id' in sup_cols:
                insert_cols.append('tax_id')
                val_placeholders.append('%s')
                val_args.append(f"29AAAAA{random.randint(1000, 9999)}A1Z1")
            if 'payment_terms' in sup_cols:
                insert_cols.append('payment_terms')
                val_placeholders.append('%s')
                val_args.append(int(terms.split(' ')[1]))
            if 'payment_terms_days' in sup_cols:
                insert_cols.append('payment_terms_days')
                val_placeholders.append('%s')
                val_args.append(int(terms.split(' ')[1]))
            if 'on_time_rate' in sup_cols:
                insert_cols.append('on_time_rate')
                val_placeholders.append('%s')
                val_args.append(rate)
            if 'is_active' in sup_cols:
                insert_cols.append('is_active')
                val_placeholders.append('%s')
                val_args.append(True)
            if 'is_deleted' in sup_cols:
                insert_cols.append('is_deleted')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'created_at' in sup_cols:
                insert_cols.append('created_at')
                val_placeholders.append('NOW()')
            if 'updated_at' in sup_cols:
                insert_cols.append('updated_at')
                val_placeholders.append('NOW()')
                
            query = f"INSERT INTO suppliers ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)}) RETURNING id"
            cur.execute(query, tuple(val_args))
            sup_id = cur.fetchone()[0]
            supplier_map[name] = sup_id
            
        # Update products with random suppliers to respect relational integrity
        if 'supplier_id' in p_cols:
            for prod in products_seeded:
                sup_id = random.choice(list(supplier_map.values()))
                cur.execute("UPDATE products SET supplier_id = %s WHERE id = %s", (sup_id, prod['id']))
                prod['supplier_id'] = sup_id
                
        conn.commit()
        print(f"   ✓ Seeded {len(supplier_map)} suppliers and linked them to products.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Suppliers seeding failed: {e}")
        raise e

    # 5. PURCHASE ORDERS
    print("\n[5/10] Seeding Purchase Orders...")
    overdue_po_ref = []  # List to track overdue POs for invoice alerts
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='purchase_orders'")
        po_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in purchase_orders: {po_cols}")
        
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='purchase_order_items'")
        poi_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in purchase_order_items: {poi_cols}")
        
        # We need a list of products with suppliers
        po_counter = 0
        for sup_name, sup_id in supplier_map.items():
            # Get payment terms
            terms = next((x[1] for x in SUPPLIERS_INFO if x[0] == sup_name), 'Net 15')
            net_days = int(terms.split(' ')[1])
            
            # Select products assigned to this supplier (or just any products if not assigned)
            sup_prods = [p for p in products_seeded if p.get('supplier_id') == sup_id]
            if not sup_prods:
                sup_prods = products_seeded
                
            num_orders = random.randint(3, 5)
            
            for order_idx in range(num_orders):
                po_counter += 1
                
                # Force the first 2 POs overall to be overdue to ensure at least 2 overdue alerts
                if po_counter <= 2:
                    status = 'confirmed'  # Overdue (due in past and still confirmed status)
                    due_date = date.today() - timedelta(days=random.randint(1, 30))
                    issue_date = due_date - timedelta(days=net_days)
                    actual_delivery_date = None
                else:
                    # Status distribution: 60% paid, 30% pending, 10% overdue
                    # Determined based on due date relative to today (2026-07-01)
                    r = random.random()
                    if r < 0.60:
                        status = 'delivered'  # Paid
                        due_date = date.today() - timedelta(days=random.randint(15, 365))
                        issue_date = due_date - timedelta(days=net_days)
                        actual_delivery_date = due_date
                    elif r < 0.90:
                        status = 'confirmed'  # Pending (due in future)
                        due_date = date.today() + timedelta(days=random.randint(1, 30))
                        issue_date = due_date - timedelta(days=net_days)
                        actual_delivery_date = None
                    else:
                        status = 'confirmed'  # Overdue
                        due_date = date.today() - timedelta(days=random.randint(1, 30))
                        issue_date = due_date - timedelta(days=net_days)
                        actual_delivery_date = None
                
                # Pick 2-5 products and scale quantities to target ₹15,000 to ₹2,50,000 total
                target_amount = random.randint(15000, 250000)
                num_items = random.randint(2, 5)
                selected_products = random.sample(sup_prods, min(num_items, len(sup_prods)))
                
                po_items_data = []
                running_sum = 0
                for idx, prod in enumerate(selected_products):
                    if idx == len(selected_products) - 1:
                        item_amt = target_amount - running_sum
                    else:
                        item_amt = random.randint(int(target_amount * 0.1), int(target_amount * 0.7 / len(selected_products)))
                        
                    qty = max(1, int(round(item_amt / prod['cost_price'])))
                    line_amt = qty * prod['cost_price']
                    running_sum += line_amt
                    po_items_data.append((prod['id'], qty, prod['cost_price']))
                    
                total_amount = running_sum
                outlet_id = random.choice(outlet_ids)
                
                # Insert PO
                insert_cols = []
                val_placeholders = []
                val_args = []
                
                if 'outlet_id' in po_cols:
                    insert_cols.append('outlet_id')
                    val_placeholders.append('%s')
                    val_args.append(outlet_id)
                if 'supplier_id' in po_cols:
                    insert_cols.append('supplier_id')
                    val_placeholders.append('%s')
                    val_args.append(sup_id)
                if 'status' in po_cols:
                    insert_cols.append('status')
                    val_placeholders.append('%s::purchaseorderstatus')
                    val_args.append(status)
                if 'total_amount' in po_cols:
                    insert_cols.append('total_amount')
                    val_placeholders.append('%s')
                    val_args.append(float(total_amount))
                if 'expected_delivery_date' in po_cols:
                    insert_cols.append('expected_delivery_date')
                    val_placeholders.append('%s')
                    val_args.append(due_date)
                if 'actual_delivery_date' in po_cols:
                    insert_cols.append('actual_delivery_date')
                    val_placeholders.append('%s')
                    val_args.append(actual_delivery_date)
                if 'notes' in po_cols:
                    insert_cols.append('notes')
                    val_placeholders.append('%s')
                    val_args.append(f"Auto-generated PO index {order_idx}")
                if 'issue_date' in po_cols:
                    insert_cols.append('issue_date')
                    val_placeholders.append('%s')
                    val_args.append(issue_date)
                if 'due_date' in po_cols:
                    insert_cols.append('due_date')
                    val_placeholders.append('%s')
                    val_args.append(due_date)
                    
                query = f"INSERT INTO purchase_orders ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)}) RETURNING id"
                cur.execute(query, tuple(val_args))
                po_id = cur.fetchone()[0]
                
                # If overdue, save PO details for alerts
                if status == 'confirmed' and due_date < date.today():
                    overdue_po_ref.append((outlet_id, po_id, sup_name, float(total_amount)))
                
                # Insert PO Items
                for prod_id, qty, cost in po_items_data:
                    item_cols = []
                    item_placeholders = []
                    item_args = []
                    
                    if 'order_id' in poi_cols:
                        item_cols.append('order_id')
                        item_placeholders.append('%s')
                        item_args.append(po_id)
                    if 'product_id' in poi_cols:
                        item_cols.append('product_id')
                        item_placeholders.append('%s')
                        item_args.append(prod_id)
                    if 'quantity_ordered' in poi_cols:
                        item_cols.append('quantity_ordered')
                        item_placeholders.append('%s')
                        item_args.append(qty)
                    if 'quantity_received' in poi_cols:
                        item_cols.append('quantity_received')
                        item_placeholders.append('%s')
                        item_args.append(qty if status == 'delivered' else 0)
                    if 'unit_price' in poi_cols:
                        item_cols.append('unit_price')
                        item_placeholders.append('%s')
                        item_args.append(float(cost))
                        
                    query = f"INSERT INTO purchase_order_items ({', '.join(item_cols)}) VALUES ({', '.join(item_placeholders)})"
                    cur.execute(query, tuple(item_args))
                    
        conn.commit()
        print(f"   ✓ Seeded all purchase orders and items successfully. Generated {len(overdue_po_ref)} overdue POs.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Purchase Orders seeding failed: {e}")
        raise e

    # 6. CUSTOMERS
    print("\n[6/10] Seeding Customers (120 rows)...")
    customer_ids = []
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='customers'")
        cust_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in customers: {cust_cols}")
        
        for idx in range(120):
            fname = random.choice(CUSTOMER_FIRST_NAMES)
            lname = random.choice(CUSTOMER_LAST_NAMES)
            email = f"{fname.lower()}.{lname.lower()}{idx}@spiceroute.com"
            phone = f"+91-9{random.randint(100000000, 999999999)}"
            
            r = random.random()
            if r < 0.70:
                cust_type = 'regular'
                loyalty = random.randint(0, 2000)
            elif r < 0.90:
                cust_type = 'corporate'
                loyalty = 0
            else:
                cust_type = 'vip'
                loyalty = random.randint(5000, 15000)
                
            insert_cols = []
            val_placeholders = []
            val_args = []
            
            if 'organization_id' in cust_cols:
                insert_cols.append('organization_id')
                val_placeholders.append('%s')
                val_args.append(org_id)
            if 'first_name' in cust_cols:
                insert_cols.append('first_name')
                val_placeholders.append('%s')
                val_args.append(fname)
            if 'last_name' in cust_cols:
                insert_cols.append('last_name')
                val_placeholders.append('%s')
                val_args.append(lname)
            if 'name' in cust_cols:
                # Fallback for tables that combine name
                insert_cols.append('name')
                val_placeholders.append('%s')
                val_args.append(f"{fname} {lname}")
            if 'email' in cust_cols:
                insert_cols.append('email')
                val_placeholders.append('%s')
                val_args.append(email)
            if 'phone' in cust_cols:
                insert_cols.append('phone')
                val_placeholders.append('%s')
                val_args.append(phone)
            if 'customer_type' in cust_cols:
                insert_cols.append('customer_type')
                val_placeholders.append('%s')
                val_args.append(cust_type)
            if 'loyalty_points' in cust_cols:
                insert_cols.append('loyalty_points')
                val_placeholders.append('%s')
                val_args.append(loyalty)
            if 'address' in cust_cols:
                import json
                insert_cols.append('address')
                val_placeholders.append('%s')
                val_args.append(json.dumps({"line1": f"Apartment {random.randint(101, 909)}, Block {random.choice(['A','B','C'])}"}))
            if 'city' in cust_cols:
                insert_cols.append('city')
                val_placeholders.append('%s')
                val_args.append(random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Ahmedabad']))
            if 'state' in cust_cols:
                insert_cols.append('state')
                val_placeholders.append('%s')
                val_args.append(random.choice(['MH', 'DL', 'KA', 'TN', 'GJ']))
            if 'country' in cust_cols:
                insert_cols.append('country')
                val_placeholders.append('%s')
                val_args.append('India')
            if 'postal_code' in cust_cols:
                insert_cols.append('postal_code')
                val_placeholders.append('%s')
                val_args.append(f"{random.randint(110001, 600001)}")
            if 'is_active' in cust_cols:
                insert_cols.append('is_active')
                val_placeholders.append('%s')
                val_args.append(True)
            if 'is_deleted' in cust_cols:
                insert_cols.append('is_deleted')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'created_at' in cust_cols:
                insert_cols.append('created_at')
                val_placeholders.append('NOW()')
            if 'updated_at' in cust_cols:
                insert_cols.append('updated_at')
                val_placeholders.append('NOW()')
                
            query = f"INSERT INTO customers ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)}) RETURNING id"
            cur.execute(query, tuple(val_args))
            customer_ids.append(cur.fetchone()[0])
            
        conn.commit()
        print(f"   ✓ Seeded {len(customer_ids)} customers successfully.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Customers seeding failed: {e}")
        raise e

    # 7. EMPLOYEES
    print("\n[7/10] Seeding Employees (25 rows)...")
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='employees'")
        emp_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in employees: {emp_cols}")
        
        emp_idx = 1
        for outlet_id in outlet_ids:
            for role, dept, employment, min_sal, max_sal in EMPLOYEE_ROLES:
                fname = random.choice(CUSTOMER_FIRST_NAMES)
                lname = random.choice(CUSTOMER_LAST_NAMES)
                email = f"{fname.lower()}.{lname.lower()}{emp_idx}@spiceroute.com"
                phone = f"+91-9{random.randint(100000000, 999999999)}"
                salary = random.randint(min_sal, max_sal)
                joining = date.today() - timedelta(days=random.randint(10, 1095))
                dob = date.today() - timedelta(days=random.randint(7300, 18000))
                
                insert_cols = []
                val_placeholders = []
                val_args = []
                
                if 'outlet_id' in emp_cols:
                    insert_cols.append('outlet_id')
                    val_placeholders.append('%s')
                    val_args.append(outlet_id)
                if 'store_id' in emp_cols:
                    insert_cols.append('store_id')
                    val_placeholders.append('%s')
                    val_args.append(outlet_id)
                if 'employee_id' in emp_cols:
                    insert_cols.append('employee_id')
                    val_placeholders.append('%s')
                    val_args.append(f"EMP{emp_idx:03d}")
                if 'first_name' in emp_cols:
                    insert_cols.append('first_name')
                    val_placeholders.append('%s')
                    val_args.append(fname)
                if 'last_name' in emp_cols:
                    insert_cols.append('last_name')
                    val_placeholders.append('%s')
                    val_args.append(lname)
                if 'name' in emp_cols:
                    insert_cols.append('name')
                    val_placeholders.append('%s')
                    val_args.append(f"{fname} {lname}")
                if 'email' in emp_cols:
                    insert_cols.append('email')
                    val_placeholders.append('%s')
                    val_args.append(email)
                if 'phone' in emp_cols:
                    insert_cols.append('phone')
                    val_placeholders.append('%s')
                    val_args.append(phone)
                if 'position' in emp_cols:
                    insert_cols.append('position')
                    val_placeholders.append('%s')
                    val_args.append(role)
                if 'role' in emp_cols:
                    insert_cols.append('role')
                    val_placeholders.append('%s')
                    val_args.append(role)
                if 'department' in emp_cols:
                    insert_cols.append('department')
                    val_placeholders.append('%s')
                    val_args.append(dept)
                if 'employment_type' in emp_cols:
                    insert_cols.append('employment_type')
                    val_placeholders.append('%s')
                    val_args.append(employment)
                if 'date_of_birth' in emp_cols:
                    insert_cols.append('date_of_birth')
                    val_placeholders.append('%s')
                    val_args.append(dob)
                if 'joining_date' in emp_cols:
                    insert_cols.append('joining_date')
                    val_placeholders.append('%s')
                    val_args.append(joining)
                if 'hire_date' in emp_cols:
                    insert_cols.append('hire_date')
                    val_placeholders.append('%s')
                    val_args.append(joining)
                if 'base_salary' in emp_cols:
                    insert_cols.append('base_salary')
                    val_placeholders.append('%s')
                    val_args.append(salary)
                if 'salary' in emp_cols:
                    insert_cols.append('salary')
                    val_placeholders.append('%s')
                    val_args.append(salary)
                if 'salary_type' in emp_cols:
                    insert_cols.append('salary_type')
                    val_placeholders.append('%s')
                    val_args.append('monthly')
                if 'is_active' in emp_cols:
                    insert_cols.append('is_active')
                    val_placeholders.append('%s')
                    val_args.append(True)
                if 'is_deleted' in emp_cols:
                    insert_cols.append('is_deleted')
                    val_placeholders.append('%s')
                    val_args.append(False)
                if 'shift' in emp_cols:
                    insert_cols.append('shift')
                    val_placeholders.append('%s')
                    val_args.append(random.choice(SHIFTS))
                if 'created_at' in emp_cols:
                    insert_cols.append('created_at')
                    val_placeholders.append('NOW()')
                if 'updated_at' in emp_cols:
                    insert_cols.append('updated_at')
                    val_placeholders.append('NOW()')
                    
                query = f"INSERT INTO employees ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)})"
                cur.execute(query, tuple(val_args))
                emp_idx += 1
                
        conn.commit()
        print(f"   ✓ Seeded {emp_idx - 1} employees successfully.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Employees seeding failed: {e}")
        raise e

    # 8. SALES & SALE ITEMS
    print("\n[8/10] Seeding Sales & Sale Items...")
    day_close_sums = {}  # Dict to track cash, upi, and card totals daily per outlet for Day Closes
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='sales'")
        s_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in sales: {s_cols}")
        
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='sale_items'")
        si_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in sale_items: {si_cols}")
        
        # We need two date ranges:
        # 1. Full Year 2024
        # 2. Last 30 days (for day closes)
        start_date_2024 = date(2024, 1, 1)
        end_date_2024 = date(2024, 12, 31)
        days_2024 = [start_date_2024 + timedelta(days=x) for x in range((end_date_2024 - start_date_2024).days + 1)]
        
        last_30_days = [date.today() - timedelta(days=x) for x in range(1, 31)]
        all_sales_days = days_2024 + last_30_days
        
        # Group days by month/year to make bulk insertions manageable
        months_grouped = {}
        for d in all_sales_days:
            key = (d.year, d.month)
            if key not in months_grouped:
                months_grouped[key] = []
            months_grouped[key].append(d)
            
        total_sales_count = 0
        total_items_count = 0
        
        for (year, month), days in sorted(months_grouped.items()):
            sales_tuples = []
            sale_items_data = []
            
            for d in days:
                is_weekend = d.weekday() in (4, 5, 6) # Fri, Sat, Sun
                base_sales = 130 if is_weekend else 80
                
                # Apply seasonal boost
                seasonal_multiplier = 1.0
                if d.month in (10, 11):
                    seasonal_multiplier = 1.15
                elif d.month == 2:
                    seasonal_multiplier = 0.90
                    
                # Apply day of week boost
                day_multiplier = 1.0
                if d.weekday() in (4, 5): # Fri, Sat
                    day_multiplier = 1.10
                    
                daily_sales_count = int(base_sales * seasonal_multiplier * day_multiplier * random.uniform(0.9, 1.1))
                
                for outlet_id in outlet_ids:
                    # Init day close tracking if within last 30 days
                    dc_key = (outlet_id, d)
                    if d in last_30_days and dc_key not in day_close_sums:
                        day_close_sums[dc_key] = {'CASH': 0.0, 'UPI': 0.0, 'CARD': 0.0, 'WALLET': 0.0}
                        
                    for _ in range(daily_sales_count):
                        # Construct realistic time
                        hour = random.choices(
                            [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
                            weights=[10, 15, 8, 5, 5, 8, 12, 20, 25, 15, 5]
                        )[0]
                        minute = random.randint(0, 59)
                        second = random.randint(0, 59)
                        trans_dt = datetime.combine(d, datetime.min.time()) + timedelta(hours=hour, minutes=minute, seconds=second)
                        
                        cust_id = random.choice(customer_ids) if random.random() < 0.60 else None
                        pay_method = random.choices(PAYMENT_METHODS, weights=[45, 25, 25, 5])[0]
                        order_type = random.choices(ORDER_TYPES, weights=[55, 30, 15])[0]
                        
                        # Generate items (combo)
                        chosen_prods = get_realistic_combo(products_seeded)
                        
                        subtotal = Decimal('0.00')
                        tax_amount = Decimal('0.00')
                        items_info = []
                        
                        for prod in chosen_prods:
                            qty = random.randint(1, 3)
                            price = Decimal(str(prod['selling_price']))
                            gst = Decimal(str(prod['gst_rate']))
                            
                            line_total = price * qty
                            line_tax = line_total * (gst / Decimal('100.00'))
                            
                            subtotal += line_total
                            tax_amount += line_tax
                            
                            items_info.append((prod['id'], qty, float(price), 0.0, float(line_total), trans_dt))
                            
                        total_amount = subtotal + tax_amount
                        discount = Decimal('0.00')
                        sale_num = f"SR-SALE-{outlet_id}-{year}-{month:02d}-{total_sales_count:07d}"
                        
                        # Build sale insert
                        sale_args = []
                        sale_cols = []
                        
                        if 'outlet_id' in s_cols:
                            sale_cols.append('outlet_id')
                            sale_args.append(outlet_id)
                        if 'store_id' in s_cols:
                            sale_cols.append('store_id')
                            sale_args.append(outlet_id)
                        if 'organization_id' in s_cols:
                            sale_cols.append('organization_id')
                            sale_args.append(org_id)
                        if 'user_id' in s_cols:
                            sale_cols.append('user_id')
                            sale_args.append(user_id)
                        if 'customer_id' in s_cols:
                            sale_cols.append('customer_id')
                            sale_args.append(cust_id)
                        if 'sale_number' in s_cols:
                            sale_cols.append('sale_number')
                            sale_args.append(sale_num)
                        if 'subtotal' in s_cols:
                            sale_cols.append('subtotal')
                            sale_args.append(float(subtotal))
                        if 'tax_amount' in s_cols:
                            sale_cols.append('tax_amount')
                            sale_args.append(float(tax_amount))
                        if 'discount_amount' in s_cols:
                            sale_cols.append('discount_amount')
                            sale_args.append(float(discount))
                        if 'total_amount' in s_cols:
                            sale_cols.append('total_amount')
                            sale_args.append(float(total_amount))
                        if 'payment_method' in s_cols:
                            sale_cols.append('payment_method')
                            sale_args.append(pay_method)
                        if 'payment_status' in s_cols:
                            sale_cols.append('payment_status')
                            sale_args.append('COMPLETED')
                        if 'amount_paid' in s_cols:
                            sale_cols.append('amount_paid')
                            sale_args.append(float(total_amount))
                        if 'status' in s_cols:
                            sale_cols.append('status')
                            sale_args.append('COMPLETED')
                        if 'notes' in s_cols:
                            sale_cols.append('notes')
                            sale_args.append(f"Sale at outlet {outlet_id}")
                        if 'order_type' in s_cols:
                            sale_cols.append('order_type')
                            sale_args.append(order_type)
                        if 'sale_date' in s_cols:
                            sale_cols.append('sale_date')
                            sale_args.append(trans_dt)
                        if 'transaction_date' in s_cols:
                            sale_cols.append('transaction_date')
                            sale_args.append(trans_dt)
                        if 'created_at' in s_cols:
                            sale_cols.append('created_at')
                            sale_args.append(trans_dt)
                        if 'updated_at' in s_cols:
                            sale_cols.append('updated_at')
                            sale_args.append(trans_dt)
                            
                        sales_tuples.append(tuple(sale_args))
                        sale_items_data.append(items_info)
                        
                        # Track daily cash/upi/card for last 30 days
                        if d in last_30_days:
                            day_close_sums[dc_key][pay_method] += float(total_amount)
                            
                        total_sales_count += 1
                        
            # Manual chunking of sales to safely retrieve all RETURNING ids
            if sales_tuples:
                chunk_size = 1000
                inserted_ids = []
                for i in range(0, len(sales_tuples), chunk_size):
                    chunk_tuples = sales_tuples[i:i+chunk_size]
                    sales_query = f"INSERT INTO sales ({', '.join(sale_cols)}) VALUES %s RETURNING id"
                    execute_values(cur, sales_query, chunk_tuples, page_size=len(chunk_tuples))
                    inserted_ids.extend([r[0] for r in cur.fetchall()])
                
                # Build sale items tuples
                items_tuples = []
                for s_id, items_list in zip(inserted_ids, sale_items_data):
                    for item in items_list:
                        item_args = []
                        if 'sale_id' in si_cols:
                            item_args.append(s_id)
                        if 'product_id' in si_cols:
                            item_args.append(item[0])
                        if 'quantity' in si_cols:
                            item_args.append(item[1])
                        if 'unit_price' in si_cols:
                            item_args.append(item[2])
                        if 'discount_percent' in si_cols:
                            item_args.append(item[3])
                        if 'line_total' in si_cols:
                            item_args.append(item[4])
                        if 'created_at' in si_cols:
                            item_args.append(item[5])
                            
                        items_tuples.append(tuple(item_args))
                        total_items_count += 1
                        
                # Bulk Insert items for this month/year chunk
                # Find column names without sale_id and dynamic values
                item_insert_cols = []
                if 'sale_id' in si_cols: item_insert_cols.append('sale_id')
                if 'product_id' in si_cols: item_insert_cols.append('product_id')
                if 'quantity' in si_cols: item_insert_cols.append('quantity')
                if 'unit_price' in si_cols: item_insert_cols.append('unit_price')
                if 'discount_percent' in si_cols: item_insert_cols.append('discount_percent')
                if 'line_total' in si_cols: item_insert_cols.append('line_total')
                if 'created_at' in si_cols: item_insert_cols.append('created_at')
                
                items_query = f"INSERT INTO sale_items ({', '.join(item_insert_cols)}) VALUES %s"
                execute_values(cur, items_query, items_tuples, page_size=2000)
                
            print(f"   ✓ Seeded sales chunk for Year {year} Month {month}.")
            conn.commit()
            
        print(f"   ✓ Seeded {total_sales_count} sales and {total_items_count} sale items in total.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Sales seeding failed: {e}")
        raise e

    # 9. ALERTS
    print("\n[9/10] Seeding Alerts (Exactly 8 rows)...")
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='alerts'")
        alt_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in alerts: {alt_cols}")
        
        alerts_seeded = 0
        
        # A. 3 low stock alerts (queried from inventory table where stock < 20)
        cur.execute("""
            SELECT outlet_id, product_id, current_stock 
            FROM inventory 
            WHERE current_stock < 20 
            LIMIT 3
        """)
        low_stock_rows = cur.fetchall()
        for out_id, prod_id, stock in low_stock_rows:
            cur.execute("SELECT name FROM products WHERE id = %s", (prod_id,))
            p_name = cur.fetchone()[0]
            
            insert_cols = []
            val_placeholders = []
            val_args = []
            
            if 'outlet_id' in alt_cols:
                insert_cols.append('outlet_id')
                val_placeholders.append('%s')
                val_args.append(out_id)
            if 'alert_type' in alt_cols:
                insert_cols.append('alert_type')
                val_placeholders.append('%s')
                val_args.append('low_stock')
            if 'severity' in alt_cols:
                insert_cols.append('severity')
                val_placeholders.append('%s')
                val_args.append('high')
            if 'title' in alt_cols:
                insert_cols.append('title')
                val_placeholders.append('%s')
                val_args.append('Low Stock warning')
            if 'message' in alt_cols:
                insert_cols.append('message')
                val_placeholders.append('%s')
                val_args.append(f"Stock levels for {p_name} are below reorder threshold of 20 portion (current: {stock}).")
            if 'product_id' in alt_cols:
                insert_cols.append('product_id')
                val_placeholders.append('%s')
                val_args.append(prod_id)
            if 'is_read' in alt_cols:
                insert_cols.append('is_read')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'is_resolved' in alt_cols:
                insert_cols.append('is_resolved')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'is_acknowledged' in alt_cols:
                insert_cols.append('is_acknowledged')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'status' in alt_cols:
                insert_cols.append('status')
                val_placeholders.append('%s')
                val_args.append('active')
            if 'created_at' in alt_cols:
                insert_cols.append('created_at')
                val_placeholders.append('NOW()')
                
            query = f"INSERT INTO alerts ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)})"
            cur.execute(query, tuple(val_args))
            alerts_seeded += 1

        # B. 2 overstock alerts
        cur.execute("""
            SELECT outlet_id, product_id, current_stock 
            FROM inventory 
            WHERE current_stock > 150 
            LIMIT 2
        """)
        overstock_rows = cur.fetchall()
        for out_id, prod_id, stock in overstock_rows:
            cur.execute("SELECT name FROM products WHERE id = %s", (prod_id,))
            p_name = cur.fetchone()[0]
            
            insert_cols = []
            val_placeholders = []
            val_args = []
            
            if 'outlet_id' in alt_cols:
                insert_cols.append('outlet_id')
                val_placeholders.append('%s')
                val_args.append(out_id)
            if 'alert_type' in alt_cols:
                insert_cols.append('alert_type')
                val_placeholders.append('%s')
                val_args.append('sales_anomaly')
            if 'severity' in alt_cols:
                insert_cols.append('severity')
                val_placeholders.append('%s')
                val_args.append('medium')
            if 'title' in alt_cols:
                insert_cols.append('title')
                val_placeholders.append('%s')
                val_args.append('Overstock alert')
            if 'message' in alt_cols:
                insert_cols.append('message')
                val_placeholders.append('%s')
                val_args.append(f"Product {p_name} has high stock levels ({stock} portion). Spoilage risk.")
            if 'product_id' in alt_cols:
                insert_cols.append('product_id')
                val_placeholders.append('%s')
                val_args.append(prod_id)
            if 'is_read' in alt_cols:
                insert_cols.append('is_read')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'is_resolved' in alt_cols:
                insert_cols.append('is_resolved')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'is_acknowledged' in alt_cols:
                insert_cols.append('is_acknowledged')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'status' in alt_cols:
                insert_cols.append('status')
                val_placeholders.append('%s')
                val_args.append('active')
            if 'created_at' in alt_cols:
                insert_cols.append('created_at')
                val_placeholders.append('NOW()')
                
            query = f"INSERT INTO alerts ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)})"
            cur.execute(query, tuple(val_args))
            alerts_seeded += 1

        # C. 2 invoice overdue alerts
        for idx in range(min(2, len(overdue_po_ref))):
            out_id, po_id, sup_name, amt = overdue_po_ref[idx]
            
            insert_cols = []
            val_placeholders = []
            val_args = []
            
            if 'outlet_id' in alt_cols:
                insert_cols.append('outlet_id')
                val_placeholders.append('%s')
                val_args.append(out_id)
            if 'alert_type' in alt_cols:
                insert_cols.append('alert_type')
                val_placeholders.append('%s')
                val_args.append('supplier_delay')
            if 'severity' in alt_cols:
                insert_cols.append('severity')
                val_placeholders.append('%s')
                val_args.append('medium')
            if 'title' in alt_cols:
                insert_cols.append('title')
                val_placeholders.append('%s')
                val_args.append('Payment Overdue')
            if 'message' in alt_cols:
                insert_cols.append('message')
                val_placeholders.append('%s')
                val_args.append(f"Supplier Invoice PO-{po_id} from {sup_name} is unpaid and overdue by ₹{amt:.2f}.")
            if 'is_read' in alt_cols:
                insert_cols.append('is_read')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'is_resolved' in alt_cols:
                insert_cols.append('is_resolved')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'is_acknowledged' in alt_cols:
                insert_cols.append('is_acknowledged')
                val_placeholders.append('%s')
                val_args.append(False)
            if 'status' in alt_cols:
                insert_cols.append('status')
                val_placeholders.append('%s')
                val_args.append('active')
            if 'created_at' in alt_cols:
                insert_cols.append('created_at')
                val_placeholders.append('NOW()')
                
            query = f"INSERT INTO alerts ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)})"
            cur.execute(query, tuple(val_args))
            alerts_seeded += 1

        # D. 1 forecast deviation alert
        cur.execute("SELECT id FROM products WHERE name = 'Chicken Biryani' OR name = 'Veg Biryani' LIMIT 1")
        biryani_row = cur.fetchone()
        biryani_id = biryani_row[0] if biryani_row else products_seeded[0]['id']
        
        insert_cols = []
        val_placeholders = []
        val_args = []
        
        if 'outlet_id' in alt_cols:
            insert_cols.append('outlet_id')
            val_placeholders.append('%s')
            val_args.append(outlet_ids[0])
        if 'alert_type' in alt_cols:
            insert_cols.append('alert_type')
            val_placeholders.append('%s')
            val_args.append('forecast_deviation')
        if 'severity' in alt_cols:
            insert_cols.append('severity')
            val_placeholders.append('%s')
            val_args.append('medium')
        if 'title' in alt_cols:
            insert_cols.append('title')
            val_placeholders.append('%s')
            val_args.append('Sales Deviation')
        if 'message' in alt_cols:
            insert_cols.append('message')
            val_placeholders.append('%s')
            val_args.append("Biryani sales 18% below forecast this week")
        if 'product_id' in alt_cols:
            insert_cols.append('product_id')
            val_placeholders.append('%s')
            val_args.append(biryani_id)
        if 'is_read' in alt_cols:
            insert_cols.append('is_read')
            val_placeholders.append('%s')
            val_args.append(False)
        if 'is_resolved' in alt_cols:
            insert_cols.append('is_resolved')
            val_placeholders.append('%s')
            val_args.append(False)
        if 'is_acknowledged' in alt_cols:
            insert_cols.append('is_acknowledged')
            val_placeholders.append('%s')
            val_args.append(False)
        if 'status' in alt_cols:
            insert_cols.append('status')
            val_placeholders.append('%s')
            val_args.append('active')
        if 'created_at' in alt_cols:
            insert_cols.append('created_at')
            val_placeholders.append('NOW()')
            
        query = f"INSERT INTO alerts ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)})"
        cur.execute(query, tuple(val_args))
        alerts_seeded += 1
        
        conn.commit()
        print(f"   ✓ Seeded exactly {alerts_seeded} active alerts.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Alerts seeding failed: {e}")
        raise e

    # 10. DAY CLOSES
    print("\n[10/10] Seeding Day Close Records...")
    try:
        # Check column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='day_closes'")
        dc_cols = [r[0] for r in cur.fetchall()]
        print(f"Columns in day_closes: {dc_cols}")
        
        day_close_count = 0
        for idx, target_date in enumerate(sorted(last_30_days)):
            # The last 2 days get discrepancies (not verified)
            # Since sorted(last_30_days) goes chronologically, the last two items in sorted list are the most recent two days
            is_unverified = idx >= len(last_30_days) - 2
            
            for outlet_id in outlet_ids:
                daily_stats = day_close_sums.get((outlet_id, target_date), {'CASH': 0.0, 'UPI': 0.0, 'CARD': 0.0})
                
                cash_sales = daily_stats.get('CASH', 0.0)
                upi_total = daily_stats.get('UPI', 0.0)
                card_total = daily_stats.get('CARD', 0.0)
                
                opening_float = 5000.0
                expected_cash = opening_float + cash_sales
                
                variance = random.choice([-150.0, -100.0, 50.0, 100.0]) if is_unverified else 0.0
                physical_cash = expected_cash + variance
                
                status = 'Discrepancy' if variance != 0.0 else 'Matched'
                notes = f"Day close verified. Cash matching." if status == 'Matched' else f"Cash discrepancy of ₹{variance} reported."
                
                opened_at = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=11)
                closed_at = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=23)
                
                insert_cols = []
                val_placeholders = []
                val_args = []
                
                if 'outlet_id' in dc_cols:
                    insert_cols.append('outlet_id')
                    val_placeholders.append('%s')
                    val_args.append(outlet_id)
                if 'date' in dc_cols:
                    insert_cols.append('date')
                    val_placeholders.append('%s')
                    val_args.append(target_date)
                if 'opening_float' in dc_cols:
                    insert_cols.append('opening_float')
                    val_placeholders.append('%s')
                    val_args.append(opening_float)
                if 'opening_cash' in dc_cols:
                    insert_cols.append('opening_cash')
                    val_placeholders.append('%s')
                    val_args.append(opening_float)
                if 'closing_float' in dc_cols:
                    insert_cols.append('closing_float')
                    val_placeholders.append('%s')
                    val_args.append(physical_cash)
                if 'expected_cash' in dc_cols:
                    insert_cols.append('expected_cash')
                    val_placeholders.append('%s')
                    val_args.append(expected_cash)
                if 'physical_cash' in dc_cols:
                    insert_cols.append('physical_cash')
                    val_placeholders.append('%s')
                    val_args.append(physical_cash)
                if 'variance' in dc_cols:
                    insert_cols.append('variance')
                    val_placeholders.append('%s')
                    val_args.append(variance)
                if 'reconciliation_status' in dc_cols:
                    insert_cols.append('reconciliation_status')
                    val_placeholders.append('%s')
                    val_args.append(status)
                if 'notes' in dc_cols:
                    insert_cols.append('notes')
                    val_placeholders.append('%s')
                    val_args.append(notes)
                if 'opened_by' in dc_cols:
                    insert_cols.append('opened_by')
                    val_placeholders.append('%s')
                    val_args.append(user_id)
                if 'closed_by' in dc_cols:
                    insert_cols.append('closed_by')
                    val_placeholders.append('%s')
                    val_args.append(user_id)
                if 'opened_at' in dc_cols:
                    insert_cols.append('opened_at')
                    val_placeholders.append('%s')
                    val_args.append(opened_at)
                if 'closed_at' in dc_cols:
                    insert_cols.append('closed_at')
                    val_placeholders.append('%s')
                    val_args.append(closed_at)
                if 'upi_total' in dc_cols:
                    insert_cols.append('upi_total')
                    val_placeholders.append('%s')
                    val_args.append(upi_total)
                if 'card_total' in dc_cols:
                    insert_cols.append('card_total')
                    val_placeholders.append('%s')
                    val_args.append(card_total)
                if 'is_verified' in dc_cols:
                    insert_cols.append('is_verified')
                    val_placeholders.append('%s')
                    val_args.append(not is_unverified)
                if 'created_at' in dc_cols:
                    insert_cols.append('created_at')
                    val_placeholders.append('NOW()')
                if 'updated_at' in dc_cols:
                    insert_cols.append('updated_at')
                    val_placeholders.append('NOW()')
                    
                query = f"INSERT INTO day_closes ({', '.join(insert_cols)}) VALUES ({', '.join(val_placeholders)})"
                cur.execute(query, tuple(val_args))
                day_close_count += 1
                
        conn.commit()
        print(f"   ✓ Seeded {day_close_count} Day Close records.")
    except Exception as e:
        conn.rollback()
        print(f"   ✗ Day Close seeding failed: {e}")
        raise e

    # Final counts print
    print("\n" + "=" * 70)
    print("📊 SEEDING COMPLETED SUCCESSFULLY - TABLE ROW COUNTS:")
    print("=" * 70)
    for table in tables_to_truncate:
        try:
            cur.execute("SELECT exists(SELECT * FROM information_schema.tables WHERE table_name=%s)", (table,))
            exists = cur.fetchone()[0]
            if exists:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"   ✓ {table:25} : {count:8} rows")
        except Exception:
            conn.rollback()
    print("=" * 70)

    cur.close()
    conn.close()
    print("👋 Seeding process finished successfully.")

if __name__ == '__main__':
    main()
