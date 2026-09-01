"""
Dataset Verification Script
Checks if all required Olist CSV files are present and validates basic structure
"""

import os
import pandas as pd
from pathlib import Path

# Expected files and their minimum row counts
EXPECTED_FILES = {
    'olist_orders_dataset.csv': 99000,
    'olist_order_items_dataset.csv': 112000,
    'olist_products_dataset.csv': 32000,
    'olist_customers_dataset.csv': 99000,
    'olist_sellers_dataset.csv': 3000,
    'olist_order_payments_dataset.csv': 103000,
    'olist_geolocation_dataset.csv': 1000000
}

def verify_dataset():
    """
    Verify Olist dataset files exist and meet minimum requirements
    """
    print("🔍 R-DIOS v5.0 - Dataset Verification\n")
    
    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent.parent / 'data' / 'raw'
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        print("\nℹ️  Please create the directory and download the Olist dataset")
        print("   URL: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
        return False
    
    print(f"📁 Checking directory: {data_dir}\n")
    
    all_ok = True
    total_rows = 0
    total_size = 0
    
    for filename, min_rows in EXPECTED_FILES.items():
        filepath = data_dir / filename
        
        if not filepath.exists():
            print(f"❌ {filename} - NOT FOUND")
            all_ok = False
            continue
        
        # Get file size
        file_size = filepath.stat().st_size / (1024 * 1024)  # MB
        total_size += file_size
        
        # Read CSV and count rows
        try:
            df = pd.read_csv(filepath)
            row_count = len(df)
            total_rows += row_count
            
            if row_count >= min_rows:
                print(f"✅ {filename}")
                print(f"   Rows: {row_count:,} | Size: {file_size:.2f} MB")
            else:
                print(f"⚠️  {filename}")
                print(f"   Rows: {row_count:,} (expected >= {min_rows:,})")
                print(f"   Size: {file_size:.2f} MB")
                all_ok = False
                
        except Exception as e:
            print(f"❌ {filename} - ERROR reading file")
            print(f"   {str(e)}")
            all_ok = False
    
    print(f"\n{'='*60}")
    print(f"📊 Summary:")
    print(f"   Total Files: {len(EXPECTED_FILES)}")
    print(f"   Total Rows: {total_rows:,}")
    print(f"   Total Size: {total_size:.2f} MB")
    
    if all_ok:
        print(f"\n✅ All dataset files verified successfully!")
        print(f"\n🎯 Next step: Run data_quality_check.py")
        return True
    else:
        print(f"\n❌ Verification failed. Please check missing/incomplete files.")
        return False

if __name__ == "__main__":
    success = verify_dataset()
    exit(0 if success else 1)
