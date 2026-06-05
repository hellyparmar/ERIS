#!/usr/bin/env python3
"""
Petpooja Baseline Model Validation
Runs 7-day moving average on test set to validate data quality
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error
import json

def main():
    print("\n" + "="*80)
    print("PETPOOJA BASELINE MODEL VALIDATION")
    print("="*80)

    # Load data
    data_dir = Path("/tmp/petpooja_18months_data")

    if not data_dir.exists():
        print("❌ Data directory not found!")
        return 1

    print("📦 Loading sales data...")
    sales = pd.read_csv(data_dir / "sales.csv")
    sales['sale_date'] = pd.to_datetime(sales['sale_date'])

    # Split train/test
    train_sales = sales[sales['is_training_data'] == True].copy()
    test_sales = sales[sales['is_testing_data'] == True].copy()

    # Daily aggregation
    train_daily = train_sales.groupby(train_sales['sale_date'].dt.date)['total_amount'].sum()
    test_daily = test_sales.groupby(test_sales['sale_date'].dt.date)['total_amount'].sum()

    # Convert to datetime index
    train_daily.index = pd.to_datetime(train_daily.index)
    test_daily.index = pd.to_datetime(test_daily.index)

    print("
✅ Data loaded successfully"    print(f"Training period: {train_daily.index.min().date()} to {train_daily.index.max().date()}")
    print(f"Testing period:  {test_daily.index.min().date()} to {test_daily.index.max().date()}")
    print(f"Training samples: {len(train_daily)} days")
    print(f"Testing samples:  {len(test_daily)} days")

    # Baseline: 7-day moving average
    print("
🤖 Running 7-Day Moving Average Baseline..."    forecast = np.full(len(test_daily), train_daily.iloc[-7:].mean())

    # Calculate metrics
    mae = mean_absolute_error(test_daily.values, forecast)
    rmse = np.sqrt(mean_squared_error(test_daily.values, forecast))
    mape = np.mean(np.abs((test_daily.values - forecast) / test_daily.values)) * 100

    print("
📊 BASELINE MODEL RESULTS"    print("="*80)
    print(f"Model:              7-Day Moving Average")
    print(f"MAE (₹):           {mae:>12,.2f}")
    print(f"RMSE (₹):          {rmse:>12,.2f}")
    print(f"MAPE (%):          {mape:>12.2f}")
    print(f"Training Avg (₹):  {train_daily.mean():>12,.2f}")
    print(f"Testing Avg (₹):   {test_daily.mean():>12,.2f}")
    print(f"Forecast Value (₹):{forecast[0]:>12,.2f}")

    # Save results
    results = {
        'model': '7-Day Moving Average',
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape),
        'training_avg': float(train_daily.mean()),
        'testing_avg': float(test_daily.mean()),
        'forecast_value': float(forecast[0]),
        'training_period': {
            'start': str(train_daily.index.min().date()),
            'end': str(train_daily.index.max().date())
        },
        'testing_period': {
            'start': str(test_daily.index.min().date()),
            'end': str(test_daily.index.max().date())
        }
    }

    with open('/tmp/petpooja_baseline_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("
✅ Results saved to /tmp/petpooja_baseline_results.json"    print("\n" + "="*80)
    print("🎯 VALIDATION COMPLETE!")
    print("="*80)

    # Assessment
    if mape < 15:
        print("✅ GOOD: Baseline MAPE < 15% - Data quality validated!")
    elif mape < 25:
        print("⚠️  FAIR: Baseline MAPE 15-25% - Data shows some variance")
    else:
        print("❌ POOR: Baseline MAPE > 25% - Data may have quality issues")

    return 0

if __name__ == "__main__":
    exit(main())
