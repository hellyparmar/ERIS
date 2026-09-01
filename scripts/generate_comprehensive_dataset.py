"""
Comprehensive Universal Retail Dataset Generator for R-DIOS
PetPooja Internship Project

Generates realistic synthetic data across multiple retail domains:
- Electronics, Fashion, Home & Living, Beauty, Sports, Books, Toys, Automotive
- Products, Inventory, Sales, Customers, Suppliers, Alerts, Forecasts
"""

import os
import sys
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Set environment variable before importing
# Set environment variable before importing
os.environ['USE_SQLITE'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///./rdios.db'

from sqlalchemy.orm import Session
from api.db.database import engine, Base
from api.db.models import (
    Product, Inventory, Customer, Sale, SaleItem,
    Supplier, Alert, AlertSeverity
)

# Product catalog by domain
PRODUCT_CATALOG = {
    "Electronics": [
        ("Laptop Pro 15", "LAP-001", 75000, "Computers"),
        ("Laptop Air 13", "LAP-002", 65000, "Computers"),
        ("Gaming Laptop", "LAP-003", 95000, "Computers"),
        ("Wireless Mouse", "MOU-001", 800, "Accessories"),
        ("Gaming Mouse RGB", "MOU-002", 2500, "Accessories"),
        ("Mechanical Keyboard", "KEY-001", 3500, "Accessories"),
        ("Wireless Keyboard", "KEY-002", 1800, "Accessories"),
        ("USB-C Hub 7-in-1", "HUB-001", 2500, "Accessories"),
        ("Webcam HD 1080p", "CAM-001", 4500, "Accessories"),
        ("Headphones Wireless", "AUD-001", 5500, "Audio"),
        ("Earbuds Pro", "AUD-002", 8000, "Audio"),
        ("Bluetooth Speaker", "AUD-003", 3500, "Audio"),
        ("Smartphone 5G 128GB", "PHO-001", 25000, "Phones"),
        ("Smartphone Pro 256GB", "PHO-002", 45000, "Phones"),
        ("Tablet 10 inch", "TAB-001", 18000, "Tablets"),
        ("Smartwatch Fitness", "SMA-001", 12000, "Wearables"),
        ("Power Bank 20000mAh", "POW-001", 1500, "Accessories"),
        ("USB Cable Type-C", "CAB-001", 300, "Accessories"),
        ("Phone Case Premium", "CAS-001", 500, "Accessories"),
        ("Screen Protector", "SCR-001", 200, "Accessories"),
    ],
    "Fashion & Apparel": [
        ("Men's T-Shirt Cotton", "TSH-M-001", 599, "Men's Clothing"),
        ("Men's Jeans Slim Fit", "JEA-M-001", 1299, "Men's Clothing"),
        ("Men's Formal Shirt", "SHI-M-001", 899, "Men's Clothing"),
        ("Women's Kurti", "KUR-W-001", 799, "Women's Clothing"),
        ("Women's Jeans", "JEA-W-001", 1199, "Women's Clothing"),
        ("Women's Top", "TOP-W-001", 699, "Women's Clothing"),
        ("Men's Sneakers", "SNE-M-001", 2499, "Footwear"),
        ("Women's Sandals", "SAN-W-001", 1299, "Footwear"),
        ("Men's Watch Analog", "WAT-M-001", 3499, "Accessories"),
        ("Women's Handbag", "BAG-W-001", 1999, "Accessories"),
        ("Sunglasses UV Protection", "SUN-001", 899, "Accessories"),
        ("Belt Leather", "BEL-001", 599, "Accessories"),
    ],
    "Home & Living": [
        ("Bedsheet Cotton Double", "BED-001", 1299, "Bedroom"),
        ("Pillow Set of 2", "PIL-001", 799, "Bedroom"),
        ("Curtains Blackout", "CUR-001", 1499, "Decor"),
        ("Table Lamp LED", "LAM-001", 899, "Lighting"),
        ("Wall Clock Modern", "CLO-001", 699, "Decor"),
        ("Dinner Set 24pcs", "DIN-001", 2499, "Kitchen"),
        ("Cookware Set 5pcs", "COO-001", 3499, "Kitchen"),
        ("Water Purifier", "WAT-001", 8999, "Appliances"),
        ("Vacuum Cleaner", "VAC-001", 5999, "Appliances"),
        ("Iron Steam", "IRO-001", 1299, "Appliances"),
    ],
    "Beauty & Personal Care": [
        ("Face Cream SPF 30", "CRE-001", 499, "Skincare"),
        ("Face Wash Gel", "WAS-001", 299, "Skincare"),
        ("Shampoo Anti-Dandruff", "SHA-001", 349, "Haircare"),
        ("Conditioner Smooth", "CON-001", 399, "Haircare"),
        ("Lipstick Matte", "LIP-001", 599, "Makeup"),
        ("Perfume EDT 100ml", "PER-001", 1299, "Fragrance"),
        ("Body Lotion", "LOT-001", 449, "Bodycare"),
        ("Sunscreen SPF 50", "SUN-002", 549, "Skincare"),
    ],
    "Sports & Fitness": [
        ("Yoga Mat Premium", "YOG-001", 899, "Fitness"),
        ("Dumbbells 5kg Pair", "DUM-001", 1299, "Fitness"),
        ("Resistance Bands Set", "RES-001", 599, "Fitness"),
        ("Cricket Bat Kashmir Willow", "CRI-001", 1999, "Cricket"),
        ("Football Size 5", "FOO-001", 799, "Football"),
        ("Badminton Racket", "BAD-001", 1299, "Badminton"),
        ("Running Shoes Men", "RUN-M-001", 2999, "Footwear"),
        ("Sports Bottle 1L", "BOT-001", 299, "Accessories"),
    ],
    "Books & Stationery": [
        ("Notebook A4 Ruled", "NOT-001", 99, "Stationery"),
        ("Pen Set Blue 10pcs", "PEN-001", 50, "Stationery"),
        ("Pencil Set HB 12pcs", "PEN-002", 60, "Stationery"),
        ("Eraser White", "ERA-001", 10, "Stationery"),
        ("Sharpener Metal", "SHP-001", 15, "Stationery"),
        ("Highlighter Set 4 Colors", "HIG-001", 120, "Stationery"),
        ("Sticky Notes Pack", "STI-001", 80, "Stationery"),
        ("File Folder Plastic", "FIL-001", 40, "Stationery"),
    ],
    "Toys & Games": [
        ("Building Blocks 100pcs", "BLO-001", 799, "Construction"),
        ("Remote Control Car", "CAR-001", 1299, "Vehicles"),
        ("Puzzle 1000 pieces", "PUZ-001", 599, "Puzzles"),
        ("Board Game Family", "BOA-001", 899, "Board Games"),
        ("Soft Toy Teddy Bear", "TED-001", 499, "Soft Toys"),
    ],
    "Automotive": [
        ("Car Phone Holder", "HOL-001", 299, "Accessories"),
        ("Car Charger Dual USB", "CHA-001", 399, "Accessories"),
        ("Car Air Freshener", "FRE-001", 149, "Accessories"),
    ]
}

# Indian customer names
CUSTOMER_NAMES = [
    "Rajesh Kumar", "Priya Sharma", "Amit Patel", "Sneha Gupta", "Vikram Singh",
    "Anjali Reddy", "Rahul Verma", "Pooja Desai", "Arjun Nair", "Kavita Joshi",
    "Sanjay Mehta", "Neha Kapoor", "Karthik Iyer", "Divya Menon", "Rohit Agarwal",
    "Swati Kulkarni", "Manoj Rao", "Ritu Malhotra", "Anil Chopra", "Meera Pillai"
]

# Supplier companies
SUPPLIERS = [
    ("TechVision Electronics", "Electronics", "Mumbai", 7),
    ("StyleHub Fashion", "Fashion & Apparel", "Delhi", 5),
    ("HomeComfort Solutions", "Home & Living", "Bangalore", 6),
    ("BeautyPro Distributors", "Beauty & Personal Care", "Pune", 4),
    ("FitZone Sports", "Sports & Fitness", "Chennai", 5),
    ("BookWorld Supplies", "Books & Stationery", "Kolkata", 3),
    ("ToyLand Distributors", "Toys & Games", "Hyderabad", 4),
    ("AutoParts India", "Automotive", "Ahmedabad", 5),
]

def generate_dataset():
    """Generate comprehensive synthetic dataset"""
    print("🚀 Starting dataset generation for R-DIOS...")
    print("=" * 60)
    
    session = Session(engine)
    
    try:
        # Step 1: Create all tables
        print("\n📊 Creating database schema...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Schema created successfully")
        
        # Step 2: Generate Products & Inventory
        print("\n📦 Generating products and inventory...")
        products = []
        product_count = 0
        
        for domain, items in PRODUCT_CATALOG.items():
            for name, sku, price, subcategory in items:
                product = Product(
                    name=name,
                    category=domain,
                    sku=sku,
                    unit_price=price,
                    created_at=datetime.now() - timedelta(days=random.randint(30, 365))
                )
                session.add(product)
                session.flush()
                
                # Generate inventory
                base_stock = random.choice([50, 100, 150, 200, 250])
                current_stock = base_stock - random.randint(0, base_stock // 2)
                
                inventory = Inventory(
                    product_id=product.id,
                    current_stock=current_stock,
                    reserved_stock=random.randint(0, 10),
                    available_stock=current_stock - random.randint(0, 10),
                    reorder_point=20,
                    reorder_quantity=50,
                    warehouse_location=f"Warehouse-{random.choice(['A', 'B', 'C'])}"
                )
                session.add(inventory)
                products.append(product)
                product_count += 1
        
        session.commit()
        print(f"✅ Generated {product_count} products across {len(PRODUCT_CATALOG)} domains")
        
        # Step 3: Generate Customers
        print("\n👥 Generating customers...")
        customers = []
        for i, name in enumerate(CUSTOMER_NAMES * 8):  # ~160 customers
            customer = Customer(
                name=f"{name} {i//20 + 1}" if i >= 20 else name,
                email=f"{name.lower().replace(' ', '.')}_{i}@example.com",
                phone=f"+91{random.randint(7000000000, 9999999999)}",
                address=f"{random.randint(1, 999)} MG Road, {random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune'])}",
                loyalty_points=random.randint(0, 5000),
                created_at=datetime.now() - timedelta(days=random.randint(1, 730))
            )
            session.add(customer)
            customers.append(customer)
        
        session.commit()
        print(f"✅ Generated {len(customers)} customers")
        
        # Step 4: Generate Sales Transactions
        print("\n💰 Generating sales transactions...")
        sales_count = 0
        
        for _ in range(1200):  # 1200 transactions
            customer = random.choice(customers)
            sale_date = datetime.now() - timedelta(days=random.randint(0, 180))
            
            # Create sale
            sale = Sale(
                customer_id=customer.id,
                total_amount=0,  # Will calculate
                payment_method=random.choice(['cash', 'card', 'upi', 'wallet']),
                created_at=sale_date,
                transaction_date=sale_date
            )
            session.add(sale)
            session.flush()
            
            # Add 1-5 items per sale
            num_items = random.randint(1, 5)
            total = 0
            
            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                price = product.unit_price
                
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=price,
                    total_price=price * quantity
                )
                session.add(sale_item)
                total += price * quantity
            
            sale.total_amount = total
            sales_count += 1
        
        session.commit()
        print(f"✅ Generated {sales_count} sales transactions")
        
        # Step 5: Generate Suppliers
        print("\n🏭 Generating suppliers...")
        for name, category, location, lead_time in SUPPLIERS:
            supplier = Supplier(
                name=name,
                contact_person=random.choice(CUSTOMER_NAMES),
                email=f"contact@{name.lower().replace(' ', '')}.com",
                phone=f"+91{random.randint(7000000000, 9999999999)}",
                address=f"Industrial Area, {location}",
                created_at=datetime.now() - timedelta(days=random.randint(365, 1095))
            )
            session.add(supplier)
        
        session.commit()
        print(f"✅ Generated {len(SUPPLIERS)} suppliers")
        
        # Step 6: Generate Alerts
        print("\n🚨 Generating system alerts...")
        alert_messages = [
            ("Low stock alert for Wireless Mouse", AlertSeverity.WARNING, "stock"),
            ("Reorder required: Smartphone 5G 128GB", AlertSeverity.CRITICAL, "stock"),
            ("High demand detected for Gaming Laptop", AlertSeverity.INFO, "sales"),
            ("Stock running low: Men's T-Shirt Cotton", AlertSeverity.WARNING, "stock"),
            ("Supplier delivery delayed", AlertSeverity.WARNING, "system"),
        ]
        
        for message, severity, category in alert_messages:
            alert = Alert(
                severity=severity,
                category=category,
                title=message.split(':')[0],
                message=message,
                is_acknowledged=random.choice([True, False]),
                created_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            session.add(alert)
        
        session.commit()
        print(f"✅ Generated {len(alert_messages)} alerts")
        
        print("\n" + "=" * 60)
        print("🎉 Dataset generation complete!")
        print(f"📊 Summary:")
        print(f"   - Products: {product_count}")
        print(f"   - Customers: {len(customers)}")
        print(f"   - Sales: {sales_count}")
        print(f"   - Suppliers: {len(SUPPLIERS)}")
        print(f"   - Alerts: {len(alert_messages)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during dataset generation: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    generate_dataset()
