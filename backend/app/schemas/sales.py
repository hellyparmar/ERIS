"""Request and response schemas for manual sales entry."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)


class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    outlet_id: int
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    payment_method: str = Field(default="cash", pattern="^(cash|card|upi|netbanking|wallet|credit)$")
    items: List[SaleItemCreate] = Field(min_length=1)


class SaleItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class SaleResponse(BaseModel):
    id: int
    sale_number: str
    sale_date: datetime
    customer_id: Optional[int]
    outlet_id: int
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_method: str
    payment_status: str
    status: str
    items: List[SaleItemResponse]

    model_config = {"from_attributes": True}


class SalesAnalytics(BaseModel):
    total_sales: Decimal
    transaction_count: int
    average_order_value: Decimal
    top_categories: List[dict]
