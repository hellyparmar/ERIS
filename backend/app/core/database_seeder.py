"""
Database Seeding Module
Automatically seeds database with initial data on first startup if empty.
Designed to run asynchronously without blocking application startup.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import random
from typing import Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models import (
    User, Product, Customer, Inventory, SaleTransaction, Alert,
    Role, Organization, Outlet, Supplier, AlertType, AlertSeverity
)
from app.core.security import hash_password

logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Handles automatic database seeding."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize seeder with optional session."""
        self.db = db
    
    def _get_db(self) -> Session:
        """Get database session."""
        if self.db is None:
            return SessionLocal()
        return self.db
    
    def _close_db(self, db: Session):
        """Close database session if we created it."""
        if self.db is None:
            db.close()
    
    def is_database_empty(self) -> bool:
        """Check if database has any data."""
        db = self._get_db()
        try:
            user_count = db.query(func.count(User.id)).scalar()
            return user_count == 0
        except Exception as e:
            logger.error(f"Error checking if database is empty: {e}")
            return True
        finally:
            self._close_db(db)
    
    def get_data_summary(self) -> dict:
        """Get count of existing data."""
        db = self._get_db()
        try:
            return {
                "users": db.query(func.count(User.id)).scalar() or 0,
                "products": db.query(func.count(Product.id)).scalar() or 0,
                "customers": db.query(func.count(Customer.id)).scalar() or 0,
                "inventory": db.query(func.count(Inventory.id)).scalar() or 0,
                "sales": db.query(func.count(SaleTransaction.id)).scalar() or 0,
                "alerts": db.query(func.count(Alert.id)).scalar() or 0,
            }
        except Exception as e:
            logger.warning(f"Error getting data summary: {e}")
            return {}
        finally:
            self._close_db(db)
    
    def seed_database(self, 
                      num_days: int = 365,
                      num_products: int = 50,
                      num_customers: int = 20) -> bool:
        """
        Seed database with realistic initial data.
        
        Args:
            num_days: Number of days of sales data to generate
            num_products: Number of products to create
            num_customers: Number of customers to create
            
        Returns:
            True if successful, False otherwise
        """
        db = self._get_db()
        
        try:
            # Check if already seeded
            if not self.is_database_empty():
                logger.info("Database already has data, skipping seed operation")
                return True
            
            logger.info("🌱 Starting database seeding...")
            
            # 1. Create default Organization
            org = db.query(Organization).filter(Organization.id == 1).first()
            if not org:
                org = Organization(id=1, name="Default Organization")
                db.add(org)
                db.flush()
                logger.info("✅ Created default organization")
            
            # 2. Create roles
            roles = {
                "admin": Role(id=1, name="admin", description="System Administrator", is_system_role=True),
                "manager": Role(id=2, name="manager", description="Store Manager", is_system_role=True),
                "staff": Role(id=3, name="staff", description="Staff", is_system_role=True)
            }
            for role_name, role_obj in roles.items():
                existing_role = db.query(Role).filter(Role.name == role_name).first()
                if not existing_role:
                    db.add(role_obj)
            db.flush()
            logger.info("✅ Created system roles")
            
            # 3. Create users
            admin_user = db.query(User).filter(User.email == "admin@eris.local").first()
            if not admin_user:
                admin_user = User(
                    username="admin",
                    email="admin@eris.local",
                    password_hash=hash_password("AdminPassword123!"),
                    first_name="System",
                    last_name="Administrator",
                    role_id=1,
                    organization_id=1,
                    is_active=True
                )
                db.add(admin_user)
            
            helly_user = db.query(User).filter(User.email == "hellyparmar306@gmail.com").first()
            if not helly_user:
                helly_user = User(
                    username="hellyparmar",
                    email="hellyparmar306@gmail.com",
                    password_hash=hash_password("password123"),
                    first_name="Helly",
                    last_name="Parmar",
                    role_id=1,
                    organization_id=1,
                    is_active=True
                )
                db.add(helly_user)
            db.flush()
            logger.info("✅ Created default and portfolio admin users")
            
            # 4. Create sample outlets
            cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata']
            outlets = []
            for i, city in enumerate(cities, 1):
                existing_outlet = db.query(Outlet).filter(Outlet.name == f"{city} Outlet").first()
                if not existing_outlet:
                    outlet = Outlet(
                        organization_id=1,
                        name=f"{city} Outlet",
                        code=f"OUTLET-{100+i}",
                        address=f"Street {i}, {city}",
                        city=city,
                        state=city,
                        postal_code=f"40000{i}",
                        phone=f"+91-900000000{i}",
                        email=f"{city.lower()}@eris.local",
                        is_active=True
                    )
                    db.add(outlet)
                    outlets.append(outlet)
                else:
                    outlets.append(existing_outlet)
            db.flush()
            logger.info(f"✅ Created {len(outlets)} outlets")
            
            # 5. Create sample suppliers
            suppliers = []
            for i in range(1, 6):
                existing_supplier = db.query(Supplier).filter(Supplier.name == f"Supplier {i}").first()
                if not existing_supplier:
                    supplier = Supplier(
                        name=f"Supplier {i}",
                        supplier_code=f"SUP-{1000+i}",
                        contact_person=f"Contact Person {i}",
                        phone=f"+91-888888888{i}",
                        email=f"supplier{i}@example.com",
                        address=f"Supplier Address {i}",
                        city="Mumbai",
                        state="Maharashtra",
                        is_active=True,
                        organization_id="1"
                    )
                    db.add(supplier)
                    suppliers.append(supplier)
                else:
                    suppliers.append(existing_supplier)
            db.flush()
            logger.info(f"✅ Created {len(suppliers)} suppliers")
            
            # 6. Create sample products
            categories = ['Electronics', 'Groceries', 'Clothing', 'Home & Kitchen', 'Sports', 'Beauty']
            products = []
            for i in range(1, num_products + 1):
                category = random.choice(categories)
                supplier = random.choice(suppliers)
                product = Product(
                    sku_code=f"SKU-{1000 + i}",
                    name=f"Product {i} - {category}",
                    category=category,
                    base_price=round(random.uniform(100.0, 5000.0), 2),
                    cost_price=round(random.uniform(50.0, 2500.0), 2),
                    gst_rate=random.choice([5, 12, 18, 28]),
                    hsn_code=f"HSN-{random.randint(100000, 999999)}",
                    supplier_id=supplier.id,
                    reorder_point=random.randint(20, 50),
                    max_stock=random.randint(100, 500),
                    unit="pcs",
                    is_active=True
                )
                products.append(product)
                db.add(product)
            db.flush()
            logger.info(f"✅ Created {len(products)} products")
            
            # 7. Create inventory records
            for outlet in outlets:
                for product in products:
                    stock = random.randint(50, 500)
                    reserved = random.randint(0, min(stock // 10, 50))
                    
                    inventory = Inventory(
                        outlet_id=outlet.id,
                        product_id=product.id,
                        current_stock=stock,
                        reserved_stock=reserved,
                        last_restocked_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                    )
                    db.add(inventory)
            db.flush()
            logger.info("✅ Created inventory records")
            
            # 8. Create sample customers
            cities_list = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Pune', 'Hyderabad']
            customers = []
            org_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
            
            for i in range(1, num_customers + 1):
                customer = Customer(
                    organization_id=org_uuid,
                    name=f"Customer {i}",
                    phone=f"+91-70000000{i:02d}",
                    email=f"customer{i}@example.local",
                    city=random.choice(cities_list),
                    state=random.choice(cities_list),
                    pincode=f"4000{i:02d}",
                    is_active=True,
                    customer_type="b2c"
                )
                customers.append(customer)
                db.add(customer)
            db.flush()
            logger.info(f"✅ Created {len(customers)} customers")
            
            # 9. Create sales transactions
            sales_count = 0
            start_date = datetime.utcnow() - timedelta(days=num_days)
            
            for day_offset in range(num_days):
                transaction_date = start_date + timedelta(days=day_offset)
                num_sales_today = random.randint(5, 15)
                
                for _ in range(num_sales_today):
                    product = random.choice(products)
                    outlet = random.choice(outlets)
                    quantity = random.randint(1, 5)
                    discount_percent = round(random.uniform(0.0, 15.0), 2)
                    
                    subtotal = product.base_price * quantity
                    discount_amount = subtotal * (discount_percent / 100.0)
                    taxable_amount = subtotal - discount_amount
                    gst_amount = taxable_amount * (product.gst_rate / 100.0)
                    total_amount = taxable_amount + gst_amount
                    
                    sale = SaleTransaction(
                        outlet_id=outlet.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=product.base_price,
                        discount_percent=discount_percent,
                        total_amount=round(total_amount, 2),
                        gst_amount=round(gst_amount, 2),
                        payment_method=random.choice(['cash', 'card', 'upi', 'wallet']),
                        transaction_at=transaction_date,
                        cashier_id=1
                    )
                    db.add(sale)
                    sales_count += 1
            db.flush()
            logger.info(f"✅ Created {sales_count} sales transactions ({num_days} days)")
            
            # 10. Create sample alerts
            alert_templates = [
                ("low_stock", AlertSeverity.medium, "Product {} is running low on stock"),
                ("stockout", AlertSeverity.critical, "Product {} is out of stock"),
                ("sales_anomaly", AlertSeverity.high, "Product {} showing high demand"),
            ]
            
            alerts_created = 0
            for _ in range(15):
                template = random.choice(alert_templates)
                product = random.choice(products)
                outlet = random.choice(outlets)
                
                alert = Alert(
                    outlet_id=outlet.id,
                    product_id=product.id,
                    alert_type=AlertType(template[0]),
                    severity=template[1],
                    message=template[2].format(product.name),
                    is_acknowledged=random.choice([True, False])
                )
                db.add(alert)
                alerts_created += 1
            db.flush()
            logger.info(f"✅ Created {alerts_created} alerts")
            
            db.commit()
            
            # Log summary
            summary = self.get_data_summary()
            logger.info("🎉 Database seeding completed successfully!")
            logger.info("📊 Data Summary:")
            for key, value in summary.items():
                logger.info(f"   • {key}: {value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error seeding database: {e}", exc_info=True)
            db.rollback()
            return False
        finally:
            self._close_db(db)


async def seed_database_async(num_days: int = 365, 
                               num_products: int = 50,
                               num_customers: int = 20) -> bool:
    """
    Async wrapper for database seeding.
    Runs seeding in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    seeder = DatabaseSeeder()
    
    try:
        result = await loop.run_in_executor(
            None,
            seeder.seed_database,
            num_days,
            num_products,
            num_customers
        )
        return result
    except Exception as e:
        logger.error(f"Error in async seeding: {e}", exc_info=True)
        return False


def seed_database_sync(num_days: int = 365,
                       num_products: int = 50,
                       num_customers: int = 20) -> bool:
    """Synchronous wrapper for database seeding."""
    seeder = DatabaseSeeder()
    return seeder.seed_database(num_days, num_products, num_customers)
