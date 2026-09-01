"""
COMPREHENSIVE FORECAST ACCURACY VALIDATION SCRIPT
Academic-Quality Time-Series Cross-Validation for R-DIOS Thesis

This script implements rigorous forecast validation methodology:
✅ Proper time-series cross-validation (no data leakage)
✅ Multiple baseline comparisons (Naive, Seasonal Naive, Moving Average)
✅ Model comparison (Prophet vs ARIMA vs LSTM vs baselines)
✅ Statistical metrics with confidence intervals (MAPE, RMSE, MAE, R²)
✅ Publication-quality visualizations
✅ Comprehensive validation report

Author: R-DIOS Thesis Project
Date: January 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
import warnings
import json
import sys
from typing import Dict, List, Tuple, Any
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


class BaselineForecaster:
    """Baseline forecasting models for comparison"""
    
    @staticmethod
    def naive_forecast(train_data: pd.Series, horizon: int) -> np.ndarray:
        """
        Naive forecast: Last observed value repeated
        Simplest baseline - should always be beaten by any decent model
        """
        last_value = train_data.iloc[-1]
        return np.full(horizon, last_value)
    
    @staticmethod
    def seasonal_naive_forecast(train_data: pd.Series, horizon: int, season_length: int = 7) -> np.ndarray:
        """
        Seasonal Naive: Repeat values from same season last year/week
        Strong baseline for data with clear seasonality
        """
        forecasts = []
        for i in range(horizon):
            # Get value from same position in previous season
            idx = len(train_data) - season_length + (i % season_length)
            if idx >= 0:
                forecasts.append(train_data.iloc[idx])
            else:
                forecasts.append(train_data.iloc[-1])
        return np.array(forecasts)
    
    @staticmethod
    def moving_average_forecast(train_data: pd.Series, horizon: int, window: int = 7) -> np.ndarray:
        """
        Moving Average: Average of last N observations
        Simple but effective baseline
        """
        ma_value = train_data.iloc[-window:].mean()
        return np.full(horizon, ma_value)
    
    @staticmethod
    def exponential_smoothing_forecast(train_data: pd.Series, horizon: int, alpha: float = 0.3) -> np.ndarray:
        """
        Exponential Smoothing: Weighted average with exponential decay
        """
        # Simple exponential smoothing
        smoothed = [train_data.iloc[0]]
        for val in train_data.iloc[1:]:
            smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
        
        last_smoothed = smoothed[-1]
        return np.full(horizon, last_smoothed)


class ForecastValidator:
    """
    Comprehensive forecast validation with time-series cross-validation
    
    Implements walk-forward validation to prevent data leakage:
    - Train on historical data
    - Predict next N days
    - Move forward and repeat
    - Aggregate metrics across all folds
    """
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self.data = None
        self.results = {}
        self.metrics_summary = {}
        
    def load_data(self, data_path: str = None) -> pd.DataFrame:
        """Load validation dataset"""
        if data_path:
            self.data_path = data_path
        
        if not self.data_path:
            raise ValueError("Data path not provided")
        
        logger.info(f"Loading data from {self.data_path}")
        df = pd.read_csv(self.data_path)
        df['date'] = pd.to_datetime(df['date'])
        
        # Aggregate by date (sum across all stores for overall forecast)
        daily = df.groupby('date').agg({
            'revenue': 'sum',
            'num_transactions': 'sum',
            'is_holiday': 'max',
            'is_monsoon': 'max',
            'is_weekend': 'max'
        }).reset_index()
        
        daily = daily.sort_values('date').reset_index(drop=True)
        
        self.data = daily
        logger.info(f"Loaded {len(daily)} days of data")
        logger.info(f"Date range: {daily['date'].min()} to {daily['date'].max()}")
        
        return daily
    
    def time_series_split(
        self,
        initial_train_days: int = 365,
        forecast_horizon: int = 30,
        step_size: int = 30,
        max_folds: int = 5
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Create time-series cross-validation splits
        
        Args:
            initial_train_days: Initial training period
            forecast_horizon: Days to forecast ahead
            step_size: Days to move forward between folds
            max_folds: Maximum number of folds
            
        Returns:
            List of (train, test) DataFrame tuples
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        splits = []
        total_days = len(self.data)
        
        for fold in range(max_folds):
            train_end_idx = initial_train_days + (fold * step_size)
            test_end_idx = train_end_idx + forecast_horizon
            
            if test_end_idx > total_days:
                break
            
            train = self.data.iloc[:train_end_idx].copy()
            test = self.data.iloc[train_end_idx:test_end_idx].copy()
            
            splits.append((train, test))
            logger.info(f"Fold {fold+1}: Train={len(train)} days, Test={len(test)} days")
        
        logger.info(f"Created {len(splits)} time-series CV folds")
        return splits
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive forecast accuracy metrics
        
        Returns:
            Dictionary with MAPE, RMSE, MAE, R², and additional metrics
        """
        # Ensure arrays are numpy arrays
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        
        # Remove any NaN or infinite values
        mask = np.isfinite(y_true) & np.isfinite(y_pred) & (y_true > 0)
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        
        if len(y_true) == 0:
            return {
                'mape': np.nan,
                'rmse': np.nan,
                'mae': np.nan,
                'r2': np.nan,
                'mse': np.nan,
                'smape': np.nan,
                'mase': np.nan
            }
        
        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        
        # Mean Absolute Error
        mae = np.mean(np.abs(y_true - y_pred))
        
        # R-squared
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Mean Squared Error
        mse = np.mean((y_true - y_pred) ** 2)
        
        # Symmetric MAPE (better for values close to zero)
        smape = np.mean(2 * np.abs(y_pred - y_true) / (np.abs(y_true) + np.abs(y_pred))) * 100
        
        # Mean Absolute Scaled Error (MASE)
        # Scaled by naive forecast error
        naive_error = np.mean(np.abs(np.diff(y_true)))
        mase = mae / naive_error if naive_error > 0 else np.nan
        
        return {
            'mape': mape,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mse': mse,
            'smape': smape,
            'mase': mase
        }
    
    def validate_baseline_models(
        self,
        splits: List[Tuple[pd.DataFrame, pd.DataFrame]]
    ) -> Dict[str, Dict[str, List[float]]]:
        """
        Validate all baseline models across CV folds
        
        Returns:
            Dictionary of model_name -> metrics -> list of fold values
        """
        logger.info("Validating baseline models...")
        
        baseline_results = {
            'naive': {'mape': [], 'rmse': [], 'mae': [], 'r2': []},
            'seasonal_naive': {'mape': [], 'rmse': [], 'mae': [], 'r2': []},
            'moving_average': {'mape': [], 'rmse': [], 'mae': [], 'r2': []},
            'exponential_smoothing': {'mape': [], 'rmse': [], 'mae': [], 'r2': []}
        }
        
        for fold_idx, (train, test) in enumerate(splits):
            y_train = train['revenue'].values
            y_test = test['revenue'].values
            horizon = len(test)
            
            # Naive forecast
            pred_naive = BaselineForecaster.naive_forecast(train['revenue'], horizon)
            metrics_naive = self.calculate_metrics(y_test, pred_naive)
            for metric in ['mape', 'rmse', 'mae', 'r2']:
                baseline_results['naive'][metric].append(metrics_naive[metric])
            
            # Seasonal Naive (weekly seasonality)
            pred_seasonal = BaselineForecaster.seasonal_naive_forecast(train['revenue'], horizon, season_length=7)
            metrics_seasonal = self.calculate_metrics(y_test, pred_seasonal)
            for metric in ['mape', 'rmse', 'mae', 'r2']:
                baseline_results['seasonal_naive'][metric].append(metrics_seasonal[metric])
            
            # Moving Average
            pred_ma = BaselineForecaster.moving_average_forecast(train['revenue'], horizon, window=7)
            metrics_ma = self.calculate_metrics(y_test, pred_ma)
            for metric in ['mape', 'rmse', 'mae', 'r2']:
                baseline_results['moving_average'][metric].append(metrics_ma[metric])
            
            # Exponential Smoothing
            pred_es = BaselineForecaster.exponential_smoothing_forecast(train['revenue'], horizon, alpha=0.3)
            metrics_es = self.calculate_metrics(y_test, pred_es)
            for metric in ['mape', 'rmse', 'mae', 'r2']:
                baseline_results['exponential_smoothing'][metric].append(metrics_es[metric])
            
            logger.info(f"Fold {fold_idx+1} baseline validation complete")
        
        return baseline_results
    
    def validate_prophet(
        self,
        splits: List[Tuple[pd.DataFrame, pd.DataFrame]],
        use_regressors: bool = True
    ) -> Dict[str, List[float]]:
        """
        Validate Prophet model across CV folds
        
        Returns:
            Dictionary of metric -> list of fold values
        """
        logger.info("Validating Prophet model...")
        
        try:
            from src.ml.forecasting.prophet_forecaster import ProphetForecaster
        except ImportError:
            logger.error("Prophet forecaster not available")
            return {'mape': [np.nan], 'rmse': [np.nan], 'mae': [np.nan], 'r2': [np.nan]}
        
        prophet_results = {'mape': [], 'rmse': [], 'mae': [], 'r2': [], 'predictions': []}
        
        for fold_idx, (train, test) in enumerate(splits):
            try:
                # Initialize Prophet
                forecaster = ProphetForecaster(
                    yearly_seasonality=True,
                    weekly_seasonality=True,
                    include_holidays=True
                )
                
                # Prepare data
                regressors = ['is_holiday', 'is_monsoon'] if use_regressors else None
                prophet_df = forecaster.prepare_data(
                    train,
                    date_column='date',
                    target_column='revenue',
                    regressors=regressors
                )
                
                # Fit model
                forecaster.fit(prophet_df, regressors=regressors)
                
                # Generate forecast
                forecast = forecaster.predict(periods=len(test), include_history=False)
                
                # Extract predictions
                y_pred = forecast['yhat'].values[:len(test)]
                y_test = test['revenue'].values
                
                # Calculate metrics
                metrics = self.calculate_metrics(y_test, y_pred)
                for metric in ['mape', 'rmse', 'mae', 'r2']:
                    prophet_results[metric].append(metrics[metric])
                
                prophet_results['predictions'].append({
                    'fold': fold_idx,
                    'y_true': y_test,
                    'y_pred': y_pred,
                    'dates': test['date'].values
                })
                
                logger.info(f"Fold {fold_idx+1} Prophet validation complete - MAPE: {metrics['mape']:.2f}%")
                
            except Exception as e:
                logger.error(f"Prophet validation failed for fold {fold_idx+1}: {e}")
                for metric in ['mape', 'rmse', 'mae', 'r2']:
                    prophet_results[metric].append(np.nan)
        
        return prophet_results
    
    def validate_arima(
        self,
        splits: List[Tuple[pd.DataFrame, pd.DataFrame]]
    ) -> Dict[str, List[float]]:
        """
        Validate ARIMA model across CV folds
        
        Returns:
            Dictionary of metric -> list of fold values
        """
        logger.info("Validating ARIMA model...")
        
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            from pmdarima import auto_arima
        except ImportError:
            logger.warning("ARIMA libraries not available, using simple ARIMA")
            return self._validate_simple_arima(splits)
        
        arima_results = {'mape': [], 'rmse': [], 'mae': [], 'r2': []}
        
        for fold_idx, (train, test) in enumerate(splits):
            try:
                y_train = train['revenue'].values
                y_test = test['revenue'].values
                
                # Auto ARIMA to find best parameters
                model = auto_arima(
                    y_train,
                    seasonal=True,
                    m=7,  # Weekly seasonality
                    max_p=3,
                    max_q=3,
                    max_P=2,
                    max_Q=2,
                    suppress_warnings=True,
                    stepwise=True,
                    error_action='ignore'
                )
                
                # Forecast
                y_pred = model.predict(n_periods=len(test))
                
                # Calculate metrics
                metrics = self.calculate_metrics(y_test, y_pred)
                for metric in ['mape', 'rmse', 'mae', 'r2']:
                    arima_results[metric].append(metrics[metric])
                
                logger.info(f"Fold {fold_idx+1} ARIMA validation complete - MAPE: {metrics['mape']:.2f}%")
                
            except Exception as e:
                logger.error(f"ARIMA validation failed for fold {fold_idx+1}: {e}")
                for metric in ['mape', 'rmse', 'mae', 'r2']:
                    arima_results[metric].append(np.nan)
        
        return arima_results
    
    def _validate_simple_arima(self, splits) -> Dict[str, List[float]]:
        """Fallback simple ARIMA if pmdarima not available"""
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            logger.error("ARIMA not available")
            return {'mape': [np.nan], 'rmse': [np.nan], 'mae': [np.nan], 'r2': [np.nan]}
        
        arima_results = {'mape': [], 'rmse': [], 'mae': [], 'r2': []}
        
        for fold_idx, (train, test) in enumerate(splits):
            try:
                y_train = train['revenue'].values
                y_test = test['revenue'].values
                
                # Simple ARIMA(1,1,1)
                model = ARIMA(y_train, order=(1, 1, 1))
                fitted = model.fit()
                
                # Forecast
                y_pred = fitted.forecast(steps=len(test))
                
                # Calculate metrics
                metrics = self.calculate_metrics(y_test, y_pred)
                for metric in ['mape', 'rmse', 'mae', 'r2']:
                    arima_results[metric].append(metrics[metric])
                
                logger.info(f"Fold {fold_idx+1} Simple ARIMA validation complete")
                
            except Exception as e:
                logger.error(f"Simple ARIMA failed for fold {fold_idx+1}: {e}")
                for metric in ['mape', 'rmse', 'mae', 'r2']:
                    arima_results[metric].append(np.nan)
        
        return arima_results
    
    def validate_lstm(
        self,
        splits: List[Tuple[pd.DataFrame, pd.DataFrame]]
    ) -> Dict[str, List[float]]:
        """
        Validate LSTM model across CV folds
        
        Returns:
            Dictionary of metric -> list of fold values
        """
        logger.info("Validating LSTM model...")
        
        try:
            from src.ml.forecasting.lstm_forecaster import LSTMForecaster, TORCH_AVAILABLE
            
            if not TORCH_AVAILABLE:
                logger.error("PyTorch not available for LSTM")
                return {'mape': [np.nan], 'rmse': [np.nan], 'mae': [np.nan], 'r2': [np.nan]}
        except ImportError:
            logger.error("LSTM forecaster not available")
            return {'mape': [np.nan], 'rmse': [np.nan], 'mae': [np.nan], 'r2': [np.nan]}
        
        lstm_results = {'mape': [], 'rmse': [], 'mae': [], 'r2': []}
        
        for fold_idx, (train, test) in enumerate(splits):
            try:
                y_train = train['revenue'].values
                y_test = test['revenue'].values
                
                # Initialize LSTM
                forecaster = LSTMForecaster(
                    seq_length=30,
                    hidden_size=64,
                    num_layers=2,
                    dropout=0.2,
                    learning_rate=0.001,
                    batch_size=32,
                    epochs=50  # Will use early stopping
                )
                
                # Train model
                forecaster.fit(y_train, validation_split=0.1)
                
                # Generate predictions
                y_pred = forecaster.predict(y_train, horizon=len(test))
                
                # Calculate metrics
                metrics = self.calculate_metrics(y_test, y_pred)
                for metric in ['mape', 'rmse', 'mae', 'r2']:
                    lstm_results[metric].append(metrics[metric])
                
                logger.info(f"Fold {fold_idx+1} LSTM validation complete - MAPE: {metrics['mape']:.2f}%")
                
            except Exception as e:
                logger.error(f"LSTM validation failed for fold {fold_idx+1}: {e}")
                for metric in ['mape', 'rmse', 'mae', 'r2']:
                    lstm_results[metric].append(np.nan)
        
        return lstm_results
    
    def aggregate_results(self, results: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Aggregate cross-validation results with confidence intervals
        
        Returns:
            Dictionary with mean, std, and 95% CI for each metric
        """
        aggregated = {}
        
        for metric, values in results.items():
            if metric == 'predictions':
                continue
            
            # Remove NaN values
            clean_values = [v for v in values if not np.isnan(v)]
            
            if len(clean_values) == 0:
                aggregated[metric] = {
                    'mean': np.nan,
                    'std': np.nan,
                    'ci_lower': np.nan,
                    'ci_upper': np.nan
                }
                continue
            
            mean_val = np.mean(clean_values)
            std_val = np.std(clean_values)
            
            # 95% confidence interval
            if len(clean_values) > 1:
                ci = stats.t.interval(
                    0.95,
                    len(clean_values) - 1,
                    loc=mean_val,
                    scale=stats.sem(clean_values)
                )
                ci_lower, ci_upper = ci
            else:
                ci_lower, ci_upper = mean_val, mean_val
            
            aggregated[metric] = {
                'mean': mean_val,
                'std': std_val,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'values': clean_values
            }
        
        return aggregated
    
    def _generate_future_regressors(
        self,
        test: pd.DataFrame,
        train: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate future regressor values for Prophet prediction
        
        For holidays and monsoon, we can determine these from dates.
        This allows Prophet to use external regressors during forecasting.
        
        Args:
            test: Test DataFrame with dates
            train: Train DataFrame (for reference)
        
        Returns:
            DataFrame with future regressor values
        """
        future_regressors = pd.DataFrame()
        future_regressors['ds'] = test['date'].values
        
        # Generate is_holiday based on actual dates
        # We know holiday dates from our data generation
        future_regressors['is_holiday'] = test['is_holiday'].values if 'is_holiday' in test.columns else 0
        
        # Generate is_monsoon based on month
        future_regressors['is_monsoon'] = test['is_monsoon'].values if 'is_monsoon' in test.columns else 0
        
        return future_regressors
    
    def run_comprehensive_validation(
        self,
        initial_train_days: int = 365,
        forecast_horizon: int = 30,
        step_size: int = 30,
        max_folds: int = 5,
        include_lstm: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive validation across all models
        
        Args:
            include_lstm: Whether to include LSTM validation (slower)
        
        Returns:
            Complete validation results with metrics and comparisons
        """
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE FORECAST VALIDATION")
        logger.info("=" * 60)
        
        # Create time-series splits
        splits = self.time_series_split(
            initial_train_days=initial_train_days,
            forecast_horizon=forecast_horizon,
            step_size=step_size,
            max_folds=max_folds
        )
        
        # Validate all models
        results = {}
        
        # Baselines
        baseline_results = self.validate_baseline_models(splits)
        for model_name, metrics in baseline_results.items():
            results[model_name] = self.aggregate_results(metrics)
        
        # Prophet with regressors (fixed)
        logger.info("Validating Prophet WITH regressors...")
        prophet_with_reg_results = {'mape': [], 'rmse': [], 'mae': [], 'r2': [], 'predictions': []}
        
        try:
            from src.ml.forecasting.prophet_forecaster import ProphetForecaster
            
            for fold_idx, (train, test) in enumerate(splits):
                try:
                    forecaster = ProphetForecaster(
                        yearly_seasonality=True,
                        weekly_seasonality=True,
                        include_holidays=True
                    )
                    
                    # Prepare data with regressors
                    regressors = ['is_holiday', 'is_monsoon']
                    prophet_df = forecaster.prepare_data(
                        train,
                        date_column='date',
                        target_column='revenue',
                        regressors=regressors
                    )
                    
                    # Fit model
                    forecaster.fit(prophet_df, regressors=regressors)
                    
                    # Generate future regressors
                    future_regressors = self._generate_future_regressors(test, train)
                    
                    # Generate forecast with future regressors
                    forecast = forecaster.predict(
                        periods=len(test),
                        include_history=False,
                        future_regressors=future_regressors
                    )
                    
                    # Extract predictions
                    y_pred = forecast['yhat'].values[:len(test)]
                    y_test = test['revenue'].values
                    
                    # Calculate metrics
                    metrics = self.calculate_metrics(y_test, y_pred)
                    for metric in ['mape', 'rmse', 'mae', 'r2']:
                        prophet_with_reg_results[metric].append(metrics[metric])
                    
                    prophet_with_reg_results['predictions'].append({
                        'fold': fold_idx,
                        'y_true': y_test,
                        'y_pred': y_pred,
                        'dates': test['date'].values
                    })
                    
                    logger.info(f"Fold {fold_idx+1} Prophet (with regressors) complete - MAPE: {metrics['mape']:.2f}%")
                    
                except Exception as e:
                    logger.error(f"Prophet with regressors failed for fold {fold_idx+1}: {e}")
                    for metric in ['mape', 'rmse', 'mae', 'r2']:
                        prophet_with_reg_results[metric].append(np.nan)
        
        except ImportError:
            logger.error("Prophet not available")
        
        results['prophet'] = self.aggregate_results(prophet_with_reg_results)
        results['prophet_predictions'] = prophet_with_reg_results.get('predictions', [])
        
        # Prophet without regressors (for comparison)
        prophet_no_reg = self.validate_prophet(splits, use_regressors=False)
        results['prophet_no_regressors'] = self.aggregate_results(prophet_no_reg)
        
        # ARIMA
        arima_results = self.validate_arima(splits)
        results['arima'] = self.aggregate_results(arima_results)
        
        # LSTM (optional - slower)
        if include_lstm:
            lstm_results = self.validate_lstm(splits)
            results['lstm'] = self.aggregate_results(lstm_results)
        
        # Store complete results
        self.results = results
        
        # Create summary
        self.create_summary()
        
        logger.info("=" * 60)
        logger.info("VALIDATION COMPLETE")
        logger.info("=" * 60)
        
        return results
    
    def create_summary(self):
        """Create human-readable summary of results"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'data_info': {
                'total_days': len(self.data),
                'date_range': f"{self.data['date'].min()} to {self.data['date'].max()}",
                'total_revenue': float(self.data['revenue'].sum())
            },
            'models': {}
        }
        
        for model_name, metrics in self.results.items():
            if model_name.endswith('_predictions'):
                continue
            
            summary['models'][model_name] = {
                'mape': {
                    'mean': round(metrics['mape']['mean'], 2),
                    'ci': f"[{metrics['mape']['ci_lower']:.2f}, {metrics['mape']['ci_upper']:.2f}]"
                },
                'rmse': {
                    'mean': round(metrics['rmse']['mean'], 0),
                    'ci': f"[{metrics['rmse']['ci_lower']:.0f}, {metrics['rmse']['ci_upper']:.0f}]"
                },
                'mae': {
                    'mean': round(metrics['mae']['mean'], 0),
                    'ci': f"[{metrics['mae']['ci_lower']:.0f}, {metrics['mae']['ci_upper']:.0f}]"
                },
                'r2': {
                    'mean': round(metrics['r2']['mean'], 3),
                    'ci': f"[{metrics['r2']['ci_lower']:.3f}, {metrics['r2']['ci_upper']:.3f}]"
                }
            }
        
        self.metrics_summary = summary
        
    def plot_results(self, output_dir: Path):
        """Generate publication-quality plots"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating plots in {output_dir}")
        
        # 1. Model Comparison - MAPE
        self._plot_model_comparison(output_dir)
        
        # 2. Predicted vs Actual
        self._plot_predicted_vs_actual(output_dir)
        
        # 3. Error Distribution
        self._plot_error_distribution(output_dir)
        
        # 4. Metrics Heatmap
        self._plot_metrics_heatmap(output_dir)
        
        logger.info(f"All plots saved to {output_dir}")
    
    def _plot_model_comparison(self, output_dir: Path):
        """Plot model comparison bar chart"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        metrics_to_plot = ['mape', 'rmse', 'mae', 'r2']
        metric_labels = ['MAPE (%)', 'RMSE (₹)', 'MAE (₹)', 'R²']
        
        for idx, (metric, label) in enumerate(zip(metrics_to_plot, metric_labels)):
            ax = axes[idx // 2, idx % 2]
            
            models = []
            means = []
            errors = []
            
            for model_name, metrics in self.results.items():
                if model_name.endswith('_predictions'):
                    continue
                
                if metric in metrics:
                    models.append(model_name.replace('_', ' ').title())
                    means.append(metrics[metric]['mean'])
                    
                    # Error bars (95% CI)
                    ci_range = metrics[metric]['ci_upper'] - metrics[metric]['ci_lower']
                    errors.append(ci_range / 2)
            
            # Sort by performance (lower is better except for R²)
            if metric != 'r2':
                sorted_indices = np.argsort(means)
            else:
                sorted_indices = np.argsort(means)[::-1]
            
            models = [models[i] for i in sorted_indices]
            means = [means[i] for i in sorted_indices]
            errors = [errors[i] for i in sorted_indices]
            
            # Color code: best=green, worst=red
            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(models)))
            if metric == 'r2':
                colors = colors[::-1]
            
            bars = ax.barh(models, means, xerr=errors, capsize=5, color=colors, alpha=0.7, edgecolor='black')
            ax.set_xlabel(label, fontsize=12, fontweight='bold')
            ax.set_title(f'{label} Comparison (with 95% CI)', fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)
            
            # Add value labels
            for i, (bar, mean) in enumerate(zip(bars, means)):
                if metric == 'mape':
                    ax.text(mean, i, f'  {mean:.2f}%', va='center', fontsize=10)
                elif metric == 'r2':
                    ax.text(mean, i, f'  {mean:.3f}', va='center', fontsize=10)
                else:
                    ax.text(mean, i, f'  ₹{mean:,.0f}', va='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'model_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✅ Model comparison plot saved")
    
    def _plot_predicted_vs_actual(self, output_dir: Path):
        """Plot predicted vs actual for best model"""
        if 'prophet_predictions' not in self.results or not self.results['prophet_predictions']:
            logger.warning("No Prophet predictions available for plotting")
            return
        
        # Use first fold for visualization
        pred_data = self.results['prophet_predictions'][0]
        
        fig, ax = plt.subplots(figsize=(16, 8))
        
        dates = pd.to_datetime(pred_data['dates'])
        y_true = pred_data['y_true']
        y_pred = pred_data['y_pred']
        
        ax.plot(dates, y_true, 'o-', label='Actual', color='#2E86AB', linewidth=2, markersize=6)
        ax.plot(dates, y_pred, 's--', label='Predicted (Prophet)', color='#A23B72', linewidth=2, markersize=6, alpha=0.8)
        
        # Fill between for error
        ax.fill_between(dates, y_true, y_pred, alpha=0.2, color='gray', label='Prediction Error')
        
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Revenue (₹)', fontsize=12, fontweight='bold')
        ax.set_title('Predicted vs Actual Revenue (Prophet Model - Fold 1)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11, loc='best')
        ax.grid(alpha=0.3)
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x/1000:.0f}K'))
        
        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'predicted_vs_actual.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✅ Predicted vs Actual plot saved")
    
    def _plot_error_distribution(self, output_dir: Path):
        """Plot error distribution"""
        if 'prophet_predictions' not in self.results or not self.results['prophet_predictions']:
            return
        
        # Collect all errors across folds
        all_errors = []
        all_pct_errors = []
        
        for pred_data in self.results['prophet_predictions']:
            y_true = pred_data['y_true']
            y_pred = pred_data['y_pred']
            
            errors = y_true - y_pred
            pct_errors = ((y_true - y_pred) / y_true) * 100
            
            all_errors.extend(errors)
            all_pct_errors.extend(pct_errors)
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Absolute errors
        axes[0].hist(all_errors, bins=30, color='#2E86AB', alpha=0.7, edgecolor='black')
        axes[0].axvline(0, color='red', linestyle='--', linewidth=2, label='Zero Error')
        axes[0].set_xlabel('Prediction Error (₹)', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Frequency', fontsize=12, fontweight='bold')
        axes[0].set_title('Distribution of Prediction Errors', fontsize=14, fontweight='bold')
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # Percentage errors
        axes[1].hist(all_pct_errors, bins=30, color='#A23B72', alpha=0.7, edgecolor='black')
        axes[1].axvline(0, color='red', linestyle='--', linewidth=2, label='Zero Error')
        axes[1].set_xlabel('Percentage Error (%)', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('Frequency', fontsize=12, fontweight='bold')
        axes[1].set_title('Distribution of Percentage Errors', fontsize=14, fontweight='bold')
        axes[1].legend()
        axes[1].grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'error_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✅ Error distribution plot saved")
    
    def _plot_metrics_heatmap(self, output_dir: Path):
        """Plot metrics heatmap"""
        # Prepare data for heatmap
        models = []
        metrics_data = {
            'MAPE (%)': [],
            'RMSE (₹)': [],
            'MAE (₹)': [],
            'R²': []
        }
        
        for model_name, metrics in self.results.items():
            if model_name.endswith('_predictions'):
                continue
            
            models.append(model_name.replace('_', ' ').title())
            metrics_data['MAPE (%)'].append(metrics['mape']['mean'])
            metrics_data['RMSE (₹)'].append(metrics['rmse']['mean'])
            metrics_data['MAE (₹)'].append(metrics['mae']['mean'])
            metrics_data['R²'].append(metrics['r2']['mean'])
        
        # Create DataFrame
        df = pd.DataFrame(metrics_data, index=models)
        
        # Normalize for heatmap (0-1 scale, inverted for MAPE/RMSE/MAE)
        df_norm = df.copy()
        for col in ['MAPE (%)', 'RMSE (₹)', 'MAE (₹)']:
            df_norm[col] = 1 - (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        df_norm['R²'] = (df['R²'] - df['R²'].min()) / (df['R²'].max() - df['R²'].min())
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(
            df_norm,
            annot=df,
            fmt='.2f',
            cmap='RdYlGn',
            cbar_kws={'label': 'Normalized Performance (1=Best)'},
            linewidths=0.5,
            ax=ax
        )
        
        ax.set_title('Model Performance Heatmap', fontsize=14, fontweight='bold')
        ax.set_xlabel('Metrics', fontsize=12, fontweight='bold')
        ax.set_ylabel('Models', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'metrics_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✅ Metrics heatmap saved")
    
    def save_report(self, output_dir: Path):
        """Save comprehensive validation report"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / 'validation_report.md'
        
        with open(report_path, 'w') as f:
            f.write("# Forecast Accuracy Validation Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"This report presents the results of comprehensive time-series cross-validation ")
            f.write(f"for demand forecasting models in the R-DIOS system.\n\n")
            
            f.write("### Dataset Information\n\n")
            f.write(f"- **Total Days:** {self.metrics_summary['data_info']['total_days']}\n")
            f.write(f"- **Date Range:** {self.metrics_summary['data_info']['date_range']}\n")
            f.write(f"- **Total Revenue:** ₹{self.metrics_summary['data_info']['total_revenue']:,.2f}\n\n")
            
            f.write("---\n\n")
            f.write("## Methodology\n\n")
            f.write("### Time-Series Cross-Validation\n\n")
            f.write("To prevent data leakage and ensure academic rigor, we implemented **walk-forward validation**:\n\n")
            f.write("1. **Initial Training Period:** 365 days\n")
            f.write("2. **Forecast Horizon:** 30 days\n")
            f.write("3. **Step Size:** 30 days (moving forward between folds)\n")
            f.write("4. **Number of Folds:** 5\n\n")
            f.write("This approach ensures:\n")
            f.write("- ✅ No future data leaks into training\n")
            f.write("- ✅ Realistic evaluation of production performance\n")
            f.write("- ✅ Robust metrics with confidence intervals\n\n")
            
            f.write("### Models Evaluated\n\n")
            f.write("**Baseline Models:**\n")
            f.write("- **Naive Forecast:** Last observed value repeated\n")
            f.write("- **Seasonal Naive:** Values from same day last week\n")
            f.write("- **Moving Average:** 7-day moving average\n")
            f.write("- **Exponential Smoothing:** Weighted average with decay\n\n")
            f.write("**Advanced Models:**\n")
            f.write("- **Prophet:** Facebook Prophet with seasonality, holidays, and external regressors\n")
            f.write("- **Prophet (No Regressors):** Prophet without external factors (for comparison)\n")
            f.write("- **ARIMA:** Auto-ARIMA with seasonal components\n\n")
            
            f.write("---\n\n")
            f.write("## Results\n\n")
            
            # Find best model
            best_mape = float('inf')
            best_model = None
            for model_name, metrics in self.metrics_summary['models'].items():
                if metrics['mape']['mean'] < best_mape:
                    best_mape = metrics['mape']['mean']
                    best_model = model_name
            
            f.write(f"### 🏆 Best Model: **{best_model.replace('_', ' ').title()}**\n\n")
            f.write(f"- **MAPE:** {best_mape:.2f}% {self.metrics_summary['models'][best_model]['mape']['ci']}\n")
            f.write(f"- **RMSE:** ₹{self.metrics_summary['models'][best_model]['rmse']['mean']:,.0f} {self.metrics_summary['models'][best_model]['rmse']['ci']}\n")
            f.write(f"- **MAE:** ₹{self.metrics_summary['models'][best_model]['mae']['mean']:,.0f} {self.metrics_summary['models'][best_model]['mae']['ci']}\n")
            f.write(f"- **R²:** {self.metrics_summary['models'][best_model]['r2']['mean']:.3f} {self.metrics_summary['models'][best_model]['r2']['ci']}\n\n")
            
            f.write("### Complete Results Table\n\n")
            f.write("| Model | MAPE (%) | RMSE (₹) | MAE (₹) | R² |\n")
            f.write("|-------|----------|----------|---------|----|\n")
            
            # Sort by MAPE
            sorted_models = sorted(
                self.metrics_summary['models'].items(),
                key=lambda x: x[1]['mape']['mean']
            )
            
            for model_name, metrics in sorted_models:
                display_name = model_name.replace('_', ' ').title()
                f.write(f"| {display_name} | ")
                f.write(f"{metrics['mape']['mean']:.2f} ± {(metrics['mape']['mean'] - float(metrics['mape']['ci'].split('[')[1].split(',')[0])):.2f} | ")
                f.write(f"₹{metrics['rmse']['mean']:,.0f} | ")
                f.write(f"₹{metrics['mae']['mean']:,.0f} | ")
                f.write(f"{metrics['r2']['mean']:.3f} |\n")
            
            f.write("\n---\n\n")
            f.write("## Key Findings\n\n")
            
            # Compare Prophet with and without regressors
            if 'prophet' in self.metrics_summary['models'] and 'prophet_no_regressors' in self.metrics_summary['models']:
                mape_with = self.metrics_summary['models']['prophet']['mape']['mean']
                mape_without = self.metrics_summary['models']['prophet_no_regressors']['mape']['mean']
                improvement = ((mape_without - mape_with) / mape_without) * 100
                
                f.write("### Impact of External Regressors\n\n")
                f.write(f"- **Prophet with regressors:** MAPE = {mape_with:.2f}%\n")
                f.write(f"- **Prophet without regressors:** MAPE = {mape_without:.2f}%\n")
                f.write(f"- **Improvement:** {improvement:.2f}%\n\n")
                
                if improvement > 5:
                    f.write("✅ **Conclusion:** External factors (holidays, weather) significantly improve forecast accuracy.\n\n")
                else:
                    f.write("⚠️ **Conclusion:** External factors provide marginal improvement.\n\n")
            
            # Compare with baselines
            naive_mape = self.metrics_summary['models']['naive']['mape']['mean']
            improvement_over_naive = ((naive_mape - best_mape) / naive_mape) * 100
            
            f.write("### Improvement Over Naive Baseline\n\n")
            f.write(f"- **Naive MAPE:** {naive_mape:.2f}%\n")
            f.write(f"- **Best Model MAPE:** {best_mape:.2f}%\n")
            f.write(f"- **Improvement:** {improvement_over_naive:.2f}%\n\n")
            
            f.write("---\n\n")
            f.write("## Interpretation Guide\n\n")
            f.write("### What do these metrics mean?\n\n")
            f.write("- **MAPE (Mean Absolute Percentage Error):** Average percentage difference between predicted and actual values. ")
            f.write("Lower is better. <10% is excellent, 10-20% is good, >20% needs improvement.\n\n")
            f.write("- **RMSE (Root Mean Squared Error):** Average magnitude of errors in rupees. ")
            f.write("Penalizes large errors more heavily. Lower is better.\n\n")
            f.write("- **MAE (Mean Absolute Error):** Average absolute error in rupees. ")
            f.write("More interpretable than RMSE. Lower is better.\n\n")
            f.write("- **R² (Coefficient of Determination):** Proportion of variance explained by the model. ")
            f.write("Ranges from 0 to 1. Higher is better. >0.8 is good, >0.9 is excellent.\n\n")
            
            f.write("---\n\n")
            f.write("## Recommendations\n\n")
            
            if best_mape < 15:
                f.write("✅ **Production Ready:** The forecast accuracy is excellent and suitable for production deployment.\n\n")
            elif best_mape < 20:
                f.write("⚠️ **Good Performance:** The forecast accuracy is good but could be improved with additional features or model tuning.\n\n")
            else:
                f.write("❌ **Needs Improvement:** The forecast accuracy requires improvement before production deployment.\n\n")
            
            f.write("### Next Steps\n\n")
            f.write("1. **Model Deployment:** Deploy the best-performing model to production\n")
            f.write("2. **Monitoring:** Set up drift detection to monitor model performance over time\n")
            f.write("3. **Retraining:** Retrain model monthly with new data\n")
            f.write("4. **Feature Engineering:** Explore additional external factors (promotions, competitor pricing)\n")
            f.write("5. **Ensemble Methods:** Consider combining multiple models for improved robustness\n\n")
            
            f.write("---\n\n")
            f.write("## Visualizations\n\n")
            f.write("See the following plots for detailed analysis:\n\n")
            f.write("- `model_comparison.png` - Comparison of all models across metrics\n")
            f.write("- `predicted_vs_actual.png` - Time series plot of predictions vs actuals\n")
            f.write("- `error_distribution.png` - Distribution of prediction errors\n")
            f.write("- `metrics_heatmap.png` - Heatmap of model performance\n\n")
            
            f.write("---\n\n")
            f.write("*Report generated by R-DIOS Forecast Validation System*\n")
        
        logger.info(f"✅ Validation report saved to {report_path}")
        
        # Also save JSON version
        json_path = output_dir / 'validation_results.json'
        with open(json_path, 'w') as f:
            json.dump(self.metrics_summary, f, indent=2, default=str)
        
        logger.info(f"✅ JSON results saved to {json_path}")


def main():
    """Main execution function"""
    print("\n" + "=" * 70)
    print("R-DIOS COMPREHENSIVE FORECAST VALIDATION")
    print("Academic-Quality Time-Series Cross-Validation")
    print("=" * 70 + "\n")
    
    # Paths
    project_root = Path(__file__).parent.parent
    data_path = project_root / 'data' / 'validation_dataset.csv'
    output_dir = project_root / 'validation_results'
    
    # Check if data exists
    if not data_path.exists():
        print(f"❌ ERROR: Validation dataset not found at {data_path}")
        print("\n📝 Please run the data generation script first:")
        print(f"   python scripts/generate_validation_dataset.py\n")
        return
    
    # Initialize validator
    validator = ForecastValidator(data_path=str(data_path))
    
    # Load data
    print("📊 Loading validation dataset...")
    validator.load_data()
    
    # Run comprehensive validation
    print("\n🚀 Running comprehensive validation...")
    print("   This may take 5-10 minutes depending on your system...\n")
    
    results = validator.run_comprehensive_validation(
        initial_train_days=365,  # 1 year initial training
        forecast_horizon=30,     # 30-day forecasts
        step_size=30,            # Move forward 30 days between folds
        max_folds=5              # 5 validation folds
    )
    
    # Generate plots
    print("\n📈 Generating publication-quality plots...")
    validator.plot_results(output_dir)
    
    # Save report
    print("\n📄 Generating validation report...")
    validator.save_report(output_dir)
    
    # Print summary
    print("\n" + "=" * 70)
    print("✅ VALIDATION COMPLETE!")
    print("=" * 70)
    
    print("\n📊 RESULTS SUMMARY:\n")
    
    # Find best model
    best_mape = float('inf')
    best_model = None
    for model_name, metrics in validator.metrics_summary['models'].items():
        if metrics['mape']['mean'] < best_mape:
            best_mape = metrics['mape']['mean']
            best_model = model_name
    
    print(f"🏆 Best Model: {best_model.replace('_', ' ').title()}")
    print(f"   MAPE: {best_mape:.2f}%")
    print(f"   RMSE: ₹{validator.metrics_summary['models'][best_model]['rmse']['mean']:,.0f}")
    print(f"   MAE: ₹{validator.metrics_summary['models'][best_model]['mae']['mean']:,.0f}")
    print(f"   R²: {validator.metrics_summary['models'][best_model]['r2']['mean']:.3f}")
    
    print(f"\n📁 All results saved to: {output_dir}")
    print("\n📋 Files generated:")
    print(f"   - validation_report.md (comprehensive report)")
    print(f"   - validation_results.json (raw data)")
    print(f"   - model_comparison.png")
    print(f"   - predicted_vs_actual.png")
    print(f"   - error_distribution.png")
    print(f"   - metrics_heatmap.png")
    
    print("\n💡 Next steps:")
    print("   1. Review the validation report")
    print("   2. Include plots in your thesis documentation")
    print("   3. Update your README with actual metrics")
    print("   4. Prepare demo video showing these results")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
