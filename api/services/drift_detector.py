
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class DriftReport:
    """Report on model drift status"""
    is_drifted: bool
    current_mape: float
    baseline_mape: float
    drift_magnitude: float
    timestamp: str
    recommendation: str

class DriftDetector:
    """
    Detects Concept Drift in forecasting models by monitoring error rates over time.
    Uses 'Performance-Based Drift Detection' strategy.
    """
    
    def __init__(self, baseline_mape: float = 13.24, threshold_factor: float = 1.2):
        """
        Args:
            baseline_mape: The validated MAPE from training (e.g., 13.24%)
            threshold_factor: Multiplier for acceptable degradation (e.g., 1.2x = 20% worse)
        """
        self.baseline_mape = baseline_mape
        self.threshold = baseline_mape * threshold_factor
    
    def calculate_mape(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate MAPE for new data"""
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        # Avoid division by zero
        mask = y_true != 0
        return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    def check_drift(self, recent_data: pd.DataFrame) -> DriftReport:
        """
        Check for drift using recent actuals vs predictions.
        
        Args:
            recent_data: DataFrame with columns ['actual', 'predicted']
            
        Returns:
            DriftReport
        """
        if len(recent_data) < 7:
            return DriftReport(
                is_drifted=False,
                current_mape=0.0,
                baseline_mape=self.baseline_mape,
                drift_magnitude=0.0,
                timestamp=datetime.now().isoformat(),
                recommendation="Insufficient data for drift check (need 7+ days)"
            )
            
        current_mape = self.calculate_mape(recent_data['actual'], recent_data['predicted'])
        
        is_drifted = current_mape > self.threshold
        drift_magnitude = current_mape - self.baseline_mape
        
        recommendation = "Model is stable."
        if is_drifted:
            recommendation = "CRITICAL: Model performance degraded. Trigger retraining immediately."
        elif current_mape > (self.baseline_mape * 1.1):
            recommendation = "WARNING: Minor degradation detected. Monitor closely."
            
        return DriftReport(
            is_drifted=is_drifted,
            current_mape=round(current_mape, 2),
            baseline_mape=self.baseline_mape,
            drift_magnitude=round(drift_magnitude, 2),
            timestamp=datetime.now().isoformat(),
            recommendation=recommendation
        )

# Example usage
if __name__ == "__main__":
    detector = DriftDetector(baseline_mape=13.24)
    
    # Simulate data
    print("--- Drift Detection Test ---")
    
    # CASE 1: Stable
    stable_data = pd.DataFrame({
        'actual': [100, 102, 98, 105, 100, 99, 101],
        'predicted': [101, 100, 100, 102, 101, 100, 100]
    })
    report = detector.check_drift(stable_data)
    print(f"\nCase 1 (Stable): {report.recommendation} (MAPE: {report.current_mape}%)")
    
    # CASE 2: Drifted
    drifted_data = pd.DataFrame({
        'actual': [150, 160, 155, 158, 152, 165, 170], # Demand spike/shift
        'predicted': [100, 102, 98, 105, 100, 99, 101] # Old model predictions
    })
    report = detector.check_drift(drifted_data)
    print(f"\nCase 2 (Drifted): {report.recommendation} (MAPE: {report.current_mape}%)")
