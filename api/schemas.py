"""
Enterprise Retail Intelligence System v3.0
PYDANTIC SCHEMAS

Request/response validation models for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date, datetime

# ============================================================================
# PREDICTION SCHEMAS
# ============================================================================

class SalesPredictionRequest(BaseModel):
    store_id: str = Field(..., example="STORE_1")
    product_id: str = Field(..., example="PROD_001")
    start_date: date = Field(..., example="2024-01-01")
    end_date: date = Field(..., example="2024-01-30")

class PredictionPoint(BaseModel):
    date: str
    predicted: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence: Optional[float] = None

class SalesPredictionResponse(BaseModel):
    predictions: List[PredictionPoint]
    metadata: Dict = Field(default_factory=dict)

class StockoutPredictionRequest(BaseModel):
    store_id: str
    product_id: str

class StockoutPredictionResponse(BaseModel):
    days_to_stockout: int
    risk_level: str  # "critical", "warning", "healthy"
    current_stock: float
    daily_consumption: float
    recommendation: str

# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class MetricsResponse(BaseModel):
    totalRevenue: float
    avgDailySales: float
    totalOrders: int
    totalCustomers: int
    inventoryValue: float
    stockoutRisk: float
    growthRate: float
    alertCount: int
    criticalAlertCount: int

class Alert(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    recommendation: Optional[str] = None
    daysToStockout: Optional[int] = None
    productId: Optional[str] = None
    productName: Optional[str] = None
    timestamp: datetime

class AlertsResponse(BaseModel):
    alerts: List[Alert]
    total: int

class ChartDataPoint(BaseModel):
    date: str
    actual: Optional[float] = None
    predicted: Optional[float] = None
    lowerBound: Optional[float] = None
    upperBound: Optional[float] = None

class ChartDataResponse(BaseModel):
    data: List[ChartDataPoint]
    metadata: Dict = Field(default_factory=dict)

# ============================================================================
# DATA MANAGEMENT SCHEMAS
# ============================================================================

class UploadResponse(BaseModel):
    rows_processed: int
    validation_errors: List[str] = Field(default_factory=list)
    status: str  # "success", "partial", "failed"

class DataSource(BaseModel):
    name: str
    type: str  # "sales", "inventory", "macro"
    last_updated: Optional[datetime] = None
    row_count: int

class DataSourcesResponse(BaseModel):
    sources: List[DataSource]

# ============================================================================
# MODEL MANAGEMENT SCHEMAS
# ============================================================================

class ModelInfo(BaseModel):
    name: str
    type: str  # "random_forest", "gradient_boosting"
    accuracy: float  # R² score
    rmse: float
    mae: float
    last_trained: datetime
    feature_count: int

class ModelsListResponse(BaseModel):
    models: List[ModelInfo]

class RetrainRequest(BaseModel):
    model_type: str = Field(..., example="random_forest")
    dataset_id: Optional[str] = None
    hyperparameters: Dict = Field(default_factory=dict)

class RetrainResponse(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    message: str

class TrainingStatus(BaseModel):
    job_id: str
    status: str
    progress: float  # 0.0 to 1.0
    metrics: Optional[Dict] = None
    error: Optional[str] = None
