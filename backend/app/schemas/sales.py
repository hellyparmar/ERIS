from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from enum import Enum
from uuid import UUID

class PaymentStatus(str, Enum):
    PAID = "paid"
    PARTIAL = "partial"
    PENDING = "pending"
    OVERDUE = "overdue"

class SaleItemBase(BaseModel):
    product_id: UUID
    quantity: int
    unit_price: Decimal

class SaleItemCreate(SaleItemBase):
    pass

class SaleItemResponse(SaleItemBase):
    id: UUID
    product_id: UUID
    line_total: Decimal

    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    customer_id: Optional[UUID] = None
    store_id: UUID
    discount: Decimal = Field(default=Decimal('0.0'))
    tax_amount: Decimal = Field(default=Decimal('0.0'))
    payment_method: str = "cash"

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]

    model_config = {
        "json_schema_extra": {
            "example": {
                "customer_id": "550e8400-e29b-41d4-a716-446655440001",
                "store_id": "550e8400-e29b-41d4-a716-446655440001",
                "discount": 5.0,
                "tax_amount": 2.5,
                "payment_method": "credit_card",
                "items": [
                    {"product_id": "550e8400-e29b-41d4-a716-446655440003", "quantity": 2, "unit_price": 50.0}
                ]
            }
        }
    }

class SaleResponse(SaleBase):
    id: UUID
    transaction_id: str
    transaction_date: datetime
    total_amount: Decimal
    payment_status: PaymentStatus
    items: List[SaleItemResponse]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 5001,
                "transaction_id": "TRX-A1B2C3D4",
                "transaction_date": "2024-03-24T10:30:00",
                "customer_id": "550e8400-e29b-41d4-a716-446655440001",
                "store_id": "550e8400-e29b-41d4-a716-446655440001",
                "total_amount": 97.5,
                "discount": 5.0,
                "tax_amount": 2.5,
                "payment_method": "credit_card",
                "payment_status": "paid",
                "items": [
                    {"id": "550e8400-e29b-41d4-a716-446655440002", "product_id": "550e8400-e29b-41d4-a716-446655440003", "quantity": 2, "unit_price": 50.0, "line_total": 100.0}
                ]
            }
        }
    }

class SalesAnalytics(BaseModel):
    total_sales: Decimal
    transaction_count: int
    average_order_value: Decimal
    top_categories: List[dict]
