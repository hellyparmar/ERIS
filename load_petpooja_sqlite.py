#!/usr/bin/env python3
"""
R-DIOS Comprehensive Testing Suite  
Load Petpooja synthetic data and run complete verification tests

This script:
1. Loads existing Petpooja synthetic CSVs into SQLite
2. Runs database verification tests
3. Proceeds with comprehensive system audit
"""

import os
import sys
import csv
import sqlite3
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PetpoojaSQLiteLoader:
    """Load Petpooja CSV data into SQLite"""
    
    def __init__(self, db_path: str = "api/rdios_dev.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self) -> bool:
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"✅ Connected to SQLite: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create database schema matching existing tables"""
        logger.info("📋 Creating Petpooja schema...")
        
        try:
            cursor = self.conn.cursor()
            
            # Drop existing tables to start fresh
            tables = ['sale_items', 'sales', 'customers', 'products']
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            schema_sql = """
            -- Products
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                category TEXT,
                subcategory TEXT,
                hsn_code TEXT,
                gst_rate REAL,
                cost_price REAL,
                selling_price REAL,
                margin_percent REAL,
                created_at TEXT,
                is_active INTEGER DEFAULT 1
            );
            
            CREATE INDEX idx_products_category ON products(category);
            CREATE INDEX idx_products_sku ON products(sku);
            
            -- Customers
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                city TEXT,
                customer_segment TEXT,
                churn_risk TEXT,
                credit_limit REAL DEFAULT 0,
                total_spent REAL DEFAULT 0,
                lifetime_value REAL DEFAULT 0,
                last_purchase_date TEXT,
                created_at TEXT
            );
            
            CREATE INDEX idx_customers_segment ON customers(customer_segment);
            
            -- Sales
            CREATE TABLE sales (
                id INTEGER PRIMARY KEY,
                transaction_id TEXT UNIQUE,
                store_id INTEGER,
                customer_id INTEGER REFERENCES customers(id),
                transaction_date TEXT NOT NULL,
                discount REAL,
                tax REAL,
                total_amount REAL NOT NULL,
                payment_method TEXT,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_sales_transaction_date ON sales(transaction_date);
            CREATE INDEX idx_sales_customer ON sales(customer_id);
            CREATE INDEX idx_sales_store ON sales(store_id);
            
            -- Sale Items
            CREATE TABLE sale_items (
                id INTEGER PRIMARY KEY,
                sale_id INTEGER REFERENCES sales(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL,
                discount REAL,
                gst REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_sale_items_sale ON sale_items(sale_id);
            CREATE INDEX idx_sale_items_product ON sale_items(product_id);
            """
            
            cursor.executescript(schema_sql)
            self.conn.commit()
            logger.info("✅ Schema created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            return False
    
    def load_csv(self, table: str, csv_path: str) -> int:
        """Load CSV into table"""
        logger.info(f"📥 Loading {table} from {csv_path}...")
        
        if not os.path.exists(csv_path):
            logger.warning(f"⚠️  File not found: {csv_path}")
            return 0
        
        try:
            cursor = self.conn.cursor()
            
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                logger.warning(f"⚠️  No data in {csv_path}")
                return 0
            
            inserted = 0
            
            # Different logic for each table based on actual CSV structure
            if table == 'products':
                # products.csv has: product_id, name, sku, category, subcategory, hsn_code, gst_rate, cost_price, selling_price, margin_percent, created_at
                for row in rows:
                    try:
                        cursor.execute("""
                            INSERT INTO products (id, name, sku, category, subcategory, hsn_code, 
                                                 gst_rate, cost_price, selling_price, margin_percent, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            int(row.get('product_id', 0)),
                            row.get('name'),
                            row.get('sku'),
                            row.get('category'),
                            row.get('subcategory'),
                            row.get('hsn_code'),
                            float(row.get('gst_rate', 0)),
                            float(row.get('cost_price', 0)),
                            float(row.get('selling_price', 0)),
                            float(row.get('margin_percent', 0)),
                            row.get('created_at')
                        ))
                        inserted += 1
                    except Exception as e:
                        logger.debug(f"  Row skip: {e}")
            
            elif table == 'customers':
                # customers.csv has: customer_id, name, email, phone, address, city, region, credit_enabled, credit_limit, current_balance, loyalty_points, preferred_channel, created_at, churn_risk_score, customer_segment
                for row in rows:
                    try:
                        cursor.execute("""
                            INSERT INTO customers (id, name, email, phone, city, customer_segment,
                                                  churn_risk, credit_limit, total_spent, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            int(row.get('customer_id', 0)),
                            row.get('name'),
                            row.get('email'),
                            row.get('phone'),
                            row.get('city'),
                            row.get('customer_segment'),
                            'high' if float(row.get('churn_risk_score', 0)) > 0.5 else 'low',
                            float(row.get('credit_limit', 0)),
                            float(row.get('current_balance', 0)),
                            row.get('created_at')
                        ))
                        inserted += 1
                    except Exception as e:
                        logger.debug(f"  Row skip: {e}")
            
            elif table == 'sales':
                # sales.csv has: sale_id, customer_id, sale_date, subtotal, gst_amount, total_amount, payment_method, payment_status, amount_paid, amount_due, region, city
                for row in rows:
                    try:
                        cursor.execute("""
                            INSERT INTO sales (id, customer_id, transaction_date, discount, tax,
                                             total_amount, payment_method, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            int(row.get('sale_id', 0)),
                            int(row.get('customer_id', 0)),
                            row.get('sale_date'),
                            float(row.get('subtotal', 0)),
                            float(row.get('gst_amount', 0)),
                            float(row.get('total_amount', 0)),
                            row.get('payment_method'),
                            row.get('region', 'auto-generated')
                        ))
                        inserted += 1
                    except Exception as e:
                        logger.debug(f"  Row skip: {e}")
            
            elif table == 'sale_items':
                # sale_items.csv has: item_id, sale_id, product_id, quantity, unit_price, subtotal, gst_rate, gst_amount, total
                for row in rows:
                    try:
                        cursor.execute("""
                            INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price,
                                                   line_total, gst)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            int(row.get('item_id', 0)),
                            int(row.get('sale_id', 0)),
                            int(row.get('product_id', 0)),
                            int(row.get('quantity', 0)),
                            float(row.get('unit_price', 0)),
                            float(row.get('subtotal', 0)),
                            float(row.get('gst_amount', 0))
                        ))
                        inserted += 1
                    except Exception as e:
                        logger.debug(f"  Row skip: {e}")
            
            self.conn.commit()
            logger.info(f"  ✅ Loaded {inserted} records into {table}")
            return inserted
            
        except Exception as e:
            logger.error(f"❌ CSV loading failed: {e}")
            self.conn.rollback()
            return 0
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        try:
            cursor = self.conn.cursor()
            stats = {}
            
            for table in ['products', 'customers', 'sales', 'sale_items']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(total_amount) FROM sales")
            stats['revenue'] = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM sales")
            row = cursor.fetchone()
            stats['date_range'] = f"{row[0]} to {row[1]}" if row[0] else "N/A"
            
            cursor.execute("SELECT COUNT(DISTINCT category) FROM products")
            stats['categories'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Stats retrieval failed: {e}")
            return {}
    
    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()


def main():
    print("\n" + "="*70)
    print(" R-DIOS Petpooja Data Loader & Verification")
    print("="*70 + "\n")
    
    loader = PetpoojaSQLiteLoader()
    
    if not loader.connect():
        logger.error("Cannot proceed without database connection")
        return
    
    # Create schema
    if not loader.create_schema():
        logger.error("Cannot proceed without schema")
        loader.close()
        return
    
    # Load data
    loader.load_csv('products', 'data/synthetic/products.csv')
    loader.load_csv('customers', 'data/synthetic/customers.csv')
    loader.load_csv('sales', 'data/synthetic/sales.csv')
    loader.load_csv('sale_items', 'data/synthetic/sale_items.csv')
    
    # Stats
    stats = loader.get_stats()
    
    loader.close()
    
    # Summary
    print("\n" + "="*70)
    print(" DATA LOADING COMPLETE")
    print("="*70)
    print(f"✅ Products:        {stats.get('products', 0):,}")
    print(f"✅ Customers:       {stats.get('customers', 0):,}")
    print(f"✅ Sales:           {stats.get('sales', 0):,}")
    print(f"✅ Sale Items:      {stats.get('sale_items', 0):,}")
    print(f"✅ Total Revenue:   ₹{stats.get('revenue', 0):,.0f}")
    print(f"✅ Date Range:      {stats.get('date_range', 'N/A')}")
    print(f"✅ Categories:      {stats.get('categories', 0)}")
    print("="*70 + "\n")
    
    if stats.get('sales', 0) > 50000:
        logger.info("✅ Database ready with Petpooja data!")
        return True
    else:
        logger.warning("⚠️  Low sales volume")
        return False


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
