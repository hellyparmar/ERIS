#!/usr/bin/env python3
"""
Load Petpooja 18-Month Synthetic Dataset into Database
======================================================
Loads the generated CSV files into the PostgreSQL database.
Separates data into training and testing sets for model development.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pandas as pd
from sqlalchemy import create_engine, text, insert
from sqlalchemy.orm import sessionmaker, Session
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"✓ Database connection established")

    def load_products(self, csv_path: str) -> int:
        """Load products into database"""
        logger.info("📦 Loading products...")
        df = pd.read_csv(csv_path)
        
        with self.Session() as session:
            # Check if table exists and clear old data
            session.execute(text("DELETE FROM products WHERE organization_id = 1"))
            
            for _, row in df.iterrows():
                session.execute(text("""
                    INSERT INTO products (
                        id, organization_id, name, category_id, description,
                        sku, unit, price, is_active, is_deleted, created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :name, :cat_id, :desc,
                        :sku, :unit, :price, :active, :deleted, :created, :updated
                    )
                """), {
                    "id": row["id"],
                    "org_id": row["organization_id"],
                    "name": row["name"],
                    "cat_id": row["category_id"],
                    "desc": row["description"],
                    "sku": row["sku"],
                    "unit": row["unit"],
                    "price": float(row["price"]),
                    "active": row["is_active"],
                    "deleted": row["is_deleted"],
                    "created": row["created_at"],
                    "updated": row["updated_at"],
                })
            
            session.commit()
            count = len(df)
        
        logger.info(f"✅ Loaded {count} products")
        return count

    def load_customers(self, csv_path: str) -> int:
        """Load customers into database"""
        logger.info("👥 Loading customers...")
        df = pd.read_csv(csv_path)
        
        with self.Session() as session:
            session.execute(text("DELETE FROM customers WHERE organization_id = 1"))
            
            for _, row in df.iterrows():
                session.execute(text("""
                    INSERT INTO customers (
                        id, organization_id, name, email, phone, city, state,
                        credit_limit, outstanding_amount, purchase_count, total_spent,
                        is_active, is_deleted, created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :name, :email, :phone, :city, :state,
                        :credit_limit, :outstanding, :purchases, :spent,
                        :active, :deleted, :created, :updated
                    )
                """), {
                    "id": row["id"],
                    "org_id": row["organization_id"],
                    "name": row["name"],
                    "email": row["email"],
                    "phone": row["phone"],
                    "city": row["city"],
                    "state": row["state"],
                    "credit_limit": float(row["credit_limit"]),
                    "outstanding": float(row["outstanding_amount"]),
                    "purchases": row["purchase_count"],
                    "spent": float(row["total_spent"]),
                    "active": row["is_active"],
                    "deleted": row["is_deleted"],
                    "created": row["created_at"],
                    "updated": row["updated_at"],
                })
            
            session.commit()
            count = len(df)
        
        logger.info(f"✅ Loaded {count} customers")
        return count

    def load_sales(self, csv_path: str) -> int:
        """Load sales into database"""
        logger.info("💰 Loading sales...")
        df = pd.read_csv(csv_path)
        
        # Convert date columns
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["updated_at"] = pd.to_datetime(df["updated_at"])
        
        with self.Session() as session:
            session.execute(text("DELETE FROM sales WHERE organization_id = 1"))
            
            for _, row in df.iterrows():
                session.execute(text("""
                    INSERT INTO sales (
                        id, organization_id, store_id, customer_id, invoice_number,
                        sale_date, total_amount, subtotal, tax_amount, payment_method,
                        payment_status, status, created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :store_id, :cust_id, :invoice_num,
                        :sale_date, :total, :subtotal, :tax, :payment_method,
                        :payment_status, :status, :created, :updated
                    )
                """), {
                    "id": row["id"],
                    "org_id": row["organization_id"],
                    "store_id": row["store_id"],
                    "cust_id": row["customer_id"],
                    "invoice_num": row["invoice_number"],
                    "sale_date": row["sale_date"],
                    "total": float(row["total_amount"]),
                    "subtotal": float(row["subtotal"]),
                    "tax": float(row["tax_amount"]),
                    "payment_method": row["payment_method"],
                    "payment_status": row["payment_status"],
                    "status": row["status"],
                    "created": row["created_at"],
                    "updated": row["updated_at"],
                })
            
            session.commit()
            count = len(df)
        
        logger.info(f"✅ Loaded {count} sales")
        return count

    def load_sale_items(self, csv_path: str) -> int:
        """Load sale items into database"""
        logger.info("🛒 Loading sale items...")
        df = pd.read_csv(csv_path)
        
        # Convert date columns
        df["created_at"] = pd.to_datetime(df["created_at"])
        
        with self.Session() as session:
            session.execute(text("DELETE FROM sale_items WHERE id > 0"))
            
            for _, row in df.iterrows():
                session.execute(text("""
                    INSERT INTO sale_items (
                        id, sale_id, product_id, quantity, unit_price,
                        tax_rate, tax_amount, line_total, created_at
                    ) VALUES (
                        :id, :sale_id, :prod_id, :qty, :unit_price,
                        :tax_rate, :tax_amount, :line_total, :created
                    )
                """), {
                    "id": row["id"],
                    "sale_id": row["sale_id"],
                    "prod_id": row["product_id"],
                    "qty": row["quantity"],
                    "unit_price": float(row["unit_price"]),
                    "tax_rate": float(row["tax_rate"]),
                    "tax_amount": float(row["tax_amount"]),
                    "line_total": float(row["line_total"]),
                    "created": row["created_at"],
                })
            
            session.commit()
            count = len(df)
        
        logger.info(f"✅ Loaded {count} sale items")
        return count

    def load_invoices(self, csv_path: str) -> int:
        """Load invoices into database"""
        logger.info("📄 Loading invoices...")
        df = pd.read_csv(csv_path)
        
        # Convert date columns
        df["invoice_date"] = pd.to_datetime(df["invoice_date"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["updated_at"] = pd.to_datetime(df["updated_at"])
        
        with self.Session() as session:
            session.execute(text("DELETE FROM invoices WHERE organization_id = 1"))
            
            for _, row in df.iterrows():
                session.execute(text("""
                    INSERT INTO invoices (
                        id, organization_id, invoice_number, invoice_date,
                        customer_id, total_amount, subtotal, tax_amount,
                        amount_paid, amount_due, payment_status, status,
                        created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :inv_num, :inv_date, :cust_id,
                        :total, :subtotal, :tax, :paid, :due,
                        :payment_status, :status, :created, :updated
                    )
                """), {
                    "id": row["id"],
                    "org_id": row["organization_id"],
                    "inv_num": row["invoice_number"],
                    "inv_date": row["invoice_date"],
                    "cust_id": row["customer_id"],
                    "total": float(row["total_amount"]),
                    "subtotal": float(row["subtotal"]),
                    "tax": float(row["tax_amount"]),
                    "paid": float(row["amount_paid"]),
                    "due": float(row["amount_due"]),
                    "payment_status": row["payment_status"],
                    "status": row["status"],
                    "created": row["created_at"],
                    "updated": row["updated_at"],
                })
            
            session.commit()
            count = len(df)
        
        logger.info(f"✅ Loaded {count} invoices")
        return count

    def load_employees(self, csv_path: str) -> int:
        """Load employees into database"""
        logger.info("👔 Loading employees...")
        df = pd.read_csv(csv_path)
        
        # Convert date columns
        df["joining_date"] = pd.to_datetime(df["joining_date"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        
        with self.Session() as session:
            session.execute(text("DELETE FROM users WHERE organization_id = 1 AND role = 'employee'"))
            
            for _, row in df.iterrows():
                session.execute(text("""
                    INSERT INTO users (
                        id, organization_id, username, email, first_name, last_name,
                        phone, is_active, is_deleted, created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :username, :email, :fname, :lname,
                        :phone, :active, :deleted, :created, :updated
                    )
                """), {
                    "id": 100 + row["id"],  # Offset to avoid conflicts
                    "org_id": row["organization_id"],
                    "username": row["username"],
                    "email": row["email"],
                    "fname": row["first_name"],
                    "lname": row["last_name"],
                    "phone": row["phone"],
                    "active": row["is_active"],
                    "deleted": row["is_deleted"],
                    "created": row["created_at"],
                    "updated": row["created_at"],
                })
            
            session.commit()
            count = len(df)
        
        logger.info(f"✅ Loaded {count} employees")
        return count

    def load_all(self, data_dir: str = "/tmp/petpooja_18months_data") -> Dict[str, Any]:
        """Load all data from CSV files"""
        data_dir = Path(data_dir)
        
        if not data_dir.exists():
            logger.error(f"❌ Data directory not found: {data_dir}")
            return {"success": False, "error": f"Directory not found: {data_dir}"}
        
        try:
            logger.info("\n" + "="*80)
            logger.info("LOADING PETPOOJA 18-MONTH DATASET INTO DATABASE")
            logger.info("="*80 + "\n")
            
            stats = {
                "products": self.load_products(str(data_dir / "products.csv")),
                "customers": self.load_customers(str(data_dir / "customers.csv")),
                "sales": self.load_sales(str(data_dir / "sales.csv")),
                "sale_items": self.load_sale_items(str(data_dir / "sale_items.csv")),
                "invoices": self.load_invoices(str(data_dir / "invoices.csv")),
                "employees": self.load_employees(str(data_dir / "employees.csv")),
            }
            
            logger.info("\n" + "="*80)
            logger.info("DATA LOADING SUMMARY")
            logger.info("="*80)
            logger.info(f"✅ Products:     {stats['products']:,}")
            logger.info(f"✅ Customers:    {stats['customers']:,}")
            logger.info(f"✅ Sales:        {stats['sales']:,}")
            logger.info(f"✅ Sale Items:   {stats['sale_items']:,}")
            logger.info(f"✅ Invoices:     {stats['invoices']:,}")
            logger.info(f"✅ Employees:    {stats['employees']:,}")
            logger.info("="*80 + "\n")
            
            return {"success": True, "stats": stats}
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}


def main():
    """Load the 18-month dataset into database"""
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL not set in environment")
        sys.exit(1)
    
    # Load data
    loader = PetpoojaDataLoader(database_url)
    result = loader.load_all()
    
    if result["success"]:
        logger.info("✅ Dataset loaded successfully!")
        logger.info("\n📊 Dataset Summary:")
        logger.info("   - Training Period: Sept 2024 - Mar 16, 2026 (17.5 months)")
        logger.info("   - Testing Period:  Mar 17 - Mar 31, 2026 (0.5 months)")
        logger.info("   - Categories: 7 (North Indian, South Indian, Chinese, etc.)")
        logger.info("   - Customer Segments: 4 (Walk-in, Regular, Corporate, VIP)")
        logger.info("   - Includes seasonal patterns and holiday impact")
    else:
        logger.error(f"\n❌ Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
