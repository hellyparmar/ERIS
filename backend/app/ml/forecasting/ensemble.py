from typing import Dict, List, Optional
import numpy as np


class EnsembleForecaster:
    """Combine forecasts from multiple models and adapt weights."""

    def combine_predictions(
        self,
        prophet_pred: np.ndarray,
        xgb_pred: np.ndarray,
        weights: Optional[List[float]] = None,
    ) -> np.ndarray:
        if len(prophet_pred) != len(xgb_pred):
            raise ValueError("Prediction arrays must have the same length")

        weights = weights or [0.5, 0.5]
        if len(weights) != 2 or any(weight < 0 for weight in weights) or sum(weights) <= 0:
            raise ValueError("Weights must contain two positive values")

        weights = np.array(weights, dtype=float)
        weights = weights / weights.sum()
        combined = weights[0] * prophet_pred + weights[1] * xgb_pred
        combined = np.clip(combined, 0, None)
        return combined

    def adaptive_weighting(self, metrics: Dict[str, Dict[str, float]]) -> List[float]:
        """Calculate weights based on validation MAPE (inverse-error weighting)."""
        if not metrics:
            return [0.5, 0.5]

        p = metrics.get("prophet", {})
        x = metrics.get("xgboost", {})

        # Use 1e6 for missing or failed models
        p_mape = p.get("mape")
        x_mape = x.get("mape")

        # If a model failed to generate a valid MAPE (e.g. PyTorch not available), assign near zero weight
        pv = 1.0 / (p_mape + 1e-9) if p_mape is not None and not np.isnan(p_mape) else 0.0
        xv = 1.0 / (x_mape + 1e-9) if x_mape is not None and not np.isnan(x_mape) else 0.0
        total = pv + xv
        if total == 0:
            return [0.5, 0.5]

        return [float(pv / total), float(xv / total)]
