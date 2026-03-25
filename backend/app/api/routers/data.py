"""
Enterprise Retail Intelligence System v3.0
DATA MANAGEMENT ROUTER

Endpoints for data upload and source management.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.api.schemas import UploadResponse, DataSourcesResponse, DataSource
from app.api.services.data_service import DataService
from datetime import datetime

router = APIRouter()
data_service = DataService()

@router.post("/data/upload/sales", response_model=UploadResponse)
async def upload_sales_data(file: UploadFile = File(...)):
    """
    Upload sales data from CSV file.
    
    File should contain columns: date, store_id, product_id, sales, quantity
    """
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV format")
        
        # Read file content
        contents = await file.read()
        
        # Process with data service
        result = await data_service.process_sales_upload(contents)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/upload/inventory", response_model=UploadResponse)
async def upload_inventory_data(file: UploadFile = File(...)):
    """
    Upload inventory data from CSV file.
    
    File should contain columns: date, store_id, product_id, stock_level
    """
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV format")
        
        contents = await file.read()
        result = await data_service.process_inventory_upload(contents)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/sources", response_model=DataSourcesResponse)
async def get_data_sources():
    """
    List all available data sources with metadata.
    """
    try:
        # Simulated data sources (in production, query from database)
        sources = [
            DataSource(
                name="Sales Data (Synthetic)",
                type="sales",
                last_updated=datetime.now(),
                row_count=18250
            ),
            DataSource(
                name="Inventory Data (Synthetic)",
                type="inventory",
                last_updated=datetime.now(),
                row_count=20
            )
        ]
        
        return DataSourcesResponse(sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
