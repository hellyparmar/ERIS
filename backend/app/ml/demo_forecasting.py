#!/usr/bin/env python
"""
Forecasting System Demo & Test Script

Demonstrates the complete forecasting workflow:
1. Generate synthetic sales data
2. Train Prophet model
3. Generate forecasts
4. Evaluate model accuracy
5. Display metrics

Usage:
    python app/ml/demo_forecasting.py
"""

import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.forecasting import ProphetForecaster
from app.ml.data import SalesDataGenerator
import tempfile


def demo_basic_forecast():
    """Demo: Basic single-product forecasting."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Sales Forecasting")
    print("="*60)
    
    # Generate synthetic data
    print("\n1. Generating synthetic sales data (365 days)...")
    generator = SalesDataGenerator(random_seed=42)
    df = generator.generate(
        days=365,
        base_sales=125000,
        seasonality_strength=0.3,
        trend_strength=0.001
    )
    print(f"   ✅ Generated {len(df)} records")
    print(f"   Mean sales: ₹{df['sales'].mean():,.2f}")
    print(f"   Std dev: ₹{df['sales'].std():,.2f}")
    
    # Split data
    train_df, test_df = generator.split_train_test(df, test_size=0.2)
    print(f"\n2. Split data: {len(train_df)} train, {len(test_df)} test")
    
    # Train model
    print("\n3. Training Prophet model...")
    model_dir = tempfile.mkdtemp()
    forecaster = ProphetForecaster(country_code='IN', model_dir=model_dir)
    
    result = forecaster.train(train_df, product_id='prod_coffee')
    print(f"   ✅ Model trained successfully")
    print(f"   Training samples: {result['training_samples']}")
    print(f"   Model saved: {result['model_path']}")
    
    # Generate forecast
    print("\n4. Generating 30-day forecast...")
    forecast = forecaster.predict(days_ahead=30)
    print(f"   ✅ Generated {len(forecast)} forecast points")
    print(f"\n   Sample forecast (first 5 days):")
    print("   Date              | Forecast      | Lower Bound   | Upper Bound")
    print("   " + "-"*62)
    for _, row in forecast.head(5).iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        print(f"   {date_str} | ₹{row['yhat']:>11,.0f} | ₹{row['yhat_lower']:>11,.0f} | ₹{row['yhat_upper']:>11,.0f}")
    
    # Evaluate model
    print("\n5. Evaluating model accuracy...")
    metrics = forecaster.evaluate(test_df, product_id='prod_coffee')
    print(f"   ✅ Evaluation complete")
    print(f"\n   Metrics:")
    print(f"   • RMSE (Root Mean Square Error): ₹{metrics['rmse']:,.2f}")
    print(f"   • MAE (Mean Absolute Error):     ₹{metrics['mae']:,.2f}")
    print(f"   • MAPE (Mean Absolute % Error):  {metrics['mape']:.2f}%")
    print(f"   • Direction Accuracy:            {metrics['direction_accuracy']:.2f}%")
    print(f"   • Evaluation Samples:            {metrics['samples']}")
    
    return metrics


def demo_multi_product():
    """Demo: Multi-product portfolio forecasting."""
    print("\n" + "="*60)
    print("DEMO 2: Multi-Product Portfolio Forecasting")
    print("="*60)
    
    # Generate multi-product data
    print("\n1. Generating multi-product data (10 products, 90 days)...")
    generator = SalesDataGenerator(random_seed=42)
    df = generator.generate_multi_product(
        days=90,
        num_products=10,
        correlation=0.6
    )
    print(f"   ✅ Generated {len(df)} total records")
    print(f"   Products: {df['product_id'].nunique()}")
    print(f"   Days: {df.groupby('product_id')['date'].nunique().iloc[0]}")
    
    # Train models for each product
    print("\n2. Training models for each product...")
    model_dir = tempfile.mkdtemp()
    forecaster = ProphetForecaster(country_code='IN', model_dir=model_dir)
    
    products = df['product_id'].unique()[:3]  # Just demo 3 products
    metrics_all = {}
    
    for product_id in products:
        product_data = df[df['product_id'] == product_id].reset_index(drop=True)
        product_data = product_data.rename(columns={'date': 'date', 'sales': 'sales'})
        
        try:
            forecaster.train(product_data, product_id=product_id)
            print(f"   ✅ Trained: {product_id}")
        except Exception as e:
            print(f"   ⚠️  Skipped {product_id}: {str(e)[:50]}")
    
    # Generate forecasts
    print("\n3. Generating forecasts...")
    for product_id in products[:1]:  # Demo first product
        forecast = forecaster.predict(days_ahead=30)
        print(f"   ✅ Forecast for {product_id}: {len(forecast)} days")
        print(f"      Average predicted sales: ₹{forecast['yhat'].mean():,.0f}")
        print(f"      Confidence interval: ₹{forecast['yhat_lower'].mean():,.0f} - ₹{forecast['yhat_upper'].mean():,.0f}")


def demo_seasonality():
    """Demo: Seasonality pattern analysis."""
    print("\n" + "="*60)
    print("DEMO 3: Seasonality Pattern Analysis")
    print("="*60)
    
    # Generate data with patterns
    print("\n1. Generating data with multiple seasonality patterns...")
    generator = SalesDataGenerator(random_seed=42)
    df = generator.generate(days=365)
    
    # Add patterns
    df = generator.add_seasonality_pattern(df, pattern='monthly', strength=0.15)
    print("   ✅ Added monthly seasonality (month-end peaks)")
    
    df = generator.add_seasonality_pattern(df, pattern='yearly', strength=0.2)
    print("   ✅ Added yearly seasonality (year-end boost)")
    
    # Analyze patterns
    print("\n2. Analyzing seasonal patterns...")
    
    # Weekend effect
    weekend_avg = df[df['is_weekend'] == 1]['sales'].mean()
    weekday_avg = df[df['is_weekend'] == 0]['sales'].mean()
    weekend_boost = ((weekend_avg - weekday_avg) / weekday_avg * 100)
    
    print(f"   Weekend boost: {weekend_boost:+.1f}%")
    print(f"   • Weekday average: ₹{weekday_avg:,.0f}")
    print(f"   • Weekend average: ₹{weekend_avg:,.0f}")
    
    # Holiday effect
    holiday_avg = df[df['is_holiday'] == 1]['sales'].mean()
    regular_avg = df[df['is_holiday'] == 0]['sales'].mean()
    holiday_boost = ((holiday_avg - regular_avg) / regular_avg * 100)
    
    print(f"   Holiday boost: {holiday_boost:+.1f}%")
    print(f"   • Regular day average: ₹{regular_avg:,.0f}")
    print(f"   • Holiday average: ₹{holiday_avg:,.0f}")


def main():
    """Run all demos."""
    print("\n" + "█"*60)
    print("█  Sales Forecasting System - Complete Demo")
    print("█  MSc Data Science Project")
    print("█"*60)
    
    try:
        # Run demos
        metrics = demo_basic_forecast()
        demo_multi_product()
        demo_seasonality()
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"""
✅ All demos completed successfully!

Key Results:
• MAPE: {metrics['mape']:.2f}% (Model accuracy)
• Direction Accuracy: {metrics['direction_accuracy']:.2f}% (Trend prediction)
• Samples Evaluated: {metrics['samples']}

The forecasting system is ready for:
✓ Product-level demand forecasting
✓ Portfolio optimization
✓ Inventory planning
✓ Revenue forecasting
✓ Seasonality analysis

Next Steps:
1. Integrate with real sales data
2. Set up automated retraining pipeline
3. Deploy API endpoints
4. Monitor forecast accuracy over time
5. Incorporate external regressors (promotions, events)
        """)
        
        return 0
    
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
