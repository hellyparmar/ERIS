#!/usr/bin/env python3
"""
Standalone Petpooja Dataset Loader
Loads all 18-month data into PostgreSQL without pager interaction
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any
import json

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

# Setup logging to file instead of stdout initially
log_file = Path("/tmp/petpooja_loader.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PetpoojaDataLoader:
    """Load 18-month dataset into database"""

    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://eris_admin:admin1234@127.0.0.1:5432/eris_production"
            )
        
        # Use psycopg2 for sync operations
        database_url = database_url.replace("asyncpg://", "psycopg2://")
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
        
        try:
            self.engine = create_engine(database_url, echo=False)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

        self.Session = sessionmaker(bind=self.engine)

    def load_products(self, csv_path: str) -> int:
        """Load products into database"""
        logger.info("Loading products...")
        df = pd.read_csv(csv_path)
        
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM product WHERE id > 0"))
            
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO product (id, name, category, unit_price, cost_price, gst_percentage, is_active, created_at)
                    VALUES (:id, :name, :category, :unit_price, :cost_price, :gst_percentage, :is_active, :created_at)
                    ON CONFLICT(id) DO UPDATE SET name = EXCLUDED.name
                """), {
                    'id': int(row['id']),
                    'name': str(row['name']),
                    'category': str(row['category']),
                    'unit_price': float(row['unit_price']),
                    'cost_price': float(row['cost_price']),
                    'gst_percentage': float(row['gst_percentage']),
                    'is_active': bool(row['is_active']),
                    'created_at': pd.to_datetime(row['created_at'])
                })
        
        logger.info(f"✅ {len(df)} products loaded")
        return len(df)

    def load_customers(self, csv_path: str) -> int:
        """Load customers into database"""
        logger.info("Loading customers...")
        df = pd.read_csv(csv_path)
        
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM customer WHERE id > 0"))
            
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO customer (id, name, phone, email, city, segment, loyalty_points, total_spent, is_active, created_at)
                    VALUES (:id, :name, :phone, :email, :city, :segment, :loyalty_points, :total_spent, :is_active, :created_at)
                    ON CONFLICT(id) DO UPDATE SET name = EXCLUDED.name
                """), {
                    'id': int(row['id']),
                    'name': str(row['name']),
                    'phone': str(row['phone']),
                    'email': str(row['email']) if pd.notna(row['email']) else None,
                    'city': str(row['city']),
                    'segment': str(row['segment']),
                    'loyalty_points': int(row['loyalty_points']),
                    'total_spent': float(row['total_spent']),
                    'is_active': bool(row['is_active']),
                    'created_at': pd.to_datetime(row['created_at'])
                })
        
        logger.info(f"✅ {len(df)} customers loaded")
        return len(df)

    def load_sales(self, csv_path: str) -> int:
        """Load sales into database"""
        logger.info("Loading sales...")
        df = pd.read_csv(csv_path)
        
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM sale WHERE id > 0"))
            
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO sale (id, customer_id, sale_date, total_items, subtotal, tax_amount, discount_amount, total_amount, payment_method, payment_status, is_training_data, is_testing_data, created_at)
                    VALUES (:id, :customer_id, :sale_date, :total_items, :subtotal, :tax_amount, :discount_amount, :total_amount, :payment_method, :payment_status, :is_training_data, :is_testing_data, :created_at)
                    ON CONFLICT(id) DO UPDATE SET total_amount = EXCLUDED.total_amount
                """), {
                    'id': int(row['id']),
                    'customer_id': int(row['customer_id']),
                    'sale_date': pd.to_datetime(row['sale_date']),
                    'total_items': int(row['total_items']),
                    'subtotal': float(row['subtotal']),
                    'tax_amount': float(row['tax_amount']),
                    'discount_amount': float(row['discount_amount']),
                    'total_amount': float(row['total_amount']),
                    'payment_method': str(row['payment_method']),
                    'payment_status': str(row['payment_status']),
                    'is_training_data': bool(row['is_training_data']),
                    'is_testing_data': bool(row['is_testing_data']),
                    'created_at': pd.to_datetime(row['created_at'])
                })
        
        logger.info(f"✅ {len(df)} sales loaded")
        return len(df)

    def load_sale_items(self, csv_path: str) -> int:
        """Load sale items into database"""
        logger.info("Loading sale items...")
        df = pd.read_csv(csv_path)
        
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM sale_item WHERE id > 0"))
            
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO sale_item (id, sale_id, product_id, quantity, unit_price, gst_percentage, line_total, created_at)
                    VALUES (:id, :sale_id, :product_id, :quantity, :unit_price, :gst_percentage, :line_total, :created_at)
                    ON CONFLICT(id) DO UPDATE SET line_total = EXCLUDED.line_total
                """), {
                    'id': int(row['id']),
                    'sale_id': int(row['sale_id']),
                    'product_id': int(row['product_id']),
                    'quantity': int(row['quantity']),
                    'unit_price': float(row['unit_price']),
                    'gst_percentage': float(row['gst_percentage']),
                    'line_total': float(row['line_total']),
                    'created_at': pd.to_datetime(row['created_at'])
                })
        
        logger.info(f"✅ {len(df)} sale items loaded")
        return len(df)

    def load_invoices(self, csv_path: str) -> int:
        """Load invoices into database"""
        logger.info("Loading invoices...")
        df = pd.read_csv(csv_path)
        
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM invoice WHERE id > 0"))
            
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO invoice (id, sale_id, invoice_number, issue_date, due_date, subtotal, tax, discount, total, paid_amount, balance, status, created_at)
                    VALUES (:id, :sale_id, :invoice_number, :issue_date, :due_date, :subtotal, :tax, :discount, :total, :paid_amount, :balance, :status, :created_at)
                    ON CONFLICT(id) DO UPDATE SET total = EXCLUDED.total
                """), {
                    'id': int(row['id']),
                    'sale_id': int(row['sale_id']),
                    'invoice_number': str(row['invoice_number']),
                    'issue_date': pd.to_datetime(row['issue_date']),
                    'due_date': pd.to_datetime(row['due_date']) if pd.notna(row['due_date']) else None,
                    'subtotal': float(row['subtotal']),
                    'tax': float(row['tax']),
                    'discount': float(row['discount']),
                    'total': float(row['total']),
                    'paid_amount': float(row['paid_amount']),
                    'balance': float(row['balance']),
                    'status': str(row['status']),
                    'created_at': pd.to_datetime(row['created_at'])
                })
        
        logger.info(f"✅ {len(df)} invoices loaded")
        return len(df)

    def load_employees(self, csv_path: str) -> int:
        """Load employees into database"""
        logger.info("Loading employees...")
        df = pd.read_csv(csv_path)
        
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM \"user\" WHERE id > 0 AND role = 'STAFF'"))
            
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO "user" (id, name, email, phone, role, is_active, created_at)
                    VALUES (:id, :name, :email, :phone, :role, :is_active, :created_at)
                    ON CONFLICT(id) DO UPDATE SET name = EXCLUDED.name
                """), {
                    'id': int(row['id']),
                    'name': str(row['name']),
                    'email': str(row['email']),
                    'phone': str(row['phone']),
                    'role': 'STAFF',
                    'is_active': bool(row['is_active']),
                    'created_at': pd.to_datetime(row['created_at'])
                })
        
        logger.info(f"✅ {len(df)} employees loaded")
        return len(df)


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("PETPOOJA 18-MONTH DATASET LOADER")
    print("=" * 80 + "\n")
    
    data_dir = Path("/tmp/petpooja_18months_data")
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return 1
    
    try:
        loader = PetpoojaDataLoader()
        
        counts = {}
        counts['products'] = loader.load_products(str(data_dir / "products.csv"))
        counts['customers'] = loader.load_customers(str(data_dir / "customers.csv"))
        counts['sales'] = loader.load_sales(str(data_dir / "sales.csv"))
        counts['sale_items'] = loader.load_sale_items(str(data_dir / "sale_items.csv"))
        counts['invoices'] = loader.load_invoices(str(data_dir / "invoices.csv"))
        counts['employees'] = loader.load_employees(str(data_dir / "employees.csv"))
        
        print("\n" + "=" * 80)
        print("📊 DATA LOAD SUMMARY")
        print("=" * 80)
        for key, count in counts.items():
            print(f"  {key.title():15} {count:>8,} records")
        print("=" * 80)
        print("\n✅ All data loaded successfully to PostgreSQL!\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during data load: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
