"""
Database Initialization Script for R-DIOS v5.0
Loads enriched Olist data into PostgreSQL/SQLite
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import logging

# Import database and models from api package
from api.db.database import engine, Base, SessionLocal, create_tables
from api.db.models import (
    Product, Customer, Sale, Inventory, Alert,
    PaymentStatus
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseLoader:
    def __init__(self, processed_data_dir):
        self.data_dir = Path(processed_data_dir)
        self.db = SessionLocal()
        
    def drop_and_create_tables(self):
        """Drop existing tables and recreate them"""
        logger.info("🗑️  Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        logger.info("🏗️  Creating new tables...")
        create_tables()
        
    def load_products(self):
        """Load products with Indian enrichment"""
        logger.info("\n📦 Loading Products...")
        
        df = pd.read_csv(self.data_dir / 'products_enriched.csv')
        
        # Clean and prepare data
        df = df.where(pd.notnull(df), None)
        
        products = []
        for _, row in df.iterrows():
            # Get product name safely
            category_name = row.get('product_category_name', 'Unknown Product')
            product_name = category_name if category_name and pd.notnull(category_name) else 'Unknown Product'
            
            product = Product(
                sku=row['product_id'],
                name=str(product_name)[:255],
                category=row.get('product_category_name'),
                unit_price=float(row['selling_price_inr']) if pd.notnull(row.get('selling_price_inr')) else 0.0,
                cost_price=float(row['cost_price_inr']) if pd.notnull(row.get('cost_price_inr')) else 0.0,
                hsn_code=row.get('hsn_code'),
                gst_rate=float(row['gst_rate']) if pd.notnull(row.get('gst_rate')) else 18.0,
                is_dead_stock=bool(row.get('is_dead_stock', False)),
                last_sale_date=pd.to_datetime(row['last_sale_date']) if pd.notnull(row.get('last_sale_date')) else None,
                days_since_last_sale=int(row['days_since_last_sale']) if pd.notnull(row.get('days_since_last_sale')) else None,
                source='olist'
            )
            products.append(product)
            
            if len(products) >= 1000:
                self.db.bulk_save_objects(products)
                self.db.commit()
                logger.info(f"  ✓ Loaded {len(products)} products...")
                products = []
        
        if products:
            self.db.bulk_save_objects(products)
            self.db.commit()
        
        total = self.db.query(Product).count()
        logger.info(f"✅ Total products loaded: {total:,}")
        
    def load_customers(self):
        """Load customers with WhatsApp and credit info"""
        logger.info("\n👥 Loading Customers...")
        
        df = pd.read_csv(self.data_dir / 'customers_enriched.csv')
        df = df.where(pd.notnull(df), None)
        
        customers = []
        for _, row in df.iterrows():
            customer = Customer(
                customer_code=row['customer_id'],
                name=f"Customer {row['customer_id'][:8]}",  # Anonymous
                email=f"{row['customer_id'][:10]}@customer.rdios.com",
                phone=row.get('whatsapp_number'),
                whatsapp_number=row.get('whatsapp_number'),
                preferred_channel=row.get('preferred_channel', 'whatsapp'),
                city=row.get('customer_city'),
                loyalty_points=int(row['loyalty_points']) if pd.notnull(row.get('loyalty_points')) else 0,
                credit_allowed=bool(row.get('credit_allowed', False)),
                source='olist'
            )
            customers.append(customer)
            
            if len(customers) >= 1000:
                self.db.bulk_save_objects(customers)
                self.db.commit()
                logger.info(f"  ✓ Loaded {len(customers)} customers...")
                customers = []
        
        if customers:
            self.db.bulk_save_objects(customers)
            self.db.commit()
        
        total = self.db.query(Customer).count()
        logger.info(f"✅ Total customers loaded: {total:,}")
        
    def load_sales(self):
        """Load sales transactions"""
        logger.info("\n💰 Loading Sales...")
        
        # Load sales enriched data
        df = pd.read_csv(self.data_dir / 'sales_enriched.csv')
        df = df.where(pd.notnull(df), None)
        
        # Get product and customer ID mappings
        products = {p.sku: p.id for p in self.db.query(Product.id, Product.sku).all()}
        customers = {c.customer_code: c.id for c in self.db.query(Customer.id, Customer.customer_code).all()}
        
        # Load order items to get product details
        items_df = pd.read_csv(self.data_dir.parent / 'raw' / 'olist_order_items_dataset.csv')
        
        # Merge sales with items to get product info
        df = df.merge(items_df[['order_id', 'product_id', 'price', 'freight_value']].drop_duplicates(subset=['order_id']), 
                     on='order_id', how='left')
        
        sales = []
        batch_size = 1000
        skipped = 0
        
        for _, row in df.iterrows():
            product_id = products.get(row['product_id'])
            customer_id = customers.get(row['customer_id'])
            
            if not product_id:
                skipped += 1
                continue
            
            # Determine payment status
            installments = int(row['payment_installments']) if pd.notnull(row.get('payment_installments')) else 1
            payment_status = PaymentStatus.PARTIAL if installments > 1 else PaymentStatus.PAID
            
            sale = Sale(
                transaction_id=row['order_id'],
                product_id=product_id,
                customer_id=customer_id,
                transaction_date=pd.to_datetime(row['order_purchase_timestamp']),
                quantity=1,  # Olist doesn't have quantity per order
                unit_price=float(row['price']) if pd.notnull(row.get('price')) else 0.0,
                discount=0.0,
                tax=0.0,
                total_amount=float(row['payment_value_inr']) if pd.notnull(row.get('payment_value_inr')) else 0.0,
                payment_method=row.get('payment_type'),
                payment_status=payment_status,
                installments=installments,
                source='olist'
            )
            sales.append(sale)
            
            if len(sales) >= batch_size:
                self.db.bulk_save_objects(sales)
                self.db.commit()
                logger.info(f"  ✓ Loaded {len(sales)} sales...")
                sales = []
        
        if sales:
            self.db.bulk_save_objects(sales)
            self.db.commit()
        
        total = self.db.query(Sale).count()
        logger.info(f"✅ Total sales loaded: {total:,} (skipped {skipped:,} due to missing products)")
        
    def load_inventory(self):
        """Load inventory records"""
        logger.info("\n📊 Loading Inventory...")
        
        df = pd.read_csv(self.data_dir / 'inventory_enriched.csv')
        df = df.where(pd.notnull(df), None)
        
        # Get product ID mappings
        products = {p.sku: p.id for p in self.db.query(Product.id, Product.sku).all()}
        
        inventory_records = []
        skipped = 0
        
        for _, row in df.iterrows():
            product_id = products.get(row['product_id'])
            
            if not product_id:
                skipped += 1
                continue
            
            stock_qty = int(row['stock_quantity']) if pd.notnull(row.get('stock_quantity')) else 0
            
            inventory = Inventory(
                product_id=product_id,
                current_stock=stock_qty,
                reserved_stock=0,
                available_stock=stock_qty,
                reorder_point=int(row['reorder_point']) if pd.notnull(row.get('reorder_point')) else 10,
                reorder_quantity=int(row.get('reorder_point', 50)),
                max_stock_level=int(row['max_stock_level']) if pd.notnull(row.get('max_stock_level')) else stock_qty * 2,
                last_restocked=pd.to_datetime(row['last_restocked']) if pd.notnull(row.get('last_restocked')) else None
            )
            inventory_records.append(inventory)
            
            if len(inventory_records) >= 1000:
                self.db.bulk_save_objects(inventory_records)
                self.db.commit()
                logger.info(f"  ✓ Loaded {len(inventory_records)} inventory records...")
                inventory_records = []
        
        if inventory_records:
            self.db.bulk_save_objects(inventory_records)
            self.db.commit()
        
        total = self.db.query(Inventory).count()
        logger.info(f"✅ Total inventory records loaded: {total:,} (skipped {skipped:,})")
    
    def create_sample_alerts(self):
        """Create sample alerts for dead stock and low inventory"""
        logger.info("\n🔔 Creating Sample Alerts...")
        
        # Alert for dead stock
        dead_stock_products = self.db.query(Product).filter(Product.is_dead_stock == True).limit(5).all()
        
        alerts = []
        for product in dead_stock_products:
            alert = Alert(
                severity='warning',
                title=f"Dead Stock Alert: {product.name}",
                message=f"Product {product.sku} has not sold in {product.days_since_last_sale} days. Consider clearance sale.",
                category="inventory",
                related_product_id=product.id,
                is_acknowledged=False
            )
            alerts.append(alert)
        
        # Alert for low stock
        low_stock_items = self.db.query(Inventory, Product).join(Product).filter(
            Inventory.current_stock < Inventory.reorder_point
        ).limit(5).all()
        
        for inv, product in low_stock_items:
            alert = Alert(
                severity='critical',
                title=f"Low Stock Alert: {product.name}",
                message=f"Product {product.sku} is below reorder point. Current: {inv.current_stock}, Reorder at: {inv.reorder_point}.",
                category="inventory",
                related_product_id=product.id,
                is_acknowledged=False
            )
            alerts.append(alert)
        
        if alerts:
            self.db.bulk_save_objects(alerts)
            self.db.commit()
        
        logger.info(f"✅ Created {len(alerts)} sample alerts")
    
    def print_summary(self):
        """Print database summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 DATABASE SUMMARY")
        logger.info("=" * 80)
        
        stats = {
            "Products": self.db.query(Product).count(),
            "Customers": self.db.query(Customer).count(),
            "Sales": self.db.query(Sale).count(),
            "Inventory Records": self.db.query(Inventory).count(),
            "Alerts": self.db.query(Alert).count(),
        }
        
        for entity, count in stats.items():
            logger.info(f"  {entity}: {count:,}")
        
        # Additional insights
        dead_stock = self.db.query(Product).filter(Product.is_dead_stock == True).count()
        credit_customers = self.db.query(Customer).filter(Customer.credit_allowed == True).count()
        partial_payments = self.db.query(Sale).filter(Sale.payment_status == PaymentStatus.PARTIAL).count()
        
        logger.info(f"\n📈 Insights:")
        logger.info(f"  Dead Stock Products: {dead_stock:,} ({dead_stock/stats['Products']*100:.1f}%)")
        logger.info(f"  Credit-Enabled Customers: {credit_customers:,} ({credit_customers/stats['Customers']*100:.1f}%)")
        logger.info(f"  Orders with Partial Payments: {partial_payments:,} ({partial_payments/stats['Sales']*100:.1f}%)")
        
        logger.info("\n✅ Database initialization complete!")
        logger.info("=" * 80 + "\n")
    
    def close(self):
        """Close database connection"""
        self.db.close()

def main():
    """Main execution"""
    print("🚀 R-DIOS v5.0 - Database Initialization")
    print("=" * 80)
    print()
    
    # Get paths
    project_root = Path(__file__).parent.parent.parent
    processed_dir = project_root / 'data' / 'processed'
    
    print(f"📂 Looking for data in: {processed_dir}")
    
    if not processed_dir.exists():
        print(f"❌ Processed data directory not found: {processed_dir}")
        print("   Please run data_enricher.py first")
        return
    
    # Initialize loader
    loader = DatabaseLoader(processed_dir)
    
    try:
        # Execute pipeline
        loader.drop_and_create_tables()
        loader.load_products()
        loader.load_customers()
        loader.load_sales()
        loader.load_inventory()
        loader.create_sample_alerts()
        loader.print_summary()
        
    except Exception as e:
        logger.error(f"❌ Error during database loading: {str(e)}")
        raise
    finally:
        loader.close()

if __name__ == "__main__":
    main()
