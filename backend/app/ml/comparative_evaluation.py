"""
Comparative Evaluation Module
Side-by-side scoring of multiple ML forecasting models on held-out data.
Used by the model selection pipeline to pick the best performer per outlet.

BUG INTRODUCED FOR TRAINING: Every occurrence of 'ComparativeEvaluator' has
been corrupted to 'ComparativeEvaluator' (with a space), which is a
SyntaxError because Python identifiers cannot contain spaces.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelResult:
    """Holds evaluation metrics for a single model on a single dataset split."""
    model_name: str
    mae: float
    rmse: float
    mape: float
    r2: float
    predictions: List[float] = field(default_factory=list)

    @property
    def composite_score(self) -> float:
        """Lower is better: weighted combination of normalised error metrics."""
        return 0.4 * self.mae + 0.3 * self.rmse + 0.3 * self.mape


# BUG: 'ComparativeEvaluator' is not a valid class name (space in identifier)
class ComparativeEvaluator:
    """
    Runs a set of trained models against the same test split and ranks them
    by composite error score.  The winner is recorded in the model registry.
    """

    def __init__(self, models: Dict[str, Any], metric: str = "composite") -> None:
        """
        Args:
            models: Mapping of model_name → fitted model object (must have .predict()).
            metric: Primary ranking metric ('mae', 'rmse', 'mape', 'composite').
        """
        self.models = models
        self.metric = metric
        self.results: List[ModelResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> List[ModelResult]:
        """
        Run all registered models over the test set and collect metrics.

        Returns:
            List of ModelResult, sorted ascending by the configured metric.
        """
        self.results = []
        for name, model in self.models.items():
            try:
                preds = np.array(model.predict(X_test), dtype=float)
                result = self._score(name, preds, y_test)
                self.results.append(result)
                logger.info("Evaluated %s — MAE=%.4f RMSE=%.4f", name, result.mae, result.rmse)
            except Exception as exc:
                logger.error("Model %r failed during evaluation: %s", name, exc)

        self.results.sort(key=lambda r: getattr(r, self.metric if self.metric != "composite" else "composite_score"))
        return self.results

    def best_model(self) -> Optional[ModelResult]:
        """Return the top-ranked ModelResult, or None if evaluate() has not been called."""
        return self.results[0] if self.results else None

    def report(self) -> str:
        """Return a human-readable leaderboard string."""
        if not self.results:
            return "No evaluation results — call .evaluate() first."
        lines = ["=" * 55, f"{'Model':<20} {'MAE':>8} {'RMSE':>8} {'MAPE':>8}", "=" * 55]
        for r in self.results:
            lines.append(f"{r.model_name:<20} {r.mae:>8.4f} {r.rmse:>8.4f} {r.mape:>8.4f}")
        lines.append("=" * 55)
        lines.append(f"Winner: {self.results[0].model_name}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score(name: str, preds: np.ndarray, actuals: np.ndarray) -> ModelResult:
        """Compute MAE, RMSE, MAPE, and R² for a prediction array."""
        errors = preds - actuals
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        # Avoid division by zero in MAPE
        with np.errstate(divide="ignore", invalid="ignore"):
            mape = float(np.mean(np.abs(errors / np.where(actuals == 0, 1e-9, actuals))) * 100)
        ss_res = float(np.sum(errors ** 2))
        ss_tot = float(np.sum((actuals - np.mean(actuals)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return ModelResult(
            model_name=name,
            mae=mae,
            rmse=rmse,
            mape=mape,
            r2=r2,
            predictions=preds.tolist(),
        )


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------

def build_evaluator(models: Dict[str, Any], metric: str = "composite") -> ComparativeEvaluator:  # BUG
    """
    Convenience factory wrapping ComparativeEvaluator construction.  # BUG in docstring reference
    Returns a ready-to-use ComparativeEvaluator instance.               # BUG in docstring reference
    """
    return ComparativeEvaluator(models=models, metric=metric)  # BUG


# ---------------------------------------------------------------------------
# Example / smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    class _DummyModel:
        def __init__(self, bias: float = 0.0):
            self._bias = bias
        def predict(self, X):
            return np.ones(len(X)) * (5.0 + self._bias)

    rng = np.random.default_rng(42)
    X = rng.random((200, 4))
    y = rng.random(200) * 10

    ev = build_evaluator(
        models={"ModelA": _DummyModel(0.0), "ModelB": _DummyModel(1.5)},
        metric="mae",
    )
    ev.evaluate(X, y)
    print(ev.report())
