"""
baseline_validation.py
Validates that current model performance is within acceptable bounds
relative to a previously recorded baseline stored in baseline_results.json.

Run:  python -m backend.scripts.baseline_validation
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

BASELINE_FILE = Path(__file__).parent / "baseline_results.json"

# Thresholds — if current metric exceeds baseline by more than this %, fail
TOLERANCE = {
    "mae": 0.10,   # 10 % degradation allowed
    "rmse": 0.10,
    "mape": 0.15,
}


def load_baseline(path: Path = BASELINE_FILE) -> Optional[Dict]:
    """Load the baseline metrics JSON.  Returns None if the file does not exist."""
    if not path.exists():
        logger.warning("Baseline file not found at %s — skipping comparison", path)
        return None
    with path.open() as fh:
        return json.load(fh)


def save_baseline(metrics: Dict, path: Path = BASELINE_FILE) -> None:
    """Persist the current metrics as the new baseline."""
    with path.open("w") as fh:
        json.dump(metrics, fh, indent=2)
    logger.info("Baseline saved to %s", path)


def validate(current: Dict, baseline: Dict) -> bool:
    """
    Compare *current* metrics against *baseline*.
    Returns True if all metrics are within tolerance, False otherwise.
    """
    passed = True
    for metric, tolerance in TOLERANCE.items():
        base_val = baseline.get(metric)
        curr_val = current.get(metric)
        if base_val is None or curr_val is None:
            continue
        delta = (curr_val - base_val) / max(abs(base_val), 1e-9)
        if delta > tolerance:
            logger.error(
                "FAIL %s: current=%.4f baseline=%.4f degradation=%.1f%% (limit %.0f%%)",
                metric, curr_val, base_val, delta * 100, tolerance * 100,
            )
            passed = False
        else:
            logger.info("OK   %s: current=%.4f baseline=%.4f Δ=%.1f%%",
                        metric, curr_val, base_val, delta * 100)
    return passed


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # Simulate fetching current evaluation metrics (replace with real eval call)
    current_metrics = {"mae": 0.312, "rmse": 0.447, "mape": 4.21}

    baseline = load_baseline()
    if baseline is None:
        save_baseline(current_metrics)
        # BUG FIXED: added closing " before the closing paren
        print("No prior baseline found. Current metrics saved as the new baseline.")
        return 0

    ok = validate(current_metrics, baseline)
    if ok:
        print("Baseline validation PASSED — all metrics within tolerance.")
        save_baseline(current_metrics)
        return 0
    else:
        print("Baseline validation FAILED — see log for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
