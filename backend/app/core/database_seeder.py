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

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import SessionLocal
from app.models.schema import (
    User, Product, Customer, InventoryMovement, Sale, Alert,
    UserRoleEnum, AlertSeverityEnum
)
from app.api.utils.auth import get_password_hash

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
                "sales": db.query(func.count(Sale.id)).scalar() or 0,
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
            
            # 1. Create admin user
            admin_user = User(
                email="admin@eris.local",
                hashed_password=get_password_hash("AdminPassword123!"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.flush()
            logger.info("✅ Created admin user")
            
            # 2. Create sample products
            categories = ['Electronics', 'Groceries', 'Clothing', 'Home & Kitchen', 'Sports', 'Beauty']
            products = []
            
            for i in range(1, num_products + 1):
                category = random.choice(categories)
                product = Product(
                    sku=f"SKU-{1000 + i}",
                    name=f"Product {i} - {category}",
                    category=category,
                    unit_price=round(random.uniform(100, 5000), 2),
                    cost_price=round(random.uniform(50, 2500), 2),
                    description=f"High quality {category.lower()} product",
                    source="system_seed"
                )
                products.append(product)
                db.add(product)
            
            db.flush()
            logger.info(f"✅ Created {len(products)} products")
            
            # 3. Create inventory
            for product in products:
                stock = random.randint(50, 500)
                reserved = random.randint(0, min(stock // 10, 50))
                
                inventory = Inventory(
                    product_id=product.id,
                    current_stock=stock,
                    reserved_stock=reserved,
                    available_stock=stock - reserved,
                    reorder_point=random.randint(20, 50),
                    reorder_quantity=random.randint(50, 200),
                    warehouse_location=f"W{random.randint(1, 5)}-A{random.randint(1, 10)}",
                    last_stocked_date=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )
                db.add(inventory)
            
            db.flush()
            logger.info("✅ Created inventory records")
            
            # 4. Create sample customers
            cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Pune', 'Hyderabad']
            customers = []
            
            for i in range(1, num_customers + 1):
                customer = Customer(
                    customer_code=f"CUST-{2000 + i}",
                    name=f"Customer {i}",
                    email=f"customer{i}@example.local",
                    phone=f"+91-{random.randint(7000000000, 9999999999)}",
                    city=random.choice(cities),
                    country="India",
                    source="system_seed"
                )
                customers.append(customer)
                db.add(customer)
            
            db.flush()
            logger.info(f"✅ Created {len(customers)} customers")
            
            # 5. Create sales transactions for last N days
            sales_count = 0
            start_date = datetime.utcnow() - timedelta(days=num_days)
            
            for day_offset in range(num_days):
                transaction_date = start_date + timedelta(days=day_offset)
                num_sales_today = random.randint(5, 30)
                
                for _ in range(num_sales_today):
                    product = random.choice(products)
                    customer = random.choice(customers)
                    quantity = random.randint(1, 10)
                    discount = round(random.uniform(0, min(product.unit_price * quantity * 0.2, 5000)), 2)
                    tax = round((product.unit_price * quantity - discount) * 0.18, 2)  # 18% GST
                    total = (product.unit_price * quantity) - discount + tax
                    
                    sale = Sale(
                        transaction_id=f"TXN-{transaction_date.strftime('%Y%m%d')}-{random.randint(10000, 99999)}",
                        product_id=product.id,
                        customer_id=customer.id,
                        store_id=random.randint(1, 5),
                        transaction_date=transaction_date,
                        quantity=quantity,
                        unit_price=product.unit_price,
                        discount=discount,
                        tax=tax,
                        total_amount=max(0, total),  # Ensure non-negative
                        payment_method=random.choice(['cash', 'card', 'upi', 'wallet']),
                        source="system_seed"
                    )
                    db.add(sale)
                    sales_count += 1
            
            db.flush()
            logger.info(f"✅ Created {sales_count} sales transactions ({num_days} days)")
            
            # 6. Create sample alerts
            alert_templates = [
                ("Low Stock Alert", "Product {} is running low on stock", "inventory", AlertSeverity.WARNING),
                ("Critical Stock", "Product {} is out of stock", "inventory", AlertSeverity.CRITICAL),
                ("High Demand", "Product {} showing high demand", "sales", AlertSeverity.INFO),
                ("Price Alert", "Product {} price changed", "product", AlertSeverity.INFO),
            ]
            
            alerts_created = 0
            for _ in range(20):
                template = random.choice(alert_templates)
                product = random.choice(products)
                
                alert = Alert(
                    severity=template[3],
                    title=template[0],
                    message=template[1].format(product.name),
                    category=template[2],
                    related_product_id=product.id,
                    is_acknowledged=random.choice([True, False]),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
                )
                db.add(alert)
                alerts_created += 1
            
            db.commit()
            logger.info(f"✅ Created {alerts_created} alerts")
            
            # Log summary
            summary = self.get_data_summary()
            logger.info("🎉 Database seeding completed successfully!")
            logger.info(f"📊 Data Summary:")
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
