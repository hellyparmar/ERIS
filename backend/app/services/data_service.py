"""
Enterprise Retail Intelligence System v3.0
DATA SERVICE

Service for data processing, validation, and CSV upload handling.
"""

import pandas as pd
import io
from app.api.schemas import UploadResponse
from pathlib import Path
import os
from sqlalchemy.orm import Session

class DataService:
    """Service for data processing and validation."""
    
    def __init__(self):
        self.data_dir = Path(os.getenv('DATA_DIR', '../data'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_sales_upload(self, file_content: bytes) -> UploadResponse:
        """Process uploaded sales CSV file."""
        try:
            # Read CSV
            df = pd.read_csv(io.BytesIO(file_content))
            
            # Basic validation
            required_cols = ['date', 'store_id', 'product_id', 'sales']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                return UploadResponse(
                    rows_processed=0,
                    validation_errors=[f"Missing required columns: {', '.join(missing_cols)}"],
                    status="failed"
                )
            
            # Process data
            rows_processed = len(df)
            validation_errors = []
            
            # Check for null values
            null_counts = df[required_cols].isnull().sum()
            for col, count in null_counts.items():
                if count > 0:
                    validation_errors.append(f"Column '{col}' has {count} null values")
            
            # Save processed data (in production, save to database)
            output_path = self.data_dir / f"sales_upload_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_path, index=False)
            
            status = "success" if not validation_errors else "partial"
            
            return UploadResponse(
                rows_processed=rows_processed,
                validation_errors=validation_errors,
                status=status
            )
        except Exception as e:
            return UploadResponse(
                rows_processed=0,
                validation_errors=[str(e)],
                status="failed"
            )
    
    async def process_inventory_upload(self, file_content: bytes) -> UploadResponse:
        """Process uploaded inventory CSV file."""
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            
            required_cols = ['date', 'store_id', 'product_id', 'stock_level']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                return UploadResponse(
                    rows_processed=0,
                    validation_errors=[f"Missing required columns: {', '.join(missing_cols)}"],
                    status="failed"
                )
            
            rows_processed = len(df)
            validation_errors = []
            
            # Check for negative stock levels
            if (df['stock_level'] < 0).any():
                validation_errors.append("Found negative stock levels")
            
            # Save processed data
            output_path = self.data_dir / f"inventory_upload_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_path, index=False)
            
            status = "success" if not validation_errors else "partial"
            
            return UploadResponse(
                rows_processed=rows_processed,
                validation_errors=validation_errors,
                status=status
            )
        except Exception as e:
            return UploadResponse(
                rows_processed=0,
                validation_errors=[str(e)],
                status="failed"
            )
            
    async def process_economic_indicators_upload(self, file_content: bytes, db_session: Session) -> UploadResponse:
        """Process uploaded economic indicators CSV file."""
        try:
            from app.models.external_factors_models import EconomicIndicatorHistory
            df = pd.read_csv(io.BytesIO(file_content))
            
            required_cols = ['date', 'cpi_inflation', 'wpi_inflation', 'food_inflation', 'repo_rate']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                return UploadResponse(
                    rows_processed=0,
                    validation_errors=[f"Missing required columns: {', '.join(missing_cols)}"],
                    status="failed"
                )
            
            df['date'] = pd.to_datetime(df['date']).dt.date
            rows_processed = 0
            validation_errors = []
            
            for _, row in df.iterrows():
                try:
                    existing = db_session.query(EconomicIndicatorHistory).filter(EconomicIndicatorHistory.date == row['date']).first()
                    if existing:
                        existing.cpi_inflation = row['cpi_inflation']
                        existing.wpi_inflation = row['wpi_inflation']
                        existing.food_inflation = row['food_inflation']
                        existing.repo_rate = row['repo_rate']
                    else:
                        new_record = EconomicIndicatorHistory(
                            date=row['date'],
                            cpi_inflation=row['cpi_inflation'],
                            wpi_inflation=row['wpi_inflation'],
                            food_inflation=row['food_inflation'],
                            repo_rate=row['repo_rate']
                        )
                        db_session.add(new_record)
                    rows_processed += 1
                except Exception as e:
                    validation_errors.append(f"Row error on {row['date']}: {str(e)}")
                    
            db_session.commit()
            
            status = "success" if not validation_errors else "partial"
            return UploadResponse(
                rows_processed=rows_processed,
                validation_errors=validation_errors,
                status=status
            )
        except Exception as e:
            if db_session:
                db_session.rollback()
            return UploadResponse(
                rows_processed=0,
                validation_errors=[str(e)],
                status="failed"
            )
