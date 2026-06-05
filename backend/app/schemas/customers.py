from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, Field
import re

class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{9,14}$")
    city: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Basic check already handled by pattern, but could add more logic here
        return v

class CustomerCreate(CustomerBase):
    organization_id: UUID = Field(..., description="Organization ID owning the customer")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+12345678901",
                "city": "Mumbai",
                "organization_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    }

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int
    loyalty_points: int
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+12345678901",
                "city": "Mumbai",
                "customer_code": "CUST-A1B2C3",
                "loyalty_points": 150,
                "created_at": "2024-03-24T10:00:00"
            }
        }
    }

class PurchaseHistoryItem(BaseModel):
    sale_id: int
    transaction_date: datetime
    total_amount: Decimal
    items_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "sale_id": 5001,
                "transaction_date": "2024-03-24T10:30:00",
                "total_amount": 97.5,
                "items_count": 2
            }
        }
    }
