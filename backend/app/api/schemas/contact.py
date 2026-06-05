"""
Pydantic schemas for Business Contacts Management endpoints
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID


class ContactType(str, Enum):
    SUPPLIER = "supplier"
    DISTRIBUTOR = "distributor"
    LOGISTICS = "logistics"


# ==================== BUSINESS CONTACT ====================

class BusinessContactCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    contact_person: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=20)
    email: str = Field(..., min_length=5, max_length=255)
    gst_number: Optional[str] = Field(None, min_length=15, max_length=15)
    address: str = Field(..., min_length=10, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    contact_type: ContactType
    product_categories: List[str] = Field(default_factory=list)


class BusinessContactUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    contact_type: Optional[ContactType] = None
    product_categories: Optional[List[str]] = None
    is_active: Optional[bool] = None


class BusinessContactResponse(BaseModel):
    contact_id: UUID
    company_name: str
    contact_person: str
    phone: str
    email: str
    gst_number: Optional[str]
    address: str
    city: str
    contact_type: str
    product_categories: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BusinessContactListResponse(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    items: List[BusinessContactResponse]


class InvoiceHistorySummary(BaseModel):
    total_invoices: int
    total_amount: float
    paid_amount: float
    pending_amount: float
    overdue_amount: float
    last_invoice_date: Optional[datetime]