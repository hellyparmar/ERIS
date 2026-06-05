from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import get_db
from app.models import Invoice, User
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])

class InvoiceCreate(BaseModel):
    customer_name: str
    billed_to_gstin: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    subtotal: float
    tax_amount: float
    total_amount: float
    payment_terms: Optional[str] = "cash"
    invoice_type: str = "sale"
    notes: Optional[str] = None

class PaymentUpdate(BaseModel):
    payment_terms: str
    status: str = "paid"

@router.get("/")
def list_invoices(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Invoice)
    if current_user.role == "manager" and current_user.outlet_id:
        q = q.filter(Invoice.store_id == current_user.outlet_id)
    if status:
        q = q.filter(Invoice.status == status)
    total = q.count()
    rows = q.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "invoices": [{
            "id": r.id,
            "invoice_number": r.invoice_number,
            "customer_name": r.customer_name,
            "billed_to_gstin": r.billed_to_gstin,
            "invoice_date": str(r.invoice_date),
            "due_date": str(r.due_date) if r.due_date else None,
            "subtotal": r.subtotal,
            "tax_amount": r.tax_amount,
            "total_amount": r.total_amount,
            "status": r.status,
            "payment_terms": r.payment_terms,
            "invoice_type": r.invoice_type,
        } for r in rows]
    }

@router.post("/")
def create_invoice(
    body: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(func.count(Invoice.id)).scalar() or 0
    inv_number = f"INV-{date.today().year}-{str(count + 1).zfill(5)}"
    invoice = Invoice(
        invoice_number=inv_number,
        organization_id=current_user.organization_id,
        store_id=current_user.outlet_id,
        customer_name=body.customer_name,
        billed_to_gstin=body.billed_to_gstin,
        invoice_date=body.invoice_date,
        due_date=body.due_date,
        subtotal=body.subtotal,
        tax_amount=body.tax_amount,
        total_amount=body.total_amount,
        payment_terms=body.payment_terms,
        invoice_type=body.invoice_type,
        notes=body.notes,
        status="pending",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return {"id": invoice.id, "invoice_number": inv_number, "message": "Invoice created"}

@router.patch("/{invoice_id}/payment")
def record_payment(
    invoice_id: int,
    body: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    from datetime import datetime
    invoice.status = body.status
    invoice.payment_terms = body.payment_terms
    invoice.last_payment_at = datetime.utcnow()
    db.commit()
    return {"message": "Payment recorded", "invoice_number": invoice.invoice_number}
