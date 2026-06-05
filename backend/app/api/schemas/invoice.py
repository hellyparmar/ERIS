"""
Pydantic schemas for Invoice Management endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
from uuid import UUID


class InvoiceStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    OVERDUE = "overdue"


# ==================== INVOICE ====================

class InvoiceCreate(BaseModel):
    contact_id: UUID = Field(..., description="Business contact ID")
    outlet_id: UUID = Field(..., description="Outlet ID")
    total_amount: float = Field(..., gt=0)
    tax_amount: float = Field(..., ge=0)
    items: Dict[str, Any] = Field(..., description="Invoice items as JSON")
    issue_date: date
    due_date: date
    notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    paid_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    invoice_id: UUID
    contact_id: UUID
    outlet_id: UUID
    total_amount: float
    tax_amount: float
    items: Dict[str, Any]
    status: str
    issue_date: date
    due_date: date
    paid_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Related data
    contact: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    items: List[InvoiceResponse]


class OverdueInvoiceResponse(BaseModel):
    invoice_id: UUID
    contact_id: UUID
    outlet_id: UUID
    contact_name: str
    contact_company: str
    total_amount: float
    due_date: date
    days_overdue: int
    status: str


class OverdueInvoicesListResponse(BaseModel):
    total_overdue: int
    total_amount: float
    items: List[OverdueInvoiceResponse]


class InvoiceSummaryResponse(BaseModel):
    period_days: int
    paid_amount: float
    pending_amount: float
    overdue_amount: float
    total_amount: float
    invoice_count: int

class InvoiceResponse(InvoiceBase):
    id: int
    payments: List[InvoicePaymentResponse] = []

    class Config:
        from_attributes = True

class InvoiceListResponse(BaseModel):
    items: List[InvoiceResponse]
    total: int
    page: int
    size: int
