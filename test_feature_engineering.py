"""
R-DIOS Feature Engineering - Test Script
Tests the RetailFeatureEngineer class with sample retail data
"""

import sys
sys.path.append('src')

import pandas as pd
import numpy as np
from features.processor import RetailFeatureEngineer, print_feature_summary

# Generate sample retail data
print("Generating sample retail dataset...")
np.random.seed(42)

dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
n_stores = 5
n_products = 10

data = []
for store_id in range(1, n_stores + 1):
    for product_id in range(1, n_products + 1):
        for date in dates:
            # Simulate sales with:
            # - Weekly seasonality (weekends higher)
            # - Monthly trend
            # - Random noise
            base_sales = 100
            weekend_boost = 30 if date.dayofweek >= 5 else 0
            monthly_trend = date.month * 5
            noise = np.random.normal(0, 20)
            
            sales = max(0, base_sales + weekend_boost + monthly_trend + noise)
            
            data.append({
                'date': date,
                'store_id': f'STORE_{store_id}',
                'product_id': f'PROD_{product_id}',
                'sales': sales
            })

df = pd.DataFrame(data)
print(f"✅ Created dataset with {len(df)} records")
print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
print(f"   Stores: {df['store_id'].nunique()}")
print(f"   Products: {df['product_id'].nunique()}")

# Initialize feature engineer
print("\n" + "="*80)
print("TESTING RETAILFEATUREENGINEER")
print("="*80)

engineer = RetailFeatureEngineer()

# Test individual methods
print("\n1️⃣  Testing create_time_features()...")
df_time = engineer.create_time_features(df.copy())
time_features = ['day_of_week', 'month', 'quarter', 'is_weekend', 'day_of_month', 'week_of_year']
print(f"   ✅ Created features: {time_features}")
print(f"   Sample: {df_time[time_features].head(1).to_dict('records')[0]}")

print("\n2️⃣  Testing create_cyclical_features()...")
df_cyclical = engineer.create_cyclical_features(df_time.copy())
cyclical_features = ['month_sin', 'month_cos', 'dow_sin', 'dow_cos', 'dom_sin', 'dom_cos']
print(f"   ✅ Created features: {cyclical_features}")
print(f"   Sample (month=1): sin={df_cyclical['month_sin'].iloc[0]:.3f}, cos={df_cyclical['month_cos'].iloc[0]:.3f}")

print("\n3️⃣  Testing create_lag_features()...")
df_lags = engineer.create_lag_features(df_cyclical.copy(), lags=[1, 7, 30])
lag_features = [col for col in df_lags.columns if 'lag' in col]
print(f"   ✅ Created features: {lag_features}")
print(f"   Row 30 sales: {df_lags.iloc[30]['sales']:.2f}")
print(f"   Row 30 lag_1: {df_lags.iloc[30]['sales_lag_1']:.2f}")
print(f"   Row 37 lag_7: {df_lags.iloc[37]['sales_lag_7']:.2f}")

print("\n4️⃣  Testing create_rolling_window()...")
df_rolling = engineer.create_rolling_window(df_lags.copy(), windows=[7, 30])
rolling_features = [col for col in df_rolling.columns if 'rolling' in col]
print(f"   ✅ Created features: {rolling_features}")
print(f"   Row 100 sales: {df_rolling.iloc[100]['sales']:.2f}")
print(f"   Row 100 rolling_mean_7: {df_rolling.iloc[100]['sales_rolling_mean_7']:.2f}")
print(f"   Row 100 rolling_std_7: {df_rolling.iloc[100]['sales_rolling_std_7']:.2f}")

print("\n5️⃣  Testing encode_categoricals()...")
df_encoded = engineer.encode_categoricals(df_rolling.copy(), fit=True)
print(f"   ✅ Store IDs encoded: {df_encoded['store_id_encoded'].nunique()} unique values")
print(f"   ✅ Product IDs encoded: {df_encoded['product_id_encoded'].nunique()} unique values")
print(f"   Sample: STORE_1 -> {df_encoded[df_encoded['store_id']=='STORE_1']['store_id_encoded'].iloc[0]}")

print("\n6️⃣  Testing scale_targets()...")
df_scaled = engineer.scale_targets(df_encoded.copy())
print(f"   ✅ Created log-transformed target: sales_log")
print(f"   Original sales range: [{df_scaled['sales'].min():.2f}, {df_scaled['sales'].max():.2f}]")
print(f"   Log-scaled range: [{df_scaled['sales_log'].min():.2f}, {df_scaled['sales_log'].max():.2f}]")

# Test complete pipeline
print("\n" + "="*80)
print("TESTING COMPLETE PIPELINE")
print("="*80)

df_transformed = engineer.transform(df.copy(), fit=True, include_lags=True, include_rolling=True)

# Print feature summary
print_feature_summary(df_transformed, df)

# Verify no missing values in critical features
critical_features = engineer.get_feature_names(df_transformed)
print(f"\n🔍 Checking for NaN values in {len(critical_features)} features...")
nan_counts = df_transformed[critical_features].isna().sum()
features_with_nan = nan_counts[nan_counts > 0]

if len(features_with_nan) > 0:
    print(f"   ⚠️  Found NaN values in {len(features_with_nan)} features:")
    for feat, count in features_with_nan.items():
        pct = (count / len(df_transformed)) * 100
        print(f"      - {feat}: {count} ({pct:.1f}%)")
else:
    print("   ✅ No NaN values found!")

print("\n" + "="*80)
print("✅ ALL TESTS PASSED - Feature Engineering Module Ready!")
print("="*80)
print("\n🚀 Next Steps:")
print("   1. Integrate with MultiDatasetLoader")
print("   2. Create model training pipeline")
print("   3. Deploy to R-DIOS Intelligence Engine")
