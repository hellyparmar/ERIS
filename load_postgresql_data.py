#!/usr/bin/env python3
"""
R-DIOS PostgreSQL Data Loader
Imports existing Petpooja synthetic data (CSV) into PostgreSQL database
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgreSQLLoader:
    """Load Petpooja synthetic data into PostgreSQL"""
    
    def __init__(self, host='localhost', port=5432, user='postgres', password='password', database='rdios'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Connect to PostgreSQL database"""
        logger.info(f"🔗 Connecting to PostgreSQL at {self.host}:{self.port}/{self.database}...")
        
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connect_timeout=5
            )
            self.cursor = self.conn.cursor()
            logger.info("✅ PostgreSQL connection successful")
            return True
        except psycopg2.OperationalError as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def create_database(self) -> bool:
        """Create database if it doesn't exist"""
        logger.info(f"📦 Creating database '{self.database}' if not exists...")
        
        try:
            # Connect to default postgres database first
            default_conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres',
                connect_timeout=5
            )
            default_conn.autocommit = True
            default_cursor = default_conn.cursor()
            
            # Check if database exists
            default_cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{self.database}'")
            exists = default_cursor.fetchone()
            
            if not exists:
                logger.info(f"  Creating database '{self.database}'...")
                default_cursor.execute(f"CREATE DATABASE {self.database}")
                logger.info(f"  ✅ Database created")
            else:
                logger.info(f"  Database already exists")
            
            default_cursor.close()
            default_conn.close()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Could not create database: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create database schema"""
        logger.info("📋 Creating database schema...")
        
        if not self.conn:
            logger.error("❌ Not connected to database")
            return False
        
        try:
            schema_sql = """
            -- Products table
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                sku VARCHAR(100) UNIQUE NOT NULL,
                category VARCHAR(100),
                subcategory VARCHAR(100),
                hsn_code VARCHAR(20),
                gst_rate DECIMAL(5, 2),
                cost_price DECIMAL(12, 2),
                selling_price DECIMAL(12, 2),
                margin_percent DECIMAL(5, 2),
                created_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
            
            -- Customers table
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(20),
                city VARCHAR(100),
                customer_segment VARCHAR(50),
                churn_risk VARCHAR(50),
                credit_limit DECIMAL(12, 2) DEFAULT 0,
                total_spent DECIMAL(15, 2) DEFAULT 0,
                lifetime_value DECIMAL(15, 2) DEFAULT 0,
                last_purchase_date TIMESTAMP,
                created_at TIMESTAMP
            );
            
            -- Sales transactions table
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                transaction_id VARCHAR(100) UNIQUE,
                store_id INTEGER,
                customer_id INTEGER REFERENCES customers(id),
                transaction_date TIMESTAMP NOT NULL,
                discount DECIMAL(12, 2),
                tax DECIMAL(12, 2),
                total_amount DECIMAL(12, 2) NOT NULL,
                payment_method VARCHAR(50),
                source VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Sale items (line items) table
            CREATE TABLE IF NOT EXISTS sale_items (
                id SERIAL PRIMARY KEY,
                sale_id INTEGER REFERENCES sales(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(12, 2) NOT NULL,
                line_total DECIMAL(12, 2),
                discount DECIMAL(12, 2),
                gst DECIMAL(12, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
            CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(transaction_date);
            CREATE INDEX IF NOT EXISTS idx_sales_store ON sales(store_id);
            CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);
            CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id);
            CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(customer_segment);
            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
            """
            
            self.cursor.execute(schema_sql)
            self.conn.commit()
            logger.info("✅ Schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            self.conn.rollback()
            return False
    
    def load_products(self, csv_path: str) -> int:
        """Load products from CSV"""
        logger.info(f"📦 Loading products from {csv_path}...")
        
        if not os.path.exists(csv_path):
            logger.error(f"❌ File not found: {csv_path}")
            return 0
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"  Read {len(df)} products from CSV")
            
            # Clear existing data
            self.cursor.execute("TRUNCATE TABLE products CASCADE")
            self.conn.commit()
            
            # Insert data
            records = df.values.tolist()
            
            insert_sql = """
            INSERT INTO products (id, name, sku, category, subcategory, hsn_code, 
                                 gst_rate, cost_price, selling_price, margin_percent, created_at)
            VALUES %s
            ON CONFLICT (sku) DO NOTHING
            """
            
            execute_values(self.cursor, insert_sql, records, page_size=1000)
            self.conn.commit()
            
            logger.info(f"  ✅ Loaded {len(df)} products")
            return len(df)
            
        except Exception as e:
            logger.error(f"❌ Product loading failed: {e}")
            self.conn.rollback()
            return 0
    
    def load_customers(self, csv_path: str) -> int:
        """Load customers from CSV"""
        logger.info(f"👥 Loading customers from {csv_path}...")
        
        if not os.path.exists(csv_path):
            logger.error(f"❌ File not found: {csv_path}")
            return 0
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"  Read {len(df)} customers from CSV")
            
            # Clear existing data
            self.cursor.execute("TRUNCATE TABLE customers CASCADE")
            self.conn.commit()
            
            # Map columns
            records = []
            for _, row in df.iterrows():
                records.append((
                    row.get('customer_id'),
                    row.get('name'),
                    row.get('email'),
                    row.get('phone'),
                    row.get('city'),
                    row.get('segment'),
                    row.get('churn_risk'),
                    row.get('credit_limit', 0),
                    row.get('total_spent', 0),
                    row.get('lifetime_value', 0),
                    row.get('last_purchase_date'),
                    row.get('created_at')
                ))
            
            insert_sql = """
            INSERT INTO customers (id, name, email, phone, city, customer_segment, 
                                  churn_risk, credit_limit, total_spent, lifetime_value,
                                  last_purchase_date, created_at)
            VALUES %s
            """
            
            execute_values(self.cursor, insert_sql, records, page_size=1000)
            self.conn.commit()
            
            logger.info(f"  ✅ Loaded {len(df)} customers")
            return len(df)
            
        except Exception as e:
            logger.error(f"❌ Customer loading failed: {e}")
            self.conn.rollback()
            return 0
    
    def load_sales(self, csv_path: str) -> int:
        """Load sales transactions from CSV"""
        logger.info(f"💳 Loading sales transactions from {csv_path}...")
        
        if not os.path.exists(csv_path):
            logger.error(f"❌ File not found: {csv_path}")
            return 0
        
        try:
            # Read CSV in chunks
            total_loaded = 0
            chunk_size = 10000
            
            for i, df_chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
                logger.info(f"  Processing chunk {i+1} ({len(df_chunk)} records)...")
                
                # Map columns
                records = []
                for _, row in df_chunk.iterrows():
                    records.append((
                        row.get('transaction_id'),
                        row.get('store_id'),
                        row.get('customer_id'),
                        row.get('transaction_date'),
                        row.get('discount', 0),
                        row.get('tax', 0),
                        row.get('total_amount'),
                        row.get('payment_method'),
                        row.get('source', 'auto-generated')
                    ))
                
                insert_sql = """
                INSERT INTO sales (transaction_id, store_id, customer_id, transaction_date,
                                  discount, tax, total_amount, payment_method, source)
                VALUES %s
                ON CONFLICT (transaction_id) DO NOTHING
                """
                
                execute_values(self.cursor, insert_sql, records, page_size=5000)
                self.conn.commit()
                total_loaded += len(df_chunk)
            
            logger.info(f"  ✅ Loaded {total_loaded} sales transactions")
            return total_loaded
            
        except Exception as e:
            logger.error(f"❌ Sales loading failed: {e}")
            self.conn.rollback()
            return 0
    
    def load_sale_items(self, csv_path: str) -> int:
        """Load sale line items from CSV"""
        logger.info(f"📄 Loading sale items from {csv_path}...")
        
        if not os.path.exists(csv_path):
            logger.error(f"❌ File not found: {csv_path}")
            return 0
        
        try:
            # Read CSV in chunks
            total_loaded = 0
            chunk_size = 20000
            
            for i, df_chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
                logger.info(f"  Processing chunk {i+1} ({len(df_chunk)} records)...")
                
                # Map columns
                records = []
                for _, row in df_chunk.iterrows():
                    records.append((
                        row.get('sale_id'),
                        row.get('product_id'),
                        row.get('quantity'),
                        row.get('unit_price'),
                        row.get('line_total'),
                        row.get('discount', 0),
                        row.get('gst', 0)
                    ))
                
                insert_sql = """
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, 
                                       line_total, discount, gst)
                VALUES %s
                """
                
                execute_values(self.cursor, insert_sql, records, page_size=10000)
                self.conn.commit()
                total_loaded += len(df_chunk)
            
            logger.info(f"  ✅ Loaded {total_loaded} sale items")
            return total_loaded
            
        except Exception as e:
            logger.error(f"❌ Sale items loading failed: {e}")
            self.conn.rollback()
            return 0
    
    def get_statistics(self) -> dict:
        """Get database statistics"""
        logger.info("📊 Generating statistics...")
        
        try:
            stats = {}
            
            # Count records
            self.cursor.execute("SELECT COUNT(*) FROM products")
            stats['products'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM customers")
            stats['customers'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM sales")
            stats['sales'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM sale_items")
            stats['sale_items'] = self.cursor.fetchone()[0]
            
            # Revenue
            self.cursor.execute("SELECT SUM(total_amount) FROM sales")
            stats['total_revenue'] = self.cursor.fetchone()[0] or 0
            
            # Date range
            self.cursor.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM sales")
            min_date, max_date = self.cursor.fetchone()
            stats['date_range'] = f"{min_date} to {max_date}"
            
            # Categories
            self.cursor.execute("SELECT COUNT(DISTINCT category) FROM products")
            stats['categories'] = self.cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Statistics retrieval failed: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("🔌 Database connection closed")


def main():
    """Main execution"""
    
    print("\n" + "=" * 70)
    print("  R-DIOS PostgreSQL Data Loader - Petpooja Synthetic Dataset")
    print("=" * 70 + "\n")
    
    # Configuration (update as needed)
    # Try multiple database connection options
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'rdios_user'),
        'password': os.getenv('DB_PASSWORD', 'rdios_password'),
        'database': os.getenv('DB_NAME', 'rdios_dev')
    }
    
    DATA_DIR = "data/synthetic"
    
    loader = PostgreSQLLoader(**DB_CONFIG)
    
    # Step 1: Try to create database
    logger.info(f"Configuration: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    loader.create_database()
    
    # Step 2: Connect
    if not loader.connect():
        logger.error("\n❌ FATAL: Could not connect to database")
        return
    
    # Step 3: Create schema
    if not loader.create_schema():
        logger.error("\n❌ Schema creation failed")
        loader.close()
        return
    
    # Step 4: Load data
    products_loaded = loader.load_products(f"{DATA_DIR}/products.csv")
    customers_loaded = loader.load_customers(f"{DATA_DIR}/customers.csv")
    sales_loaded = loader.load_sales(f"{DATA_DIR}/sales.csv")
    items_loaded = loader.load_sale_items(f"{DATA_DIR}/sale_items.csv")
    
    # Step 5: Statistics
    stats = loader.get_statistics()
    
    # Step 6: Close
    loader.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("  DATA LOADING COMPLETE")
    print("=" * 70)
    print(f"✅ Products:        {products_loaded:,}")
    print(f"✅ Customers:       {customers_loaded:,}")
    print(f"✅ Sales:           {sales_loaded:,}")
    print(f"✅ Sale Items:      {items_loaded:,}")
    print(f"✅ Total Revenue:   ₹{stats.get('total_revenue', 0):,.0f}")
    print(f"✅ Date Range:      {stats.get('date_range', 'N/A')}")
    print(f"✅ Categories:      {stats.get('categories', 0)}")
    print("=" * 70 + "\n")
    
    if sales_loaded > 50000:
        logger.info("✅ Database successfully loaded with Petpooja data!")
    else:
        logger.warning("⚠️  Low number of sales records - verify data loading")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Loading interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
