"""
Generate Realistic Retail Transaction Dataset for Forecast Validation
Academic-Quality Data Generation for R-DIOS Thesis

This script generates 18 months of realistic retail transaction data with:
- Multiple stores and products
- Realistic seasonality patterns (weekly, monthly, yearly)
- Indian holiday effects (Diwali, Holi, Eid, etc.)
- Weather impacts (monsoon season)
- Promotional periods
- Realistic noise and variance
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetailDataGenerator:
    """Generate realistic retail transaction data for validation"""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        self.seed = seed
        
        # Indian holidays (2023-2024)
        self.holidays = {
            'Diwali': [
                ('2023-11-12', '2023-11-14', 1.45),  # 45% boost
                ('2024-10-31', '2024-11-02', 1.45)
            ],
            'Holi': [
                ('2023-03-07', '2023-03-09', 1.30),  # 30% boost
                ('2024-03-25', '2024-03-27', 1.30)
            ],
            'Eid': [
                ('2023-04-21', '2023-04-23', 1.35),
                ('2024-04-10', '2024-04-12', 1.35)
            ],
            'Christmas': [
                ('2023-12-24', '2023-12-26', 1.28),
                ('2024-12-24', '2024-12-26', 1.28)
            ],
            'Independence_Day': [
                ('2023-08-14', '2023-08-16', 1.15),
                ('2024-08-14', '2024-08-16', 1.15)
            ],
            'Republic_Day': [
                ('2023-01-25', '2023-01-27', 1.12),
                ('2024-01-25', '2024-01-27', 1.12)
            ],
            'Dussehra': [
                ('2023-10-23', '2023-10-25', 1.25),
                ('2024-10-12', '2024-10-14', 1.25)
            ],
            'Ganesh_Chaturthi': [
                ('2023-09-18', '2023-09-20', 1.20),
                ('2024-09-06', '2024-09-08', 1.20)
            ]
        }
        
    def _get_holiday_multiplier(self, date):
        """Get revenue multiplier for holidays"""
        date_str = date.strftime('%Y-%m-%d')
        
        for holiday_name, periods in self.holidays.items():
            for start_str, end_str, multiplier in periods:
                if start_str <= date_str <= end_str:
                    return multiplier, holiday_name
        
        return 1.0, None
    
    def _get_seasonal_multiplier(self, date):
        """Calculate seasonal effects"""
        # Yearly seasonality (peak in Oct-Dec, low in Jun-Aug)
        day_of_year = date.timetuple().tm_yday
        yearly = 1 + 0.25 * np.sin((day_of_year - 90) * 2 * np.pi / 365)
        
        # Weekly seasonality (high on weekends)
        day_of_week = date.weekday()
        if day_of_week in [5, 6]:  # Saturday, Sunday
            weekly = 1.25
        elif day_of_week == 4:  # Friday
            weekly = 1.15
        else:
            weekly = 0.95
        
        # Monthly seasonality (peak at month start and end - salary days)
        day_of_month = date.day
        if day_of_month <= 5 or day_of_month >= 25:
            monthly = 1.12
        else:
            monthly = 1.0
        
        # Monsoon effect (June-September) - reduced footfall
        if date.month in [6, 7, 8, 9]:
            monsoon = 0.82
        else:
            monsoon = 1.0
        
        return yearly * weekly * monthly * monsoon
    
    def generate_daily_aggregates(
        self,
        start_date='2023-06-01',
        end_date='2024-12-31',
        base_daily_revenue=85000,
        num_stores=5
    ):
        """
        Generate daily aggregated sales data
        
        Args:
            start_date: Start date for data generation
            end_date: End date for data generation
            base_daily_revenue: Base daily revenue per store
            num_stores: Number of stores
            
        Returns:
            DataFrame with daily aggregated sales
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        dates = pd.date_range(start=start, end=end, freq='D')
        
        logger.info(f"Generating {len(dates)} days of data for {num_stores} stores...")
        
        data = []
        
        for date in dates:
            for store_id in range(1, num_stores + 1):
                # Base revenue with slight store variation
                store_multiplier = 0.8 + (store_id * 0.1)  # Stores have different sizes
                revenue = base_daily_revenue * store_multiplier
                
                # Add trend (3% annual growth)
                days_since_start = (date - start).days
                trend = 1 + (0.03 * days_since_start / 365)
                revenue *= trend
                
                # Seasonal effects
                seasonal = self._get_seasonal_multiplier(date)
                revenue *= seasonal
                
                # Holiday effects
                holiday_mult, holiday_name = self._get_holiday_multiplier(date)
                revenue *= holiday_mult
                
                # Random noise (±8%)
                noise = np.random.normal(1.0, 0.08)
                revenue *= noise
                
                # Ensure non-negative
                revenue = max(revenue, 0)
                
                # Calculate derived metrics
                avg_transaction = 450 + np.random.normal(0, 50)
                num_transactions = int(revenue / avg_transaction)
                avg_items_per_transaction = 3.5 + np.random.normal(0, 1.2)
                total_items = int(num_transactions * avg_items_per_transaction)
                
                data.append({
                    'date': date,
                    'store_id': store_id,
                    'revenue': round(revenue, 2),
                    'num_transactions': num_transactions,
                    'total_items_sold': total_items,
                    'avg_transaction_value': round(revenue / num_transactions if num_transactions > 0 else 0, 2),
                    'is_weekend': 1 if date.weekday() in [5, 6] else 0,
                    'is_holiday': 1 if holiday_name else 0,
                    'holiday_name': holiday_name,
                    'is_monsoon': 1 if date.month in [6, 7, 8, 9] else 0,
                    'day_of_week': date.dayofweek,
                    'day_of_month': date.day,
                    'month': date.month,
                    'quarter': (date.month - 1) // 3 + 1,
                    'year': date.year
                })
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} store-day records")
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"Total revenue: ₹{df['revenue'].sum():,.0f}")
        logger.info(f"Avg daily revenue per store: ₹{df['revenue'].mean():,.0f}")
        
        return df
    
    def save_to_csv(self, df, output_path):
        """Save dataset to CSV"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved dataset to {output_path}")
        
        # Also save summary statistics
        summary_path = output_path.parent / f"{output_path.stem}_summary.txt"
        with open(summary_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("RETAIL VALIDATION DATASET SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Seed: {self.seed}\n\n")
            f.write(f"Records: {len(df):,}\n")
            f.write(f"Date Range: {df['date'].min()} to {df['date'].max()}\n")
            f.write(f"Number of Stores: {df['store_id'].nunique()}\n")
            f.write(f"Number of Days: {df['date'].nunique()}\n\n")
            f.write(f"Total Revenue: ₹{df['revenue'].sum():,.2f}\n")
            f.write(f"Avg Daily Revenue (per store): ₹{df['revenue'].mean():,.2f}\n")
            f.write(f"Median Daily Revenue: ₹{df['revenue'].median():,.2f}\n")
            f.write(f"Std Dev: ₹{df['revenue'].std():,.2f}\n\n")
            f.write(f"Holiday Days: {df['is_holiday'].sum()}\n")
            f.write(f"Weekend Days: {df['is_weekend'].sum()}\n")
            f.write(f"Monsoon Days: {df['is_monsoon'].sum()}\n\n")
            f.write("Revenue by Month:\n")
            f.write(df.groupby('month')['revenue'].agg(['sum', 'mean']).to_string())
            f.write("\n\n")
            f.write("Revenue by Store:\n")
            f.write(df.groupby('store_id')['revenue'].agg(['sum', 'mean', 'count']).to_string())
        
        logger.info(f"Saved summary to {summary_path}")
        
        return output_path


def main():
    """Generate validation dataset"""
    generator = RetailDataGenerator(seed=42)
    
    # Generate 18 months of data (June 2023 - Dec 2024)
    df = generator.generate_daily_aggregates(
        start_date='2023-06-01',
        end_date='2024-12-31',
        base_daily_revenue=85000,  # ₹85,000 per store per day
        num_stores=5
    )
    
    # Save to CSV
    output_path = Path(__file__).parent.parent / 'data' / 'validation_dataset.csv'
    generator.save_to_csv(df, output_path)
    
    print("\n" + "=" * 60)
    print("✅ VALIDATION DATASET GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nDataset saved to: {output_path}")
    print(f"Records: {len(df):,}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total revenue: ₹{df['revenue'].sum():,.0f}")
    print(f"\nYou can now run the forecast validation script!")


if __name__ == "__main__":
    main()
