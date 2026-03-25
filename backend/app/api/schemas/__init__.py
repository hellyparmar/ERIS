"""API Schemas Package"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

# ─── Analytics Schemas ──────────────────────────────────────────────────────
class Alert(BaseModel):
    """Single alert entry"""
    id: Optional[str] = None
    type: Optional[str] = None
    severity: str
    message: str
    timestamp: Optional[str] = None
    product: Optional[str] = None
    value: Optional[float] = None

class MetricsResponse(BaseModel):
    """Dashboard KPI metrics"""
    totalRevenue: Optional[float] = None
    avgDailySales: Optional[float] = None
    inventoryValue: Optional[float] = None
    stockoutRisk: Optional[float] = None
    alertCount: Optional[int] = 0
    criticalAlertCount: Optional[int] = 0
    model_config = {"extra": "allow"}

class AlertsResponse(BaseModel):
    """Response containing a list of alerts"""
    alerts: List[Alert] = []
    total: int = 0

class ChartDataPoint(BaseModel):
    """Single chart data point"""
    date: str
    actual: Optional[float] = None
    predicted: Optional[float] = None
    lowerBound: Optional[float] = None
    upperBound: Optional[float] = None

class ChartDataResponse(BaseModel):
    """Response containing chart data"""
    data: List[ChartDataPoint] = []
    metadata: Dict[str, Any] = {}

# Data Upload schemas
class DataSource(BaseModel):
    """Data source information"""
    name: str
    type: str
    connection_string: Optional[str] = None
    last_synced: Optional[datetime] = None

class DataSourcesResponse(BaseModel):
    """Response with data sources"""
    sources: List[DataSource]
    count: int

class UploadResponse(BaseModel):
    """Response for data upload"""
    status: str
    message: str
    rows_processed: int = 0
    errors: List[str] = []

# Model Service schemas
class ModelInfo(BaseModel):
    """Information about a trained model"""
    model_name: str
    model_type: str
    accuracy: float
    last_trained: Optional[datetime] = None
    version: str = "1.0"

class ModelsListResponse(BaseModel):
    """Response with list of models"""
    models: List[ModelInfo]
    count: int

class RetrainRequest(BaseModel):
    """Request to retrain a model"""
    model_name: str
    data_source: str
    force_retrain: bool = False

class RetrainResponse(BaseModel):
    """Response for retrain operation"""
    success: bool
    message: str
    model_name: str
    training_status: str
    estimated_time_minutes: Optional[int] = None

class TrainingStatus(BaseModel):
    """Training status information"""
    model_name: str
    status: str  # "pending", "training", "completed", "failed"
    progress_percent: int = 0
    message: str = ""
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None

# Prediction schemas
class PredictionPoint(BaseModel):
    """Single prediction data point"""
    date: str
    value: float
    confidence_lower: float
    confidence_upper: float

class SalesPredictionRequest(BaseModel):
    """Request for sales prediction"""
    store_id: str
    product_name: Optional[str] = None
    start_date: datetime
    end_date: datetime
    forecast_days: int = 30

class SalesPredictionResponse(BaseModel):
    """Response for sales prediction"""
    store_id: str
    product_name: Optional[str]
    predictions: List[PredictionPoint]
    model_accuracy: float
    confidence_level: str

class StockoutPredictionRequest(BaseModel):
    """Request for stockout prediction"""
    store_id: str
    product_name: str
    current_stock: int
    daily_consumption: float

class StockoutPredictionResponse(BaseModel):
    """Response for stockout prediction"""
    store_id: str
    product_name: str
    days_until_stockout: int
    recommendation: str
    urgency: str

# RLS schemas
try:
    from app.api.schemas.rls import (
        AccessTypeEnum,
        RLSExceptionCreate,
        RLSExceptionResponse,
        RLSViolationEntry,
        RLSViolationReport,
        RLSTableStatus,
        RLSStatusReport,
        RLSContextInfo,
        RLSValidationResult,
        RLSCleanupResult,
    )
except ImportError:
    pass

__all__ = [
    # Data schemas
    "DataSource",
    "DataSourcesResponse",
    "UploadResponse",
    # Model schemas
    "ModelInfo",
    "ModelsListResponse",
    "RetrainRequest",
    "RetrainResponse",
    "TrainingStatus",
    # Prediction schemas
    "PredictionPoint",
    "SalesPredictionRequest",
    "SalesPredictionResponse",
    "StockoutPredictionRequest",
    "StockoutPredictionResponse",
    # RLS schemas
    "AccessTypeEnum",
    "RLSExceptionCreate",
    "RLSExceptionResponse",
    "RLSViolationEntry",
    "RLSViolationReport",
    "RLSTableStatus",
    "RLSStatusReport",
    "RLSContextInfo",
    "RLSValidationResult",
    "RLSCleanupResult",
]
