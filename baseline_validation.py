#!/usr/bin/env python3
"""
Petpooja 18-Month Dataset - Baseline Model Validation
Validates data quality and establishes baseline forecasting metrics
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error
import json
from datetime import datetime

print("\n" + "="*80)
print("PETPOOJA 18-MONTH DATASET - BASELINE VALIDATION")
print("="*80)

# Load datasets
data_dir = Path("/tmp/petpooja_18months_data")

print("\n📦 Loading datasets...")
products = pd.read_csv(data_dir / "products.csv")
customers = pd.read_csv(data_dir / "customers.csv")
sales = pd.read_csv(data_dir / "sales.csv")
sale_items = pd.read_csv(data_dir / "sale_items.csv")
invoices = pd.read_csv(data_dir / "invoices.csv")
employees = pd.read_csv(data_dir / "employees.csv")

# Convert dates
sales['sale_date'] = pd.to_datetime(sales['sale_date'])
sales['created_at'] = pd.to_datetime(sales['created_at'])

# Prepare time series
train_sales = sales[sales['is_training_data'] == True].copy()
test_sales = sales[sales['is_testing_data'] == True].copy()

train_sales = train_sales.sort_values('sale_date')
test_sales = test_sales.sort_values('sale_date')

train_daily = train_sales.groupby(train_sales['sale_date'].dt.date)['total_amount'].sum()
test_daily = test_sales.groupby(test_sales['sale_date'].dt.date)['total_amount'].sum()

# Convert to datetime index
train_daily.index = pd.to_datetime(train_daily.index)
test_daily.index = pd.to_datetime(test_daily.index)

print("\n✅ Datasets loaded successfully")

# Validation Report
print("\n" + "="*80)
print("DATA QUALITY REPORT")
print("="*80)

print(f"\nDataset Summary:")
print(f"  Products:           {len(products):>6} records")
print(f"  Customers:          {len(customers):>6} records")
print(f"  Sales:              {len(sales):>6} records")
print(f"  Sale Items:         {len(sale_items):>6} records")
print(f"  Invoices:           {len(invoices):>6} records")
print(f"  Employees:          {len(employees):>6} records")

print(f"\nTraining/Testing Split:")
print(f"  Training period:    {train_daily.index.min().date()} to {train_daily.index.max().date()}")
print(f"  Training samples:   {len(train_daily):>6} days ({len(train_sales):>8} transactions)")
print(f"  Training revenue:   ₹{train_sales['total_amount'].sum():>15,.2f}")
print(f"\n  Testing period:     {test_daily.index.min().date()} to {test_daily.index.max().date()}")
print(f"  Testing samples:    {len(test_daily):>6} days ({len(test_sales):>8} transactions)")
print(f"  Testing revenue:    ₹{test_sales['total_amount'].sum():>15,.2f}")

print(f"\nTrain/Test Split Ratio:")
total_days = len(train_daily) + len(test_daily)
print(f"  Train days:         {len(train_daily)/total_days*100:>6.1f}%")
print(f"  Test days:          {len(test_daily)/total_days*100:>6.1f}%")

print(f"\nDaily Sales Statistics (Training Set):")
print(f"  Mean:               ₹{train_daily.mean():>15,.2f}")
print(f"  Median:             ₹{train_daily.median():>15,.2f}")
print(f"  Std Dev:            ₹{train_daily.std():>15,.2f}")
print(f"  Min:                ₹{train_daily.min():>15,.2f}")
print(f"  Max:                ₹{train_daily.max():>15,.2f}")
print(f"  CV:                 {(train_daily.std()/train_daily.mean()):>16.1%}")

print(f"\nDaily Sales Statistics (Testing Set):")
print(f"  Mean:               ₹{test_daily.mean():>15,.2f}")
print(f"  Median:             ₹{test_daily.median():>15,.2f}")
print(f"  Std Dev:            ₹{test_daily.std():>15,.2f}")
print(f"  Min:                ₹{test_daily.min():>15,.2f}")
print(f"  Max:                ₹{test_daily.max():>15,.2f}")
print(f"  CV:                 {(test_daily.std()/test_daily.mean()):>16.1%}")

# Data quality checks
print(f"\nData Quality Checks:")
missing_train = train_daily.isna().sum()
missing_test = test_daily.isna().sum()
print(f"  ✓ Training data completeness: {(1 - missing_train/len(train_daily))*100:.1f}%")
print(f"  ✓ Testing data completeness:  {(1 - missing_test/len(test_daily))*100:.1f}%")
print(f"  ✓ No negative values:         {(train_daily >= 0).all()}")
print(f"  ✓ All records dated correctly: {(sales['sale_date'] <= pd.Timestamp.now()).all()}")

# Baseline Model: 7-Day Moving Average
print("\n" + "="*80)
print("BASELINE MODEL VALIDATION: 7-DAY MOVING AVERAGE")
print("="*80)

forecast_baseline = np.full(len(test_daily), train_daily.iloc[-7:].mean())

mae = mean_absolute_error(test_daily.values, forecast_baseline)
rmse = np.sqrt(mean_squared_error(test_daily.values, forecast_baseline))
mape = np.mean(np.abs((test_daily.values - forecast_baseline) / test_daily.values)) * 100

print(f"\nBaseline Forecast Metrics:")
print(f"  MAE (Mean Absolute Error):  ₹{mae:>12,.2f}")
print(f"  RMSE (Root MSE):            ₹{rmse:>12,.2f}")
print(f"  MAPE (Mean Abs % Error):    {mape:>12.2f}%")

print(f"\nInterpretation:")
print(f"  • On average, forecast is off by ₹{mae:,.0f} per day")
print(f"  • Root squared error of ₹{rmse:,.0f}")
print(f"  • Percentage error of {mape:.1f}%")

if mape < 15:
    print(f"  ✅ GOOD: MAPE < 15% indicates reasonable baseline")
elif mape < 25:
    print(f"  ⚠️  FAIR: MAPE 15-25% suggests model improvements needed")
else:
    print(f"  ❌ POOR: MAPE > 25% indicates need for advanced models")

# Advanced insights
print("\n" + "="*80)
print("DATA INSIGHTS FOR MODEL SELECTION")
print("="*80)

# Check for strong seasonality
sales_by_month = sales.groupby(sales['sale_date'].dt.month)['total_amount'].sum()
monthly_cv = sales_by_month.std() / sales_by_month.mean()
print(f"\nSeasonality Strength (Monthly CV): {monthly_cv:.2f}")
if monthly_cv > 0.2:
    print(f"  → Strong seasonality detected. Use seasonal models (SARIMA, Prophet, XGBoost)")
else:
    print(f"  → Weak seasonality. Simple models may suffice.")

# Check for trend
from scipy import stats
x = np.arange(len(train_daily))
slope, intercept, r_value, p_value, std_err = stats.linregress(x, train_daily.values)
print(f"\nTrend Analysis:")
print(f"  Slope: ₹{slope:.2f} per day (annualized: ₹{slope*365:,.0f})")
print(f"  Trend strength (R²): {r_value**2:.4f}")
if abs(slope) > train_daily.std() * 0.01:
    print(f"  → Significant trend detected. Include trend in models.")
else:
    print(f"  → No significant trend.")

# Recommended models
print(f"\n🤖 Recommended Models:")
print(f"  1. 7-Day MA:           ✓ Quick baseline (baseline)")
print(f"  2. Exp Smoothing:      ✓ Handles trend & seasonality")
print(f"  3. SARIMA:             ✓ Best for strong seasonality")
print(f"  4. Prophet:            ✓ Robust with holidays")
print(f"  5. XGBoost:            ✓ Feature-based, flexible")
print(f"  6. LSTM:               ✓ Deep learning for complex patterns")

# Save validation report
validation_report = {
    'timestamp': datetime.now().isoformat(),
    'dataset': {
        'products': int(len(products)),
        'customers': int(len(customers)),
        'sales': int(len(sales)),
        'sale_items': int(len(sale_items)),
        'invoices': int(len(invoices)),
        'employees': int(len(employees)),
        'total_revenue': float(sales['total_amount'].sum()),
        'avg_daily_sales': float((sales['total_amount'].sum() / len(train_daily + len(test_daily))))
    },
    'train_test_split': {
        'train_days': int(len(train_daily)),
        'test_days': int(len(test_daily)),
        'train_transactions': int(len(train_sales)),
        'test_transactions': int(len(test_sales)),
        'train_period': f"{train_daily.index.min().date()} to {train_daily.index.max().date()}",
        'test_period': f"{test_daily.index.min().date()} to {test_daily.index.max().date()}"
    },
    'baseline_metrics': {
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape),
        'model': '7-Day Moving Average'
    },
    'quality_indicators': {
        'seasonality_strength': float(monthly_cv),
        'trend_slope': float(slope),
        'trend_r_squared': float(r_value**2)
    }
}

with open('/tmp/petpooja_validation_report.json', 'w') as f:
    json.dump(validation_report, f, indent=2)

print("\n✅ Validation report saved to /tmp/petpooja_validation_report.json")

print("\n" + "="*80)
print("✅ BASELINE VALIDATION COMPLETE!")
print("="*80)
print("\nNext Steps:")
print("  1. Run Jupyter notebook for comprehensive model training")
print("  2. Evaluate all 6 models on test set")
print("  3. Select best model for production deployment")
print("  4. Monitor performance over time")
print("\n")
