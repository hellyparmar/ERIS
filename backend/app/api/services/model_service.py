"""
Enterprise Retail Intelligence System v3.0
MODEL SERVICE

Singleton service for loading and managing ML models.
Thread-safe model caching and access.
"""

import os
import joblib
from pathlib import Path
from datetime import datetime
from threading import Lock
from typing import Optional, Dict
from app.api.schemas import ModelInfo

class ModelService:
    """Singleton service for ML model management."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.model_dir = Path(os.getenv('MODEL_DIR', '../models'))
        self.models = {}
        self._load_models()
        self._initialized = True
    
    def _load_models(self):
        """Load all available models from disk."""
        if not self.model_dir.exists():
            print(f"Warning: Model directory {self.model_dir} does not exist")
            return
        
        # Load retail forecaster model
        model_path = self.model_dir / "retail_forecaster_model.pkl"
        if model_path.exists():
            try:
                self.models['retail_forecaster'] = joblib.load(model_path)
                print(f"✅ Loaded model: retail_forecaster")
            except Exception as e:
                print(f"❌ Failed to load {model_path}: {e}")
    
    def get_model(self, name: str):
        """Get a loaded model by name."""
        return self.models.get(name)
    
    def get_models_info(self) -> list[ModelInfo]:
        """Get information about all loaded models."""
        models_info = []
        
        # Check for trained models
        if self.model_dir.exists():
            model_path = self.model_dir / "retail_forecaster_model.pkl"
            if model_path.exists():
                # Get file modification time
                mtime = datetime.fromtimestamp(model_path.stat().st_mtime)
                
                models_info.append(ModelInfo(
                    name="retail_forecaster",
                    type="random_forest",
                    accuracy=0.9814,  # From training results
                    rmse=0.0185,
                    mae=0.0156,
                    last_trained=mtime,
                    feature_count=23
                ))
        
        return models_info
    
    def reload_model(self, name: str):
        """Reload a specific model from disk."""
        model_path =self.model_dir / f"{name}_model.pkl"
        if model_path.exists():
            try:
                self.models[name] = joblib.load(model_path)
                print(f"✅ Reloaded model: {name}")
                return True
            except Exception as e:
                print(f"❌ Failed to reload {name}: {e}")
                return False
        return False
