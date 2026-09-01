"""
R-DIOS Forecast Validation Framework
Production-Grade Time-Series Validation with Enterprise Quality Standards

This framework addresses critical gaps identified in the comprehensive review:
1. Proper time-series cross-validation (no data leakage)
2. Multiple model comparison with statistical significance testing
3. Comprehensive metrics (MAPE, RMSE, MAE, R², confidence intervals)
4. Error distribution analysis and failure case documentation
5. Modular, scalable, and maintainable architecture

Author: R-DIOS Team
Date: January 2026
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging
from abc import ABC, abstractmethod
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES FOR TYPE SAFETY AND MAINTAINABILITY
# ============================================================================

@dataclass
class ValidationConfig:
    """Configuration for validation framework"""
    # Data parameters
    train_ratio: float = 0.70
    validation_ratio: float = 0.15
    test_ratio: float = 0.15
    
    # Cross-validation parameters
    n_splits: int = 5
    forecast_horizon: int = 7  # 7-day forecast
    
    # Model parameters
    prophet_params: Dict[str, Any] = None
    arima_params: Dict[str, Any] = None
    
    # Output parameters
    output_dir: Path = Path('validation_results')
    save_plots: bool = True
    save_predictions: bool = True
    
    # Performance parameters
    confidence_level: float = 0.95
    significance_level: float = 0.05
    
    def __post_init__(self):
        """Validate configuration"""
        if self.prophet_params is None:
            self.prophet_params = {
                'changepoint_prior_scale': 0.05,
                'seasonality_prior_scale': 10.0,
                'seasonality_mode': 'multiplicative',
                'yearly_seasonality': True,
                'weekly_seasonality': True,
                'daily_seasonality': False
            }
        
        if self.arima_params is None:
            self.arima_params = {
                'seasonal': True,
                'm': 7,  # Weekly seasonality
                'max_p': 5,
                'max_q': 5,
                'max_P': 2,
                'max_Q': 2,
                'max_d': 2,
                'max_D': 1
            }
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate ratios
        total_ratio = self.train_ratio + self.validation_ratio + self.test_ratio
        if not np.isclose(total_ratio, 1.0):
            raise ValueError(f"Train/Val/Test ratios must sum to 1.0, got {total_ratio}")


@dataclass
class ModelMetrics:
    """Metrics for a single model"""
    model_name: str
    mape: float
    rmse: float
    mae: float
    r2: float
    mape_ci_lower: float
    mape_ci_upper: float
    training_time: float
    prediction_time: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def __str__(self) -> str:
        """String representation"""
        return (
            f"{self.model_name}:\n"
            f"  MAPE: {self.mape:.2f}% (95% CI: [{self.mape_ci_lower:.2f}%, {self.mape_ci_upper:.2f}%])\n"
            f"  RMSE: {self.rmse:.2f}\n"
            f"  MAE: {self.mae:.2f}\n"
            f"  R²: {self.r2:.4f}\n"
            f"  Training Time: {self.training_time:.2f}s\n"
            f"  Prediction Time: {self.prediction_time:.2f}s"
        )


@dataclass
class ValidationResults:
    """Complete validation results"""
    metrics: Dict[str, ModelMetrics]
    predictions: Dict[str, pd.DataFrame]
    baseline_comparison: Dict[str, float]
    statistical_tests: Dict[str, Any]
    error_analysis: Dict[str, Any]
    config: ValidationConfig
    timestamp: str
    
    def save(self, output_path: Path):
        """Save results to JSON"""
        output_data = {
            'timestamp': self.timestamp,
            'config': {
                'train_ratio': self.config.train_ratio,
                'validation_ratio': self.config.validation_ratio,
                'test_ratio': self.config.test_ratio,
                'n_splits': self.config.n_splits,
                'forecast_horizon': self.config.forecast_horizon
            },
            'metrics': {name: metrics.to_dict() for name, metrics in self.metrics.items()},
            'baseline_comparison': self.baseline_comparison,
            'statistical_tests': self.statistical_tests,
            'error_analysis': self.error_analysis
        }
        
        # Convert numpy types to Python types for JSON serialization
        def convert_types(obj):
            """Recursively convert numpy types to Python types"""
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            elif isinstance(obj, Path):
                return str(obj)
            return obj
        
        output_data = convert_types(output_data)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved validation results to {output_path}")


# ============================================================================
# ABSTRACT BASE CLASS FOR FORECASTING MODELS
# ============================================================================

class ForecastModel(ABC):
    """Abstract base class for all forecasting models"""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
        self.is_fitted = False
    
    @abstractmethod
    def fit(self, train_data: pd.DataFrame) -> 'ForecastModel':
        """Train the model"""
        pass
    
    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        """Generate predictions"""
        pass
    
    @abstractmethod
    def get_params(self) -> Dict:
        """Get model parameters"""
        pass
    
    def validate_data(self, data: pd.DataFrame):
        """Validate input data format"""
        required_columns = ['ds', 'y']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Data must contain columns: {required_columns}")
        
        if data['y'].isnull().any():
            raise ValueError("Target variable 'y' contains null values")
        
        if not pd.api.types.is_datetime64_any_dtype(data['ds']):
            raise ValueError("'ds' column must be datetime type")


# ============================================================================
# CONCRETE MODEL IMPLEMENTATIONS
# ============================================================================

class ProphetModel(ForecastModel):
    """Facebook Prophet implementation"""
    
    def __init__(self, **kwargs):
        super().__init__("Prophet")
        self.params = kwargs
    
    def fit(self, train_data: pd.DataFrame) -> 'ProphetModel':
        """Train Prophet model"""
        from prophet import Prophet
        
        self.validate_data(train_data)
        
        # Initialize and fit model
        self.model = Prophet(**self.params)
        
        # Suppress Prophet's verbose output
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(train_data)
        
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int) -> pd.DataFrame:
        """Generate predictions"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        future = self.model.make_future_dataframe(periods=horizon)
        forecast = self.model.predict(future)
        
        # Return only future predictions (last 'horizon' rows)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(horizon).reset_index(drop=True)
    
    def get_params(self) -> Dict:
        """Get model parameters"""
        return self.params


class ARIMAModel(ForecastModel):
    """Auto-ARIMA implementation using pmdarima"""
    
    def __init__(self, **kwargs):
        super().__init__("ARIMA")
        self.params = kwargs
        self.last_date = None
        self.freq = None
    
    def fit(self, train_data: pd.DataFrame) -> 'ARIMAModel':
        """Train ARIMA model"""
        from pmdarima import auto_arima
        
        self.validate_data(train_data)
        
        # Sort by date
        train_data = train_data.sort_values('ds')
        self.last_date = train_data['ds'].max()
        self.freq = pd.infer_freq(train_data['ds'])
        
        # Fit auto-ARIMA
        self.model = auto_arima(
            train_data['y'],
            **self.params,
            suppress_warnings=True,
            error_action='ignore'
        )
        
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int) -> pd.DataFrame:
        """Generate predictions"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        # Generate predictions
        forecast, conf_int = self.model.predict(
            n_periods=horizon,
            return_conf_int=True,
            alpha=0.05
        )
        
        # Create date range
        future_dates = pd.date_range(
            start=self.last_date + pd.Timedelta(days=1),
            periods=horizon,
            freq='D'
        )
        
        return pd.DataFrame({
            'ds': future_dates,
            'yhat': forecast,
            'yhat_lower': conf_int[:, 0],
            'yhat_upper': conf_int[:, 1]
        })
    
    def get_params(self) -> Dict:
        """Get model parameters"""
        if self.is_fitted:
            return {
                'order': self.model.order,
                'seasonal_order': self.model.seasonal_order,
                'aic': self.model.aic(),
                'bic': self.model.bic()
            }
        return self.params


class NaiveModel(ForecastModel):
    """Naive baseline: last value repeated"""
    
    def __init__(self):
        super().__init__("Naive Baseline")
        self.last_value = None
        self.last_date = None
    
    def fit(self, train_data: pd.DataFrame) -> 'NaiveModel':
        """Fit naive model (just store last value)"""
        self.validate_data(train_data)
        
        train_data = train_data.sort_values('ds')
        self.last_value = train_data['y'].iloc[-1]
        self.last_date = train_data['ds'].max()
        self.is_fitted = True
        
        return self
    
    def predict(self, horizon: int) -> pd.DataFrame:
        """Predict last value for all future periods"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        future_dates = pd.date_range(
            start=self.last_date + pd.Timedelta(days=1),
            periods=horizon,
            freq='D'
        )
        
        return pd.DataFrame({
            'ds': future_dates,
            'yhat': [self.last_value] * horizon,
            'yhat_lower': [self.last_value] * horizon,
            'yhat_upper': [self.last_value] * horizon
        })
    
    def get_params(self) -> Dict:
        """Get model parameters"""
        return {'last_value': self.last_value}


class SeasonalNaiveModel(ForecastModel):
    """Seasonal Naive baseline: last season's values"""
    
    def __init__(self, season_length: int = 7):
        super().__init__("Seasonal Naive")
        self.season_length = season_length
        self.historical_data = None
        self.last_date = None
    
    def fit(self, train_data: pd.DataFrame) -> 'SeasonalNaiveModel':
        """Fit seasonal naive model"""
        self.validate_data(train_data)
        
        train_data = train_data.sort_values('ds')
        self.historical_data = train_data.copy()
        self.last_date = train_data['ds'].max()
        self.is_fitted = True
        
        return self
    
    def predict(self, horizon: int) -> pd.DataFrame:
        """Predict using last season's values"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        # Get last season's values
        last_season = self.historical_data['y'].iloc[-self.season_length:].values
        
        # Repeat pattern for forecast horizon
        predictions = np.tile(last_season, (horizon // self.season_length) + 1)[:horizon]
        
        future_dates = pd.date_range(
            start=self.last_date + pd.Timedelta(days=1),
            periods=horizon,
            freq='D'
        )
        
        return pd.DataFrame({
            'ds': future_dates,
            'yhat': predictions,
            'yhat_lower': predictions,
            'yhat_upper': predictions
        })
    
    def get_params(self) -> Dict:
        """Get model parameters"""
        return {'season_length': self.season_length}


# ============================================================================
# METRICS CALCULATION
# ============================================================================

class MetricsCalculator:
    """Calculate forecasting metrics with statistical rigor"""
    
    @staticmethod
    def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Mean Absolute Percentage Error"""
        # Avoid division by zero
        mask = y_true != 0
        return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    @staticmethod
    def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Root Mean Squared Error"""
        return np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    @staticmethod
    def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Mean Absolute Error"""
        return np.mean(np.abs(y_true - y_pred))
    
    @staticmethod
    def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """R-squared (Coefficient of Determination)"""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    @staticmethod
    def confidence_interval(
        errors: np.ndarray,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for MAPE"""
        from scipy import stats
        
        mean = np.mean(errors)
        sem = stats.sem(errors)
        ci = stats.t.interval(confidence, len(errors) - 1, loc=mean, scale=sem)
        
        return ci[0], ci[1]
    
    @staticmethod
    def calculate_all_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str,
        training_time: float = 0.0,
        prediction_time: float = 0.0
    ) -> ModelMetrics:
        """Calculate all metrics for a model"""
        # Calculate base metrics
        mape_val = MetricsCalculator.mape(y_true, y_pred)
        rmse_val = MetricsCalculator.rmse(y_true, y_pred)
        mae_val = MetricsCalculator.mae(y_true, y_pred)
        r2_val = MetricsCalculator.r2(y_true, y_pred)
        
        # Calculate percentage errors for CI
        mask = y_true != 0
        percentage_errors = np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]) * 100
        
        # Confidence interval
        ci_lower, ci_upper = MetricsCalculator.confidence_interval(percentage_errors)
        
        return ModelMetrics(
            model_name=model_name,
            mape=mape_val,
            rmse=rmse_val,
            mae=mae_val,
            r2=r2_val,
            mape_ci_lower=ci_lower,
            mape_ci_upper=ci_upper,
            training_time=training_time,
            prediction_time=prediction_time
        )


# ============================================================================
# CONTINUATION IN NEXT FILE DUE TO LENGTH
# ============================================================================
