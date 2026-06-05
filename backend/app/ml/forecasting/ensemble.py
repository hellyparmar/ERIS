from typing import Dict, List
import numpy as np


class EnsembleForecaster:
    """Combine forecasts from multiple models and adapt weights."""

    def combine_predictions(
        self,
        prophet_pred: np.ndarray,
        xgb_pred: np.ndarray,
        weights: List[float] = [0.6, 0.4]
    ) -> np.ndarray:
        if len(prophet_pred) != len(xgb_pred):
            raise ValueError("Prediction arrays must have the same length")

        if len(weights) != 2 or sum(weights) <= 0:
            raise ValueError("Weights must be two positive values")

        weights = np.array(weights, dtype=float)
        weights = weights / weights.sum()
        combined = weights[0] * prophet_pred + weights[1] * xgb_pred
        combined = np.clip(combined, 0, None)
        return combined

    def select_best_model(
        self,
        prophet_metrics: Dict[str, float],
        xgb_metrics: Dict[str, float]
    ) -> str:
        # Prefer lower MAPE, then RMSE
        p_score = prophet_metrics.get("mape", float("inf")) * 0.7 + prophet_metrics.get("rmse", float("inf")) * 0.3
        x_score = xgb_metrics.get("mape", float("inf")) * 0.7 + xgb_metrics.get("rmse", float("inf")) * 0.3

        if p_score <= x_score:
            return "prophet"
        return "xgboost"

    def adaptive_weighting(
        self,
        recent_performance: List[Dict[str, float]]
    ) -> List[float]:
        """Adjust weights based on recent performance metrics."""
        if not recent_performance:
            return [0.6, 0.4]

        weight_prophet = 0.0
        weight_xgb = 0.0
        for item in recent_performance:
            p = item.get("prophet", {})
            x = item.get("xgboost", {})
            pv = 1.0 / (p.get("mape", 1e6) + 1e-9)
            xv = 1.0 / (x.get("mape", 1e6) + 1e-9)
            weight_prophet += pv
            weight_xgb += xv

        total = weight_prophet + weight_xgb
        if total == 0:
            return [0.6, 0.4]

        return [float(weight_prophet / total), float(weight_xgb / total)]
