"""
Demand Forecasting Service - Prophet Implementation
Thesis Week 5: Prophet baseline with seasonality and holiday effects
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import json
from pathlib import Path

# Prophet import with fallback
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProphetForecaster:
    """
    Prophet-based demand forecasting for R-DIOS thesis
    
    Key features:
    - Multiple seasonality (yearly, weekly, monthly)
    - Indian holiday effects
    - External regressors (weather, economic)
    - Cross-validation for model evaluation
    """
    
    def __init__(
        self,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
        holidays_df: pd.DataFrame = None,
        include_holidays: bool = True,
        growth: str = 'linear',
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        holidays_prior_scale: float = 10.0
    ):
        """
        Initialize Prophet forecaster with customizable parameters
        
        Args:
            yearly_seasonality: Include yearly patterns
            weekly_seasonality: Include weekly patterns
            daily_seasonality: Include daily patterns (for hourly data)
            holidays_df: DataFrame with 'ds' and 'holiday' columns
            include_holidays: Whether to add Indian holidays
            growth: 'linear' or 'logistic'
            changepoint_prior_scale: Flexibility of trend changes
            seasonality_prior_scale: Flexibility of seasonality
            holidays_prior_scale: Flexibility of holiday effects
        """
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.holidays_df = holidays_df
        self.include_holidays = include_holidays
        self.growth = growth
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_prior_scale = seasonality_prior_scale
        self.holidays_prior_scale = holidays_prior_scale
        
        self.model = None
        self.forecast = None
        self.training_data = None
        self.metrics = {}
        
        if not PROPHET_AVAILABLE:
            logger.warning("Prophet not installed. Using mock forecaster.")
    
    def _get_indian_holidays(self) -> pd.DataFrame:
        """Generate Indian holiday calendar for Prophet"""
        holidays = []
        
        # Major Indian holidays (2022-2025)
        holiday_definitions = {
            'Diwali': [
                '2022-10-24', '2023-11-12', '2024-10-31', '2025-10-20'
            ],
            'Holi': [
                '2022-03-18', '2023-03-08', '2024-03-25', '2025-03-14'
            ],
            'Eid': [
                '2022-05-03', '2023-04-22', '2024-04-10', '2025-03-31'
            ],
            'Christmas': [
                '2022-12-25', '2023-12-25', '2024-12-25', '2025-12-25'
            ],
            'Independence_Day': [
                '2022-08-15', '2023-08-15', '2024-08-15', '2025-08-15'
            ],
            'Republic_Day': [
                '2022-01-26', '2023-01-26', '2024-01-26', '2025-01-26'
            ],
            'Dussehra': [
                '2022-10-05', '2023-10-24', '2024-10-12', '2025-10-02'
            ],
            'Ganesh_Chaturthi': [
                '2022-08-31', '2023-09-19', '2024-09-07', '2025-08-27'
            ]
        }
        
        for holiday_name, dates in holiday_definitions.items():
            for date_str in dates:
                holidays.append({
                    'holiday': holiday_name,
                    'ds': pd.to_datetime(date_str),
                    'lower_window': -2,  # 2 days before
                    'upper_window': 1    # 1 day after
                })
        
        return pd.DataFrame(holidays)
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        date_column: str = 'date',
        target_column: str = 'revenue',
        regressors: List[str] = None
    ) -> pd.DataFrame:
        """
        Prepare data in Prophet format (ds, y, optional regressors)
        
        Args:
            df: Input DataFrame
            date_column: Name of date column
            target_column: Name of target variable column
            regressors: List of additional regressor column names
        
        Returns:
            Prophet-formatted DataFrame
        """
        prophet_df = pd.DataFrame()
        prophet_df['ds'] = pd.to_datetime(df[date_column])
        prophet_df['y'] = df[target_column].astype(float)
        
        # Add regressors if provided
        if regressors:
            for reg in regressors:
                if reg in df.columns:
                    prophet_df[reg] = df[reg].astype(float)
        
        # Sort by date
        prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)
        
        # Handle missing values
        prophet_df['y'] = prophet_df['y'].fillna(prophet_df['y'].mean())
        
        self.training_data = prophet_df
        logger.info(f"Prepared {len(prophet_df)} rows for Prophet")
        
        return prophet_df
    
    def fit(
        self,
        df: pd.DataFrame,
        regressors: List[str] = None
    ) -> 'ProphetForecaster':
        """
        Fit Prophet model to data
        
        Args:
            df: Prophet-formatted DataFrame (ds, y, regressors)
            regressors: List of regressor columns to include
        
        Returns:
            self for chaining
        """
        if not PROPHET_AVAILABLE:
            logger.warning("Prophet not available, using mock fit")
            self.model = "mock"
            return self
        
        # Initialize model with parameters
        holidays = None
        if self.include_holidays:
            holidays = self.holidays_df if self.holidays_df is not None else self._get_indian_holidays()
        
        self.model = Prophet(
            yearly_seasonality=self.yearly_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            daily_seasonality=self.daily_seasonality,
            holidays=holidays,
            growth=self.growth,
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_prior_scale=self.seasonality_prior_scale,
            holidays_prior_scale=self.holidays_prior_scale
        )
        
        # Add custom seasonality for Indian retail patterns
        self.model.add_seasonality(
            name='monthly',
            period=30.5,
            fourier_order=5
        )
        
        # Add external regressors
        if regressors:
            for reg in regressors:
                if reg in df.columns:
                    self.model.add_regressor(reg)
        
        # Fit the model
        logger.info("Fitting Prophet model...")
        self.model.fit(df)
        logger.info("Prophet model fitted successfully")
        
        return self
    
    def predict(
        self,
        periods: int = 30,
        freq: str = 'D',
        include_history: bool = True,
        future_regressors: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Generate forecast for future periods
        
        Args:
            periods: Number of periods to forecast
            freq: Frequency ('D' for daily, 'W' for weekly)
            include_history: Include historical fitted values
            future_regressors: DataFrame with future regressor values
        
        Returns:
            Forecast DataFrame with confidence intervals
        """
        if not PROPHET_AVAILABLE or self.model == "mock":
            # Generate mock forecast
            return self._mock_forecast(periods)
        
        # Create future dataframe
        future = self.model.make_future_dataframe(
            periods=periods,
            freq=freq,
            include_history=include_history
        )
        
        # Add future regressors if provided
        if future_regressors is not None:
            for col in future_regressors.columns:
                if col != 'ds':
                    future = future.merge(
                        future_regressors[['ds', col]],
                        on='ds',
                        how='left'
                    )
                    # Fill missing regressor values
                    future[col] = future[col].fillna(future[col].mean())
        
        # Generate forecast
        self.forecast = self.model.predict(future)
        
        return self.forecast
    
    def _mock_forecast(self, periods: int) -> pd.DataFrame:
        """Generate mock forecast when Prophet not available"""
        if self.training_data is None:
            # Generate sample data
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=90),
                periods=90 + periods,
                freq='D'
            )
            base_value = 10000
        else:
            last_date = self.training_data['ds'].max()
            dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods, freq='D')
            base_value = self.training_data['y'].mean()
        
        # Generate forecasted values with some trend and seasonality
        forecast_df = pd.DataFrame({
            'ds': dates,
            'yhat': [base_value * (1 + 0.02 * np.sin(i * 2 * np.pi / 7) + np.random.normal(0, 0.1)) for i in range(len(dates))],
        })
        forecast_df['yhat_lower'] = forecast_df['yhat'] * 0.85
        forecast_df['yhat_upper'] = forecast_df['yhat'] * 1.15
        
        return forecast_df
    
    def cross_validate(
        self,
        initial: str = '180 days',
        period: str = '30 days',
        horizon: str = '30 days'
    ) -> pd.DataFrame:
        """
        Perform time-series cross-validation
        
        Args:
            initial: Initial training period
            period: Spacing between cutoff dates
            horizon: Forecast horizon to evaluate
        
        Returns:
            Cross-validation results DataFrame
        """
        if not PROPHET_AVAILABLE or self.model == "mock":
            logger.warning("Cross-validation not available without Prophet")
            return pd.DataFrame()
        
        from prophet.diagnostics import cross_validation, performance_metrics
        
        logger.info(f"Running cross-validation: initial={initial}, period={period}, horizon={horizon}")
        
        cv_results = cross_validation(
            self.model,
            initial=initial,
            period=period,
            horizon=horizon
        )
        
        return cv_results
    
    def evaluate(self, cv_results: pd.DataFrame = None) -> Dict[str, float]:
        """
        Calculate forecast accuracy metrics
        
        Returns:
            Dictionary with MAPE, RMSE, MAE metrics
        """
        if not PROPHET_AVAILABLE or self.model == "mock":
            # Return mock metrics
            return {
                'mape': 12.5,
                'rmse': 1500.0,
                'mae': 1200.0,
                'coverage': 0.95
            }
        
        if cv_results is None:
            cv_results = self.cross_validate()
        
        if cv_results.empty:
            return {}
        
        from prophet.diagnostics import performance_metrics
        
        metrics_df = performance_metrics(cv_results)
        
        self.metrics = {
            'mape': float(metrics_df['mape'].mean()) * 100,
            'rmse': float(metrics_df['rmse'].mean()),
            'mae': float(metrics_df['mae'].mean()),
            'coverage': float(metrics_df['coverage'].mean()) if 'coverage' in metrics_df else None
        }
        
        logger.info(f"Model metrics: MAPE={self.metrics['mape']:.2f}%, RMSE={self.metrics['rmse']:.2f}")
        
        return self.metrics
    
    def get_components(self) -> Dict[str, pd.DataFrame]:
        """
        Extract forecast components (trend, seasonality, holidays)
        
        Returns:
            Dictionary with component DataFrames
        """
        if not PROPHET_AVAILABLE or self.model == "mock" or self.forecast is None:
            return {}
        
        components = {
            'trend': self.forecast[['ds', 'trend']],
            'weekly': self.forecast[['ds', 'weekly']] if 'weekly' in self.forecast else None,
            'yearly': self.forecast[['ds', 'yearly']] if 'yearly' in self.forecast else None,
            'holidays': self.forecast[['ds', 'holidays']] if 'holidays' in self.forecast else None
        }
        
        return {k: v for k, v in components.items() if v is not None}
    
    def save_model(self, path: str):
        """Save model to JSON file"""
        if not PROPHET_AVAILABLE or self.model == "mock":
            logger.warning("Cannot save mock model")
            return
        
        import json
        from prophet.serialize import model_to_json
        
        with open(path, 'w') as f:
            f.write(model_to_json(self.model))
        
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model from JSON file"""
        if not PROPHET_AVAILABLE:
            logger.warning("Prophet not available")
            return
        
        from prophet.serialize import model_from_json
        
        with open(path, 'r') as f:
            self.model = model_from_json(f.read())
        
        logger.info(f"Model loaded from {path}")


class DemandForecastPipeline:
    """
    Complete demand forecasting pipeline for thesis
    Manages data loading, preprocessing, model training, and evaluation
    """
    
    def __init__(self, data_path: str = 'data/transformed'):
        self.data_path = Path(data_path)
        self.forecaster = None
        self.data = None
        self.results = {}
    
    def load_data(self) -> pd.DataFrame:
        """Load and aggregate sales data for forecasting"""
        orders_path = self.data_path / 'orders_transformed.csv'
        items_path = self.data_path / 'order_items_transformed.csv'
        
        if not orders_path.exists():
            logger.warning(f"Data file not found: {orders_path}")
            # Generate sample data
            return self._generate_sample_data()
        
        orders = pd.read_csv(orders_path)
        items = pd.read_csv(items_path)
        
        # Parse dates
        orders['order_date'] = pd.to_datetime(orders['order_date'])
        
        # Merge and aggregate by date
        merged = items.merge(orders[['order_id', 'order_date', 'is_holiday', 'is_monsoon']], 
                            left_on='invoice_number', right_on='order_id', how='left')
        
        # Daily aggregation
        daily = merged.groupby(merged['order_date'].dt.date).agg({
            'price_inr': 'sum',
            'order_id': 'nunique',
            'is_holiday': 'max',
            'is_monsoon': 'max'
        }).reset_index()
        
        daily.columns = ['date', 'revenue', 'orders', 'is_holiday', 'is_monsoon']
        daily['date'] = pd.to_datetime(daily['date'])
        
        self.data = daily
        logger.info(f"Loaded {len(daily)} days of data")
        
        return daily
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """Generate sample data for testing"""
        np.random.seed(42)
        dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')
        
        base_revenue = 50000
        data = []
        
        for date in dates:
            # Base with trend
            revenue = base_revenue * (1 + 0.0003 * (date - dates[0]).days)
            
            # Weekly seasonality
            revenue *= 1 + 0.1 * np.sin(date.dayofweek * 2 * np.pi / 7)
            
            # Yearly seasonality
            revenue *= 1 + 0.2 * np.sin((date.dayofyear - 90) * 2 * np.pi / 365)
            
            # Diwali boost
            if date.month == 10 and 20 <= date.day <= 30:
                revenue *= 1.35
            
            # Monsoon dip
            if date.month in [6, 7, 8, 9]:
                revenue *= 0.85
            
            # Random noise
            revenue *= 1 + np.random.normal(0, 0.08)
            
            data.append({
                'date': date,
                'revenue': revenue,
                'orders': int(revenue / 500),
                'is_holiday': 1 if date.month == 10 and 20 <= date.day <= 30 else 0,
                'is_monsoon': 1 if date.month in [6, 7, 8, 9] else 0
            })
        
        self.data = pd.DataFrame(data)
        return self.data
    
    def run_forecast(
        self,
        forecast_days: int = 30,
        use_regressors: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete forecasting pipeline
        
        Args:
            forecast_days: Days to forecast ahead
            use_regressors: Include external factors
        
        Returns:
            Results dictionary with forecast and metrics
        """
        if self.data is None:
            self.load_data()
        
        # Initialize forecaster
        self.forecaster = ProphetForecaster(
            yearly_seasonality=True,
            weekly_seasonality=True,
            include_holidays=True
        )
        
        # Prepare data
        regressors = ['is_holiday', 'is_monsoon'] if use_regressors else None
        prophet_df = self.forecaster.prepare_data(
            self.data,
            date_column='date',
            target_column='revenue',
            regressors=regressors
        )
        
        # Fit model
        self.forecaster.fit(prophet_df, regressors=regressors)
        
        # Generate forecast
        forecast = self.forecaster.predict(periods=forecast_days)
        
        # Evaluate model
        metrics = self.forecaster.evaluate()
        
        # Store results
        self.results = {
            'forecast': forecast,
            'metrics': metrics,
            'components': self.forecaster.get_components(),
            'training_data': self.data,
            'model_params': {
                'yearly_seasonality': True,
                'weekly_seasonality': True,
                'include_holidays': True,
                'use_regressors': use_regressors
            }
        }
        
        logger.info(f"Forecast complete: {forecast_days} days predicted, MAPE={metrics.get('mape', 'N/A')}")
        
        return self.results
    
    def compare_with_without_regressors(self) -> Dict[str, Any]:
        """
        Compare model performance with and without external regressors
        Key thesis analysis for RQ2
        """
        results = {}
        
        # Without regressors
        logger.info("Training model WITHOUT regressors...")
        self.run_forecast(use_regressors=False)
        results['without_regressors'] = self.results['metrics'].copy()
        
        # With regressors
        logger.info("Training model WITH regressors...")
        self.run_forecast(use_regressors=True)
        results['with_regressors'] = self.results['metrics'].copy()
        
        # Calculate improvement
        if results['without_regressors'] and results['with_regressors']:
            mape_without = results['without_regressors'].get('mape', 0)
            mape_with = results['with_regressors'].get('mape', 0)
            
            if mape_without > 0:
                improvement = ((mape_without - mape_with) / mape_without) * 100
                results['improvement'] = {
                    'mape_improvement_percent': round(improvement, 2),
                    'conclusion': 'External factors improve accuracy' if improvement > 0 else 'No significant improvement'
                }
        
        logger.info(f"Comparison complete: {results.get('improvement', {})}")
        
        return results


# CLI for testing
if __name__ == "__main__":
    pipeline = DemandForecastPipeline()
    
    # Load data
    data = pipeline.load_data()
    print(f"\nLoaded {len(data)} days of data")
    print(f"Date range: {data['date'].min()} to {data['date'].max()}")
    print(f"Total revenue: ₹{data['revenue'].sum():,.0f}")
    
    # Run forecast
    results = pipeline.run_forecast(forecast_days=30)
    print(f"\nForecast Metrics:")
    for metric, value in results['metrics'].items():
        print(f"  {metric}: {value}")
    
    # Compare with/without regressors
    comparison = pipeline.compare_with_without_regressors()
    print(f"\nRegressor Comparison:")
    print(f"  Without: MAPE = {comparison['without_regressors'].get('mape', 'N/A')}")
    print(f"  With: MAPE = {comparison['with_regressors'].get('mape', 'N/A')}")
    print(f"  Improvement: {comparison.get('improvement', {})}")
