"""
Unit Tests for Forecasting Models

Tests:
- Prophet forecaster training and prediction
- XGBoost forecaster training and prediction
- ARIMA/SARIMA forecaster training and prediction
- Ensemble forecaster combination
- Feature engineering for ML models

Run: pytest tests/unit/test_forecasting.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.ml.forecasting import (  # type: ignore
    ProphetForecaster,
    XGBoostForecaster,
    ARIMAForecaster,
    SARIMAForecaster,
)


class TestDataGeneration:
    """Generate test data for forecasting"""
    
    @pytest.fixture
    def sample_sales_data(self):
        """Generate sample sales time series data"""
        dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
        
        # Create synthetic sales with trend, seasonality, and noise
        trend = np.linspace(500, 1000, 365)
        seasonality = 200 * np.sin(np.arange(365) * 2 * np.pi / 365)
        noise = np.random.normal(0, 50, 365)
        sales = trend + seasonality + noise
        sales = np.maximum(sales, 0)  # Ensure non-negative
        
        return pd.DataFrame({
            'date': dates,
            'sales': sales,
            'amount': sales * 100  # Price per unit
        })
    
    @pytest.fixture
    def short_series_data(self):
        """Generate short time series (30 days)"""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        sales = np.random.normal(500, 100, 30)
        sales = np.maximum(sales, 0)
        
        return pd.DataFrame({
            'date': dates,
            'sales': sales
        })
    
    @pytest.fixture
    def seasonal_data(self):
        """Generate data with strong seasonality (2 years)"""
        dates = pd.date_range(start='2022-01-01', periods=730, freq='D')
        
        # Strong weekly seasonality (weekends have higher sales)
        day_of_week = dates.dayofweek
        weekly_pattern = 300 + 200 * (day_of_week >= 4)  # Higher on weekends
        
        # Yearly seasonality
        day_of_year = dates.dayofyear
        yearly_pattern = 100 * np.sin(day_of_year * 2 * np.pi / 365)
        
        noise = np.random.normal(0, 50, 730)
        sales = weekly_pattern + yearly_pattern + noise
        sales = np.maximum(sales, 0)
        
        return pd.DataFrame({
            'date': dates,
            'sales': sales
        })


class TestProphetForecaster:
    """Test Prophet-based forecasting"""
    
    def test_prophet_initialization(self):
        """Prophet forecaster should initialize correctly"""
        forecaster = ProphetForecaster(country_code="IN")
        
        assert forecaster is not None
        assert forecaster.country_code == "IN"
        assert forecaster.model is None
    
    def test_prophet_data_preparation(self, sample_sales_data):
        """Data preparation should convert to Prophet format"""
        forecaster = ProphetForecaster()
        prepared_data = forecaster.prepare_data(sample_sales_data)
        
        assert 'ds' in prepared_data.columns
        assert 'y' in prepared_data.columns
        assert len(prepared_data) == len(sample_sales_data)
    
    def test_prophet_training(self, sample_sales_data):
        """Prophet should train successfully"""
        forecaster = ProphetForecaster()
        
        result = forecaster.train(
            sample_sales_data[['date', 'sales']].rename(columns={'date': 'ds', 'sales': 'y'}),
            product_id="TEST_001"
        )
        
        assert result['status'] == 'success'
        assert result['product_id'] == "TEST_001"
        assert forecaster.model is not None
    
    def test_prophet_forecast(self, sample_sales_data):
        """Prophet should generate forecast"""
        forecaster = ProphetForecaster()
        
        # Train first
        forecaster.train(
            sample_sales_data[['date', 'sales']].rename(columns={'date': 'ds', 'sales': 'y'}),
            product_id="TEST_001"
        )
        
        # Generate forecast
        forecast = forecaster.forecast(product_id="TEST_001", days=30)
        
        assert 'fcst' in forecast.columns
        assert len(forecast) == 30
        assert 'yhat_lower' in forecast.columns
        assert 'yhat_upper' in forecast.columns
    
    def test_prophet_forecast_values_positive(self, sample_sales_data):
        """Forecast values should be non-negative"""
        forecaster = ProphetForecaster()
        
        forecaster.train(
            sample_sales_data[['date', 'sales']].rename(columns={'date': 'ds', 'sales': 'y'}),
            product_id="TEST_002"
        )
        
        forecast = forecaster.forecast(product_id="TEST_002", days=30)
        
        # Most forecast values should be positive for sales data
        assert (forecast['fcst'] > 0).sum() > 20  # At least 20 out of 30


class TestXGBoostForecaster:
    """Test XGBoost-based forecasting"""
    
    def test_xgboost_initialization(self):
        """XGBoost forecaster should initialize correctly"""
        forecaster = XGBoostForecaster()
        
        assert forecaster is not None
        assert forecaster.model is None
    
    def test_xgboost_feature_creation(self, sample_sales_data):
        """Feature creation should generate appropriate lag and rolling features"""
        prepared = sample_sales_data[['date', 'sales']].copy()
        prepared.rename(columns={'date': 'ds', 'sales': 'y'}, inplace=True)
        
        features = XGBoostForecaster.create_features(prepared)
        
        # Check for lag features
        assert 'lag_1' in features.columns
        assert 'lag_7' in features.columns
        assert 'lag_30' in features.columns
        
        # Check for rolling features
        assert 'roll_mean_7' in features.columns
        assert 'roll_std_7' in features.columns
        
        # Check for cyclical features
        assert 'dow_sin' in features.columns
        assert 'month_sin' in features.columns
    
    def test_xgboost_training(self, sample_sales_data):
        """XGBoost should train successfully"""
        forecaster = XGBoostForecaster()
        
        prepared = sample_sales_data[['date', 'sales']].copy()
        prepared.rename(columns={'date': 'ds', 'sales': 'y'}, inplace=True)
        
        features = XGBoostForecaster.create_features(prepared)
        X = features.drop('y', axis=1)
        y = features['y']
        
        result = forecaster.train(X, y, product_id="TEST_XGB_001")
        
        assert result['status'] == 'success'
        assert forecaster.model is not None
    
    def test_xgboost_prediction(self, sample_sales_data):
        """XGBoost should generate predictions"""
        forecaster = XGBoostForecaster()
        
        prepared = sample_sales_data[['date', 'sales']].copy()
        prepared.rename(columns={'date': 'ds', 'sales': 'y'}, inplace=True)
        
        features = XGBoostForecaster.create_features(prepared)
        X = features.drop('y', axis=1)
        y = features['y']
        
        forecaster.train(X, y, product_id="TEST_XGB_002")
        
        # Test prediction on same data
        predictions = forecaster.model.predict(X[-30:])
        
        assert len(predictions) == 30
        assert all(p > 0 for p in predictions)


class TestARIMAForecaster:
    """Test ARIMA/SARIMA forecasting"""
    
    def test_arima_initialization(self):
        """ARIMA forecaster should initialize correctly"""
        forecaster = ARIMAForecaster(seasonal_periods=7)
        
        assert forecaster is not None
        assert forecaster.seasonal_periods == 7
        assert forecaster.model is None
    
    def test_arima_data_preparation(self, sample_sales_data):
        """Data preparation should handle various column names"""
        forecaster = ARIMAForecaster()
        
        prepared = forecaster.prepare_data(sample_sales_data[['date', 'sales']])
        
        assert isinstance(prepared, pd.Series)
        assert len(prepared) == len(sample_sales_data)
        assert all(prepared >= 0)  # Non-negative sales
    
    def test_arima_stationarity_test(self, sample_sales_data):
        """Stationarity test should detect non-stationary data"""
        forecaster = ARIMAForecaster()
        prepared = forecaster.prepare_data(sample_sales_data[['date', 'sales']])
        
        test_result = forecaster.test_stationarity(prepared)
        
        assert 'stationary' in test_result
        assert 'adf_p_value' in test_result
        assert 'kpss_p_value' in test_result
    
    def test_arima_seasonality_decomposition(self, seasonal_data):
        """Should decompose series into trend and seasonality"""
        forecaster = ARIMAForecaster(seasonal_periods=7)
        prepared = forecaster.prepare_data(seasonal_data[['date', 'sales']])
        
        decomposition = forecaster.decompose_seasonality(prepared)
        
        assert 'observed' in decomposition
        assert 'trend' in decomposition
        assert 'seasonal' in decomposition
        assert 'residual' in decomposition
    
    def test_arima_auto_order_selection(self, sample_sales_data):
        """Auto order selection should find appropriate parameters"""
        forecaster = ARIMAForecaster()
        prepared = forecaster.prepare_data(sample_sales_data[['date', 'sales']])
        
        arima_order, sarima_order = forecaster.auto_select_order(prepared)
        
        assert isinstance(arima_order, tuple)
        assert len(arima_order) == 3  # (p, d, q)
        assert isinstance(sarima_order, tuple)
        assert len(sarima_order) == 4  # (P, D, Q, m)
    
    def test_arima_training(self, sample_sales_data):
        """ARIMA should train successfully"""
        forecaster = ARIMAForecaster()
        prepared = forecaster.prepare_data(sample_sales_data[['date', 'sales']])
        
        result = forecaster.train(prepared, product_id="TEST_ARIMA_001")
        
        assert result['status'] == 'success'
        assert result['product_id'] == "TEST_ARIMA_001"
        assert 'order' in result
        assert 'seasonal_order' in result
        assert forecaster.model is not None
    
    def test_sarima_training(self, seasonal_data):
        """SARIMA should train on seasonal data"""
        forecaster = SARIMAForecaster(seasonal_periods=7)
        prepared = forecaster.prepare_data(seasonal_data[['date', 'sales']])
        
        result = forecaster.train(prepared, product_id="TEST_SARIMA_001")
        
        assert result['status'] == 'success'
        assert result['model_type'] == 'SARIMA'
    
    def test_arima_forecast(self, sample_sales_data):
        """ARIMA should generate forecast with confidence intervals"""
        forecaster = ARIMAForecaster()
        prepared = forecaster.prepare_data(sample_sales_data[['date', 'sales']])
        
        forecaster.train(prepared, product_id="TEST_ARIMA_002")
        
        forecast = forecaster.forecast(steps=30, confidence=0.95)
        
        assert forecast['status'] == 'success'
        assert len(forecast['forecast']) == 30
        assert len(forecast['lower_ci']) == 30
        assert len(forecast['upper_ci']) == 30
        
        # Confidence intervals should bracket forecast
        for i in range(30):
            assert forecast['lower_ci'][i] <= forecast['forecast'][i] <= forecast['upper_ci'][i]
    
    def test_arima_diagnostics(self, sample_sales_data):
        """Should provide model diagnostics"""
        forecaster = ARIMAForecaster()
        prepared = forecaster.prepare_data(sample_sales_data[['date', 'sales']])
        
        forecaster.train(prepared, product_id="TEST_ARIMA_003")
        
        diagnostics = forecaster.get_diagnostics()
        
        assert 'aic' in diagnostics
        assert 'bic' in diagnostics
        assert 'order' in diagnostics


class TestForecastComparison:
    """Compare different forecasting models"""
    
    def test_all_models_produce_similar_magnitude(self, sample_sales_data):
        """Different models should produce forecasts in similar range"""
        # Prepare data
        prep_data = sample_sales_data[['date', 'sales']].copy()
        
        # Prophet
        prophet_forecaster = ProphetForecaster()
        prophet_forecaster.train(
            prep_data.rename(columns={'date': 'ds', 'sales': 'y'}),
            product_id="COMPARE_001"
        )
        prophet_forecast = prophet_forecaster.forecast(
            product_id="COMPARE_001", days=30
        )
        prophet_mean = prophet_forecast['fcst'].mean()
        
        # ARIMA
        arima_forecaster = ARIMAForecaster()
        arima_prep = arima_forecaster.prepare_data(prep_data)
        arima_forecaster.train(arima_prep, product_id="COMPARE_002")
        arima_forecast = arima_forecaster.forecast(steps=30)
        arima_mean = np.mean(arima_forecast['forecast'])
        
        # Means should be within 50% of each other
        ratio = max(prophet_mean, arima_mean) / min(prophet_mean, arima_mean)
        assert ratio < 1.5, "Model forecasts differ by more than 50%"


class TestForecastingEdgeCases:
    """Test edge cases and error handling"""
    
    def test_arima_with_minimum_data(self):
        """Should handle very short time series"""
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        short_data = pd.DataFrame({
            'date': dates,
            'sales': np.random.normal(500, 100, 20)
        })
        
        forecaster = ARIMAForecaster()
        prepared = forecaster.prepare_data(short_data)
        
        result = forecaster.train(prepared, product_id="SHORT_DATA")
        assert result['status'] == 'success'
    
    def test_forecast_with_constant_values(self):
        """Should handle constant/no-variation data"""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        constant_data = pd.DataFrame({
            'date': dates,
            'sales': [500.0] * 30  # Constant sales
        })
        
        forecaster = ARIMAForecaster()
        prepared = forecaster.prepare_data(constant_data)
        
        result = forecaster.train(prepared, product_id="CONSTANT")
        assert result['status'] == 'success'
    
    def test_forecast_handles_zero_values(self):
        """Should handle zero sales days"""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'sales': np.concatenate([np.zeros(5), np.random.normal(500, 100, 25)])
        })
        
        forecaster = ARIMAForecaster()
        prepared = forecaster.prepare_data(data)
        
        result = forecaster.train(prepared, product_id="WITH_ZEROS")
        assert result['status'] == 'success'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
