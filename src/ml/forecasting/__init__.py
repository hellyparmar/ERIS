"""
ML Forecasting Package
Thesis ML Pipeline for Demand Forecasting
"""

from pathlib import Path

# Package info
__version__ = "1.0.0"
__author__ = "R-DIOS Team"

# Ensure data directories exist
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
MODELS_DIR = Path(__file__).parent / "saved_models"

DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
