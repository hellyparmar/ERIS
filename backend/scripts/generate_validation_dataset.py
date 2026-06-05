#!/usr/bin/env python3
"""
Generate validation dataset for forecasting tests.
Creates synthetic retail sales data with known patterns for model validation.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ml.data.generate_sales_data import SalesDataGenerator

def generate_validation_dataset():
    """Generate validation dataset for forecasting tests."""
    print("""================================================================================
TESTING FORECAST VALIDATION FRAMEWORK
================================================================================
""")

    print("[1/5] Checking validation dataset...")

    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)

    validation_file = os.path.join(data_dir, 'validation_dataset.csv')

    if os.path.exists(validation_file):
        print(f"✅ Validation dataset already exists: {validation_file}")
        return True

    print("❌ Validation dataset not found. Generating...")

    print("[2/5] Initializing data generator...")
    generator = SalesDataGenerator(random_seed=42)

    print("[3/5] Generating multi-product sales data...")
    # Generate 2 years of data for 5 products
    df = generator.generate_multi_product(days=730, num_products=5)

    print("[4/5] Adding validation features...")
    # Add some additional features for validation
    df['product_category'] = df['product_id'].apply(lambda x: f"Category_{x.split('_')[1]}")
    df['store_region'] = np.random.choice(['North', 'South', 'East', 'West'], len(df))
    df['promotion_active'] = np.random.choice([0, 1], len(df), p=[0.85, 0.15])

    print("[5/5] Saving validation dataset...")
    df.to_csv(validation_file, index=False)

    print(f"✅ Validation dataset created: {validation_file}")
    print(f"   - Shape: {df.shape}")
    print(f"   - Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   - Products: {df['product_id'].nunique()}")
    print(f"   - Total sales: {df['sales'].sum():,.0f}")

    return True

if __name__ == "__main__":
    try:
        generate_validation_dataset()
        print("\n✅ Validation dataset generation complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error generating validation dataset: {e}")
        sys.exit(1)