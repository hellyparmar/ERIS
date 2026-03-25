from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DashboardMetrics(BaseModel):
    total_sales: float = Field(..., description="Sum of all sales in the specified period")
    total_orders: int = Field(..., description="Count of all transactions")
    average_order_value: float = Field(..., description="Total sales divided by total orders")
    top_products: List[Dict[str, Any]] = Field(default_factory=list, description="Top 10 performing products")
    pending_orders: List[Dict[str, Any]] = Field(default_factory=list, description="Orders awaiting processing or delivery")
    daily_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Sales and order counts day-by-day")
    timestamp: datetime = Field(default_factory=datetime.now, description="Data generation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_sales": 125000.50,
                "total_orders": 245,
                "average_order_value": 510.20,
                "top_products": [{"id": 1, "name": "Coffee", "revenue": 4500.0}],
                "pending_orders": [{"id": 1001, "status": "Packed"}],
                "daily_trend": [{"date": "2024-03-24", "sales": 15000.0}],
                "timestamp": "2024-03-24T12:00:00"
            }
        }
    }

class TopProductsResponse(BaseModel):
    id: int
    name: str
    quantity_sold: int
    revenue: float
    last_sold: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 101,
                "name": "Arabica Coffee Beans",
                "quantity_sold": 85,
                "revenue": 3825.0,
                "last_sold": "2024-03-24T10:30:00"
            }
        }
    }

class PendingOrderResponse(BaseModel):
    id: int
    customer_name: str
    total_amount: float
    status: str
    created_at: datetime
    expected_delivery: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 5002,
                "customer_name": "Jane Smith",
                "total_amount": 120.0,
                "status": "Processing",
                "created_at": "2024-03-24T09:00:00",
                "expected_delivery": "2024-03-25T17:00:00"
            }
        }
    }

class SalesMetricsResponse(BaseModel):
    period: str
    total_sales: float
    total_transactions: int
    average_transaction_value: float
    growth_rate: float
    peak_hour: Optional[str] = None
    timestamp: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "daily",
                "total_sales": 125000.50,
                "total_transactions": 245,
                "average_transaction_value": 510.20,
                "growth_rate": 12.5,
                "peak_hour": "2 PM - 3 PM",
                "timestamp": "2024-03-24T12:00:00"
            }
        }
    }

class CategoryRevenue(BaseModel):
    category: str
    revenue: float
    percentage: float

class RevenueByCategoryResponse(BaseModel):
    period_days: int
    categories: List[CategoryRevenue]
    total_revenue: float
    timestamp: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "period_days": 30,
                "categories": [
                    {"category": "Beverages", "revenue": 45000, "percentage": 36.0}
                ],
                "total_revenue": 125000,
                "timestamp": "2024-03-24T12:00:00"
            }
        }
    }

class CustomerInsightsResponse(BaseModel):
    total_customers: int
    new_customers_today: int
    repeat_customers: int
    repeat_rate: float
    average_customer_value: float
    customer_satisfaction: float
    timestamp: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_customers": 5432,
                "new_customers_today": 145,
                "repeat_customers": 2134,
                "repeat_rate": 39.3,
                "average_customer_value": 23.0,
                "customer_satisfaction": 4.5,
                "timestamp": "2024-03-24T12:00:00"
            }
        }
    }
