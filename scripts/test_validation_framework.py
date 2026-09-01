"""
Quick Test Script for Forecast Validation Framework
Tests core functionality before running full validation
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

print("=" * 80)
print("TESTING FORECAST VALIDATION FRAMEWORK")
print("=" * 80)

# Test 1: Check data file exists
print("\n[1/5] Checking validation dataset...")
data_path = Path('data/validation_dataset.csv')
if not data_path.exists():
    print(f"❌ ERROR: {data_path} not found!")
    print("Run: python scripts/generate_validation_dataset.py")
    sys.exit(1)

df = pd.read_csv(data_path)
print(f"✅ Dataset loaded: {len(df)} records")
print(f"   Date range: {df['date'].min()} to {df['date'].max()}")

# Test 2: Check Prophet installation
print("\n[2/5] Testing Prophet installation...")
try:
    from prophet import Prophet
    print("✅ Prophet installed successfully")
except ImportError as e:
    print(f"❌ ERROR: Prophet not installed - {e}")
    print("Run: pip install prophet")
    sys.exit(1)

# Test 3: Check pmdarima installation
print("\n[3/5] Testing pmdarima installation...")
try:
    from pmdarima import auto_arima
    print("✅ pmdarima installed successfully")
except ImportError as e:
    print(f"❌ ERROR: pmdarima not installed - {e}")
    print("Run: pip install pmdarima")
    sys.exit(1)

# Test 4: Check visualization libraries
print("\n[4/5] Testing visualization libraries...")
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    print("✅ Matplotlib and Seaborn installed")
except ImportError as e:
    print(f"❌ ERROR: Visualization libraries not installed - {e}")
    print("Run: pip install matplotlib seaborn")
    sys.exit(1)

# Test 5: Quick Prophet test
print("\n[5/5] Running quick Prophet test...")
try:
    # Prepare data
    df_test = df[['date', 'revenue']].copy()
    df_test.columns = ['ds', 'y']
    df_test['ds'] = pd.to_datetime(df_test['ds'])
    
    # Aggregate by date
    df_test = df_test.groupby('ds').agg({'y': 'sum'}).reset_index()
    
    # Train on first 100 days
    train = df_test.iloc[:100]
    
    # Fit Prophet
    model = Prophet(
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(train)
    
    # Predict 7 days
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)
    
    print(f"✅ Prophet test successful")
    print(f"   Trained on {len(train)} days")
    print(f"   Generated 7-day forecast")
    
except Exception as e:
    print(f"❌ ERROR: Prophet test failed - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - FRAMEWORK READY")
print("=" * 80)
print("\nYou can now run the full validation:")
print("  python scripts/run_forecast_validation.py")
print("\nOr follow the guide:")
print("  docs/FORECAST_VALIDATION_GUIDE.md")
