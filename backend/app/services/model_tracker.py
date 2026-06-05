"""
Model Tracker Service for monitoring forecasting model performance over time.

Essential for MSc Data Science project demonstrating model evaluation discipline.
Tracks:
- Forecast accuracy against actuals (MAE, MAPE, RMSE)
- Directional accuracy (did we predict up/down correctly?)
- Bias (systematic over/under-prediction)
- Performance trends over time
- When to trigger model retraining
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from statistics import mean
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ModelTracker:
    """
    Tracks forecasting model performance and evaluation metrics.
    
    Compares historical forecasts against actual values to compute
    performance metrics and identify when models need retraining.
    """

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.logger = logger

    def record_forecast(
        self,
        outlet_id: str,
        product_id: Optional[str],
        forecast_date: date,
        predicted_value: float,
        model_used: str,
        model_params: dict,
    ) -> bool:
        """
        Save forecast to ForecastResult table.
        
        Args:
            outlet_id: Target outlet UUID
            product_id: Target product UUID (optional, for product-level forecasts)
            forecast_date: Date of the forecast
            predicted_value: Predicted sales value
            model_used: Name of model (e.g., "Prophet", "ARIMA", "Linear Regression")
            model_params: Dict of model parameters for reproducibility
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from app.models.models import ForecastResult, ForecastType
            from uuid import UUID
            
            # Determine forecast type based on whether product_id is provided
            forecast_type = ForecastType.PRODUCT_LEVEL if product_id else ForecastType.OUTLET_LEVEL
            
            # Convert string UUIDs to UUID objects if needed
            outlet_uuid = UUID(outlet_id) if isinstance(outlet_id, str) else outlet_id
            product_uuid = UUID(product_id) if product_id and isinstance(product_id, str) else product_id
            
            # Create new forecast result
            forecast_result = ForecastResult(
                outlet_id=outlet_uuid,
                product_id=product_uuid,
                forecast_type=forecast_type,
                forecast_date=forecast_date,
                predicted_value=predicted_value,
                model_used=model_used,
                factors_considered=model_params,
                confidence_lower=None,  # Can be set if model provides confidence intervals
                confidence_upper=None,
            )
            
            self.db.add(forecast_result)
            self.db.commit()
            
            self.logger.info(
                f"Recorded forecast for outlet {outlet_id} on {forecast_date}: {predicted_value} "
                f"(model: {model_used})"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record forecast: {str(e)}", exc_info=True)
            self.db.rollback()
            return False

    def evaluate_past_forecasts(self, outlet_id: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Compare forecasts made N days ago against actual values that are now available.
        
        Computes performance metrics for all forecasts made for an outlet that have
        actual values available (must have passed the forecast date).
        
        Metrics computed:
        - MAE: Mean Absolute Error (average absolute deviation)
        - MAPE: Mean Absolute Percentage Error (error as % of actual)
        - RMSE: Root Mean Square Error (penalizes large errors more)
        - Directional Accuracy: % of correct up/down predictions
        - Bias: Average signed error (positive = over-predict, negative = under-predict)
        
        Args:
            outlet_id: Target outlet UUID
            days_back: Number of days to evaluate (default 30)
        
        Returns:
            {
                'model_name': str,
                'evaluation_period': {'start': date, 'end': date},
                'sample_size': int,
                'metrics': {
                    'mae': float,
                    'mape': float,
                    'rmse': float,
                    'directional_accuracy': float,
                    'bias': float,
                },
                'performance_trend': [
                    {'date': date, 'mape': float, 'mae': float},
                    ...
                ],
                'worst_predictions': [
                    {'date': date, 'predicted': float, 'actual': float, 'error_pct': float},
                    ...
                ]
            }
        """
        try:
            from app.models.models import ForecastResult, Sale
            from uuid import UUID
            from sqlalchemy import and_
            
            # Convert outlet_id to UUID
            outlet_uuid = UUID(outlet_id) if isinstance(outlet_id, str) else outlet_id
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Query forecasts that were made in the past and have actual sales data
            forecasts = self.db.query(
                ForecastResult.forecast_date,
                ForecastResult.predicted_value,
                ForecastResult.model_used,
                func.coalesce(func.sum(Sale.total_amount), 0).label('actual_value')
            ).outerjoin(
                Sale,
                and_(
                    Sale.outlet_id == ForecastResult.outlet_id,
                    Sale.sale_date == ForecastResult.forecast_date,
                )
            ).filter(
                and_(
                    ForecastResult.outlet_id == outlet_uuid,
                    ForecastResult.forecast_date >= start_date,
                    ForecastResult.forecast_date < end_date,
                )
            ).group_by(
                ForecastResult.forecast_date,
                ForecastResult.predicted_value,
                ForecastResult.model_used,
            ).order_by(ForecastResult.forecast_date).all()
            
            if not forecasts or len(forecasts) == 0:
                self.logger.warning(
                    f"No forecast data available for outlet {outlet_id} in last {days_back} days"
                )
                return {
                    'status': 'no_data',
                    'message': f'No forecasts found for outlet {outlet_id} in evaluation period',
                    'evaluation_period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
                    'sample_size': 0,
                }
            
            # Compute metrics
            errors = []
            absolute_errors = []
            percentage_errors = []
            predictions = []
            actuals = []
            model_names = set()
            
            for forecast_date, predicted, model_used, actual_value in forecasts:
                model_names.add(model_used)
                
                # Skip if actual is zero or negative (can't compute meaningful MAPE)
                if actual_value and actual_value > 0:
                    error = actual_value - predicted
                    abs_error = abs(error)
                    pct_error = abs_error / actual_value
                    
                    errors.append(error)
                    absolute_errors.append(abs_error)
                    percentage_errors.append(pct_error)
                    predictions.append(predicted)
                    actuals.append(actual_value)
            
            if not absolute_errors:
                return {
                    'status': 'insufficient_data',
                    'message': 'Cannot compute metrics with zero/negative actual values',
                    'evaluation_period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
                    'sample_size': len(forecasts),
                }
            
            # Compute metrics
            mae = mean(absolute_errors)
            mape = mean(percentage_errors) * 100  # Convert to percentage
            rmse = (mean([e**2 for e in absolute_errors]) ** 0.5)
            bias = mean(errors)
            
            # Directional accuracy (did we predict direction correctly?)
            directional_correct = 0
            for i in range(len(actuals) - 1):
                actual_direction = 1 if actuals[i + 1] > actuals[i] else -1
                predicted_direction = 1 if predictions[i + 1] > predictions[i] else -1
                if actual_direction == predicted_direction:
                    directional_correct += 1
            
            directional_accuracy = (
                (directional_correct / (len(actuals) - 1) * 100) if len(actuals) > 1 else 0
            )
            
            # Build performance trend (daily MAPE)
            performance_trend = []
            for forecast_date, predicted, model_used, actual_value in forecasts:
                if actual_value and actual_value > 0:
                    abs_error = abs(actual_value - predicted)
                    daily_mape = (abs_error / actual_value) * 100
                    daily_mae = abs_error
                    performance_trend.append({
                        'date': forecast_date.isoformat(),
                        'mape': round(daily_mape, 2),
                        'mae': round(daily_mae, 2),
                    })
            
            # Find worst predictions (top 5)
            worst = []
            forecast_errors = []
            for forecast_date, predicted, model_used, actual_value in forecasts:
                if actual_value and actual_value > 0:
                    error_pct = abs(actual_value - predicted) / actual_value * 100
                    forecast_errors.append({
                        'date': forecast_date.isoformat(),
                        'predicted': round(predicted, 2),
                        'actual': round(actual_value, 2),
                        'error_pct': round(error_pct, 2),
                    })
            
            worst = sorted(forecast_errors, key=lambda x: x['error_pct'], reverse=True)[:5]
            
            model_name = list(model_names)[0] if model_names else "Unknown"
            
            return {
                'status': 'success',
                'model_name': model_name,
                'evaluation_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                },
                'sample_size': len(absolute_errors),
                'metrics': {
                    'mae': round(mae, 2),
                    'mape': round(mape, 2),
                    'rmse': round(rmse, 2),
                    'directional_accuracy': round(directional_accuracy, 2),
                    'bias': round(bias, 2),
                },
                'performance_trend': performance_trend,
                'worst_predictions': worst,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate forecasts: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Forecast evaluation failed: {str(e)}',
                'evaluation_period': {
                    'start': (datetime.now().date() - timedelta(days=days_back)).isoformat(),
                    'end': datetime.now().date().isoformat(),
                },
                'sample_size': 0,
            }

    def should_retrain(self, outlet_id: str, mape_threshold: float = 15.0, days_window: int = 7) -> Dict[str, Any]:
        """
        Determine if model should be retrained based on recent performance.
        
        Returns True if MAPE has exceeded threshold over the last N days,
        indicating the model's accuracy has degraded and retraining is needed.
        
        Args:
            outlet_id: Target outlet UUID
            mape_threshold: MAPE percentage threshold (default 15%)
            days_window: Number of days to evaluate (default 7)
        
        Returns:
            {
                'should_retrain': bool,
                'reason': str,
                'current_mape': float,
                'threshold': float,
                'recent_performance': float,
            }
        """
        try:
            # Evaluate recent performance
            evaluation = self.evaluate_past_forecasts(outlet_id, days_back=days_window)
            
            if evaluation.get('status') != 'success':
                return {
                    'should_retrain': False,
                    'reason': 'Insufficient data for retraining decision',
                    'current_mape': None,
                    'threshold': mape_threshold,
                }
            
            current_mape = evaluation['metrics']['mape']
            should_retrain = current_mape > mape_threshold
            
            reason = (
                f"MAPE {current_mape:.2f}% exceeds threshold {mape_threshold:.2f}%"
                if should_retrain
                else f"MAPE {current_mape:.2f}% is within acceptable range ({mape_threshold:.2f}% threshold)"
            )
            
            return {
                'should_retrain': should_retrain,
                'reason': reason,
                'current_mape': current_mape,
                'threshold': mape_threshold,
                'recent_performance': evaluation['metrics'],
                'sample_size': evaluation['sample_size'],
            }
            
        except Exception as e:
            self.logger.error(f"Failed to determine if retraining needed: {str(e)}", exc_info=True)
            return {
                'should_retrain': False,
                'reason': f'Could not assess retraining need: {str(e)}',
                'current_mape': None,
                'threshold': mape_threshold,
            }
