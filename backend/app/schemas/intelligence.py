from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SalesForecast(BaseModel):
    date: datetime = Field(..., description="Target date for the forecast")
    predicted_sales: float = Field(..., description="Estimated sales amount")
    lower_bound: float = Field(..., description="Lower bound of the confidence interval")
    upper_bound: float = Field(..., description="Upper bound of the confidence interval")
    confidence: float = Field(..., description="Confidence level (e.g., 0.95)")
    trend: str = Field(..., description="Trend direction: up, down, or stable")

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2024-03-25T00:00:00",
                "predicted_sales": 15200.50,
                "lower_bound": 14000.00,
                "upper_bound": 16500.00,
                "confidence": 0.95,
                "trend": "up"
            }
        }
    }

class ForecastRequest(BaseModel):
    days_ahead: int = Field(..., ge=1, le=30, description="Number of days to forecast into the future")
    confidence_level: float = Field(0.95, ge=0.8, le=0.99, description="Statistical confidence level")

    model_config = {
        "json_schema_extra": {
            "example": {
                "days_ahead": 7,
                "confidence_level": 0.95
            }
        }
    }

class SalesAnomalyAlert(BaseModel):
    id: int
    alert_type: str = Field(..., description="Type of anomaly: unusual_spike, unusual_drop, pattern_deviation")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    message: str
    detected_value: float
    expected_value: float
    deviation_percent: float
    timestamp: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1001,
                "alert_type": "unusual_spike",
                "severity": "high",
                "message": "Sales spike detected: 155,000 (Z-score: 2.85)",
                "detected_value": 155000.0,
                "expected_value": 125000.0,
                "deviation_percent": 24.0,
                "timestamp": "2024-03-24T10:00:00"
            }
        }
    }

class ForecastResponse(BaseModel):
    forecasts: List[SalesForecast]
    model: str = "ARIMA(1,1,1)"
    last_trained: datetime
    accuracy_score: float
    timestamp: datetime

class AnomalyResponse(BaseModel):
    anomalies: List[SalesAnomalyAlert]
    total_alerts: int
    critical_count: int
    timestamp: datetime

class InsightItem(BaseModel):
    title: str
    description: str
    impact: str
    action: str

class RecommendationItem(BaseModel):
    id: int
    category: str
    priority: str
    message: str
    expected_impact: str
