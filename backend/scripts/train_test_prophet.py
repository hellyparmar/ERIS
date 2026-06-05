#!/usr/bin/env python3
"""
Train and test Prophet forecast on 18-month sales dataset.

- Uses 17.5 months of history for training
- Uses the final 15 days as unseen test data
- Reports RMSE, MAE, MAPE, and directional accuracy
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, select

# Ensure backend package is importable when running from scripts folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.ml.forecasting.prophet_forecaster import ProphetForecaster
except ImportError:
    ProphetForecaster = None

# Load env
load_dotenv()


def load_sales_dataframe(database_url: str, outlet_id: Optional[int] = None):
    engine = create_engine(database_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    sales_table = metadata.tables['sales']

    with engine.connect() as conn:
        query = select(sales_table)
        if outlet_id is not None:
            query = query.where(sales_table.c.outlet_id == outlet_id)
        result = conn.execute(query)
        rows = [dict(row._mapping) for row in result]

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError('No sales data found for forecasting.')

    # Keep only necessary columns
    df = df[['sale_date', 'total_amount', 'outlet_id']].copy()
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    df['sale_date'] = df['sale_date'].dt.tz_localize(None)
    return df


def aggregate_daily_sales(df: pd.DataFrame) -> pd.DataFrame:
    daily = (
        df.groupby(df['sale_date'].dt.floor('D'))['total_amount']
        .sum()
        .reset_index()
        .rename(columns={'sale_date': 'ds', 'total_amount': 'y'})
    )
    return daily


def split_train_test(df: pd.DataFrame, test_days: int = 15):
    df = df.sort_values('ds').reset_index(drop=True)
    if len(df) < test_days + 1:
        raise ValueError(f"Insufficient data for a {test_days}-day holdout")

    train = df.iloc[:-test_days].reset_index(drop=True)
    test = df.iloc[-test_days:].reset_index(drop=True)
    return train, test


def main():
    if ProphetForecaster is None:
        print('❌ ProphetForecaster import failed. Ensure the backend module path is correct and prophet is installed.')
        sys.exit(1)

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('❌ DATABASE_URL is not set in .env')
        sys.exit(1)

    try:
        raw_sales = load_sales_dataframe(database_url)
        daily_sales = aggregate_daily_sales(raw_sales)

        expected_days = 540
        if len(daily_sales) != expected_days:
            print(f'⚠️  Found {len(daily_sales)} days of aggregated sales; expected {expected_days} days for an 18-month dataset.')

        train_df, test_df = split_train_test(daily_sales, test_days=15)
        if len(train_df) != expected_days - 15 or len(test_df) != 15:
            raise ValueError('Train/test split does not match 17.5 months training and 0.5 months test data.')

        forecaster = ProphetForecaster(country_code='IN', model_dir='models', session=None)
        train_info = forecaster.train(train_df, product_id='all_products', outlet_id=None)

        forecast_df = forecaster.predict(days_ahead=15, product_id='all_products', outlet_id=None, include_history=False)
        metrics = forecaster.evaluate(test_df, product_id='all_products', outlet_id=None)

        print('\n🎯 Forecast evaluation results:')
        print(f"- Train samples: {len(train_df)}")
        print(f"- Test samples: {len(test_df)}")
        print(f"- Forecast horizon: 15 days")
        print(f"- RMSE: {metrics['rmse']:.2f}")
        print(f"- MAE: {metrics['mae']:.2f}")
        print(f"- MAPE: {metrics['mape']:.2f}%")
        print(f"- Directional accuracy: {metrics['direction_accuracy']:.2f}%")

        print('\n📅 Test period:')
        print(f"  {test_df['ds'].min().date()} to {test_df['ds'].max().date()}")

    except Exception as exc:
        print(f'❌ Error: {exc}')
        sys.exit(1)


if __name__ == '__main__':
    main()
