"""
True SHAP Integration for Model Explainability
Week 13: Real SHAP values instead of approximations

This module provides comprehensive SHAP-based model explanations:
- TreeExplainer for tree-based models (Prophet, XGBoost, RandomForest)
- KernelExplainer for model-agnostic explanations
- DeepExplainer for neural network models (LSTM)
- Summary plots and individual prediction explanations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from pathlib import Path
import json
from datetime import datetime

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Install with: pip install shap")

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """
    Unified SHAP explainer for different model types
    Automatically selects appropriate explainer based on model type
    """
    
    def __init__(self, model: Any, model_type: str = 'auto'):
        """
        Args:
            model: The model to explain (Prophet, XGBoost, RandomForest, LSTM, etc.)
            model_type: Type of model - 'prophet', 'xgboost', 'tree', 'kernel', 'auto'
        """
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP not installed. Run: pip install shap")
        
        self.model = model
        self.model_type = model_type
        self.explainer = None
        self.feature_names = None
        self.X_background = None  # Background data for explainer
        self.explanations_cache: Dict[str, Any] = {}
        
        logger.info(f"Initialized SHAPExplainer for {model_type}")
    
    def set_background_data(self, X: np.ndarray, max_samples: int = 100) -> None:
        """
        Set background data for SHAP explainer
        
        Args:
            X: Feature data (n_samples, n_features)
            max_samples: Maximum samples to use (SHAP is computationally expensive)
        """
        if len(X) > max_samples:
            # Sample randomly for efficiency
            indices = np.random.choice(len(X), max_samples, replace=False)
            self.X_background = X[indices]
        else:
            self.X_background = X
        
        logger.info(f"Set background data: {self.X_background.shape}")
    
    def set_feature_names(self, names: List[str]) -> None:
        """Set feature names for interpretability"""
        self.feature_names = names
    
    def _create_tree_explainer(self, X: np.ndarray) -> None:
        """Create TreeExplainer for tree-based models"""
        try:
            # Check if model has predict method and tree structure
            if hasattr(self.model, 'booster'):  # XGBoost
                self.explainer = shap.TreeExplainer(self.model)
            elif hasattr(self.model, 'estimators_'):  # RandomForest, GradientBoosting
                self.explainer = shap.TreeExplainer(self.model)
            else:
                logger.warning("Could not create TreeExplainer, falling back to KernelExplainer")
                self._create_kernel_explainer(X)
            
            logger.info("✓ Created TreeExplainer")
        except Exception as e:
            logger.error(f"TreeExplainer failed: {str(e)}, using KernelExplainer")
            self._create_kernel_explainer(X)
    
    def _create_kernel_explainer(self, X: np.ndarray) -> None:
        """Create KernelExplainer for model-agnostic explanations"""
        try:
            if self.X_background is None:
                self.set_background_data(X)
            
            self.explainer = shap.KernelExplainer(
                model=self.model.predict if hasattr(self.model, 'predict') else self.model,
                data=shap.sample(self.X_background, min(100, len(self.X_background)))
            )
            logger.info("✓ Created KernelExplainer")
        except Exception as e:
            logger.error(f"KernelExplainer failed: {str(e)}")
            self.explainer = None
    
    def _create_deep_explainer(self, X: np.ndarray) -> None:
        """Create DeepExplainer for neural networks"""
        try:
            if self.X_background is None:
                self.set_background_data(X)
            
            # Requires model to be a PyTorch or TensorFlow model
            self.explainer = shap.DeepExplainer(
                self.model,
                self.X_background
            )
            logger.info("✓ Created DeepExplainer")
        except Exception as e:
            logger.warning(f"DeepExplainer failed: {str(e)}, using KernelExplainer")
            self._create_kernel_explainer(X)
    
    def create_explainer(self, X: np.ndarray, model_type: str = None) -> None:
        """
        Create appropriate SHAP explainer based on model type
        
        Args:
            X: Feature data for background/reference
            model_type: Override the model type if needed
        """
        if model_type:
            self.model_type = model_type
        
        # Set background data if not already set
        if self.X_background is None:
            self.set_background_data(X)
        
        # Select explainer based on model type
        if self.model_type in ['auto', 'tree', 'xgboost', 'random_forest', 'gradient_boosting']:
            self._create_tree_explainer(X)
        
        elif self.model_type in ['kernel', 'prophet', 'statsmodels']:
            self._create_kernel_explainer(X)
        
        elif self.model_type in ['deep', 'lstm', 'neural', 'torch', 'tensorflow']:
            self._create_deep_explainer(X)
        
        else:
            logger.warning(f"Unknown model type: {self.model_type}, using KernelExplainer")
            self._create_kernel_explainer(X)
    
    def explain_instance(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
        as_dict: bool = False
    ) -> Union[np.ndarray, Dict[str, Any]]:
        """
        Get SHAP values for instance(s)
        
        Args:
            X: Single instance (1D) or batch (2D)
            feature_names: Feature names for output
            as_dict: Return as dictionary format
        
        Returns:
            SHAP values or formatted explanation dictionary
        """
        if self.explainer is None:
            raise ValueError("Explainer not initialized. Call create_explainer() first.")
        
        # Ensure 2D input
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        # Calculate SHAP values
        try:
            shap_values = self.explainer.shap_values(X)
            
            # Handle SHAP output format (can be list of arrays for multi-output)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # First output
            
            if as_dict:
                return self._format_shap_explanation(
                    shap_values,
                    X,
                    feature_names or self.feature_names
                )
            else:
                return shap_values
        
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {str(e)}")
            return None
    
    def _format_shap_explanation(
        self,
        shap_values: np.ndarray,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Format SHAP values into human-readable explanation
        
        Args:
            shap_values: SHAP values from explainer
            X: Feature values
            feature_names: Names of features
        
        Returns:
            Dictionary with explanation details
        """
        if len(shap_values.shape) > 1:
            shap_values = shap_values[0]  # First instance
        
        n_features = len(shap_values)
        if feature_names is None:
            feature_names = [f"Feature_{i}" for i in range(n_features)]
        
        # Get base value (expected model output)
        base_value = self.explainer.expected_value
        if isinstance(base_value, (list, np.ndarray)):
            base_value = base_value[0]
        
        # Sort by absolute SHAP value
        importance_order = np.argsort(np.abs(shap_values))[::-1]
        
        # Create explanation
        explanation = {
            'base_value': float(base_value),
            'features': []
        }
        
        for idx in importance_order[:10]:  # Top 10 features
            feature = {
                'name': feature_names[idx],
                'value': float(X[0][idx]),
                'shap_value': float(shap_values[idx]),
                'contribution': 'increases' if shap_values[idx] > 0 else 'decreases'
            }
            explanation['features'].append(feature)
        
        return explanation
    
    def global_explanation(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Get global feature importance from SHAP values
        
        Args:
            X: Feature data (entire dataset or sample)
            feature_names: Feature names
            top_k: Number of top features to return
        
        Returns:
            Global feature importance explanation
        """
        if self.explainer is None:
            raise ValueError("Explainer not initialized.")
        
        # Calculate SHAP values for all instances
        try:
            shap_values = self.explainer.shap_values(X)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            
            # Mean absolute SHAP value = global importance
            importance = np.abs(shap_values).mean(axis=0)
            
            # Sort by importance
            importance_order = np.argsort(importance)[::-1]
            
            if feature_names is None:
                feature_names = [f"Feature_{i}" for i in range(len(importance))]
            
            # Create summary
            explanation = {
                'method': 'SHAP Mean Absolute Value',
                'features': []
            }
            
            for idx in importance_order[:top_k]:
                explanation['features'].append({
                    'rank': len(explanation['features']) + 1,
                    'name': feature_names[idx],
                    'importance': float(importance[idx]),
                    'importance_pct': float(100 * importance[idx] / importance.sum())
                })
            
            return explanation
        
        except Exception as e:
            logger.error(f"Error in global explanation: {str(e)}")
            return None
    
    def save_explanation(self, explanation: Dict, filepath: str) -> None:
        """Save explanation to JSON"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(explanation, f, indent=2)
        logger.info(f"Saved explanation to {filepath}")
    
    def create_summary_plot_data(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
        plot_type: str = 'bar'
    ) -> Dict[str, Any]:
        """
        Create data for SHAP summary plot (can be visualized with matplotlib/plotly)
        
        Args:
            X: Feature data
            feature_names: Feature names
            plot_type: 'bar' or 'beeswarm'
        
        Returns:
            Plot data dictionary
        """
        if self.explainer is None:
            raise ValueError("Explainer not initialized.")
        
        try:
            shap_values = self.explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            
            if feature_names is None:
                feature_names = [f"Feature_{i}" for i in range(shap_values.shape[1])]
            
            # Calculate mean absolute SHAP values
            mean_shap = np.abs(shap_values).mean(axis=0)
            importance_order = np.argsort(mean_shap)[::-1]
            
            plot_data = {
                'type': plot_type,
                'features': [feature_names[i] for i in importance_order[:15]],
                'importance': [float(mean_shap[i]) for i in importance_order[:15]]
            }
            
            if plot_type == 'beeswarm':
                # Include individual values
                plot_data['details'] = {}
                for i in importance_order[:10]:
                    plot_data['details'][feature_names[i]] = {
                        'values': [float(v) for v in shap_values[:, i]],
                        'feature_values': [float(v) for v in X[:, i]]
                    }
            
            return plot_data
        
        except Exception as e:
            logger.error(f"Error creating plot data: {str(e)}")
            return None


class ExplainableForecaster:
    """
    Wrapper around forecaster models with SHAP explanations
    """
    
    def __init__(self, forecaster: Any, model_type: str = 'prophet'):
        """
        Args:
            forecaster: Forecaster model (Prophet, XGBoost, etc.)
            model_type: Type of model for SHAP explainer selection
        """
        self.forecaster = forecaster
        self.explainer = SHAPExplainer(forecaster, model_type)
        self.explanations: Dict[str, Any] = {}
    
    def predict_with_explanation(
        self,
        X: np.ndarray,
        steps: int = 30,
        explain: bool = True
    ) -> Tuple[pd.DataFrame, Optional[Dict]]:
        """
        Make prediction and generate SHAP explanation
        
        Args:
            X: Feature data
            steps: Forecast steps
            explain: Whether to generate explanation
        
        Returns:
            Tuple of (forecast_df, explanation_dict)
        """
        # Get prediction
        forecast = self.forecaster.predict(steps)
        
        # Get explanation if requested
        explanation = None
        if explain and len(X.shape) == 1:
            X = X.reshape(1, -1)
            explanation = self.explainer.explain_instance(X, as_dict=True)
        
        return forecast, explanation
    
    def get_forecast_drivers(
        self,
        feature_names: List[str],
        X_train: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get global feature importance explaining what drives forecasts
        
        Args:
            feature_names: Names of features
            X_train: Training features for SHAP background
        
        Returns:
            Global explanation dictionary
        """
        self.explainer.set_feature_names(feature_names)
        self.explainer.create_explainer(X_train)
        
        # Get global explanation
        explanation = self.explainer.global_explanation(
            X_train,
            feature_names=feature_names,
            top_k=10
        )
        
        return explanation


# Example usage
if __name__ == "__main__":
    print("✓ SHAP Integration ready")
    print("\nExample usage:")
    print("""
    # With XGBoost or tree-based model
    explainer = SHAPExplainer(model, model_type='xgboost')
    explainer.set_background_data(X_train)
    explainer.create_explainer(X_train)
    
    # For single prediction
    explanation = explainer.explain_instance(X_test[0], as_dict=True)
    
    # For global importance
    global_exp = explainer.global_explanation(X_train, feature_names)
    
    # With forecaster
    ex_forecaster = ExplainableForecaster(prophet_model, 'prophet')
    forecast, explanation = ex_forecaster.predict_with_explanation(X)
    drivers = ex_forecaster.get_forecast_drivers(feature_names, X_train)
    """)
