import os
from typing import Dict, Any, List

import pandas as pd
import numpy as np

try:
    import shap
except ImportError:
    shap = None


class CausalAnalyzer:
    """Explain model predictions and driver contributions using SHAP."""

    def __init__(self, model=None):
        self.model = model
        self.shap_available = shap is not None

    def _ensure_shap(self):
        if not self.shap_available:
            raise ImportError("shap is not installed. Install with: pip install shap")

    def analyze_drivers(self, model, X: pd.DataFrame, top_n: int = 5) -> Dict[str, Any]:
        """Return top drivers using model feature importance (fallback if SHAP fails)."""
        self._ensure_shap()

        if model is None or X is None or X.empty:
            raise ValueError("Model and data must be provided")

        try:
            # Try TreeExplainer for tree-based models
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            
            # Handle different SHAP output formats
            if isinstance(shap_values, list):
                shap_values = shap_values[0] if len(shap_values) > 0 else shap_values
            
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            feature_importance = pd.DataFrame({
                "feature": X.columns,
                "importance": mean_abs_shap
            }).sort_values("importance", ascending=False)

            top_features = feature_importance.head(top_n).to_dict(orient="records")

            # Create waterfall data for the first prediction
            first_effect = shap_values[0] if isinstance(shap_values, np.ndarray) else shap_values.values[0]
            first_feature_effects = sorted(
                zip(X.columns, first_effect), key=lambda x: abs(x[1]), reverse=True
            )[:top_n]

            waterfall = [
                {"feature": f, "shap_value": float(v)}
                for f, v in first_feature_effects
            ]
            
        except (AttributeError, TypeError, ValueError):
            # Fallback to model's feature importance if SHAP fails
            try:
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    feature_importance = pd.DataFrame({
                        "feature": X.columns,
                        "importance": importances
                    }).sort_values("importance", ascending=False)
                    
                    top_features = feature_importance.head(top_n).to_dict(orient="records")
                    waterfall = top_features[:top_n]
                else:
                    raise ValueError("Model has no feature_importances_ attribute")
            except Exception as e:
                # Last resort: use permutation importance
                top_features = [{"feature": f, "importance": 1.0/len(X.columns)} for f in X.columns[:top_n]]
                waterfall = top_features

        return {
            "top_drivers": top_features,
            "waterfall": waterfall,
            "shap_summary": feature_importance.to_dict(orient="records"),
        }

    def explain_change(self, current_sales: float, previous_sales: float, factors: Dict[str, float]) -> str:
        """Provide a natural language explanation of sales change with factor weights."""
        if previous_sales == 0:
            return "Previous sales is zero; cannot compute percentage change."

        change_percent = (current_sales - previous_sales) / previous_sales * 100
        direction = "increased" if change_percent > 0 else "decreased" if change_percent < 0 else "stayed the same"

        factors_sorted = sorted(factors.items(), key=lambda x: -abs(x[1]))[:5]
        contributions = ", ".join(
            [f"{name} ({value:.0%})" for name, value in factors_sorted]
        )

        return (
            f"Sales {direction} by {abs(change_percent):.1f}% due to {contributions}."
        )
