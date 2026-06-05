"""
ARIMA/SARIMA-based Sales Forecasting Module

Implements Auto-ARIMA forecasting with seasonal decomposition for retail sales prediction.
Provides ARIMA(p,d,q) and SARIMA(p,d,q)(P,D,Q)s for handling seasonality.
"""

import os
import pickle
from typing import Optional, Dict, Tuple, Any
from datetime import datetime, timedelta
import logging
import warnings

import pandas as pd
import numpy as np

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller, kpss
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    try:
        from pmdarima import auto_arima  # type: ignore
    except ImportError:
        auto_arima = None
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    ARIMA = None
    SARIMAX = None
    seasonal_decompose = None
    auto_arima = None

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class ARIMAForecaster:
    """
    Auto-ARIMA forecasting for retail sales with automatic parameter selection.
    
    Features:
    - Automatic parameter selection via auto_arima
    - Stationarity testing (ADF, KPSS)
    - Seasonal decomposition
    - Confidence interval generation
    - Model diagnostics
    - Forecast quality metrics
    """

    def __init__(self, model_dir: str = "models", seasonal_periods: int = 7):
        """
        Initialize ARIMA forecaster.
        
        Args:
            model_dir: Directory to save/load trained models
            seasonal_periods: Number of periods in a seasonal cycle (default: 7 for weekly)
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError(
                "statsmodels and pmdarima are not installed. "
                "Install with: pip install statsmodels pmdarima"
            )
        
        self.model_dir = model_dir
        self.seasonal_periods = seasonal_periods
        self.model: Any = None
        self.product_id: Optional[str] = None
        self.training_data: Optional[pd.DataFrame] = None
        self.order: Optional[Tuple[int, int, int]] = None
        self.seasonal_order: Optional[Tuple[int, int, int, int]] = None
        
        os.makedirs(model_dir, exist_ok=True)

    def prepare_data(self, sales_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare sales data for ARIMA.
        
        Expects input DataFrame with columns: 'date' and 'sales' (or 'amount').
        
        Args:
            sales_df: DataFrame with columns ['date', 'sales'] or ['date', 'amount']
            
        Returns:
            Cleaned DataFrame with datetime index and numeric sales values
        """
        df = sales_df.copy()
        
        # Rename columns
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        elif 'ds' in df.columns:
            df['ds'] = pd.to_datetime(df['ds'])
            df.set_index('ds', inplace=True)
        
        # Get numeric column
        if 'sales' in df.columns:
            values = df['sales'].values
        elif 'amount' in df.columns:
            values = df['amount'].values
        elif 'y' in df.columns:
            values = df['y'].values
        else:
            # Assume first numeric column is sales
            values = df.iloc[:, 0].values
        
        # Clean data
        values = pd.to_numeric(values, errors='coerce')
        values = values.fillna(values.mean())
        values = np.maximum(values, 0)  # Ensure non-negative for retail
        
        return pd.Series(values, index=df.index)

    def test_stationarity(self, timeseries: pd.Series) -> Dict[str, Any]:
        """
        Test if time series is stationary using ADF and KPSS tests.
        
        Args:
            timeseries: Time series data
            
        Returns:
            Dictionary with test results and recommendation for differencing
        """
        # Augmented Dickey-Fuller test
        adf_result = adfuller(timeseries, autolag='AIC')
        
        # KPSS test
        kpss_result = kpss(timeseries, regression='c', nlags='auto')
        
        is_stationary = (adf_result[1] < 0.05) and (kpss_result[1] > 0.05)
        
        return {
            'stationary': is_stationary,
            'adf_p_value': adf_result[1],
            'kpss_p_value': kpss_result[1],
            'adf_critical_values': adf_result[4],
            'differencing_needed': not is_stationary
        }

    def decompose_seasonality(self, timeseries: pd.Series) -> Dict[str, pd.Series]:
        """
        Decompose time series into trend, seasonal, and residual components.
        
        Args:
            timeseries: Time series data with datetime index
            
        Returns:
            Dictionary with trend, seasonal, and residual components
        """
        try:
            decomposition = seasonal_decompose(
                timeseries,
                model='additive',
                period=self.seasonal_periods,
                extrapolate='fill_ea'
            )
            
            return {
                'observed': timeseries,
                'trend': decomposition.trend,
                'seasonal': decomposition.seasonal,
                'residual': decomposition.resid
            }
        except Exception as e:
            logger.warning(f"Seasonal decomposition failed: {str(e)}")
            return {
                'observed': timeseries,
                'trend': None,
                'seasonal': None,
                'residual': None
            }

    def auto_select_order(
        self,
        timeseries: pd.Series,
        max_p: int = 5,
        max_d: int = 2,
        max_q: int = 5
    ) -> Tuple[Tuple[int, int, int], Tuple[int, int, int, int]]:
        """
        Automatically select ARIMA order using auto_arima.
        
        Args:
            timeseries: Time series data
            max_p: Maximum AR order to test
            max_d: Maximum differencing order to test
            max_q: Maximum MA order to test
            
        Returns:
            Tuple of (ARIMA order, SARIMA order)
        """
        try:
            # Auto ARIMA for non-seasonal component
            auto_model = auto_arima(
                timeseries,
                start_p=0, max_p=max_p,
                start_d=0, max_d=max_d,
                start_q=0, max_q=max_q,
                seasonal=True,
                m=self.seasonal_periods,
                stepwise=True,
                trace=False,
                error_action='ignore',
                suppress_warnings=True,
                maxiter=200
            )
            
            order = auto_model.order
            seasonal_order = auto_model.seasonal_order
            
            logger.info(f"Selected order: ARIMA{order} x SARIMA{seasonal_order}")
            
            return order, seasonal_order
            
        except Exception as e:
            logger.warning(f"Auto selection failed, using defaults: {str(e)}")
            return (1, 1, 1), (1, 1, 1, self.seasonal_periods)

    def train(
        self,
        timeseries: pd.Series,
        product_id: str = "default",
        use_sarima: bool = True
    ) -> Dict[str, Any]:
        """
        Train ARIMA or SARIMA model.
        
        Args:
            timeseries: Time series data (sales)
            product_id: Product identifier for model tracking
            use_sarima: Use SARIMA if True, ARIMA if False
            
        Returns:
            Training results with metrics
        """
        self.product_id = product_id
        self.training_data = timeseries.copy()
        
        start_time = datetime.utcnow()
        
        try:
            # Test stationarity
            stationarity_test = self.test_stationarity(timeseries)
            logger.info(f"Stationarity test: {stationarity_test}")
            
            # Decompose seasonality
            decomposition = self.decompose_seasonality(timeseries)
            
            # Auto-select order
            arima_order, sarima_order = self.auto_select_order(timeseries)
            self.order = arima_order
            self.seasonal_order = sarima_order if use_sarima else None
            
            # Train model
            if use_sarima and len(timeseries) >= 2 * self.seasonal_periods:
                self.model = SARIMAX(
                    timeseries,
                    order=arima_order,
                    seasonal_order=sarima_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                ).fit(disp=False)
                model_type = "SARIMA"
            else:
                self.model = ARIMA(
                    timeseries,
                    order=arima_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                ).fit()
                model_type = "ARIMA"
            
            # Save model
            model_path = os.path.join(self.model_dir, f"{model_type.lower()}_{product_id}.pkl")
            with open(model_path, "wb") as f:
                pickle.dump({
                    "model": self.model,
                    "order": self.order,
                    "seasonal_order": self.seasonal_order,
                    "seasonal_periods": self.seasonal_periods,
                    "product_id": product_id
                }, f)
            
            training_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "success",
                "model_type": model_type,
                "product_id": product_id,
                "order": self.order,
                "seasonal_order": self.seasonal_order,
                "aic": float(self.model.aic),
                "bic": float(self.model.bic),
                "model_path": model_path,
                "training_time_seconds": training_time,
                "trained_at": start_time.isoformat(),
                "stationarity": stationarity_test
            }
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "product_id": product_id
            }

    def forecast(
        self,
        steps: int = 30,
        confidence: float = 0.95
    ) -> Dict[str, Any]:
        """
        Generate forecast with confidence intervals.
        
        Args:
            steps: Number of steps to forecast
            confidence: Confidence level (0.90, 0.95, 0.99)
            
        Returns:
            Forecast with values and confidence intervals
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            forecast_result = self.model.get_forecast(steps=steps)
            forecast_data = forecast_result.summary_frame(alpha=1-confidence)
            
            # Extract components
            mean_forecast = forecast_data['mean'].values
            lower_ci = forecast_data['mean_ci_lower'].values
            upper_ci = forecast_data['mean_ci_upper'].values
            
            # Generate future dates
            last_date = self.training_data.index[-1]
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=steps,
                freq='D'
            )
            
            return {
                "status": "success",
                "forecast": mean_forecast.tolist(),
                "lower_ci": lower_ci.tolist(),
                "upper_ci": upper_ci.tolist(),
                "dates": [d.isoformat() for d in future_dates],
                "confidence_level": confidence,
                "steps": steps
            }
            
        except Exception as e:
            logger.error(f"Forecast failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def load(self, product_id: str, model_type: str = "sarima") -> bool:
        """
        Load a trained model from disk.
        
        Args:
            product_id: Product identifier
            model_type: Type of model to load (arima or sarima)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            model_path = os.path.join(self.model_dir, f"{model_type}_{product_id}.pkl")
            
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found: {model_path}")
                return False
            
            with open(model_path, "rb") as f:
                data = pickle.load(f)
                self.model = data["model"]
                self.order = data["order"]
                self.seasonal_order = data["seasonal_order"]
                self.seasonal_periods = data["seasonal_periods"]
                self.product_id = data["product_id"]
            
            logger.info(f"Loaded model for product {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False

    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get model diagnostics and quality metrics.
        
        Returns:
            Dictionary with diagnostic metrics
        """
        if self.model is None:
            return {"status": "error", "message": "Model not trained"}
        
        try:
            # Model fit statistics
            diagnostics = {
                "aic": float(self.model.aic),
                "bic": float(self.model.bic),
                "llf": float(self.model.llf),
                "order": self.order,
                "seasonal_order": self.seasonal_order,
            }
            
            # Residual diagnostics
            if hasattr(self.model, 'resid'):
                residuals = self.model.resid
                diagnostics.update({
                    "residual_mean": float(residuals.mean()),
                    "residual_std": float(residuals.std()),
                    "residual_min": float(residuals.min()),
                    "residual_max": float(residuals.max()),
                })
            
            return diagnostics
            
        except Exception as e:
            logger.error(f"Diagnostics generation failed: {str(e)}")
            return {"status": "error", "error": str(e)}


class SARIMAForecaster(ARIMAForecaster):
    """
    Specialized SARIMA forecaster for seasonal retail data.
    Wrapper around ARIMA forecaster with seasonal defaults.
    """
    
    def __init__(self, model_dir: str = "models", seasonal_periods: int = 7):
        """Initialize SARIMA forecaster with seasonal defaults."""
        super().__init__(model_dir, seasonal_periods)
    
    def train(self, timeseries: pd.Series, product_id: str = "default") -> Dict[str, Any]:
        """Train SARIMA model (always uses seasonal component)."""
        return super().train(timeseries, product_id, use_sarima=True)
