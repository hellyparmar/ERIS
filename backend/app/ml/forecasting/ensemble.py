from typing import Dict, List
import numpy as np


class EnsembleForecaster:
    """Combine forecasts from multiple models and adapt weights."""

    def combine_predictions(
        self,
        prophet_pred: np.ndarray,
        xgb_pred: np.ndarray,
        lstm_pred: np.ndarray,
        weights: List[float] = [0.4, 0.3, 0.3]
    ) -> np.ndarray:
        if not (len(prophet_pred) == len(xgb_pred) == len(lstm_pred)):
            raise ValueError("Prediction arrays must have the same length")

        if len(weights) != 3 or sum(weights) <= 0:
            raise ValueError("Weights must be three positive values")

        weights = np.array(weights, dtype=float)
        weights = weights / weights.sum()
        combined = weights[0] * prophet_pred + weights[1] * xgb_pred + weights[2] * lstm_pred
        combined = np.clip(combined, 0, None)
        return combined

    def adaptive_weighting(
        self,
        metrics: Dict[str, Dict[str, float]]
    ) -> List[float]:
        """Calculate weights based on validation MAPE (inverse-error weighting)."""
        if not metrics:
            return [0.4, 0.3, 0.3]

        p = metrics.get("prophet", {})
        x = metrics.get("xgboost", {})
        l = metrics.get("lstm", {})

        # Use 1e6 for missing or failed models
        p_mape = p.get("mape")
        x_mape = x.get("mape")
        l_mape = l.get("mape")

        # If a model failed to generate a valid MAPE (e.g. PyTorch not available), assign near zero weight
        pv = 1.0 / (p_mape + 1e-9) if p_mape is not None and not np.isnan(p_mape) else 0.0
        xv = 1.0 / (x_mape + 1e-9) if x_mape is not None and not np.isnan(x_mape) else 0.0
        lv = 1.0 / (l_mape + 1e-9) if l_mape is not None and not np.isnan(l_mape) else 0.0

        total = pv + xv + lv
        if total == 0:
            return [0.4, 0.3, 0.3]

        return [float(pv / total), float(xv / total), float(lv / total)]
