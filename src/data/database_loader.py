"""
Database Loader - Load transformed CSV data into PostgreSQL
Loads the thesis dataset into the R-DIOS v6.0 schema
"""

import pandas as pd
from pathlib import Path
import logging
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Load transformed data into PostgreSQL"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://rdios:rdios_password@localhost:5432/rdios_production"
        )
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        logger.info(f"DatabaseLoader initialized with: {self.database_url.split('@')[-1]}")
    
    def load_products(self, filepath: str) -> int:
        """Load products from CSV"""
        logger.info(f"Loading products from {filepath}")
        
        df = pd.read_csv(filepath)
        
        # Map columns to database schema
        products = df.rename(columns={
            "product_id": "sku",
            "product_category_name": "original_category",
            "indian_category": "category_name"
        })
        
        # Add required fields
        products["name"] = products["sku"].apply(lambda x: f"Product {x}")
        products["cost_price"] = 100.0  # Will be updated from order_items
        products["selling_price"] = 150.0
        products["stock_level"] = 100
        products["is_active"] = True
        products["created_at"] = datetime.now()
        
        # Get HSN and GST from category
        products["hsn_code"] = products.get("hsn_code", "9999")
        products["gst_rate"] = products.get("gst_rate", 18.0)
        
        # Insert to database
        count = products.to_sql(
            "products_staging",
            self.engine,
            if_exists="replace",
            index=False
        )
        
        logger.info(f"Loaded {len(products)} products to staging table")
        return len(products)
    
    def load_customers(self, filepath: str) -> int:
        """Load customers from CSV"""
        logger.info(f"Loading customers from {filepath}")
        
        df = pd.read_csv(filepath)
        
        customers = df.rename(columns={
            "customer_id": "external_id",
            "customer_city": "city",
            "customer_state": "state"
        })
        
        customers["name"] = customers["external_id"].apply(lambda x: f"Customer {x[-4:]}")
        customers["credit_limit"] = 10000.0
        customers["outstanding_amount"] = 0.0
        customers["purchase_count"] = 0
        customers["total_spent"] = 0.0
        customers["created_at"] = datetime.now()
        
        count = customers.to_sql(
            "customers_staging",
            self.engine,
            if_exists="replace",
            index=False
        )
        
        logger.info(f"Loaded {len(customers)} customers to staging table")
        return len(customers)
    
    def load_orders(self, filepath: str) -> int:
        """Load orders (sales) from CSV"""
        logger.info(f"Loading orders from {filepath}")
        
        df = pd.read_csv(filepath)
        
        # Parse dates
        df["order_date"] = pd.to_datetime(df["order_date"])
        
        sales = df.rename(columns={
            "order_id": "invoice_number",
            "order_date": "sale_date",
            "customer_id": "customer_external_id"
        })
        
        # Add causal analysis fields
        sales["is_holiday"] = sales.get("is_holiday", False)
        sales["holiday_name"] = sales.get("holiday_name", None)
        sales["is_monsoon"] = sales.get("is_monsoon", False)
        sales["payment_status"] = "paid"
        sales["payment_method"] = "upi"
        sales["channel"] = "offline"
        sales["created_at"] = datetime.now()
        
        count = sales.to_sql(
            "sales_staging",
            self.engine,
            if_exists="replace",
            index=False
        )
        
        logger.info(f"Loaded {len(sales)} orders to staging table")
        return len(sales)
    
    def load_order_items(self, filepath: str) -> int:
        """Load order items (sale_items) from CSV"""
        logger.info(f"Loading order items from {filepath}")
        
        df = pd.read_csv(filepath)
        
        items = df.rename(columns={
            "order_id": "invoice_number",
            "product_id": "product_sku",
            "price_inr": "unit_price"
        })
        
        items["quantity"] = 1
        items["line_total"] = items["unit_price"]
        items["gst_rate"] = items.get("gst_rate", 18.0)
        items["gst_amount"] = items.get("gst_amount", items["unit_price"] * 0.18)
        items["created_at"] = datetime.now()
        
        count = items.to_sql(
            "sale_items_staging",
            self.engine,
            if_exists="replace",
            index=False
        )
        
        logger.info(f"Loaded {len(items)} order items to staging table")
        return len(items)
    
    def load_weather(self, filepath: str) -> int:
        """Load weather data"""
        logger.info(f"Loading weather data from {filepath}")
        
        df = pd.read_csv(filepath)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["created_at"] = datetime.now()
        
        count = df.to_sql(
            "weather_data",
            self.engine,
            if_exists="replace",
            index=False
        )
        
        logger.info(f"Loaded {len(df)} weather records")
        return len(df)
    
    def load_economic_indicators(self, filepath: str) -> int:
        """Load economic indicators"""
        logger.info(f"Loading economic indicators from {filepath}")
        
        df = pd.read_csv(filepath)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["created_at"] = datetime.now()
        
        count = df.to_sql(
            "economic_indicators",
            self.engine,
            if_exists="replace",
            index=False
        )
        
        logger.info(f"Loaded {len(df)} economic indicator records")
        return len(df)
    
    def load_all(self, data_dir: str = "data/transformed") -> dict:
        """Load all transformed data"""
        data_path = Path(data_dir)
        results = {}
        
        # Load in dependency order
        files = {
            "products": "products_transformed.csv",
            "customers": "customers_transformed.csv",
            "orders": "orders_transformed.csv",
            "order_items": "order_items_transformed.csv",
            "weather": "weather_data.csv",
            "economic": "economic_indicators.csv"
        }
        
        for name, filename in files.items():
            filepath = data_path / filename
            if filepath.exists():
                try:
                    if name == "products":
                        results[name] = self.load_products(str(filepath))
                    elif name == "customers":
                        results[name] = self.load_customers(str(filepath))
                    elif name == "orders":
                        results[name] = self.load_orders(str(filepath))
                    elif name == "order_items":
                        results[name] = self.load_order_items(str(filepath))
                    elif name == "weather":
                        results[name] = self.load_weather(str(filepath))
                    elif name == "economic":
                        results[name] = self.load_economic_indicators(str(filepath))
                except Exception as e:
                    logger.error(f"Error loading {name}: {e}")
                    results[name] = f"ERROR: {e}"
            else:
                logger.warning(f"File not found: {filepath}")
                results[name] = "NOT FOUND"
        
        return results


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load transformed data to PostgreSQL")
    parser.add_argument("--data-dir", type=str, default="data/transformed", help="Data directory")
    parser.add_argument("--database-url", type=str, default=None, help="Database URL")
    
    args = parser.parse_args()
    
    loader = DatabaseLoader(database_url=args.database_url)
    results = loader.load_all(data_dir=args.data_dir)
    
    print("\n✅ Data Loading Complete!")
    print("=" * 50)
    for name, count in results.items():
        status = f"✓ {count:,} rows" if isinstance(count, int) else f"✗ {count}"
        print(f"  {name}: {status}")
