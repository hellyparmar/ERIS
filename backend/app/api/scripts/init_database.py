"""
Initialize Database
Creates tables and seeds initial data
Run this script to set up the database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import create_tables, drop_tables, engine, SessionLocal
from app.models.models import User, Product, Customer, Inventory, Sale, Alert, SyncLog, UserRole, AlertSeverity
from datetime import datetime, timedelta
import random
import hashlib

# Simple password hashing for seed data (use proper auth in production)
def hash_password(password: str) -> str:
    """Simple SHA256 hash for development (replace with bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database():
    """Seed database with initial data"""
    print("🌱 Seeding database with initial data...")
    
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = User(
            email="admin@rdios.com",
            hashed_password=hash_password("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("✅ Created admin user (admin@rdios.com / admin123)")
        
        # Create products
        categories = ['Electronics', 'Groceries', 'Clothing', 'Home & Kitchen', 'Sports', 'Beauty']
        products = []
        
        for i in range(1, 51):  # 50 products
            category = random.choice(categories)
            product = Product(
                sku=f"SKU-{1000 + i}",
                name=f"Product {i} - {category}",
                category=category,
                unit_price=round(random.uniform(10, 1000), 2),
                cost_price=round(random.uniform(5, 500), 2),
                description=f"High quality {category.lower()} product",
                source="manual"
            )
            products.append(product)
            db.add(product)
        
        db.commit()
        print(f"✅ Created {len(products)} products")
        
        # Create inventory for each product
        for product in products:
            stock = random.randint(0, 500)
            reserved = random.randint(0, min(stock, 50))
            
            inventory = Inventory(
                product_id=product.id,
                current_stock=stock,
                reserved_stock=reserved,
                available_stock=stock - reserved,
                reorder_point=random.randint(20, 50),
                reorder_quantity=random.randint(50, 200),
                warehouse_location=f"W{random.randint(1, 5)}-A{random.randint(1, 10)}",
                last_stocked_date=datetime.now() - timedelta(days=random.randint(0, 90))
            )
            db.add(inventory)
        
        db.commit()
        print("✅ Created inventory records")
        
        # Create customers
        for i in range(1, 21):  # 20 customers
            customer = Customer(
                customer_code=f"CUST-{2000 + i}",
                name=f"Customer {i}",
                email=f"customer{i}@example.com",
                phone=f"+91-98765{10000 + i}",
                city=random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata']),
                country="India",
                source="manual"
            )
            db.add(customer)
        
        db.commit()
        print("✅ Created 20 customers")
        
        # Create sales transactions (last 90 days)
        customers = db.query(Customer).all()
        
        for day in range(90):
            transaction_date = datetime.now() - timedelta(days=day)
            num_sales = random.randint(5, 20)  # 5-20 sales per day
            
            for _ in range(num_sales):
                product = random.choice(products)
                customer = random.choice(customers)
                quantity = random.randint(1, 10)
                discount = round(random.uniform(0, product.unit_price * 0.2), 2)
                tax = round((product.unit_price * quantity - discount) * 0.18, 2)  # 18% GST
                
                sale = Sale(
                    transaction_id=f"TXN-{transaction_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                    product_id=product.id,
                    customer_id=customer.id,
                    store_id=random.randint(1, 5),
                    transaction_date=transaction_date,
                    quantity=quantity,
                    unit_price=product.unit_price,
                    discount=discount,
                    tax=tax,
                    total_amount=(product.unit_price * quantity) - discount + tax,
                    payment_method=random.choice(['cash', 'card', 'upi', 'wallet']),
                    source="manual"
                )
                db.add(sale)
        
        db.commit()
        print("✅ Created sales transactions (90 days)")
        
        # Create some alerts
        alert_templates = [
            ("Low Stock Alert", "Product {} is running low on stock", "inventory", AlertSeverity.WARNING),
            ("Critical Stock", "Product {} is out of stock", "inventory", AlertSeverity.CRITICAL),
            ("High Demand", "Product {} showing high demand", "sales", AlertSeverity.INFO),
        ]
        
        for i in range(15):
            template = random.choice(alert_templates)
            product = random.choice(products)
            
            alert = Alert(
                severity=template[3],
                title=template[0],
                message=template[1].format(product.name),
                category=template[2],
                related_product_id=product.id,
                is_acknowledged=random.choice([True, False]),
                created_at=datetime.now() - timedelta(days=random.randint(0, 7))
            )
            db.add(alert)
        
        db.commit()
        print("✅ Created 15 alerts")
        
        print("\n🎉 Database seeded successfully!")
        print("\n📊 Summary:")
        print(f"   • 1 Admin user")
        print(f"   • {len(products)} Products")
        print(f"   • {len(products)} Inventory records")
        print(f"   • 20 Customers")
        print(f"   • ~900 Sales transactions")
        print(f"   • 15 Alerts")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 R-DIOS Database Initialization\n")
    
    # Ask user if they want to reset
    response = input("Do you want to reset the database? This will delete all existing data. (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n⚠️  Dropping existing tables...")
        drop_tables()
    
    # Create tables
    print("\n📦 Creating database tables...")
    create_tables()
    
    # Seed data
    seed_response = input("\nDo you want to seed the database with sample data? (yes/no): ")
    
    if seed_response.lower() == 'yes':
        seed_database()
    
    print("\n✅ Database initialization complete!")

if __name__ == "__main__":
    main()
