"""
seed_database.py - Comprehensive database seeding
Generates realistic Indian QSR/Restaurant chain data.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict
import random
import uuid
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import holidays
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.models.organization import Organization
from app.models.users import Role, User
from app.models.outlet import Outlet
from app.models.customers import Customer
from app.models.employee_models import Employee, EmployeeRole
from app.models.models_v6 import Supplier, Product, Sale, SaleItem
from app.models.inventory import Inventory
from app.models.day_close import DayClose

logger = logging.getLogger(__name__)

def pg_or_sqlite_insert(session: AsyncSession, model):
    try:
        bind = getattr(session, 'bind', None) or getattr(session, '_bind', None)
        if bind and hasattr(bind, 'dialect') and bind.dialect.name == "sqlite":
            return sqlite_insert(model)
    except Exception:
        pass
    return pg_insert(model)

async def safe_set_config(session: AsyncSession, key: str, val: str):
    try:
        bind = getattr(session, 'bind', None) or getattr(session, '_bind', None)
        if bind and hasattr(bind, 'dialect') and bind.dialect.name == "postgresql":
            await session.execute(text(f"SELECT set_config('{key}', :t, false)"), {"t": val})
    except Exception:
        pass

# Real cities with specific lat/lon and weather profiles
OUTLETS = [
    {"name": "Mumbai Central", "city": "Mumbai", "lat": 19.0760, "lon": 72.8777, "type": "coastal", "monsoon_months": [6, 7, 8, 9]},
    {"name": "Delhi Connaught", "city": "Delhi", "lat": 28.7041, "lon": 77.1025, "type": "extreme", "monsoon_months": [7, 8]},
    {"name": "Bangalore Indiranagar", "city": "Bangalore", "lat": 12.9716, "lon": 77.5946, "type": "mild", "monsoon_months": []},
    {"name": "Chennai T-Nagar", "city": "Chennai", "lat": 13.0827, "lon": 80.2707, "type": "coastal", "monsoon_months": [10, 11]},
    {"name": "Jaipur Pink City", "city": "Jaipur", "lat": 26.9124, "lon": 75.7873, "type": "extreme", "monsoon_months": [7, 8]},
]

# Extended Indian Menu
MENU = {
    "Starters": [
        {"name": "Paneer Tikka", "price": 180, "prep": 15, "cost": 60},
        {"name": "Veg Spring Rolls", "price": 120, "prep": 12, "cost": 40},
        {"name": "Chicken Wings", "price": 220, "prep": 18, "cost": 80},
        {"name": "Crispy Corn", "price": 140, "prep": 10, "cost": 45},
        {"name": "Mushroom Pepper Dry", "price": 160, "prep": 12, "cost": 50},
        {"name": "Gobi Manchurian", "price": 130, "prep": 15, "cost": 40},
        {"name": "Chicken Tikka", "price": 240, "prep": 20, "cost": 90},
        {"name": "Hara Bhara Kabab", "price": 160, "prep": 15, "cost": 50},
        {"name": "Chilli Chicken Dry", "price": 210, "prep": 15, "cost": 75},
        {"name": "Fish Tikka", "price": 290, "prep": 20, "cost": 120},
    ],
    "Mains": [
        {"name": "Butter Chicken", "price": 280, "prep": 20, "cost": 90},
        {"name": "Dal Makhani", "price": 180, "prep": 15, "cost": 50},
        {"name": "Paneer Butter Masala", "price": 240, "prep": 18, "cost": 80},
        {"name": "Kadai Chicken", "price": 300, "prep": 22, "cost": 100},
        {"name": "Palak Paneer", "price": 220, "prep": 15, "cost": 75},
        {"name": "Mix Veg Curry", "price": 190, "prep": 15, "cost": 60},
        {"name": "Mutton Rogan Josh", "price": 380, "prep": 30, "cost": 150},
        {"name": "Chicken Tikka Masala", "price": 310, "prep": 20, "cost": 110},
        {"name": "Dal Tadka", "price": 150, "prep": 10, "cost": 40},
        {"name": "Aloo Gobi", "price": 170, "prep": 15, "cost": 50},
    ],
    "Breads": [
        {"name": "Butter Naan", "price": 40, "prep": 8, "cost": 10},
        {"name": "Garlic Naan", "price": 50, "prep": 8, "cost": 12},
        {"name": "Tandoori Roti", "price": 30, "prep": 6, "cost": 8},
        {"name": "Laccha Paratha", "price": 60, "prep": 10, "cost": 15},
        {"name": "Pudina Paratha", "price": 65, "prep": 10, "cost": 18},
        {"name": "Cheese Naan", "price": 80, "prep": 10, "cost": 30},
        {"name": "Missi Roti", "price": 45, "prep": 8, "cost": 12},
        {"name": "Roomali Roti", "price": 50, "prep": 5, "cost": 15},
    ],
    "Rice & Biryani": [
        {"name": "Chicken Biryani", "price": 320, "prep": 25, "cost": 120},
        {"name": "Veg Biryani", "price": 220, "prep": 20, "cost": 80},
        {"name": "Jeera Rice", "price": 120, "prep": 10, "cost": 30},
        {"name": "Steamed Rice", "price": 90, "prep": 10, "cost": 20},
        {"name": "Mutton Biryani", "price": 420, "prep": 30, "cost": 180},
        {"name": "Peas Pulao", "price": 140, "prep": 15, "cost": 40},
        {"name": "Egg Biryani", "price": 240, "prep": 20, "cost": 90},
    ],
    "Desserts": [
        {"name": "Gulab Jamun", "price": 80, "prep": 5, "cost": 20},
        {"name": "Ice Cream", "price": 100, "prep": 3, "cost": 30},
        {"name": "Brownie with Ice Cream", "price": 150, "prep": 8, "cost": 50},
        {"name": "Rasmalai", "price": 120, "prep": 5, "cost": 40},
        {"name": "Gajar Ka Halwa", "price": 130, "prep": 10, "cost": 50},
        {"name": "Kulfi", "price": 90, "prep": 5, "cost": 25},
    ],
    "Beverages": [
        {"name": "Sweet Lassi", "price": 60, "prep": 5, "cost": 15},
        {"name": "Soft Drink", "price": 40, "prep": 2, "cost": 15},
        {"name": "Fresh Lime Soda", "price": 50, "prep": 5, "cost": 10},
        {"name": "Masala Chai", "price": 30, "prep": 5, "cost": 5},
        {"name": "Cold Coffee", "price": 120, "prep": 5, "cost": 30},
        {"name": "Mango Lassi", "price": 80, "prep": 5, "cost": 20},
        {"name": "Buttermilk", "price": 40, "prep": 2, "cost": 10},
    ]
}

class Scaler:
    """Calculate daily sales multipliers based on business patterns"""
    
    def __init__(self, start_date: datetime, end_date: datetime, outlet_data: dict):
        self.outlet_data = outlet_data
        self.in_holidays = holidays.IN(years=list(range(start_date.year, end_date.year + 1)))
        
    def get_festival_boost(self, date: datetime) -> float:
        if date.date() in self.in_holidays:
            return random.uniform(1.5, 2.5)
        if (date + timedelta(days=1)).date() in self.in_holidays:
            return random.uniform(1.2, 1.8)
        return 1.0
    
    def get_weekend_boost(self, date: datetime) -> float:
        if date.weekday() == 5: return random.uniform(1.3, 1.5)
        if date.weekday() == 6: return random.uniform(1.4, 1.6)
        return 1.0
    
    def get_monsoon_penalty(self, date: datetime) -> float:
        if date.month in self.outlet_data["monsoon_months"]:
            return random.uniform(0.7, 0.85)
        return 1.0
        
    def get_time_multiplier(self, hour: int) -> float:
        if 12 <= hour < 15: return 2.5
        elif 19 <= hour < 22: return 3.0
        elif 8 <= hour < 11: return 1.5
        elif 11 <= hour < 12 or 15 <= hour < 19: return 1.0
        else: return 0.3
        
    def get_trend_multiplier(self, start_date: datetime, current_date: datetime) -> float:
        days_passed = (current_date - start_date).days
        months_passed = days_passed / 30.0
        return 1.0 + (0.01 * months_passed)

async def check_data_exists(session: AsyncSession, table: str = "organizations") -> bool:
    try:
        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        return result.scalar() > 0
    except:
        return False

DEFAULT_TENANT_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "spiceroute.in") # Deterministic UUID for the tenant

async def bootstrap_essentials(session: AsyncSession) -> Dict:
    """Fast, safe, idempotent generation of essential records (org, admin user)."""
    stats = {"status": "pending", "records": {}, "errors": []}
    await safe_set_config(session, 'app.current_tenant', str(DEFAULT_TENANT_ID))
    
    try:
        if await check_data_exists(session, "users"):
            logger.info("✓ Essentials already bootstrapped")
            stats["status"] = "skipped"
            return stats
            
        logger.info("🚀 Bootstrapping essential database records...")
        await safe_set_config(session, 'app.current_tenant_id', str(DEFAULT_TENANT_ID))
        
        # 1. Organizations & Roles
        await session.execute(
            pg_or_sqlite_insert(session, Organization).values([
                {"id": 1, "tenant_id": DEFAULT_TENANT_ID, "name": 'Spice Route Retail', "is_active": True}
            ]).on_conflict_do_update(
                index_elements=['id'],
                set_={"tenant_id": DEFAULT_TENANT_ID, "name": "Spice Route Retail"}
            )
        )
        
        roles = []
        for i, role in enumerate(["Admin", "Manager", "Staff", "Guest"]):
            roles.append({"id": i+1, "name": role, "is_active": True})
        if roles:
            await session.execute(
                pg_or_sqlite_insert(session, Role).values(roles).on_conflict_do_nothing()
            )
        await session.commit()
        
        # 2. Admin User
        from app.core.security import hash_password
        admin_hash = hash_password('admin123')
        manager_hash = hash_password('manager123')
        analyst_hash = hash_password('analyst123')
        
        await session.execute(
            pg_or_sqlite_insert(session, User).values([
            {
                "id": 999, "organization_id": 1,
                "username": 'admin', "email": 'admin@eris.com', "first_name": 'System',
                "last_name": 'Admin', "password_hash": admin_hash, "role_id": 1, "is_active": True
            },
            {
                "id": 998, "organization_id": 1,
                "username": 'manager', "email": 'manager@eris.com', "first_name": 'Demo',
                "last_name": 'Manager', "password_hash": manager_hash, "role_id": 2, "is_active": True
            },
            {
                "id": 997, "organization_id": 1,
                "username": 'analyst', "email": 'analyst@eris.com', "first_name": 'Demo',
                "last_name": 'Analyst', "password_hash": analyst_hash, "role_id": 2, "is_active": True
            }]).on_conflict_do_nothing()
        )
        await session.commit()

        stats["status"] = "success"
        logger.info("✅ Bootstrap complete!")
        
    except Exception as e:
        logger.error(f"❌ Bootstrap failed: {e}", exc_info=True)
        await session.rollback()
        stats["status"] = "failed"
        stats["errors"].append(str(e))
        raise
    
    return stats

async def generate_historical_data(session: AsyncSession) -> Dict:
    """Heavy generation of history (outlets, products, sales, inventory) over 1-2 years."""
    stats = {"status": "pending", "records": {}, "errors": []}
    np.random.seed(42)
    random.seed(42)
    
    await safe_set_config(session, 'app.current_tenant', str(DEFAULT_TENANT_ID))
    
    try:
        if await check_data_exists(session, "outlets"):
            logger.info("✓ Historical data already exists")
            stats["status"] = "skipped"
            return stats
            
        logger.info("🚀 Starting realistic historical data generation (1 year)...")
        await safe_set_config(session, 'app.current_tenant_id', str(DEFAULT_TENANT_ID))
        
        # Outlets
        outlets_data = []
        for i, out in enumerate(OUTLETS):
            outlets_data.append({
                "id": i+1, "tenant_id": DEFAULT_TENANT_ID, "organization_id": 1,
                "name": out['name'], "city": out['city'], "latitude": out['lat'], "longitude": out['lon'],
                "phone": f'+91999999999{i}', "email": f'store{i+1}@spiceroute.in', "is_active": True
            })
        if outlets_data:
            await session.execute(pg_insert(Outlet).values(outlets_data).on_conflict_do_nothing())
        await session.commit()
        
        # Users
        users_data = []
        from app.core.security import hash_password
        demo_hash = hash_password('user123')
        
        for i in range(1, 11):
            users_data.append({
                "id": i, "organization_id": 1,
                "username": f'user{i}', "email": f'user{i}@eris.com', "first_name": 'User',
                "last_name": str(i), "password_hash": demo_hash, "role_id": 2,
                "outlet_id": ((i-1)%len(OUTLETS))+1, "is_active": True
            })
        if users_data:
            await session.execute(pg_insert(User).values(users_data).on_conflict_do_nothing())
        await session.commit()
        
        # Suppliers
        suppliers = ["Metro Cash & Carry", "Udaan", "Local Mandi", "FreshProduce India"]
        supp_ids = []
        supp_data = []
        for i, supp in enumerate(suppliers):
            s_id = i + 1
            supp_ids.append(s_id)
            supp_data.append({
                "id": s_id, "organization_id": 1,
                "name": supp, "phone": f'+91888888888{i}',
                "city": 'Mumbai', "is_active": True
            })
        if supp_data:
            await session.execute(pg_insert(Supplier).values(supp_data).on_conflict_do_nothing())
        await session.commit()
        
        # Products
        products = []
        prod_data = []
        prod_idx = 1
        for cat_name, items in MENU.items():
            for item in items:
                p_id = prod_idx
                sku = f"SKU{prod_idx:04d}"
                s_id = random.choice(supp_ids)
                
                prod_data.append({
                    "id": p_id, "tenant_id": DEFAULT_TENANT_ID, "organization_id": 1, "supplier_id": s_id,
                    "sku": sku, "name": item["name"], "cost_price": item["cost"], "selling_price": item["price"],
                    "hsn_code": "HSN1234", "current_stock": 100, "reorder_level": 20, "reorder_quantity": 50,
                    "is_active": True, "is_deleted": False, "is_perishable": False
                })
                
                products.append({
                    "id": p_id, "name": item["name"], "sku": sku, "price": item["price"], "cost": item["cost"]
                })
                prod_idx += 1
        if prod_data:
            await session.execute(pg_insert(Product).values(prod_data).on_conflict_do_nothing())
        await session.commit()
        
        # Employees
        emp_id = 1
        emp_data = []
        for outlet_idx in range(len(OUTLETS)):
            for display_role, enum_role in [("Manager", "manager"), ("Chef", "other"), ("Waiter", "sales_associate"), ("Waiter", "sales_associate"), ("Cashier", "cashier"), ("Delivery", "other")]:
                emp_data.append({
                    "id": emp_id, "outlet_id": outlet_idx+1,
                    "first_name": display_role, "last_name": f"Emp{emp_id}",
                    "phone": f'987654{emp_id:04d}', "position": display_role,
                    "department": "Operations", "employment_type": "Full-time",
                    "joining_date": datetime(2023,1,1).date(), "base_salary": 20000,
                    "is_active": True, "is_deleted": False
                })
                emp_id += 1
        if emp_data:
            await session.execute(pg_insert(Employee).values(emp_data).on_conflict_do_nothing())
        await session.commit()
        
        # Customers
        logger.info("Creating Customers...")
        customers = []
        cust_data = []
        now_dt = datetime.utcnow()
        for c in range(1, 101):
            cust_data.append({
                "id": c, "tenant_id": DEFAULT_TENANT_ID, "organization_id": 1,
                "phone": f'99999{c:05d}', "first_name": "Customer", "last_name": str(c),
                "created_at": now_dt, "updated_at": now_dt
            })
            customers.append(c)
        if cust_data:
            await session.execute(pg_insert(Customer).values(cust_data).on_conflict_do_nothing())
        await session.commit()
        
        regulars = customers[:20]
        occasional = customers[20:80]
        one_time = customers[80:]
        
        def get_random_customer():
            r = random.random()
            if r < 0.3: return random.choice(regulars)
            elif r < 0.6: return random.choice(occasional)
            else: return random.choice(one_time)
            
        # Sales, Day Close & Inventory History
        logger.info("Creating Sales & Day Close History (3 Days for Testing)...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        # Initialize Inventory
        inv_data = []
        for outlet_idx in range(len(OUTLETS)):
            for p in products:
                inv_data.append({
                    "tenant_id": DEFAULT_TENANT_ID, "outlet_id": outlet_idx+1, "product_id": p["id"], "current_stock": random.randint(50, 200), "reserved_stock": 0
                })
        if inv_data:
            await session.execute(pg_insert(Inventory).values(inv_data).on_conflict_do_nothing())
        await session.commit()
        
        sale_batch = []
        item_batch = []
        dc_batch = []
        inventory_tracking = { (o+1, p["id"]): random.randint(50, 200) for o in range(len(OUTLETS)) for p in products }
        
        global_sale_id = 1
        global_item_id = 1
        scalers = [Scaler(start_date, end_date, out) for out in OUTLETS]
        
        day = start_date
        while day <= end_date:
            date_str = day.date().isoformat()
            
            for outlet_idx, out in enumerate(OUTLETS):
                outlet_id = outlet_idx + 1
                scaler = scalers[outlet_idx]
                
                fest_boost = scaler.get_festival_boost(day)
                weekend_boost = scaler.get_weekend_boost(day)
                monsoon_pen = scaler.get_monsoon_penalty(day)
                trend_boost = scaler.get_trend_multiplier(start_date, day)
                
                base_orders = 80
                daily_orders = int(base_orders * fest_boost * weekend_boost * monsoon_pen * trend_boost)
                
                if random.random() < 0.05: daily_orders = int(daily_orders * 1.5)
                
                daily_cash = 0.0
                daily_card = 0.0
                
                for _ in range(daily_orders):
                    hour = random.randint(8, 22)
                    minute = random.randint(0, 59)
                    order_time = day.replace(hour=hour, minute=minute, tzinfo=timezone.utc)
                    
                    time_mult = scaler.get_time_multiplier(hour)
                    num_items = random.randint(1, max(1, int(4 * time_mult)))
                    
                    subtotal = 0.0
                    s_id = global_sale_id
                    global_sale_id += 1
                    
                    for _ in range(num_items):
                        p = random.choice(products)
                        qty = random.randint(1, 3)
                        line_total = float(p["price"] * qty)
                        
                        i_id = global_item_id
                        global_item_id += 1
                        item_batch.append({
                            "id": i_id, "organization_id": 1, "sale_id": s_id, "product_id": p["id"],
                            "quantity": qty, "unit_price": float(p["price"]), "line_total": line_total, "discount_percent": 0.0
                        })
                        subtotal += line_total
                        
                        inventory_tracking[(outlet_id, p["id"])] -= qty
                        if inventory_tracking[(outlet_id, p["id"])] < 20:
                            inventory_tracking[(outlet_id, p["id"])] += random.randint(100, 200)
                    
                    tax = float(subtotal * 0.05)
                    total = subtotal + tax
                    
                    pay_method = random.choice(["cash", "card", "upi", "card"])
                    if pay_method == "cash": daily_cash += total
                    else: daily_card += total
                    
                    c_id = get_random_customer() if random.random() > 0.2 else None
                    
                    sale_batch.append({
                        "id": s_id, "tenant_id": DEFAULT_TENANT_ID, "organization_id": 1, "outlet_id": outlet_id, "customer_id": c_id, "user_id": None,
                        "sale_date": order_time, "total_amount": total, "subtotal": subtotal, "tax_amount": tax, "discount_amount": 0.0,
                        "payment_method": pay_method, "sale_number": f"INV-{uuid.uuid4().hex[:8].upper()}", "payment_status": "paid",
                        "status": "completed"
                    })
                
                opening_float = 5000.0
                expected_cash = opening_float + daily_cash
                physical_cash = expected_cash + random.choices([0.0, -50.0, 50.0, -100.0], weights=[0.9, 0.04, 0.04, 0.02])[0]
                variance = physical_cash - expected_cash
                recon_status = 'MATCHED' if variance == 0 else ('SHORTAGE' if variance < 0 else 'OVERAGE')
                
                dc_batch.append({
                    "outlet_id": outlet_id, "date": datetime.strptime(date_str, "%Y-%m-%d").date(),
                    "opening_float": opening_float, "closing_float": physical_cash, "expected_cash": expected_cash,
                    "physical_cash": physical_cash, "variance": variance, "reconciliation_status": recon_status,
                    "opened_by": 1, "opened_at": day.replace(hour=8, minute=0, tzinfo=timezone.utc), "closed_at": day.replace(hour=23, minute=30, tzinfo=timezone.utc)
                })
            
            if len(sale_batch) >= 200:
                await session.execute(pg_insert(Sale).values(sale_batch).on_conflict_do_nothing())
                
                await session.execute(pg_insert(SaleItem).values(item_batch).on_conflict_do_nothing())
                
                await session.execute(pg_insert(DayClose).values(dc_batch).on_conflict_do_nothing())
                
                await session.commit()
                sale_batch, item_batch, dc_batch = [], [], []
                
            day += timedelta(days=1)
            
        if sale_batch:
            await session.execute(pg_insert(Sale).values(sale_batch).on_conflict_do_nothing())
            await session.execute(pg_insert(SaleItem).values(item_batch).on_conflict_do_nothing())
            await session.execute(pg_insert(DayClose).values(dc_batch).on_conflict_do_nothing())
            
            await session.commit()
            
        inv_update_data = []
        for (o, p_id), qty in inventory_tracking.items():
            inv_update_data.append({"qty": qty, "o": o, "p_id": p_id})
        
        # Updating inventory safely with parameters
        if inv_update_data:
            await session.execute(
                text("UPDATE inventory SET current_stock = :qty WHERE outlet_id = :o AND product_id = :p_id"),
                inv_update_data
            )
        await session.commit()

        stats["status"] = "success"
        logger.info("✅ Seeding complete!")
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}", exc_info=True)
        await session.rollback()
        stats["status"] = "failed"
        stats["errors"].append(str(e))
        raise
    
    return stats

async def seed_database(session: AsyncSession, skip_if_exists: bool = True) -> Dict:
    """Wrapper to run both bootstrap and historical generation."""
    from app.models.base import Base
    conn = await session.connection()
    await conn.run_sync(Base.metadata.create_all)
    await bootstrap_essentials(session)
    return await generate_historical_data(session)

if __name__ == "__main__":
    import asyncio
    from app.database import AsyncSessionLocal
    async def run():
        async with AsyncSessionLocal() as session:
            await seed_database(session, skip_if_exists=False)
    asyncio.run(run())
