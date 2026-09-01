"""
Canonical data generator for ERIS Restaurant Chain
"""

import os
import sys
import random
import asyncio
import logging
from datetime import datetime, timedelta

# Ensure backend modules can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
from sqlalchemy import text
from app.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("seed")

FESTIVALS = [
    {"name": "Makar Sankranti", "date": "2024-01-15", "boost": 1.25},
    {"name": "Republic Day", "date": "2024-01-26", "boost": 1.15},
    {"name": "Holi", "date": "2024-03-25", "boost": 1.35},
    {"name": "Eid ul-Fitr", "date": "2024-04-11", "boost": 1.30},
    {"name": "Independence Day", "date": "2024-08-15", "boost": 1.20},
    {"name": "Raksha Bandhan", "date": "2024-08-19", "boost": 1.25},
    {"name": "Ganesh Chaturthi", "date": "2024-09-07", "boost": 1.30},
    {"name": "Dussehra", "date": "2024-10-12", "boost": 1.40},
    {"name": "Diwali", "date": "2024-11-01", "boost": 1.60},
    {"name": "Christmas", "date": "2024-12-25", "boost": 1.25},
    {"name": "Makar Sankranti", "date": "2025-01-14", "boost": 1.25},
    {"name": "Republic Day", "date": "2025-01-26", "boost": 1.15},
    {"name": "Holi", "date": "2025-03-14", "boost": 1.35},
    {"name": "Eid ul-Fitr", "date": "2025-03-31", "boost": 1.30},
    {"name": "Independence Day", "date": "2025-08-15", "boost": 1.20},
    {"name": "Raksha Bandhan", "date": "2025-08-09", "boost": 1.25},
    {"name": "Ganesh Chaturthi", "date": "2025-08-27", "boost": 1.30},
    {"name": "Dussehra", "date": "2025-10-02", "boost": 1.40},
    {"name": "Diwali", "date": "2025-10-20", "boost": 1.60},
    {"name": "Christmas", "date": "2025-12-25", "boost": 1.25},
]

def get_seasonal_multiplier(date: datetime) -> float:
    month = date.month
    base_multiplier = 0.85 if 6 <= month <= 9 else (1.20 if month in [11, 12, 1, 2] else 1.0)
    for festival in FESTIVALS:
        festival_date = datetime.strptime(festival["date"], "%Y-%m-%d")
        days_diff = abs((date - festival_date).days)
        if days_diff <= 7:
            if days_diff == 0: return base_multiplier * festival["boost"]
            elif days_diff <= 3: return base_multiplier * (1 + (festival["boost"] - 1) * 0.7)
            else: return base_multiplier * (1 + (festival["boost"] - 1) * 0.4)
    if date.weekday() >= 5: base_multiplier *= 1.30
    return base_multiplier

async def clear_database(session):
    tables = ['sale_items', 'sales', 'alerts', 'employees', 'inventory', 'products', 
              'suppliers', 'users', 'outlets', 'roles', 'organizations', 'customers']
    for table in tables:
        try:
            await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        except Exception:
            pass
    await session.commit()

async def seed_all():
    async with AsyncSessionLocal() as session:
        logger.info("🧹 Wiping old data...")
        await clear_database(session)

        # 1. Organization
        logger.info("🏢 1. Creating Organization...")
        await session.execute(text("INSERT INTO organizations (id, name, email, is_active) VALUES (1, 'Spice Route Hospitality Pvt Ltd', 'admin@spiceroute.in', true) ON CONFLICT DO NOTHING"))
        
        # Roles
        for i, r in enumerate(['super_admin', 'area_manager', 'outlet_manager', 'staff'], 1):
            await session.execute(text(f"INSERT INTO roles (id, name, is_active) VALUES ({i}, '{r}', true) ON CONFLICT DO NOTHING"))
            
        # 2. Outlets
        logger.info("🏪 2. Creating Outlets...")
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Ahmedabad']
        for i, city in enumerate(cities, 1):
            await session.execute(text(f"INSERT INTO outlets (id, organization_id, name, city, phone, email, is_active) VALUES ({i}, 1, 'Spice Route {city}', '{city}', '+91900000000{i}', '{city.lower()}@spiceroute.in', true) ON CONFLICT DO NOTHING"))
            
        # 3. Users
        logger.info("👤 3. Creating Users...")
        await session.execute(text("INSERT INTO users (id, organization_id, username, email, first_name, last_name, password_hash, role_id, is_active) VALUES (1, 1, 'superadmin', 'admin@spiceroute.in', 'Raj', 'Malhotra', 'hash', 1, true) ON CONFLICT DO NOTHING"))
        user_id = 2
        for region in ['North', 'South', 'West']:
            await session.execute(text(f"INSERT INTO users (id, organization_id, username, email, first_name, last_name, password_hash, role_id, is_active) VALUES ({user_id}, 1, 'area_{region.lower()}', 'area.{region.lower()}@spiceroute.in', 'Manager', '{region}', 'hash', 2, true) ON CONFLICT DO NOTHING"))
            user_id += 1
        for i, city in enumerate(cities, 1):
            await session.execute(text(f"INSERT INTO users (id, organization_id, username, email, first_name, last_name, password_hash, role_id, is_active) VALUES ({user_id}, 1, 'mgr_{city.lower()}', 'mgr.{city.lower()}@spiceroute.in', 'Manager', '{city}', 'hash', 3, true) ON CONFLICT DO NOTHING"))
            user_id += 1

        # 4. Suppliers
        logger.info("🚚 4. Creating Suppliers...")
        suppliers = ['Fresh Farms', 'Raj Poultry', 'National Spices', 'Mega Dairy', 'Metro Wholesale', 'Local Produce']
        for i, sup in enumerate(suppliers, 1):
            await session.execute(text(f"INSERT INTO suppliers (id, organization_id, name, phone, email, city, is_active) VALUES ({i}, 1, '{sup}', '+9199999999{i:02d}', 'contact@{sup.replace(' ', '').lower()}.in', 'Mumbai', true) ON CONFLICT DO NOTHING"))

        # 5. Menu Items (Products) & 6. Ingredients
        logger.info("🍲 5 & 6. Creating Menu Items and Ingredients...")
        categories = ['North Indian', 'South Indian', 'Chinese', 'Beverages', 'Desserts', 'Breads', 'Starters', 'Rice']
        product_id = 1
        for c in categories:
            for i in range(10):
                cost = random.randint(40, 150)
                price = cost * random.uniform(2.5, 4.0)
                await session.execute(text(f"INSERT INTO products (id, organization_id, supplier_id, sku, name, cost_price, selling_price, current_stock, is_active) VALUES ({product_id}, 1, {random.randint(1,6)}, 'MENU-{c[:3].upper()}-{i:03d}', '{c} Item {i}', {cost:.2f}, {price:.2f}, 0, true) ON CONFLICT DO NOTHING"))
                product_id += 1
        
        # Ingredients (Inserted as products but act as ingredients)
        ingredients = [('Chicken (Frozen)', 'kg', 20), ('Basmati Rice', 'kg', 15), ('Paneer', 'kg', 10), ('Cooking Oil', 'litre', 10), ('Onions', 'kg', 25), ('Tomatoes', 'kg', 20), ('Heavy Cream', 'litre', 8), ('Butter', 'kg', 8), ('Masala Mix', 'kg', 5), ('Naan Dough', 'kg', 10)]
        for i in range(20): ingredients.append((f'Ingredient {i+11}', 'kg', random.randint(5, 30)))
        for ing, unit, reorder in ingredients:
            await session.execute(text(f"INSERT INTO products (id, organization_id, supplier_id, sku, name, cost_price, selling_price, current_stock, is_active) VALUES ({product_id}, 1, {random.randint(1,6)}, 'ING-{product_id:03d}', '{ing}', {random.randint(50, 500)}, 0, {random.randint(50, 200)}, true) ON CONFLICT DO NOTHING"))
            for outlet in range(1, 6):
                await session.execute(text(f"INSERT INTO inventory (id, outlet_id, product_id, current_stock) VALUES ({product_id*10+outlet}, {outlet}, {product_id}, {random.randint(20, 100)}) ON CONFLICT DO NOTHING"))
            product_id += 1

        # 7. Customers
        logger.info("👥 7. Creating Customers...")
        names = ["Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Anjali"]
        for i in range(1, 501):
            city = random.choice(cities)
            phone = f"98{random.randint(10000000, 99999999)}"
            name = f"{random.choice(names)} Customer{i}"
            await session.execute(text(f"INSERT INTO customers (id, organization_id, name, phone, city, is_active) VALUES ({i}, 1, '{name}', '{phone}', '{city}', true) ON CONFLICT DO NOTHING"))

        # 8. Sales (18 Months)
        logger.info("📈 8. Generating 18 Months of Sales...")
        start_date = datetime(2024, 12, 1)
        end_date = datetime(2026, 6, 30)
        days = (end_date - start_date).days
        
        sale_id = 1
        sale_item_id = 1
        sale_batch = []
        item_batch = []
        
        for d in range(days):
            current_date = start_date + timedelta(days=d)
            mult = get_seasonal_multiplier(current_date)
            for outlet in range(1, 6):
                daily_sales = int(random.randint(30, 80) * mult)
                for _ in range(daily_sales):
                    hour = random.choices([13, 14, 20, 21, 16], weights=[3, 2, 4, 3, 1])[0]
                    sale_time = current_date.replace(hour=hour, minute=random.randint(0, 59))
                    order_type = random.choices(['Dine-in', 'Delivery', 'Takeaway'], weights=[0.45, 0.35, 0.20])[0]
                    
                    qty = random.randint(1, 4)
                    pid = random.randint(1, 80)
                    price = 250.0
                    total = qty * price
                    tax = total * 0.05
                    grand = total + tax
                    
                    sale_batch.append(f"({sale_id}, {outlet}, 1, {random.randint(1,500)}, 'ORD-{sale_id:08d}', {total:.2f}, {tax:.2f}, 0, {grand:.2f}, 'upi', 'COMPLETED', {grand:.2f}, 'COMPLETED', '{order_type}', '{sale_time.isoformat()}')")
                    item_batch.append(f"({sale_item_id}, {sale_id}, {pid}, {qty}, {price:.2f}, 0, {total:.2f})")
                    
                    sale_id += 1
                    sale_item_id += 1
                    
                    if len(sale_batch) >= 2000:
                        await session.execute(text(f"INSERT INTO sales (id, outlet_id, user_id, customer_id, sale_number, subtotal, tax_amount, discount_amount, total_amount, payment_method, payment_status, amount_paid, status, notes, sale_date) VALUES {','.join(sale_batch)} ON CONFLICT DO NOTHING"))
                        await session.execute(text(f"INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price, discount_percent, line_total) VALUES {','.join(item_batch)} ON CONFLICT DO NOTHING"))
                        await session.commit()
                        sale_batch = []
                        item_batch = []

        if sale_batch:
            await session.execute(text(f"INSERT INTO sales (id, outlet_id, user_id, customer_id, sale_number, subtotal, tax_amount, discount_amount, total_amount, payment_method, payment_status, amount_paid, status, notes, sale_date) VALUES {','.join(sale_batch)} ON CONFLICT DO NOTHING"))
            await session.execute(text(f"INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price, discount_percent, line_total) VALUES {','.join(item_batch)} ON CONFLICT DO NOTHING"))
            await session.commit()
        
        # 9. Supplier POs (Purchase Orders)
        logger.info("🧾 9. Creating Supplier POs...")
        inv_id = 1
        for outlet in range(1, 6):
            for month in range(1, 19):
                for _ in range(random.randint(3, 4)):
                    d = start_date + timedelta(days=month*30 - random.randint(1, 28))
                    if d > end_date: continue
                    total = random.randint(5000, 20000)
                    await session.execute(text(f"INSERT INTO purchase_orders (id, outlet_id, supplier_id, status, total_amount, expected_delivery_date, notes) VALUES ({inv_id}, {outlet}, '{random.randint(1,6)}', 'delivered', {total:.2f}, '{d.isoformat()}', 'Monthly PO') ON CONFLICT DO NOTHING"))
                    inv_id += 1
        
        # 10. Alerts
        logger.info("⚠️ 10. Creating Alerts...")
        for i in range(1, 11):
            await session.execute(text(f"INSERT INTO alerts (id, outlet_id, product_id, alert_type, severity) VALUES ({i}, {random.randint(1,5)}, {random.randint(81,110)}, 'low_stock', 'high') ON CONFLICT DO NOTHING"))

        # 11. Employees
        logger.info("👨‍🍳 11. Creating Employees...")
        emp_id = 1
        roles = ['Chef', 'Sous Chef', 'Server', 'Cashier', 'Manager']
        for outlet in range(1, 6):
            for _ in range(8):
                await session.execute(text(f"INSERT INTO employees (id, outlet_id, first_name, last_name, email, position, joining_date, is_active) VALUES ({emp_id}, {outlet}, 'Emp', '{emp_id}', 'emp{emp_id}@spiceroute.in', '{random.choice(roles)}', '2024-01-01', true) ON CONFLICT DO NOTHING"))
                emp_id += 1

        # 12. Day Close
        logger.info("📅 12. Creating Day Close records...")
        dc_id = 1
        for outlet in range(1, 6):
            for d in range(30):
                d_date = end_date - timedelta(days=d)
                await session.execute(text(f"INSERT INTO day_closes (id, outlet_id, date, opening_float, closing_float, expected_cash, physical_cash, variance, reconciliation_status, opened_by, closed_by) VALUES ({dc_id}, {outlet}, '{d_date.date().isoformat()}', 2000.0, 5000.0, 5000.0, 5000.0, 0, 'Matched', 1, 1) ON CONFLICT DO NOTHING"))
                dc_id += 1
                
        await session.commit()
        logger.info("✅ Database seeded successfully with Restaurant Chain metrics!")

if __name__ == '__main__':
    asyncio.run(seed_all())
