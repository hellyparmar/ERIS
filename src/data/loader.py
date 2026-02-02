"""
Enterprise Retail Intelligence System v3.0
R-DIOS MULTI-DATASET LOADER

Centralized data ingestion engine for the 5-Layer R-DIOS Architecture:
- Layer 1: Sales (Retail Grocery + Store Sales Favorita)
- Layer 2: Inventory Forecasting
- Layer 3: Customer Behavior
- Layer 4: Macroeconomic (Census Bureau + India Gov)
- Layer 5: Validation (UCI + AdventureWorks)

Author: R-DIOS Team
Version: 3.0.0
"""

import pandas as pd
import numpy as np
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import local modules
from .harmonizer import SchemaHarmonizer
from .schemas import (
    SalesDataSchema,
    InventoryDataSchema,
    MacroDataSchema,
    TrainingDataSchema,
    validate_dataframe
)


class MultiDatasetLoader:
    """
    Centralized data loading and harmonization engine.
    
    Responsibilities:
    - Load data from multiple sources (Kaggle, APIs, local files)
    - Harmonize heterogeneous schemas
    - Merge layers for ML training
    - Cache processed data for performance
    """
    
    def __init__(self, data_dir: str = "data", cache_enabled: bool = True):
        """
        Initialize data loader.
        
        Args:
            data_dir (str): Directory for storing datasets
            cache_enabled (bool): Enable/disable caching
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_enabled = cache_enabled
        self.cache = {}
        
        self.harmonizer = SchemaHarmonizer()
        
        print(f"✅ MultiDatasetLoader initialized")
        print(f"   Data directory: {self.data_dir.absolute()}")
        print(f"   Cache enabled: {cache_enabled}")
    
    # ============================================================================
    # LAYER 4: MACROECONOMIC DATA (US Census Bureau)
    # ============================================================================
    
    def load_census_data(
        self, 
        url: str = "https://www.census.gov/retail/mrts/www/mrtssales92-present.csv",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Load retail sales data from US Census Bureau.
        
        The Census Bureau provides monthly retail sales data from 1992-present.
        This serves as an external macroeconomic indicator for the model.
        
        Args:
            url (str): Census Bureau data URL
            use_cache (bool): Use cached version if available
            
        Returns:
            pd.DataFrame: Harmonized census data
        """
        cache_key = "census_data"
        
        # Check cache
        if use_cache and self.cache_enabled and cache_key in self.cache:
            print("📦 Loading census data from cache...")
            return self.cache[cache_key].copy()
        
        print(f"\n🌐 Fetching data from US Census Bureau...")
        print(f"   URL: {url}")
        
        try:
            # Download data
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            print(f"   ✅ Downloaded {len(df)} rows, {len(df.columns)} columns")
            
            # Basic processing (Census data has specific format)
            # Typically has columns like: Period, NAICS, Value
            # We'll harmonize to our macro schema
            
            # Rename columns if needed (Census-specific logic)
            if 'Period' in df.columns:
                df = df.rename(columns={'Period': 'date'})
            if 'NAICS' in df.columns:
                df = df.rename(columns={'NAICS': 'indicator_name'})
            if 'Value' in df.columns:
                df = df.rename(columns={'Value': 'value'})
            
            # Add region
            df['region'] = 'USA'
            
            # Harmonize schema
            df = self.harmonizer.harmonize_schema(df, 'macro')
            
            # Validate schema
            df = validate_dataframe(df, MacroDataSchema, "Census Bureau Data")
            
            # Cache result
            if self.cache_enabled:
                self.cache[cache_key] = df.copy()
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Failed to fetch census data: {e}")
            print(f"   💡 Tip: Check internet connection or try again later")
            raise
        except Exception as e:
            print(f"   ❌ Error processing census data: {e}")
            raise
    
    # ============================================================================
    # LAYER 1 & 2: LOCAL/KAGGLE DATASETS
    # ============================================================================
    
    def load_local_csv(
        self,
        file_path: str,
        source_type: str,
        validate: bool = True,
        **read_csv_kwargs
    ) -> pd.DataFrame:
        """
        Load and harmonize data from local CSV file.
        
        Args:
            file_path (str): Path to CSV file
            source_type (str): One of 'sales', 'inventory', 'macro'
            validate (bool): Validate against schema
            **read_csv_kwargs: Additional arguments for pd.read_csv()
            
        Returns:
            pd.DataFrame: Harmonized dataframe
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        print(f"\n📂 Loading {source_type} data from local file...")
        print(f"   File: {file_path.name}")
        
        # Read CSV
        df = pd.read_csv(file_path, **read_csv_kwargs)
        print(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Harmonize schema
        df = self.harmonizer.harmonize_schema(df, source_type)
        
        # Validate schema
        if validate:
            if source_type == 'sales':
                df = validate_dataframe(df, SalesDataSchema, f"Local CSV: {file_path.name}")
            elif source_type == 'inventory':
                df = validate_dataframe(df, InventoryDataSchema, f"Local CSV: {file_path.name}")
            elif source_type == 'macro':
                df = validate_dataframe(df, MacroDataSchema, f"Local CSV: {file_path.name}")
        
        return df
    
    def load_kaggle_dataset(
        self,
        dataset_name: str,
        file_name: str,
        source_type: str,
        force_download: bool = False
    ) -> pd.DataFrame:
        """
        Load dataset from Kaggle (requires kaggle API credentials).
        
        Setup instructions:
        1. Create account at kaggle.com
        2. Go to Account → API → Create New API Token
        3. Place kaggle.json in ~/.kaggle/
        
        Args:
            dataset_name (str): Kaggle dataset slug (e.g., 'user/dataset-name')
            file_name (str): Specific file to load from dataset
            source_type (str): One of 'sales', 'inventory', 'macro'
            force_download (bool): Re-download even if file exists
            
        Returns:
            pd.DataFrame: Harmonized dataframe
        """
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
        except ImportError:
            raise ImportError(
                "Kaggle API not installed. Install with: pip install kaggle"
            )
        
        print(f"\n📊 Loading {source_type} data from Kaggle...")
        print(f"   Dataset: {dataset_name}")
        print(f"   File: {file_name}")
        
        # Initialize Kaggle API
        api = KaggleApi()
        api.authenticate()
        
        # Create download directory
        download_dir = self.data_dir / "kaggle" / dataset_name.replace('/', '_')
        download_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = download_dir / file_name
        
        # Download if needed
        if force_download or not file_path.exists():
            print(f"   ⬇️  Downloading from Kaggle...")
            api.dataset_download_file(
                dataset_name,
                file_name,
                path=download_dir
            )
            print(f"   ✅ Download complete")
        else:
            print(f"   📦 Using cached file")
        
        # Load the CSV
        return self.load_local_csv(file_path, source_type)
    
    # ============================================================================
    # DATA MERGING & TRAINING SET CREATION
    # ============================================================================
    
    def get_training_set(
        self,
        sales_df: pd.DataFrame,
        inventory_df: Optional[pd.DataFrame] = None,
        macro_df: Optional[pd.DataFrame] = None,
        merge_strategy: str = "left"
    ) -> pd.DataFrame:
        """
        Merge sales, inventory, and macro data into ML-ready training set.
        
        Merge Logic:
        - Primary: Sales data (every row is a sale)
        - Secondary: Inventory data (left join on date, store, product)
        - Tertiary: Macro data (left join on date only)
        
        Args:
            sales_df (pd.DataFrame): Sales data (required)
            inventory_df (pd.DataFrame): Inventory data (optional)
            macro_df (pd.DataFrame): Macroeconomic data (optional)
            merge_strategy (str): Pandas merge strategy ('left', 'inner')
            
        Returns:
            pd.DataFrame: Merged training dataset
        """
        print("\n🔗 Merging datasets for training...")
        print(f"   Sales data: {len(sales_df)} rows")
        
        # Start with sales data
        df = sales_df.copy()
        
        # Rename 'revenue' to 'sales' if needed (for consistency with feature engineering)
        if 'revenue' in df.columns and 'sales' not in df.columns:
            df = df.rename(columns={'revenue': 'sales'})
        
        # Merge inventory data
        if inventory_df is not None:
            print(f"   Inventory data: {len(inventory_df)} rows")
            
            merge_keys = ['date', 'store_id', 'product_id']
            df = df.merge(
                inventory_df[merge_keys + ['stock_level']],
                on=merge_keys,
                how=merge_strategy,
                suffixes=('', '_inv')
            )
            print(f"   ✅ After inventory merge: {len(df)} rows")
        
        # Merge macro data (only on date, broadcast to all rows)
        if macro_df is not None:
            print(f"   Macro data: {len(macro_df)} rows")
            
            # Pivot macro data (one row per date, columns = indicators)
            macro_pivot = macro_df.pivot_table(
                index='date',
                columns='indicator_name',
                values='value',
                aggfunc='first'
            ).reset_index()
            
            # Rename columns to avoid conflicts
            macro_pivot.columns = ['date'] + [
                f'macro_{col}' for col in macro_pivot.columns[1:]
            ]
            
            df = df.merge(
                macro_pivot,
                on='date',
                how='left'
            )
            print(f"   ✅ After macro merge: {len(df)} rows, {len(df.columns)} columns")
        
        # Validate final training schema
        try:
            df = validate_dataframe(df, TrainingDataSchema, "Training Set")
        except Exception as e:
            print(f"   ⚠️  Warning: Training set validation failed: {e}")
            print(f"   Proceeding without strict validation...")
        
        # Sort by date
        df = df.sort_values(['date', 'store_id', 'product_id']).reset_index(drop=True)
        
        print(f"\n✅ Training set ready!")
        print(f"   Final shape: {df.shape}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Unique stores: {df['store_id'].nunique()}")
        print(f"   Unique products: {df['product_id'].nunique()}")
        
        return df
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def clear_cache(self):
        """Clear in-memory cache."""
        self.cache = {}
        print("🗑️  Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            'enabled': self.cache_enabled,
            'items': len(self.cache),
            'keys': list(self.cache.keys())
        }
    
    def list_local_files(self, pattern: str = "*.csv") -> List[Path]:
        """
        List available local data files.
        
        Args:
            pattern (str): Glob pattern for file matching
            
        Returns:
            List[Path]: List of matching files
        """
        files = list(self.data_dir.rglob(pattern))
        print(f"\n📁 Found {len(files)} files matching '{pattern}':")
        for f in files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"   • {f.relative_to(self.data_dir)} ({size_mb:.2f} MB)")
        return files


# ============================================================================
# STANDALONE USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("R-DIOS Multi-Dataset Loader v3.0")
    print("="*80)
    
    # Initialize loader
    loader = MultiDatasetLoader(data_dir="data")
    
    # Example: Load census data (requires internet)
    try:
        census_df = loader.load_census_data()
        print(f"\n📊 Census Data Preview:")
        print(census_df.head())
    except Exception as e:
        print(f"\n⚠️  Could not load census data: {e}")
    
    # List local files
    loader.list_local_files()
    
    print("\n" + "="*80)
    print("✅ Loader ready for data ingestion")
    print("="*80)
