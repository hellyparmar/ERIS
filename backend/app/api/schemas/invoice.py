from pydantic import BaseModel, Field, UUID4, validator
from typing import List, Optional, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

class PaymentStatus(str, Enum):
    PAID = "paid"
    PARTIAL = "partial"
    PENDING = "pending"
    OVERDUE = "overdue"

class InvoicePaymentCreate(BaseModel):
    amount_paid: Decimal = Field(..., gt=0, description="Amount paid in this transaction")
    payment_method: str = Field(..., max_length=50, example="UPI")
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class InvoicePaymentResponse(InvoicePaymentCreate):
    id: int
    invoice_id: int
    payment_date: datetime

    class Config:
        from_attributes = True

class InvoiceSendRequest(BaseModel):
    method: str = Field(..., example="whatsapp", description="Method of sending: 'whatsapp' or 'email'")

class InvoiceBase(BaseModel):
    invoice_number: str
    customer_id: int
    hsn_code: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    taxable_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Decimal
    
    payment_status: PaymentStatus
    amount_paid: Decimal
    amount_due: Decimal

    tally_sync_status: str
    receipt_sent_via: Optional[str] = None
    
    invoice_date: datetime
    due_date: Optional[datetime] = None
    
    organization_id: UUID4
    store_id: UUID4

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
