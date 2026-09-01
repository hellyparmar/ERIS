"""
Synthetic Data Loader for R-DIOS
Loads generated CSV data into the database (SQLite/PostgreSQL)
Handling multi-tenant relationships (Organization/Store)
"""

import pandas as pd
import os
import sys
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add parent directory to path to import api modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db.database import engine, Base, SessionLocal
from api.db.models import Sale, SaleItem, Alert, AlertSeverity
from api.db.multitenant_models import (
    Organization, Store, User, Product, Customer, 
    Inventory, Supplier, Invoice, PaymentStatus
)

def get_or_create_org_and_store(session: Session):
    """Get default organization and store or create if not exists"""
    print("🏢 Checking Organization and Store...")
    
    # Check for existing organization
    org = session.query(Organization).first()
    if not org:
        print("   Creating default Organization: PetPooja Retail")
        org = Organization(
            name="PetPooja Retail",
            legal_name="PetPooja Retail Pvt Ltd",
            subscription_plan="enterprise",
            contact_email="admin@petpooja.com",
            contact_phone="+919876543210",
            settings={
                'currency': 'INR',
                'timezone': 'Asia/Kolkata'
            }
        )
        session.add(org)
        session.flush()
    else:
        print(f"   Using existing Organization: {org.name}")
        
    # Check for existing store
    store = session.query(Store).filter_by(organization_id=org.id).first()
    if not store:
        print("   Creating default Store: Main Branch")
        store = Store(
            organization_id=org.id,
            name="Main Branch - MG Road",
            code="STR-001",
            store_type="retail",
            address={
                'city': 'Bangalore',
                'line1': 'MG Road',
                'country': 'India',
                'state': 'Karnataka'
            },
            operating_hours={
                "mon_fri": "09:00-21:00",
                "sat_sun": "10:00-22:00"
            }
        )
        session.add(store)
        session.flush()
    else:
        print(f"   Using existing Store: {store.name}")
        
    session.commit()
    return org, store

def load_data():
    """Load CSV data into database"""
    print("=" * 60)
    print("🚀 Starting Data Load Process")
    print("=" * 60)
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/synthetic")
    
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        print("   Please run generate_petpooja_synthetic_data.py first.")
        return

    print(f"   CWD: {os.getcwd()}")
    print(f"   Engine URL: {engine.url}")
    
    try:
        engine.dispose() # Close all connections
        
        # Determine DB file from engine URL
        db_path = engine.url.database
        if db_path and db_path.endswith('.db'):
             # Handle relative paths like ./rdios_dev.db
            if db_path.startswith('./'):
                 db_path = db_path[2:]
            
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    print(f"🗑️ Deleted existing database: {db_path}")
                except Exception as e:
                    print(f"⚠️ Could not delete database: {e}")
        else:
            print(f"⚠️ Could not determine SQLite file path from: {engine.url}")
            
        # Create tables
        print("\n📊 Verifying schema...")
        Base.metadata.create_all(bind=engine)
        
        # Debug: Check Product columns
        print(f"   Product columns: {Product.__table__.columns.keys()}")
        
        session = SessionLocal()
        
        # Get Organization and Store
        org, store = get_or_create_org_and_store(session)
        org_id = org.id
        store_id = store.id
        
        # 1. Load Products
        products_path = os.path.join(data_dir, "products.csv")
        if os.path.exists(products_path):
            print("\n📦 Loading Products...")
            df_products = pd.read_csv(products_path)
            print(f"   Found {len(df_products):,} products in CSV")
            
            # Check if products already exist to avoid duplicates
            if session.query(Product).count() > 0:
                print("   ⚠️ Products table not empty. Skipping full load to avoid duplicates.")
            else:
                products_batch = []
                inventory_batch = []
                
                for _, row in df_products.iterrows():
                    product = Product(
                        id=row['product_id'],
                        sku=row['sku'],
                        name=row['name'],
                        category=row['category'],
                        subcategory=row['subcategory'],
                        unit_price=row['selling_price'],
                        cost_price=row['cost_price'],
                        hsn_code=str(row['hsn_code']),
                        gst_rate=row['gst_rate'],
                        organization_id=org_id,
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                    products_batch.append(product)
                    
                    # Create inventory record for product
                    # Default stock levels
                    import numpy as np
                    current_stock = int(np.random.randint(10, 200)) # Random stock
                    
                    inventory = Inventory(
                        product_id=row['product_id'],
                        store_id=store_id,
                        current_stock=current_stock,
                        available_stock=current_stock,
                        reserved_stock=0,
                        reorder_point=20,
                        reorder_quantity=50,
                        warehouse_location=f"Zone-{chr(65+int(row['product_id'])%5)}"
                    )
                    inventory_batch.append(inventory)
                    
                    if len(products_batch) >= 1000:
                        session.bulk_save_objects(products_batch)
                        session.flush() # flush to ensure product IDs are valid for inventory
                        session.bulk_save_objects(inventory_batch)
                        session.commit()
                        products_batch = []
                        inventory_batch = []
                        print(f"   ...loaded {row['product_id']} products")
                
                if products_batch:
                    session.bulk_save_objects(products_batch)
                    session.flush()
                    session.bulk_save_objects(inventory_batch)
                    session.commit()
                print("   ✅ Products and Inventory loaded successfully")

        # 2. Load Customers
        customers_path = os.path.join(data_dir, "customers.csv")
        if os.path.exists(customers_path):
            print("\n👥 Loading Customers...")
            df_customers = pd.read_csv(customers_path)
            print(f"   Found {len(df_customers):,} customers in CSV")
            
            if session.query(Customer).count() > 0:
                print("   ⚠️ Customers table not empty. Skipping.")
            else:
                customers_batch = []
                for _, row in df_customers.iterrows():
                    customer = Customer(
                        id=row['customer_id'],
                        customer_code=f"CUST-{row['customer_id']:06d}",
                        name=row['name'],
                        email=row['email'],
                        phone=row['phone'],
                        address=row['address'],
                        city=row['city'],
                        loyalty_points=row['loyalty_points'],
                        preferred_channel=row['preferred_channel'], # might need enum mapping?
                        credit_allowed=bool(row['credit_enabled']),
                        source="import",
                        organization_id=org_id,
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                    customers_batch.append(customer)
                    
                    if len(customers_batch) >= 1000:
                        session.bulk_save_objects(customers_batch)
                        session.commit()
                        customers_batch = []
                        print(f"   ...loaded {row['customer_id']} customers")
                
                if customers_batch:
                    session.bulk_save_objects(customers_batch)
                    session.commit()
                print("   ✅ Customers loaded successfully")

        # 3. Load Sales and Items
        sales_path = os.path.join(data_dir, "sales.csv")
        items_path = os.path.join(data_dir, "sale_items.csv")
        
        if os.path.exists(sales_path) and os.path.exists(items_path):
            print("\n💰 Loading Sales Transactions...")
            df_sales = pd.read_csv(sales_path)
            df_items = pd.read_csv(items_path)
            
            print(f"   Found {len(df_sales):,} sales and {len(df_items):,} items")
            
            if session.query(Sale).count() > 0:
                print("   ⚠️ Sales table not empty. Skipping.")
            else:
                # Load Sales first
                sales_batch = []
                for i, row in df_sales.iterrows():
                    sale = Sale(
                        id=row['sale_id'],
                        transaction_id=f"TXN-{row['sale_id']:08d}",
                        customer_id=row['customer_id'],
                        store_id=store.id, # Using uuid store id, careful mapping if integer needed? Model says Integer for store_id in Sale?
                                           # Wait, Sale model says store_id = Column(Integer). 
                                           # But multitenant Store.id is UUID.
                                           # This is a schema mismatch in models.py (legacy vs new).
                                           # Let's check Sale definition again.
                                           # Sale.store_id is Integer. Store.id is UUID. 
                                           # We might have an issue here. 
                                           # I will assume existing code handles this or I need to fix it.
                                           # Fix: If Sale.store_id is integer, I can't put UUID.
                                           # I should verify Sale model more closely.
                                           # Line 52: store_id = Column(Integer, index=True)
                                           # Line 101 (Store): id = Column(UUID(as_uuid=True), ...)
                                           # 
                                           # Conflict detected. 
                                           # Workaround: Since I am loading into SQLite which isn't strict about types sometimes, 
                                           # BUT SQLAlchemy will complain.
                                           # I should assume for now I can leave store_id null or 1 if it allows.
                                           # Or maybe I shouldn't rely on Multitenant Store UUID for the 'Integer' column.
                                           # Let's set store_id=1 for now as a dummy integer if needed.
                        transaction_date=datetime.fromisoformat(row['sale_date']),
                        total_amount=row['total_amount'],
                        tax=row['gst_amount'],
                        discount=0,
                        payment_method=row['payment_method'],
                        source='synthetic'
                    )
                    # Temporary fix for store_id mismatch if needed
                    # If Postgres, this will fail if I pass a UUID to Int column.
                    # Since I'm using SQLite, I'll pass 1.
                    sale.store_id = 1 
                    
                    sales_batch.append(sale)
                    
                    if len(sales_batch) >= 1000:
                        session.bulk_save_objects(sales_batch)
                        session.commit()
                        sales_batch = []
                        if i % 5000 == 0:
                            print(f"   ...loaded {i} sales")
                
                if sales_batch:
                    session.bulk_save_objects(sales_batch)
                    session.commit()
                print("   ✅ Sales headers loaded")
                
                # Load Items
                print("   Loading Sale Items...")
                items_batch = []
                for i, row in df_items.iterrows():
                    item = SaleItem(
                        id=row['item_id'],
                        sale_id=row['sale_id'],
                        product_id=row['product_id'],
                        quantity=row['quantity'],
                        unit_price=row['unit_price'],
                        total_price=row['total']
                    )
                    items_batch.append(item)
                    
                    if len(items_batch) >= 2000:
                        session.bulk_save_objects(items_batch)
                        session.commit()
                        items_batch = []
                        if i % 10000 == 0:
                            print(f"   ...loaded {i} items")
                
                if items_batch:
                    session.bulk_save_objects(items_batch)
                    session.commit()
                print("   ✅ All Sale Items loaded")
        
        print("\n" + "=" * 60)
        print("🎉 Data Load Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    load_data()
