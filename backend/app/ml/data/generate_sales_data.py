"""
Synthetic Sales Data Generator

Generates realistic retail sales data with:
- Seasonal patterns (higher sales on weekends)
- Holiday effects (Diwali, Holi, etc.)
- Trend components
- Noise and anomalies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


class SalesDataGenerator:
    """
    Generates synthetic retail sales data with realistic patterns.
    """
    
    INDIAN_HOLIDAYS = {
        'Republic Day': (1, 26),
        'Holi': (3, 14),
        'Good Friday': (3, 29),
        'Diwali': (11, 1),
        'New Year': (1, 1),
        'Independence Day': (8, 15),
        'Gandhi Jayanti': (10, 2),
        'Christmas': (12, 25),
    }
    
    def __init__(self, random_seed: int = 42):
        """Initialize generator with optional random seed for reproducibility."""
        np.random.seed(random_seed)
        self.random_seed = random_seed
    
    def generate(
        self,
        start_date: datetime = None,
        days: int = 365,
        base_sales: float = 125000,
        seasonality_strength: float = 0.3,
        trend_strength: float = 0.001,
        noise_level: float = 0.1,
        include_anomalies: bool = True,
    ) -> pd.DataFrame:
        """
        Generate synthetic sales data.
        
        Args:
            start_date: Start date for data generation (default: 365 days ago)
            days: Number of days to generate data for
            base_sales: Average daily sales amount
            seasonality_strength: Amplitude of seasonal variations (0-1)
            trend_strength: Daily trend growth rate
            noise_level: Standard deviation of random noise as fraction of base_sales
            include_anomalies: Whether to include anomaly spikes
            
        Returns:
            DataFrame with columns: date, sales, day_of_week, is_weekend, is_holiday
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)
        
        dates = [start_date + timedelta(days=i) for i in range(days)]
        sales = []
        
        logger.info(f"Generating {days} days of sales data starting from {start_date.date()}")
        
        for i, date in enumerate(dates):
            # Base sales with trend
            trend_component = base_sales * (1 + trend_strength * i)
            
            # Weekly seasonality (higher on weekends)
            day_of_week = date.weekday()  # 0=Monday, 6=Sunday
            is_weekend = 1 if day_of_week >= 5 else 0
            weekly_seasonality = 1 + seasonality_strength * (0.5 if is_weekend else -0.2)
            
            # Holiday effects
            holiday_effect = self._get_holiday_effect(date)
            
            # Random noise
            noise = np.random.normal(0, base_sales * noise_level)
            
            # Anomalies (occasional spikes)
            anomaly = 0
            if include_anomalies and np.random.random() < 0.02:  # 2% chance
                anomaly = np.random.uniform(base_sales * 0.2, base_sales * 0.5)
            
            # Combine components
            daily_sales = (
                trend_component * weekly_seasonality * (1 + holiday_effect) +
                noise + anomaly
            )
            
            # Ensure non-negative sales
            daily_sales = max(0, daily_sales)
            sales.append(daily_sales)
        
        df = pd.DataFrame({
            'date': dates,
            'sales': sales,
        })
        
        # Add metadata columns
        df['day_of_week'] = df['date'].dt.day_name()
        df['is_weekend'] = (df['date'].dt.weekday >= 5).astype(int)
        df['is_holiday'] = df['date'].apply(self._is_holiday)
        
        logger.info(f"Generated {len(df)} sales records")
        logger.info(f"  Mean sales: ₹{df['sales'].mean():,.2f}")
        logger.info(f"  Std dev: ₹{df['sales'].std():,.2f}")
        logger.info(f"  Min: ₹{df['sales'].min():,.2f}")
        logger.info(f"  Max: ₹{df['sales'].max():,.2f}")
        
        return df
    
    def generate_multi_product(
        self,
        start_date: datetime = None,
        days: int = 365,
        num_products: int = 10,
        correlation: float = 0.5,
    ) -> pd.DataFrame:
        """
        Generate sales data for multiple products with correlation.
        
        Args:
            start_date: Start date for data generation
            days: Number of days
            num_products: Number of products to generate
            correlation: Correlation coefficient between products (0-1)
            
        Returns:
            DataFrame with columns: date, product_id, sales, is_weekend, is_holiday
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)
        
        logger.info(f"Generating multi-product sales data: {num_products} products, {days} days")
        
        # Generate base demand
        base_demand = self.generate(start_date, days, base_sales=100000)
        
        all_data = []
        
        for product_id in range(1, num_products + 1):
            # Product-specific base sales
            product_base = np.random.uniform(80000, 150000)
            
            # Generate correlated noise
            if correlation > 0:
                # Use base_demand as anchor and add product-specific variation
                product_sales = base_demand['sales'].values * correlation
                product_sales += np.random.normal(
                    product_base * (1 - correlation),
                    product_base * 0.15 * (1 - correlation)
                )
            else:
                product_sales = self.generate(
                    start_date, days, base_sales=product_base
                )['sales'].values
            
            product_sales = np.maximum(product_sales, 0)
            
            product_df = pd.DataFrame({
                'date': base_demand['date'],
                'product_id': f'prod_{product_id:03d}',
                'sales': product_sales,
                'is_weekend': base_demand['is_weekend'],
                'is_holiday': base_demand['is_holiday'],
            })
            
            all_data.append(product_df)
        
        result = pd.concat(all_data, ignore_index=True)
        logger.info(f"Generated {len(result)} total records across {num_products} products")
        
        return result
    
    def _get_holiday_effect(self, date: datetime) -> float:
        """
        Get holiday multiplier for a specific date.
        
        Args:
            date: Date to check
            
        Returns:
            Multiplier for holiday effect (0-0.5)
        """
        month_day = (date.month, date.day)
        
        # Direct holiday match
        if month_day in self.INDIAN_HOLIDAYS.values():
            return 0.4  # 40% increase on holiday
        
        # Weekend boost (smaller effect)
        if date.weekday() >= 5:  # Friday, Saturday
            return 0.2
        
        return 0
    
    def _is_holiday(self, date: datetime) -> int:
        """Check if date is a known holiday."""
        month_day = (date.month, date.day)
        return 1 if month_day in self.INDIAN_HOLIDAYS.values() else 0
    
    def split_train_test(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into train and test sets.
        
        Args:
            df: DataFrame to split
            test_size: Fraction of data for test set (0-1)
            
        Returns:
            Tuple of (train_df, test_df)
        """
        split_point = int(len(df) * (1 - test_size))
        train = df.iloc[:split_point].reset_index(drop=True)
        test = df.iloc[split_point:].reset_index(drop=True)
        
        logger.info(f"Split data: {len(train)} train samples, {len(test)} test samples")
        
        return train, test
    
    def add_seasonality_pattern(
        self,
        df: pd.DataFrame,
        pattern: str = 'monthly',
        strength: float = 0.2,
    ) -> pd.DataFrame:
        """
        Add additional seasonality pattern to data.
        
        Args:
            df: DataFrame to enhance
            pattern: 'monthly', 'quarterly', or 'yearly'
            strength: Strength of pattern (0-1)
            
        Returns:
            Modified DataFrame
        """
        df = df.copy()
        
        if pattern == 'monthly':
            # Higher sales at month-end
            df['monthly_effect'] = (
                (df['date'].dt.day > 25).astype(int) * strength +
                (df['date'].dt.day < 5).astype(int) * strength * 0.5
            )
        elif pattern == 'quarterly':
            # Boost at quarter boundaries
            df['quarterly_effect'] = (
                (df['date'].dt.month.isin([3, 6, 9, 12])).astype(int) * strength
            )
        elif pattern == 'yearly':
            # Year-end boost
            df['yearly_effect'] = (
                (df['date'].dt.month >= 11).astype(int) * strength
            )
        
        # Apply effect to sales
        if 'monthly_effect' in df.columns:
            df['sales'] = df['sales'] * (1 + df['monthly_effect'])
        elif 'quarterly_effect' in df.columns:
            df['sales'] = df['sales'] * (1 + df['quarterly_effect'])
        elif 'yearly_effect' in df.columns:
            df['sales'] = df['sales'] * (1 + df['yearly_effect'])
        
        return df


def generate_sales_data(
    days: int = 365,
    num_products: int = 1,
    output_path: str = None,
) -> pd.DataFrame:
    """
    Convenience function to generate sales data.
    
    Args:
        days: Number of days of data
        num_products: Number of products
        output_path: Optional path to save CSV
        
    Returns:
        Generated DataFrame
    """
    generator = SalesDataGenerator(random_seed=42)
    
    if num_products == 1:
        df = generator.generate(days=days)
    else:
        df = generator.generate_multi_product(days=days, num_products=num_products)
    
    if output_path:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved data to {output_path}")
    
    return df
