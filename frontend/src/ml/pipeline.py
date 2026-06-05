"""
Enterprise Retail Intelligence System v3.0
ML PIPELINE - ORCHESTRATOR

End-to-end machine learning pipeline integrating:
- Data loading (MultiDatasetLoader)
- Feature engineering (RetailFeatureEngineer)
- Model training (BaselineModel)
- Evaluation & serialization

Author: R-DIOS Team
Version: 3.0.0
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import local modules
import sys
sys.path.append('src')

from data import MultiDatasetLoader
from features.processor import RetailFeatureEngineer
from ml.models import BaselineModel, calculate_metrics, print_metrics


class MLPipeline:
    """
    Complete ML pipeline for retail demand forecasting.
    
    Pipeline Steps:
    1. Load data from multiple sources
    2. Engineer features (time-series, lags, rolling)
    3. Split data (temporal train/val/test)
    4. Train model (baseline or advanced)
    5. Evaluate performance
    6. Save artifacts (model, metrics, predictions)
    """
    
    def __init__(
        self,
        data_dir: str = "data",
        model_dir: str = "models",
        random_state: int = 42
    ):
        """
        Initialize ML pipeline.
        
        Args:
            data_dir (str): Directory for data storage
            model_dir (str): Directory for model storage
            random_state (int): Random seed for reproducibility
        """
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.random_state = random_state
        np.random.seed(random_state)
        
        # Initialize components
        self.loader = MultiDatasetLoader(data_dir=data_dir)
        self.feature_engineer = RetailFeatureEngineer()
        self.model = None
        
        # Data storage
        self.raw_data = None
        self.engineered_data = None
        self.train_data = None
        self.val_data = None
        self.test_data = None
        
        print("="*80)
        print("R-DIOS ML PIPELINE v3.0")
        print("="*80)
        print(f"✅ Data directory: {self.data_dir.absolute()}")
        print(f"✅ Model directory: {self.model_dir.absolute()}")
        print(f"✅ Random seed: {random_state}")
    
    # ============================================================================
    # STEP 1: DATA LOADING
    # ============================================================================
    
    def load_data(
        self,
        sales_path: Optional[str] = None,
        inventory_path: Optional[str] = None,
        use_sample: bool = False
    ) -> pd.DataFrame:
        """
        Load and merge data from multiple sources.
        
        Args:
            sales_path (str): Path to sales CSV file
            inventory_path (str): Path to inventory CSV file
            use_sample (bool): Generate synthetic sample data
            
        Returns:
            pd.DataFrame: Merged training dataset
        """
        print("\n" + "="*80)
        print("STEP 1: DATA LOADING")
        print("="*80)
        
        if use_sample:
            print("\n📝 Generating synthetic sample data...")
            self.raw_data = self._generate_sample_data()
        else:
            # Load from files
            if sales_path is None:
                raise ValueError("sales_path required when use_sample=False")
            
            sales_df = self.loader.load_local_csv(sales_path, 'sales')
            inventory_df = None
            
            if inventory_path:
                inventory_df = self.loader.load_local_csv(inventory_path, 'inventory')
            
            self.raw_data = self.loader.get_training_set(
                sales_df=sales_df,
                inventory_df=inventory_df
            )
        
        print(f"\n✅ Data loaded: {self.raw_data.shape}")
        print(f"   Date range: {self.raw_data['date'].min()} to {self.raw_data['date'].max()}")
        print(f"   Stores: {self.raw_data['store_id'].nunique()}")
        print(f"   Products: {self.raw_data['product_id'].nunique()}")
        
        return self.raw_data
    
    def _generate_sample_data(self, n_days: int = 365, n_stores: int = 5, n_products: int = 10):
        """Generate synthetic retail data for testing."""
        dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
        
        data = []
        for store_id in range(1, n_stores + 1):
            for product_id in range(1, n_products + 1):
                for date in dates:
                    # Simulate realistic sales patterns
                    base_sales = 100
                    weekend_boost = 30 if date.dayofweek >= 5 else 0
                    monthly_trend = date.month * 5
                    seasonal = 20 * np.sin(2 * np.pi * date.dayofyear / 365)
                    noise = np.random.normal(0, 15)
                    
                    sales = max(0, base_sales + weekend_boost + monthly_trend + seasonal + noise)
                    
                    data.append({
                        'date': date,
                        'store_id': f'STORE_{store_id}',
                        'product_id': f'PROD_{product_id}',
                        'sales': sales,
                        'quantity': max(1, int(sales / 10)),
                        'stock_level': max(0, 500 - sales * 2 + np.random.normal(0, 50))
                    })
        
        df = pd.DataFrame(data)
        print(f"   Generated {len(df)} records")
        return df
    
    # ============================================================================
    # STEP 2: FEATURE ENGINEERING
    # ============================================================================
    
    def engineer_features(
        self,
        include_lags: bool = True,
        include_rolling: bool = True
    ) -> pd.DataFrame:
        """
        Apply feature engineering transformations.
        
        Args:
            include_lags (bool): Include lag features
            include_rolling (bool): Include rolling window features
            
        Returns:
            pd.DataFrame: Engineered dataset
        """
        print("\n" + "="*80)
        print("STEP 2: FEATURE ENGINEERING")
        print("="*80)
        
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        self.engineered_data = self.feature_engineer.transform(
            self.raw_data,
            fit=True,
            include_lags=include_lags,
            include_rolling=include_rolling
        )
        
        # Drop rows with NaN values (from lag features)
        rows_before = len(self.engineered_data)
        self.engineered_data = self.engineered_data.dropna()
        rows_dropped = rows_before - len(self.engineered_data)
        
        if rows_dropped > 0:
            pct_dropped = (rows_dropped / rows_before) * 100
            print(f"\n🗑️  Dropped {rows_dropped} rows with NaN values ({pct_dropped:.1f}%)")
        
        print(f"\n✅ Feature engineering complete: {self.engineered_data.shape}")
        
        return self.engineered_data
    
    # ============================================================================
    # STEP 3: DATA SPLITTING
    # ============================================================================
    
    def split_data(
        self,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train/val/test sets (temporal split).
        
        Args:
            train_ratio (float): Proportion for training
            val_ratio (float): Proportion for validation
            test_ratio (float): Proportion for testing
            
        Returns:
            Tuple: (train_df, val_df, test_df)
        """
        print("\n" + "="*80)
        print("STEP 3: DATA SPLITTING (Temporal)")
        print("="*80)
        
        if self.engineered_data is None:
            raise ValueError("No engineered data. Call engineer_features() first.")
        
        # Sort by date first
        df = self.engineered_data.sort_values('date').reset_index(drop=True)
        
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        self.train_data = df.iloc[:train_end]
        self.val_data = df.iloc[train_end:val_end]
        self.test_data = df.iloc[val_end:]
        
        print(f"\n📊 Split Summary:")
        print(f"   Training:   {len(self.train_data):6d} rows ({train_ratio*100:.0f}%)")
        print(f"   Validation: {len(self.val_data):6d} rows ({val_ratio*100:.0f}%)")
        print(f"   Test:       {len(self.test_data):6d} rows ({test_ratio*100:.0f}%)")
        
        print(f"\n📅 Date Ranges:")
        print(f"   Train: {self.train_data['date'].min()} to {self.train_data['date'].max()}")
        print(f"   Val:   {self.val_data['date'].min()} to {self.val_data['date'].max()}")
        print(f"   Test:  {self.test_data['date'].min()} to {self.test_data['date'].max()}")
        
        return self.train_data, self.val_data, self.test_data
    
    # ============================================================================
    # STEP 4: MODEL TRAINING
    # ============================================================================
    
    def train_model(
        self,
        model_type: str = 'random_forest',
        target_col: str = 'sales_log',
        **model_params
    ) -> Dict:
        """
        Train forecasting model.
        
        Args:
            model_type (str): Type of model ('random_forest', 'gradient_boosting')
            target_col (str): Target column name
            **model_params: Model-specific hyperparameters
            
        Returns:
            Dict: Training metrics
        """
        print("\n" + "="*80)
        print("STEP 4: MODEL TRAINING")
        print("="*80)
        
        if self.train_data is None:
            raise ValueError("No training data. Call split_data() first.")
        
        # Get feature names (exclude metadata and target)
        feature_cols = self.feature_engineer.get_feature_names(self.train_data)
        
        # Prepare training data
        X_train = self.train_data[feature_cols]
        y_train = self.train_data[target_col]
        
        X_val = self.val_data[feature_cols]
        y_val = self.val_data[target_col]
        
        # Initialize and train model
        self.model = BaselineModel(model_type=model_type, **model_params)
        metrics = self.model.train(X_train, y_train, X_val, y_val)
        
        return metrics
    
    # ============================================================================
    # STEP 5: EVALUATION
    # ============================================================================
    
    def evaluate(self, dataset: str = 'test') -> Dict:
        """
        Evaluate model on specified dataset.
        
        Args:
            dataset (str): One of 'train', 'val', 'test'
            
        Returns:
            Dict: Evaluation metrics
        """
        print("\n" + "="*80)
        print(f"STEP 5: EVALUATION ({dataset.upper()} SET)")
        print("="*80)
        
        if self.model is None:
            raise ValueError("No trained model. Call train_model() first.")
        
        # Select dataset
        if dataset == 'train':
            data = self.train_data
        elif dataset == 'val':
            data = self.val_data
        elif dataset == 'test':
            data = self.test_data
        else:
            raise ValueError(f"Unknown dataset: {dataset}")
        
        # Get features
        feature_cols = self.feature_engineer.get_feature_names(data)
        X = data[feature_cols]
        y_true = data['sales_log'].values
        
        # Predict
        y_pred = self.model.predict(X)
        
        # Calculate metrics
        metrics = calculate_metrics(y_true, y_pred)
        print_metrics(metrics, dataset_name=dataset.capitalize())
        
        return metrics
    
    # ============================================================================
    # STEP 6: MODEL PERSISTENCE
    # ============================================================================
    
    def save_pipeline(self, name: str = "retail_forecaster"):
        """
        Save complete pipeline (model + feature engineer).
        
        Args:
            name (str): Base name for saved files
        """
        print("\n" + "="*80)
        print("STEP 6: SAVING PIPELINE")
        print("="*80)
        
        # Save model
        model_path = self.model_dir / f"{name}_model.pkl"
        self.model.save(model_path)
        
        # Save feature engineer
        import joblib
        engineer_path = self.model_dir / f"{name}_feature_engineer.pkl"
        joblib.dump(self.feature_engineer, engineer_path)
        print(f"✅ Feature engineer saved to: {engineer_path}")
        
        print(f"\n✅ Pipeline saved successfully!")
    
    def run_full_pipeline(
        self,
        sales_path: Optional[str] = None,
        model_type: str = 'random_forest',
        use_sample: bool = True
    ) -> Dict:
        """
        Run complete end-to-end pipeline.
        
        Args:
            sales_path (str): Path to sales data
            model_type (str): Model type
            use_sample (bool): Use synthetic sample data
            
        Returns:
            Dict: Final evaluation metrics
        """
        # Step 1: Load data
        self.load_data(sales_path=sales_path, use_sample=use_sample)
        
        # Step 2: Engineer features
        self.engineer_features()
        
        # Step 3: Split data
        self.split_data()
        
        # Step 4: Train model
        self.train_model(model_type=model_type)
        
        # Step 5: Evaluate
        test_metrics = self.evaluate('test')
        
        # Step 6: Save
        self.save_pipeline()
        
        return test_metrics


if __name__ == "__main__":
    print("R-DIOS ML Pipeline Module v3.0")
    print("Ready for end-to-end training")
