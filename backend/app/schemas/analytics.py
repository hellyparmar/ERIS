from pydantic import BaseModel, Field
from typing import List, Optional

class MetricData(BaseModel):
    totalRevenue: float = Field(..., description="Total revenue for the organization")
    avgDailySales: float = Field(..., description="Average daily sales volume over the last 30 days")
    inventoryValue: float = Field(..., description="Total value of current inventory based on cost price")
    stockoutRisk: float = Field(..., description="Count of products at risk of stockout")
    alertCount: int = Field(0, description="Number of unacknowledged alerts")
    criticalAlertCount: int = Field(0, description="Number of critical unacknowledged alerts")

    model_config = {
        "json_schema_extra": {
            "example": {
                "totalRevenue": 1250000.50,
                "avgDailySales": 4500.0,
                "inventoryValue": 85000.0,
                "stockoutRisk": 12.0,
                "alertCount": 5,
                "criticalAlertCount": 1
            }
        }
    }

class AlertItem(BaseModel):
    id: int = Field(..., description="Unique ID of the alert")
    severity: str = Field(..., description="Severity level (critical, warning, info)")
    message: str = Field(..., description="Descriptive alert message")
    timestamp: str = Field(..., description="ISO 8601 timestamp of when the alert was created")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 101,
                "severity": "critical",
                "message": "Stock for Product 'Laptop Pro' is critically low (2 remaining).",
                "timestamp": "2024-03-24T10:30:00Z"
            }
        }
    }

class AlertsResponse(BaseModel):
    alerts: List[AlertItem] = Field(..., description="List of unacknowledged alerts")
    total: int = Field(..., description="Total count of alerts returned")

    model_config = {
        "json_schema_extra": {
            "example": {
                "alerts": [
                    {
                        "id": 101,
                        "severity": "critical",
                        "message": "Stock low",
                        "timestamp": "2024-03-24T10:30:00Z"
                    }
                ],
                "total": 1
            }
        }
    }

class ChartPoint(BaseModel):
    date: str = Field(..., description="The date for this data point (YYYY-MM-DD)")
    actual: Optional[float] = Field(None, description="Actual sales value recorded")
    predicted: Optional[float] = Field(None, description="Predicted sales value from AI model")
    lowerBound: Optional[float] = Field(None, description="Lower bound of the prediction interval")
    upperBound: Optional[float] = Field(None, description="Upper bound of the prediction interval")

class ChartDataResponse(BaseModel):
    data: List[ChartPoint] = Field(..., description="Time-series data for historical and forecasted sales")
    metadata: dict = Field(..., description="Additional context about the query parameters")

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"date": "2024-03-01", "actual": 5000.0, "predicted": None},
                    {"date": "2024-04-01", "actual": None, "predicted": 5200.0, "lowerBound": 4800.0, "upperBound": 5600.0}
                ],
                "metadata": {
                    "historical_days": 30,
                    "forecast_days": 15,
                    "organization_id": "org_123"
                }
            }
        }
    }
