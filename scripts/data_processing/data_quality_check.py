"""
Data Quality Check Script for Olist Dataset
Analyzes data completeness, types, relationships, and identifies issues
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class DataQualityChecker:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.datasets = {}
        self.report = []
        
    def load_datasets(self):
        """Load all Olist CSV files"""
        print("📂 Loading datasets...\n")
        
        files = {
            'orders': 'olist_orders_dataset.csv',
            'order_items': 'olist_order_items_dataset.csv',
            'products': 'olist_products_dataset.csv',
            'customers': 'olist_customers_dataset.csv',
            'sellers': 'olist_sellers_dataset.csv',
            'payments': 'olist_order_payments_dataset.csv',
            'reviews': 'olist_order_reviews_dataset.csv',
            'geolocation': 'olist_geolocation_dataset.csv',
            'category_translation': 'product_category_name_translation.csv'
        }
        
        for name, filename in files.items():
            filepath = self.data_dir / filename
            if filepath.exists():
                self.datasets[name] = pd.read_csv(filepath)
                print(f"✅ Loaded {name}: {len(self.datasets[name]):,} rows")
            else:
                print(f"⚠️  {filename} not found")
        
        print(f"\n📊 Total datasets loaded: {len(self.datasets)}\n")
        
    def check_missing_values(self):
        """Analyze missing values across all datasets"""
        print("=" * 80)
        print("1️⃣  MISSING VALUES ANALYSIS")
        print("=" * 80 + "\n")
        
        for name, df in self.datasets.items():
            missing = df.isnull().sum()
            missing_pct = (missing / len(df)) * 100
            
            if missing.sum() > 0:
                print(f"📋 {name.upper()}:")
                for col, count in missing[missing > 0].items():
                    pct = missing_pct[col]
                    status = "⚠️ " if pct > 10 else "ℹ️ "
                    print(f"   {status} {col}: {count:,} ({pct:.2f}%)")
                print()
            else:
                print(f"✅ {name.upper()}: No missing values\n")
    
    def check_data_types(self):
        """Verify data types of key columns"""
        print("=" * 80)
        print("2️⃣  DATA TYPE VERIFICATION")
        print("=" * 80 + "\n")
        
        # Check orders dataset
        if 'orders' in self.datasets:
            df = self.datasets['orders']
            print("📋 ORDERS:")
            print(f"   order_id: {df['order_id'].dtype}")
            print(f"   customer_id: {df['customer_id'].dtype}")
            
            # Convert date columns
            date_cols = [col for col in df.columns if 'timestamp' in col or 'date' in col]
            print(f"   Date columns found: {len(date_cols)}")
            for col in date_cols:
                print(f"     - {col}: {df[col].dtype}")
            print()
    
    def check_date_ranges(self):
        """Analyze date ranges in the dataset"""
        print("=" * 80)
        print("3️⃣  DATE RANGE ANALYSIS")
        print("=" * 80 + "\n")
        
        if 'orders' in self.datasets:
            df = self.datasets['orders']
            
            # Parse purchase timestamp
            df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
            
            min_date = df['order_purchase_timestamp'].min()
            max_date = df['order_purchase_timestamp'].max()
            date_range = (max_date - min_date).days
            
            print(f"📅 Order Date Range:")
            print(f"   Start: {min_date.strftime('%Y-%m-%d')}")
            print(f"   End: {max_date.strftime('%Y-%m-%d')}")
            print(f"   Duration: {date_range} days ({date_range/365:.2f} years)")
            
            # Monthly distribution
            df['year_month'] = df['order_purchase_timestamp'].dt.to_period('M')
            monthly_counts = df['year_month'].value_counts().sort_index()
            
            print(f"\n📊 Orders per Month:")
            print(f"   Min: {monthly_counts.min():,} orders")
            print(f"   Max: {monthly_counts.max():,} orders")
            print(f"   Avg: {monthly_counts.mean():.0f} orders")
            print()
    
    def check_foreign_keys(self):
        """Verify referential integrity"""
        print("=" * 80)
        print("4️⃣  FOREIGN KEY INTEGRITY")
        print("=" * 80 + "\n")
        
        checks = [
            ('order_items', 'order_id', 'orders', 'order_id'),
            ('payments', 'order_id', 'orders', 'order_id'),
            ('order_items', 'product_id', 'products', 'product_id'),
            ('order_items', 'seller_id', 'sellers', 'seller_id'),
            ('orders', 'customer_id', 'customers', 'customer_id'),
        ]
        
        for child_table, child_key, parent_table, parent_key in checks:
            if child_table in self.datasets and parent_table in self.datasets:
                child_df = self.datasets[child_table]
                parent_df = self.datasets[parent_table]
                
                child_values = set(child_df[child_key].dropna())
                parent_values = set(parent_df[parent_key].dropna())
                
                orphans = child_values - parent_values
                orphan_pct = (len(orphans) / len(child_values)) * 100 if child_values else 0
                
                if len(orphans) == 0:
                    print(f"✅ {child_table}.{child_key} → {parent_table}.{parent_key}: Valid")
                else:
                    print(f"⚠️  {child_table}.{child_key} → {parent_table}.{parent_key}: {len(orphans)} orphans ({orphan_pct:.2f}%)")
        
        print()
    
    def check_duplicates(self):
        """Check for duplicate records"""
        print("=" * 80)
        print("5️⃣  DUPLICATE RECORDS")
        print("=" * 80 + "\n")
        
        for name, df in self.datasets.items():
            if name == 'geolocation':
                continue  # Skip geolocation (expected duplicates)
            
            # Find primary key column
            id_cols = [col for col in df.columns if col.endswith('_id') and not col.startswith('customer') and not col.startswith('seller')]
            
            if id_cols:
                pk_col = id_cols[0]
                duplicates = df[pk_col].duplicated().sum()
                
                if duplicates > 0:
                    print(f"⚠️  {name.upper()}: {duplicates:,} duplicate {pk_col} values")
                else:
                    print(f"✅ {name.upper()}: No duplicates in {pk_col}")
        
        print()
    
    def analyze_business_metrics(self):
        """Calculate key business metrics"""
        print("=" * 80)
        print("6️⃣  BUSINESS METRICS SNAPSHOT")
        print("=" * 80 + "\n")
        
        if 'orders' in self.datasets and 'order_items' in self.datasets and 'payments' in self.datasets:
            orders = self.datasets['orders']
            items = self.datasets['order_items']
            payments = self.datasets['payments']
            
            # Total orders
            total_orders = len(orders)
            print(f"📦 Total Orders: {total_orders:,}")
            
            # Total revenue
            total_revenue = payments['payment_value'].sum()
            print(f"💰 Total Revenue: R$ {total_revenue:,.2f}")
            
            # Average order value
            avg_order_value = total_revenue / total_orders
            print(f"📊 Avg Order Value: R$ {avg_order_value:.2f}")
            
            # Products sold
            total_products_sold = len(items)
            print(f"🛒 Total Products Sold: {total_products_sold:,}")
            
            # Unique customers
            unique_customers = orders['customer_id'].nunique()
            print(f"👥 Unique Customers: {unique_customers:,}")
            
            # Unique sellers
            unique_sellers = items['seller_id'].nunique()
            print(f"🏪 Unique Sellers: {unique_sellers:,}")
            
            # Payment methods
            if 'payment_type' in payments.columns:
                print(f"\n💳 Payment Methods:")
                payment_dist = payments['payment_type'].value_counts()
                for method, count in payment_dist.items():
                    pct = (count / len(payments)) * 100
                    print(f"   {method}: {count:,} ({pct:.1f}%)")
            
            print()
    
    def generate_summary_report(self):
        """Generate overall data quality summary"""
        print("=" * 80)
        print("📋 DATA QUALITY SUMMARY")
        print("=" * 80 + "\n")
        
        total_rows = sum(len(df) for df in self.datasets.values())
        total_cols = sum(len(df.columns) for df in self.datasets.values())
        
        print(f"✅ Datasets Loaded: {len(self.datasets)}")
        print(f"✅ Total Rows: {total_rows:,}")
        print(f"✅ Total Columns: {total_cols}")
        
        # Calculate overall missing percentage
        total_cells = sum(df.size for df in self.datasets.values())
        total_missing = sum(df.isnull().sum().sum() for df in self.datasets.values())
        missing_pct = (total_missing / total_cells) * 100
        
        print(f"📊 Overall Missing Data: {missing_pct:.2f}%")
        
        print("\n🎯 Ready for:")
        print("   ✅ Enrichment (HSN codes, GST rates, cost prices)")
        print("   ✅ External factors integration (weather, economy)")
        print("   ✅ PostgreSQL loading with partitioning")
        
        print("\n⚠️  Action Items:")
        print("   1. Handle missing values in reviews (optional table)")
        print("   2. Add synthetic fields for Indian context")
        print("   3. Fetch external factor data (2016-2018)")
        
        print()

def main():
    print("🔍 R-DIOS v5.0 - Data Quality Check")
    print("=" * 80)
    print()
    
    # Initialize checker
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    checker = DataQualityChecker(data_dir)
    
    # Run checks
    checker.load_datasets()
    checker.check_missing_values()
    checker.check_data_types()
    checker.check_date_ranges()
    checker.check_foreign_keys()
    checker.check_duplicates()
    checker.analyze_business_metrics()
    checker.generate_summary_report()
    
    print("✅ Data quality check complete!")
    print()

if __name__ == "__main__":
    main()
