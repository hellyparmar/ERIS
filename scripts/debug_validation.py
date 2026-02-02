"""
Debug script to test validation framework components
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, 'scripts')

from forecast_validation_framework import ProphetModel, NaiveModel

print("=" * 80)
print("DEBUGGING VALIDATION FRAMEWORK")
print("=" * 80)

# Load data
print("\n[1] Loading data...")
df = pd.read_csv('data/validation_dataset.csv')
print(f"Loaded {len(df)} records")

# Prepare data
print("\n[2] Preparing data...")
df['ds'] = pd.to_datetime(df['date'])
df = df.groupby('ds').agg({'revenue': 'sum'}).reset_index()
df = df.rename(columns={'revenue': 'y'})
df = df.sort_values('ds').reset_index(drop=True)

print(f"Aggregated to {len(df)} days")
print(f"Date range: {df['ds'].min()} to {df['ds'].max()}")
print(f"Revenue range: ₹{df['y'].min():,.0f} to ₹{df['y'].max():,.0f}")
print(f"Mean revenue: ₹{df['y'].mean():,.0f}")

# Split data
print("\n[3] Splitting data...")
train_size = int(len(df) * 0.7)
train = df.iloc[:train_size].copy()
test = df.iloc[train_size:train_size+7].copy()  # Just 7 days for testing

print(f"Train: {len(train)} days ({train['ds'].min()} to {train['ds'].max()})")
print(f"Test: {len(test)} days ({test['ds'].min()} to {test['ds'].max()})")

# Test Naive Model
print("\n[4] Testing Naive Model...")
naive = NaiveModel()
naive.fit(train)
naive_pred = naive.predict(horizon=len(test))

print("Naive predictions:")
print(naive_pred[['ds', 'yhat']].head())
print(f"Predicted values: {naive_pred['yhat'].values}")

# Merge with actual
naive_pred = naive_pred.merge(test[['ds', 'y']], on='ds', how='inner')
print(f"\nMerged shape: {naive_pred.shape}")
print(naive_pred[['ds', 'yhat', 'y']])

# Calculate MAPE
if len(naive_pred) > 0 and not naive_pred['y'].isnull().any():
    mape = np.mean(np.abs((naive_pred['y'] - naive_pred['yhat']) / naive_pred['y'])) * 100
    print(f"\nNaive MAPE: {mape:.2f}%")
else:
    print("\n❌ Cannot calculate MAPE - missing or null values")

# Test Prophet Model
print("\n[5] Testing Prophet Model...")
try:
    prophet = ProphetModel()
    
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        prophet.fit(train)
    
    prophet_pred = prophet.predict(horizon=len(test))
    
    print("Prophet predictions:")
    print(prophet_pred[['ds', 'yhat']].head())
    print(f"Predicted values: {prophet_pred['yhat'].values}")
    
    # Merge with actual
    prophet_pred = prophet_pred.merge(test[['ds', 'y']], on='ds', how='inner')
    print(f"\nMerged shape: {prophet_pred.shape}")
    print(prophet_pred[['ds', 'yhat', 'y']])
    
    # Calculate MAPE
    if len(prophet_pred) > 0 and not prophet_pred['y'].isnull().any():
        mape = np.mean(np.abs((prophet_pred['y'] - prophet_pred['yhat']) / prophet_pred['y'])) * 100
        print(f"\nProphet MAPE: {mape:.2f}%")
    else:
        print("\n❌ Cannot calculate MAPE - missing or null values")
        
except Exception as e:
    print(f"❌ Prophet failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
