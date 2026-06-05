"""
Prophet-based Sales Forecasting Module

Implements Facebook's Prophet time-series forecasting model for retail sales prediction.
Supports product-level forecasts with seasonal decomposition, holiday effects, and regressors.
Integrates with database for external regressors (temperature, CPI, fuel prices) and Redis caching.
"""

import os
import pickle
import json
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timedelta
import logging

import pandas as pd
import numpy as np
import redis

try:
    from prophet import Prophet
except ImportError:
    Prophet = None

logger = logging.getLogger(__name__)

# Redis configuration
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
except:
    redis_client = None


class ProphetForecaster:
    """
    Facebook Prophet-based forecasting for retail sales.
    
    Features:
    - Automatic seasonality detection (daily, weekly, yearly)
    - Holiday effect modeling
    - Trend changepoints
    - Custom regressors (weekend, holiday indicators)
    - Model serialization for persistence
    """

    def __init__(self, country_code: str = "IN", model_dir: str = "models", session=None):
        """
        Initialize the Prophet forecaster.
        
        Args:
            country_code: ISO country code for holiday calendar (default: India)
            model_dir: Directory to save/load trained models
            session: SQLAlchemy async session for database queries
        """
        if Prophet is None:
            raise ImportError(
                "Prophet is not installed. Install with: pip install prophet"
            )
        
        self.country_code = country_code
        self.model_dir = model_dir
        self.model: Optional[Prophet] = None
        self.product_id: Optional[str] = None
        self.outlet_id: Optional[int] = None
        self.training_data: Optional[pd.DataFrame] = None
        self.session = session  # Database session for external regressors
        self.external_regressors: Dict[str, List[float]] = {}
        
        os.makedirs(model_dir, exist_ok=True)

    def prepare_data(self, sales_df: pd.DataFrame, include_external_regressors: bool = True) -> pd.DataFrame:
        """
        Prepare sales data for Prophet by converting to Prophet format.
        
        Expects input DataFrame with columns: 'date' and 'sales' (or 'amount').
        Adds regressors for weekend, holiday, and external factors (temperature, CPI, fuel).
        
        Args:
            sales_df: DataFrame with columns ['date', 'sales'] or ['date', 'amount']
            include_external_regressors: Whether to include external regressors from DB
            
        Returns:
            DataFrame in Prophet format with columns ['ds', 'y'] and additional regressors
        """
        df = sales_df.copy()
        
        # Rename columns to Prophet format
        if 'date' in df.columns:
            df.rename(columns={'date': 'ds'}, inplace=True)
        
        if 'sales' in df.columns:
            df.rename(columns={'sales': 'y'}, inplace=True)
        elif 'amount' in df.columns:
            df.rename(columns={'amount': 'y'}, inplace=True)
        
        # Ensure ds is datetime
        df['ds'] = pd.to_datetime(df['ds'])
        df['y'] = pd.to_numeric(df['y'], errors='coerce').fillna(0)
        
        # Sort by date
        df = df.sort_values('ds').reset_index(drop=True)
        
        # Add regressors
        df['day_of_week'] = df['ds'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_holiday'] = self._get_holiday_indicator(df['ds'])
        df['month'] = df['ds'].dt.month
        df['day_of_month'] = df['ds'].dt.day
        df['quarter'] = df['ds'].dt.quarter
        
        # Add lag features for seasonality
        df['sales_lag_7'] = df['y'].shift(7).fillna(df['y'].mean())
        df['sales_lag_30'] = df['y'].shift(30).fillna(df['y'].mean())
        df['sales_ma7'] = df['y'].rolling(window=7, min_periods=1).mean()
        df['sales_ma30'] = df['y'].rolling(window=30, min_periods=1).mean()
        
        # Add external regressors if available
        if include_external_regressors and self.external_regressors:
            for regressor_name, values in self.external_regressors.items():
                if len(values) == len(df):
                    df[regressor_name] = values
        
        # Select relevant columns
        base_cols = ['ds', 'y', 'is_weekend', 'is_holiday', 'month', 'day_of_month', 
                     'quarter', 'sales_lag_7', 'sales_lag_30', 'sales_ma7', 'sales_ma30']
        
        result_cols = [col for col in base_cols if col in df.columns]
        
        # Add external regressors to result columns
        if include_external_regressors and self.external_regressors:
            result_cols.extend(list(self.external_regressors.keys()))
        
        return df[result_cols]

    def load_external_regressors(self, start_date: datetime, end_date: datetime) -> Dict[str, List[float]]:
        """
        Load external regressors (temperature, CPI, fuel prices) from database.
        
        Args:
            start_date: Start date for regressor data
            end_date: End date for regressor data
            
        Returns:
            Dictionary mapping regressor names to lists of values
        """
        if not self.session:
            logger.warning("No database session available. Skipping external regressors.")
            return {}
        
        try:
            from sqlalchemy import select
            from app.models.external_regressor import ExternalRegressor
            
            # Query external regressors from database
            stmt = select(ExternalRegressor).where(
                (ExternalRegressor.date >= start_date) &
                (ExternalRegressor.date <= end_date)
            ).order_by(ExternalRegressor.date)
            
            result = self.session.execute(stmt)
            regressors_data = result.scalars().all()
            
            if not regressors_data:
                logger.info("No external regressors found in database")
                return {}
            
            # Convert to dictionary of lists
            regressor_dict = {
                'temperature': [],
                'cpi': [],
                'fuel_price': [],
            }
            
            for regressor in regressors_data:
                regressor_dict['temperature'].append(regressor.temperature or 25.0)
                regressor_dict['cpi'].append(regressor.cpi or 100.0)
                regressor_dict['fuel_price'].append(regressor.fuel_price or 100.0)
            
            # Normalize regressors to 0-1 scale for better Prophet fitting
            for key in regressor_dict:
                values = np.array(regressor_dict[key])
                if len(values) > 0:
                    min_val, max_val = values.min(), values.max()
                    if max_val > min_val:
                        regressor_dict[key] = ((values - min_val) / (max_val - min_val)).tolist()
            
            self.external_regressors = regressor_dict
            logger.info(f"Loaded external regressors: {list(regressor_dict.keys())}")
            return regressor_dict
        
        except Exception as e:
            logger.error(f"Error loading external regressors: {str(e)}")
            return {}

    def _get_holiday_indicator(self, dates: pd.Series) -> pd.Series:
        """
        Generate holiday indicator for Indian holidays.
        
        Args:
            dates: Series of datetime values
            
        Returns:
            Binary Series (1 for holiday, 0 otherwise)
        """
        # Indian holidays (approximate dates - can be customized)
        holidays = {
            'Republic Day': (1, 26),
            'Holi': (3, 14),  # Approximate
            'Good Friday': (3, 29),  # Varies by year
            'Diwali': (11, 1),  # Approximate
            'New Year': (1, 1),
            'Independence Day': (8, 15),
            'Gandhi Jayanti': (10, 2),
        }
        
        is_holiday = pd.Series(0, index=dates.index)
        
        for holiday_name, (month, day) in holidays.items():
            holiday_dates = pd.to_datetime(
                [f"{year}-{month:02d}-{day:02d}" for year in dates.dt.year.unique()]
            )
            is_holiday |= dates.dt.date.isin(holiday_dates.date).astype(int)
        
        return is_holiday

    def train(
        self,
        data: pd.DataFrame,
        product_id: str,
        outlet_id: Optional[int] = None,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
    ) -> Dict[str, any]:
        """
        Train a Prophet model on historical sales data.
        
        Args:
            data: DataFrame with columns ['ds', 'y'] and optional regressors
            product_id: Identifier for the product being forecasted
            outlet_id: Optional outlet ID for multi-outlet forecasting
            yearly_seasonality: Include yearly seasonality
            weekly_seasonality: Include weekly seasonality
            daily_seasonality: Include daily seasonality
            
        Returns:
            Dictionary with training metadata
        """
        # Prepare data
        df = self.prepare_data(data, include_external_regressors=True)
        
        if len(df) < 14:  # Minimum data for meaningful forecast
            raise ValueError("Insufficient training data. Need at least 14 days of history.")
        
        self.product_id = product_id
        self.outlet_id = outlet_id
        self.training_data = df.copy()
        
        try:
            # Initialize Prophet model with optimized parameters
            self.model = Prophet(
                yearly_seasonality=yearly_seasonality,
                weekly_seasonality=weekly_seasonality,
                daily_seasonality=daily_seasonality,
                interval_width=0.95,
                changepoint_prior_scale=0.05,
                seasonality_mode='multiplicative' if df['y'].std() > df['y'].mean() * 0.5 else 'additive',
                seasonality_prior_scale=10,
            )
            
            # Add regressors with appropriate priors
            self.model.add_regressor('is_weekend', prior_scale=10)
            self.model.add_regressor('is_holiday', prior_scale=15)
            self.model.add_regressor('month', prior_scale=5)
            self.model.add_regressor('day_of_month', prior_scale=3)
            self.model.add_regressor('quarter', prior_scale=2)
            self.model.add_regressor('sales_lag_7', prior_scale=20)
            self.model.add_regressor('sales_lag_30', prior_scale=15)
            self.model.add_regressor('sales_ma7', prior_scale=25)
            self.model.add_regressor('sales_ma30', prior_scale=20)
            
            # Add external regressors if available
            if self.external_regressors:
                self.model.add_regressor('temperature', prior_scale=5)
                self.model.add_regressor('cpi', prior_scale=8)
                self.model.add_regressor('fuel_price', prior_scale=6)
            
            # Add Indian holidays to the model
            holidays_df = self._create_holidays_df()
            if not holidays_df.empty:
                self.model.add_country_holidays('IN')
            
            # Fit the model
            logger.info(f"Training Prophet model for product {product_id}...")
            with open(os.devnull, 'w') as devnull:
                # Suppress Prophet's verbose output
                import sys
                old_stdout = sys.stdout
                sys.stdout = devnull
                try:
                    self.model.fit(df)
                finally:
                    sys.stdout = old_stdout
            
            # Save model
            model_path = os.path.join(
                self.model_dir, 
                f"prophet_{outlet_id}_{product_id}.pkl" if outlet_id else f"prophet_{product_id}.pkl"
            )
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            logger.info(f"Model saved to {model_path}")
            
            # Cache training metadata in Redis
            cache_key = f"forecast_meta:{outlet_id}:{product_id}" if outlet_id else f"forecast_meta:{product_id}"
            metadata = {
                'product_id': product_id,
                'outlet_id': outlet_id,
                'training_samples': len(df),
                'trained_at': datetime.utcnow().isoformat(),
                'model_path': model_path,
                'mean_sales': float(df['y'].mean()),
                'std_sales': float(df['y'].std()),
            }
            
            if redis_client:
                try:
                    redis_client.setex(cache_key, 86400, json.dumps(metadata))
                except Exception as e:
                    logger.warning(f"Redis caching failed: {e}")
            
            return {
                'status': 'success',
                **metadata
            }
        
        except Exception as e:
            logger.error(f"Error training Prophet model: {str(e)}")
            raise

    def predict(
        self,
        days_ahead: int = 30,
        product_id: Optional[str] = None,
        outlet_id: Optional[int] = None,
        include_history: bool = False,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Generate sales forecast for specified number of days.
        
        Uses Redis caching (6-hour TTL) to avoid retraining for repeated requests.
        
        Args:
            days_ahead: Number of days to forecast (default: 30)
            product_id: Product ID (uses last trained if not provided)
            outlet_id: Optional outlet ID
            include_history: Include historical data in forecast
            use_cache: Use Redis cache if available
            
        Returns:
            DataFrame with columns: date, yhat (forecast), yhat_lower, yhat_upper, trend, explanation
        """
        if product_id:
            self._load_model(product_id, outlet_id)
        elif not self.model:
            raise ValueError("No model trained. Call train() first or provide product_id.")
        
        # Check cache first
        cache_key = f"forecast:{outlet_id}:{product_id}:{days_ahead}" if outlet_id else f"forecast:{product_id}:{days_ahead}"
        
        if use_cache and redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info(f"Using cached forecast for {cache_key}")
                    forecast_data = json.loads(cached)
                    return pd.DataFrame(forecast_data)
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
        
        try:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=days_ahead)
            
            # Add regressors
            future['day_of_week'] = future['ds'].dt.dayofweek
            future['is_weekend'] = (future['day_of_week'] >= 5).astype(int)
            future['is_holiday'] = self._get_holiday_indicator(future['ds'])
            future['month'] = future['ds'].dt.month
            future['day_of_month'] = future['ds'].dt.day
            future['quarter'] = future['ds'].dt.quarter
            
            # Add lag features based on training data mean/std
            if self.training_data is not None:
                future['sales_lag_7'] = self.training_data['y'].tail(7).mean()
                future['sales_lag_30'] = self.training_data['y'].tail(30).mean()
                future['sales_ma7'] = self.training_data['y'].tail(7).mean()
                future['sales_ma30'] = self.training_data['y'].tail(30).mean()
            else:
                future['sales_lag_7'] = 0
                future['sales_lag_30'] = 0
                future['sales_ma7'] = 0
                future['sales_ma30'] = 0
            
            # Fill external regressors with forward-fill strategy for future dates
            if self.external_regressors:
                for regressor_name in ['temperature', 'cpi', 'fuel_price']:
                    if regressor_name in self.external_regressors:
                        last_value = self.external_regressors[regressor_name][-1]
                        future[regressor_name] = last_value
            
            # Generate forecast
            forecast = self.model.predict(future)
            
            # Extract relevant columns
            result = forecast[[
                'ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend'
            ]].copy()
            
            result.columns = ['date', 'yhat', 'yhat_lower', 'yhat_upper', 'trend']
            result = result.reset_index(drop=True)
            
            # Ensure positive values
            result['yhat'] = result['yhat'].clip(lower=0)
            result['yhat_lower'] = result['yhat_lower'].clip(lower=0)
            
            # Add explanation
            result['explanation'] = result.apply(
                lambda row: self._generate_forecast_explanation(row, forecast),
                axis=1
            )
            
            # Filter to forecast period if not including history
            if not include_history and self.training_data is not None:
                last_date = self.training_data['ds'].max()
                result = result[result['date'] > last_date].reset_index(drop=True)
            
            logger.info(f"Generated {len(result)} forecast points")
            
            # Cache the result (6-hour TTL)
            if redis_client:
                try:
                    redis_client.setex(cache_key, 21600, result.to_json(orient='records'))
                except Exception as e:
                    logger.warning(f"Cache storage failed: {e}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            raise

    def _generate_forecast_explanation(self, row: pd.Series, full_forecast: pd.DataFrame) -> str:
        """
        Generate human-readable explanation for a forecast value.
        
        Args:
            row: Row from forecast DataFrame
            full_forecast: Complete forecast DataFrame for context
            
        Returns:
            Explanation string
        """
        try:
            date = row['date']
            yhat = row['yhat']
            trend = row['trend']
            upper = row['yhat_upper']
            lower = row['yhat_lower']
            
            # Get average and trend direction
            avg_forecast = full_forecast['yhat'].mean()
            trend_direction = "upward" if trend > full_forecast['trend'].mean() else "downward"
            
            # Calculate confidence level
            confidence_width = upper - lower
            avg_width = (full_forecast['yhat_upper'] - full_forecast['yhat_lower']).mean()
            confidence = "high" if confidence_width < avg_width else "moderate"
            
            # Get day of week
            day_name = date.strftime("%A")
            
            # Build explanation
            explanation = f"Predicted sales of ₹{yhat:,.0f} on {day_name}. "
            
            if yhat > avg_forecast * 1.1:
                explanation += "Strong demand expected. "
            elif yhat < avg_forecast * 0.9:
                explanation += "Lower demand expected. "
            else:
                explanation += "Average demand expected. "
            
            explanation += f"{confidence.capitalize()} confidence (₹{lower:,.0f}-₹{upper:,.0f}). "
            explanation += f"{trend_direction.capitalize()} trend observed."
            
            return explanation
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Forecast value generated. Please refer to confidence interval."

    def evaluate(
        self,
        test_data: pd.DataFrame,
        product_id: Optional[str] = None,
        outlet_id: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        Evaluate model performance on test set.
        
        Calculates RMSE, MAE, MAPE, and directional accuracy.
        
        Args:
            test_data: DataFrame with columns ['ds', 'y']
            product_id: Product ID (uses last trained if not provided)
            outlet_id: Optional outlet ID
            
        Returns:
            Dictionary with metrics: rmse, mae, mape, direction_accuracy
        """
        if product_id:
            self._load_model(product_id, outlet_id)
        elif not self.model:
            raise ValueError("No model trained. Call train() first or provide product_id.")
        
        try:
            # Prepare test data
            test_df = self.prepare_data(test_data, include_external_regressors=True)
            
            # Generate predictions
            forecast = self.model.predict(test_df[['ds', 'is_weekend', 'is_holiday', 'month', 
                                                      'day_of_month', 'quarter', 'sales_lag_7',
                                                      'sales_lag_30', 'sales_ma7', 'sales_ma30']])
            
            # Merge actual and predicted
            eval_df = test_df[['ds', 'y']].copy()
            eval_df['yhat'] = forecast['yhat'].values
            
            # Ensure positive values
            eval_df['yhat'] = eval_df['yhat'].clip(lower=0)
            
            # Calculate metrics
            y_actual = eval_df['y'].values
            y_pred = eval_df['yhat'].values
            
            # RMSE
            rmse = np.sqrt(np.mean((y_actual - y_pred) ** 2))
            
            # MAE
            mae = np.mean(np.abs(y_actual - y_pred))
            
            # MAPE (Mean Absolute Percentage Error)
            mask = y_actual != 0
            mape = np.mean(np.abs((y_actual[mask] - y_pred[mask]) / y_actual[mask])) * 100 if mask.sum() > 0 else 0
            
            # Directional Accuracy
            actual_direction = np.diff(y_actual) > 0
            pred_direction = np.diff(y_pred) > 0
            direction_accuracy = (actual_direction == pred_direction).sum() / len(actual_direction) * 100 if len(actual_direction) > 0 else 0
            
            metrics = {
                'rmse': float(rmse),
                'mae': float(mae),
                'mape': float(mape),
                'direction_accuracy': float(direction_accuracy),
                'samples': len(eval_df),
            }
            
            logger.info(f"Evaluation metrics: {metrics}")
            return metrics
        
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise

    def _load_model(self, product_id: str, outlet_id: Optional[int] = None) -> None:
        """Load a previously trained model from disk."""
        model_path = os.path.join(
            self.model_dir, 
            f"prophet_{outlet_id}_{product_id}.pkl" if outlet_id else f"prophet_{product_id}.pkl"
        )
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.product_id = product_id
            self.outlet_id = outlet_id
            logger.info(f"Model loaded from {model_path}")
        
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def _create_holidays_df(self) -> pd.DataFrame:
        """Create DataFrame with Indian holidays for Prophet."""
        years = range(2024, 2026)
        holidays_list = []
        
        # Define Indian holidays
        indian_holidays = {
            'Republic Day': (1, 26),
            'Holi': (3, 14),
            'Good Friday': (3, 29),
            'Diwali': (11, 1),
            'New Year': (1, 1),
            'Independence Day': (8, 15),
            'Gandhi Jayanti': (10, 2),
        }
        
        for holiday_name, (month, day) in indian_holidays.items():
            for year in years:
                holidays_list.append({
                    'holiday': holiday_name,
                    'ds': pd.Timestamp(year=year, month=month, day=day),
                    'lower_window': 0,
                    'upper_window': 0,
                })
        
        return pd.DataFrame(holidays_list)

    def get_model_info(self) -> Dict[str, any]:
        """Return information about the current model."""
        return {
            'product_id': self.product_id,
            'outlet_id': self.outlet_id,
            'model_type': 'Prophet',
            'is_trained': self.model is not None,
            'training_samples': len(self.training_data) if self.training_data is not None else 0,
            'country_code': self.country_code,
            'external_regressors_count': len(self.external_regressors),
            'has_cache_support': redis_client is not None,
        }
