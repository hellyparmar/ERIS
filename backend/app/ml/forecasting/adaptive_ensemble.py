"""
Adaptive Ensemble Forecaster with Dynamic Weight Optimization
Week 11-12: Dynamic model weighting based on rolling performance

This module implements intelligent ensemble forecasting where model weights
are dynamically adjusted based on recent validation performance.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
import logging
from pathlib import Path
import json
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class ModelMetric:
    """Track individual model performance"""
    timestamp: datetime
    model_name: str
    mape: float
    rmse: float
    mae: float
    coverage: float  # % of forecasts within confidence interval
    
    def composite_score(self) -> float:
        """Calculate weighted composite score"""
        # Lower is better for MAPE, RMSE, MAE
        # Higher is better for coverage
        return (
            (1 - self.mape / 100) * 0.4 +  # MAPE weight
            (1 - min(self.rmse / 1000, 1)) * 0.3 +  # RMSE weight
            (1 - min(self.mae / 500, 1)) * 0.2 +  # MAE weight
            self.coverage * 0.1  # Coverage weight
        )


@dataclass
class WeightHistory:
    """Track weight changes over time"""
    timestamp: datetime
    model_name: str
    weight: float
    reason: str = ""


class PerformanceTracker:
    """Track rolling performance of each model"""
    
    def __init__(self, window_size: int = 4):
        """
        Args:
            window_size: Number of periods to track (weeks/months)
        """
        self.window_size = window_size
        self.metrics: Dict[str, deque] = {}
        self.weight_history: List[WeightHistory] = []
        
    def add_metric(self, metric: ModelMetric) -> None:
        """Add performance metric for a model"""
        if metric.model_name not in self.metrics:
            self.metrics[metric.model_name] = deque(maxlen=self.window_size)
        
        self.metrics[metric.model_name].append(metric)
        logger.info(f"Added metric for {metric.model_name}: MAPE={metric.mape:.2f}%")
    
    def get_rolling_score(self, model_name: str) -> float:
        """Get average composite score for model"""
        if model_name not in self.metrics or len(self.metrics[model_name]) == 0:
            return 0.5  # Default neutral score
        
        scores = [m.composite_score() for m in self.metrics[model_name]]
        return np.mean(scores)
    
    def get_all_rolling_scores(self) -> Dict[str, float]:
        """Get scores for all models"""
        return {
            name: self.get_rolling_score(name)
            for name in self.metrics.keys()
        }
    
    def get_recent_metrics(self, model_name: str) -> Optional[ModelMetric]:
        """Get most recent metric for model"""
        if model_name not in self.metrics or len(self.metrics[model_name]) == 0:
            return None
        return self.metrics[model_name][-1]
    
    def save_metrics(self, filepath: str) -> None:
        """Save metrics history to JSON"""
        data = {
            name: [asdict(m) for m in metrics]
            for name, metrics in self.metrics.items()
        }
        # Convert datetime objects to strings
        for model_metrics in data.values():
            for metric in model_metrics:
                metric['timestamp'] = metric['timestamp'].isoformat()
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved metrics to {filepath}")
    
    def load_metrics(self, filepath: str) -> None:
        """Load metrics history from JSON"""
        if not Path(filepath).exists():
            logger.warning(f"Metrics file not found: {filepath}")
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for model_name, metrics_list in data.items():
            for metric_dict in metrics_list:
                metric_dict['timestamp'] = datetime.fromisoformat(metric_dict['timestamp'])
                metric = ModelMetric(**metric_dict)
                self.add_metric(metric)
        
        logger.info(f"Loaded metrics from {filepath}")


class AdaptiveWeightOptimizer:
    """Optimize ensemble weights based on performance"""
    
    def __init__(self, tracker: PerformanceTracker, min_weight: float = 0.05):
        """
        Args:
            tracker: PerformanceTracker instance
            min_weight: Minimum weight for any model (prevents zeroing out)
        """
        self.tracker = tracker
        self.min_weight = min_weight
        self.current_weights: Dict[str, float] = {}
        self.weight_history: List[WeightHistory] = []
    
    def calculate_adaptive_weights(self) -> Dict[str, float]:
        """
        Calculate weights based on rolling performance scores
        
        Returns:
            Dict of model_name -> weight (sum to 1.0)
        """
        scores = self.tracker.get_all_rolling_scores()
        
        if not scores or all(v == 0 for v in scores.values()):
            # No performance data, use equal weights
            n_models = len(scores) if scores else 1
            return {name: 1.0 / n_models for name in scores.keys()}
        
        # Normalize scores to [min_weight, 1.0]
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        if max_score == min_score:
            # All same score, equal weights
            n = len(scores)
            return {name: 1.0 / n for name in scores.keys()}
        
        # Scale scores to weight range
        raw_weights = {}
        for name, score in scores.items():
            # Normalize to 0-1
            normalized = (score - min_score) / (max_score - min_score)
            # Scale to [min_weight, 1.0]
            weight = self.min_weight + normalized * (1 - self.min_weight)
            raw_weights[name] = weight
        
        # Normalize to sum to 1.0
        total = sum(raw_weights.values())
        weights = {name: w / total for name, w in raw_weights.items()}
        
        logger.info(f"Calculated adaptive weights: {weights}")
        return weights
    
    def update_weights(self, reason: str = "Periodic update") -> Dict[str, float]:
        """
        Update ensemble weights and track history
        
        Args:
            reason: Reason for weight update
        
        Returns:
            Updated weights
        """
        weights = self.calculate_adaptive_weights()
        self.current_weights = weights
        
        # Track history
        for name, weight in weights.items():
            history = WeightHistory(
                timestamp=datetime.now(),
                model_name=name,
                weight=weight,
                reason=reason
            )
            self.weight_history.append(history)
        
        return weights
    
    def get_weight_for_model(self, model_name: str) -> float:
        """Get current weight for a model"""
        return self.current_weights.get(model_name, 0.0)
    
    def should_update_weights(self, hours_since_last_update: float) -> bool:
        """
        Determine if weights should be updated
        
        Args:
            hours_since_last_update: Hours since last weight update
        
        Returns:
            True if update is needed
        """
        # Update weights at least weekly
        if hours_since_last_update > 7 * 24:
            return True
        
        # Update if recent model performance significantly changed
        recent_metrics = self.tracker.metrics
        for model_name, metrics in recent_metrics.items():
            if len(metrics) >= 2:
                latest = metrics[-1].composite_score()
                previous = metrics[-2].composite_score()
                # Update if change > 10%
                if abs(latest - previous) / (previous + 0.001) > 0.1:
                    return True
        
        return False
    
    def get_weight_stability(self) -> Dict[str, float]:
        """
        Get stability metric for each model weight
        (lower = more stable)
        """
        if not self.weight_history:
            return {}
        
        model_histories: Dict[str, List[float]] = {}
        for entry in self.weight_history:
            if entry.model_name not in model_histories:
                model_histories[entry.model_name] = []
            model_histories[entry.model_name].append(entry.weight)
        
        stability = {}
        for name, weights in model_histories.items():
            if len(weights) > 1:
                # Coefficient of variation
                stability[name] = np.std(weights) / (np.mean(weights) + 0.001)
            else:
                stability[name] = 0.0
        
        return stability


class AdaptiveEnsembleForecaster:
    """
    Ensemble forecaster with adaptive weights
    Automatically adjusts model weights based on validation performance
    """
    
    def __init__(self, models: Dict[str, Any] = None, window_size: int = 4):
        """
        Args:
            models: Dictionary of {model_name: forecaster_instance}
            window_size: Periods to track for performance
        """
        self.models = models or {}
        self.tracker = PerformanceTracker(window_size=window_size)
        self.optimizer = AdaptiveWeightOptimizer(self.tracker)
        self.forecasts: Dict[str, pd.DataFrame] = {}
        self.last_weight_update = datetime.now()
        
        logger.info(f"Initialized AdaptiveEnsembleForecaster with {len(self.models)} models")
    
    def add_model(self, name: str, model: Any, initial_weight: float = None) -> None:
        """Add a forecaster model to ensemble"""
        self.models[name] = model
        if initial_weight:
            self.optimizer.current_weights[name] = initial_weight
        logger.info(f"Added model: {name}")
    
    def fit_all(self, data: pd.DataFrame, **kwargs) -> None:
        """Fit all models in ensemble"""
        for name, model in self.models.items():
            logger.info(f"Fitting {name}...")
            try:
                model.fit(data, **kwargs)
                logger.info(f"✓ {name} fitted successfully")
            except Exception as e:
                logger.error(f"✗ Error fitting {name}: {str(e)}")
    
    def predict_all(self, steps: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Generate predictions from all models
        
        Args:
            steps: Number of periods to forecast
        
        Returns:
            Dictionary of forecasts by model
        """
        self.forecasts = {}
        
        for name, model in self.models.items():
            try:
                forecast = model.predict(steps)
                self.forecasts[name] = forecast
                logger.info(f"✓ {name} forecast: {len(forecast)} periods")
            except Exception as e:
                logger.error(f"✗ Error predicting {name}: {str(e)}")
        
        return self.forecasts
    
    def evaluate_models(self, actual: pd.Series, model_names: List[str] = None) -> None:
        """
        Evaluate models and update performance tracker
        
        Args:
            actual: Actual values to compare against
            model_names: Which models to evaluate (None = all)
        """
        if model_names is None:
            model_names = list(self.models.keys())
        
        for name in model_names:
            if name not in self.forecasts:
                logger.warning(f"No forecast for {name}, skipping evaluation")
                continue
            
            forecast = self.forecasts[name]
            
            # Align actual and forecast lengths
            n = min(len(actual), len(forecast))
            actual_values = actual.iloc[-n:].values
            forecast_values = forecast['yhat'].iloc[-n:].values
            
            # Calculate metrics
            mape = np.mean(np.abs((actual_values - forecast_values) / actual_values)) * 100
            rmse = np.sqrt(np.mean((actual_values - forecast_values) ** 2))
            mae = np.mean(np.abs(actual_values - forecast_values))
            
            # Coverage: % within confidence interval
            if 'yhat_lower' in forecast.columns and 'yhat_upper' in forecast.columns:
                lower = forecast['yhat_lower'].iloc[-n:].values
                upper = forecast['yhat_upper'].iloc[-n:].values
                coverage = np.mean((actual_values >= lower) & (actual_values <= upper))
            else:
                coverage = 0.5  # Default estimate
            
            # Add metric
            metric = ModelMetric(
                timestamp=datetime.now(),
                model_name=name,
                mape=mape,
                rmse=rmse,
                mae=mae,
                coverage=coverage
            )
            self.tracker.add_metric(metric)
            
            logger.info(f"{name} evaluation - MAPE: {mape:.2f}%, RMSE: {rmse:.2f}, MAE: {mae:.2f}")
    
    def maybe_update_weights(self) -> bool:
        """
        Check if weights should be updated and do so if needed
        
        Returns:
            True if weights were updated
        """
        hours_since_update = (datetime.now() - self.last_weight_update).total_seconds() / 3600
        
        if self.optimizer.should_update_weights(hours_since_update):
            logger.info("Updating adaptive weights...")
            self.optimizer.update_weights(
                reason=f"Scheduled update after {hours_since_update:.1f} hours"
            )
            self.last_weight_update = datetime.now()
            return True
        
        return False
    
    def combine_forecasts(self, method: str = 'weighted_average') -> pd.DataFrame:
        """
        Combine model forecasts using adaptive weights
        
        Args:
            method: 'weighted_average' (uses adaptive weights), 'median', 'mean'
        
        Returns:
            Combined forecast DataFrame
        """
        if not self.forecasts:
            raise ValueError("No forecasts available. Call predict_all() first.")
        
        # Ensure weights are calculated
        if not self.optimizer.current_weights:
            self.optimizer.update_weights(reason="Initial weight calculation")
        
        weights = self.optimizer.current_weights
        
        if method == 'weighted_average':
            # Combine using adaptive weights
            n_periods = len(list(self.forecasts.values())[0])
            combined = np.zeros(n_periods)
            
            for name, forecast in self.forecasts.items():
                weight = weights.get(name, 1.0 / len(self.forecasts))
                combined += forecast['yhat'].values * weight
            
            logger.info(f"Combined forecasts with weights: {weights}")
        
        elif method == 'median':
            forecast_values = [f['yhat'].values for f in self.forecasts.values()]
            combined = np.median(forecast_values, axis=0)
        
        elif method == 'mean':
            forecast_values = [f['yhat'].values for f in self.forecasts.values()]
            combined = np.mean(forecast_values, axis=0)
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Create result DataFrame
        sample_forecast = list(self.forecasts.values())[0]
        
        result = pd.DataFrame({
            'ds': sample_forecast['ds'],
            'yhat': combined,
            'yhat_lower': combined * 0.9,
            'yhat_upper': combined * 1.1
        })
        
        # Add individual model predictions
        for name, forecast in self.forecasts.items():
            result[f'yhat_{name}'] = forecast['yhat'].values
            result[f'weight_{name}'] = weights.get(name, 0.0)
        
        return result
    
    def get_model_weights(self) -> Dict[str, float]:
        """Get current model weights"""
        return self.optimizer.current_weights.copy()
    
    def get_weight_history(self) -> List[dict]:
        """Get weight update history"""
        return [
            {
                'timestamp': h.timestamp.isoformat(),
                'model': h.model_name,
                'weight': h.weight,
                'reason': h.reason
            }
            for h in self.optimizer.weight_history
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of model performance and weights"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'models': {},
            'weights': self.optimizer.current_weights,
            'stability': self.optimizer.get_weight_stability()
        }
        
        for name in self.models.keys():
            recent = self.tracker.get_recent_metrics(name)
            if recent:
                summary['models'][name] = {
                    'mape': recent.mape,
                    'rmse': recent.rmse,
                    'mae': recent.mae,
                    'coverage': recent.coverage,
                    'score': recent.composite_score()
                }
        
        return summary
    
    def save_state(self, filepath: str) -> None:
        """Save tracker and weight history"""
        self.tracker.save_metrics(f"{filepath}.metrics.json")
        
        history_data = [asdict(h) for h in self.optimizer.weight_history]
        for entry in history_data:
            entry['timestamp'] = entry['timestamp'].isoformat()
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(f"{filepath}.weights.json", 'w') as f:
            json.dump(history_data, f, indent=2)
        
        logger.info(f"Saved ensemble state to {filepath}")
    
    def load_state(self, filepath: str) -> None:
        """Load tracker and weight history"""
        self.tracker.load_metrics(f"{filepath}.metrics.json")
        
        weights_file = f"{filepath}.weights.json"
        if Path(weights_file).exists():
            with open(weights_file, 'r') as f:
                history_data = json.load(f)
            
            for entry in history_data:
                entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                history = WeightHistory(**entry)
                self.optimizer.weight_history.append(history)
            
            logger.info(f"Loaded ensemble state from {filepath}")


# Example usage
if __name__ == "__main__":
    # This would be used with actual forecaster models
    # ensemble = AdaptiveEnsembleForecaster()
    # ensemble.add_model('prophet', prophet_model)
    # ensemble.add_model('lstm', lstm_model)
    # ensemble.add_model('arima', arima_model)
    # 
    # ensemble.fit_all(data)
    # forecasts = ensemble.predict_all(steps=30)
    # ensemble.evaluate_models(actual_values)
    # ensemble.maybe_update_weights()
    # combined = ensemble.combine_forecasts()
    # 
    # print(ensemble.get_performance_summary())
    
    print("✓ Adaptive Ensemble Forecaster ready for integration")
