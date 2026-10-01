"""GST calculation, customer invoices, payments, PDFs, and GSTR-1 summaries."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_outlet_scope, require_role
from app.database import get_db_sync_dependency
from app.models import Customer, Invoice, InvoiceLineItem, InvoiceTax, Payment, User
from app.services.audit_service import log_audit_action_sync
from app.services.gst_calculator import CATEGORY_GST_RATES, GSTCalculator, get_rate_for_category
from app.services.gstr1_service import generate_gstr1_report, validate_gstr1
from app.services.invoice_pdf_service import generate_invoice_pdf


router = APIRouter(
    prefix="/gst",
    tags=["GST / Billing"],
    dependencies=[Depends(get_current_active_user)],
)


class SimpleGSTRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    category: str
    is_interstate: bool = False


class InvoiceItemRequest(BaseModel):
    product_id: Optional[int] = None
    description: str = Field(min_length=1, max_length=300)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    gst_rate: Decimal = Field(default=Decimal("18"), ge=0, le=28)


class CreateInvoiceRequest(BaseModel):
    outlet_id: int
    customer_id: Optional[int] = None
    customer_name: Optional[str] = Field(default=None, max_length=255)
    customer_gstin: Optional[str] = Field(default=None, max_length=15)
    customer_address: Optional[str] = Field(default=None, max_length=500)
    due_date: Optional[datetime] = None
    items: List[InvoiceItemRequest] = Field(min_length=1)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = Field(default=None, max_length=1000)


class InvoicePaymentRequest(BaseModel):
    amount: Optional[Decimal] = Field(default=None, gt=0)
    payment_method: str = Field(default="cash", pattern="^(cash|card|upi|bank_transfer|wallet)$")
    reference_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)


def _invoice_query(db: Session):
    return db.query(Invoice).options(
        selectinload(Invoice.line_items),
        selectinload(Invoice.payments),
        selectinload(Invoice.taxes),
    )


def _allowed_outlets(current_user: User, db: Session) -> list[int]:
    return get_outlet_scope(current_user, db)


def _require_invoice_access(invoice: Invoice, current_user: User, db: Session) -> None:
    allowed = _allowed_outlets(current_user, db)
    if invoice.organization_id != current_user.organization_id or invoice.outlet_id not in allowed:
        raise HTTPException(status_code=403, detail="Access denied to this invoice")


def _status(invoice: Invoice) -> str:
    if invoice.is_voided or invoice.payment_status == "cancelled":
        return "cancelled"
    if Decimal(invoice.amount_due or 0) <= 0:
        return "paid"
    due = invoice.due_date
    if due and due.replace(tzinfo=None) < datetime.now().replace(tzinfo=None):
        return "overdue"
    return "pending"


def _serialize(invoice: Invoice, include_items: bool = True) -> dict:
    data = {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "customer_id": invoice.customer_id,
        "customer_name": invoice.billed_to_name or "Walk-in Customer",
        "customer_gstin": invoice.billed_to_gstin,
        "outlet_id": invoice.outlet_id,
        "issue_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "subtotal": float(invoice.subtotal or 0),
        "discount": float(invoice.discount or 0),
        "tax_amount": float(invoice.tax_amount or 0),
        "total": float(invoice.total_amount or 0),
        "amount_paid": float(invoice.amount_paid or 0),
        "amount_due": float(invoice.amount_due or 0),
        "status": _status(invoice),
        "payment_status": invoice.payment_status,
        "notes": invoice.notes,
    }
    if include_items:
        data["items"] = [
            {
                "id": item.id,
                "product_id": item.product_id,
                "description": item.description or item.product_name,
                "product_name": item.product_name or item.description,
                "quantity": float(item.quantity or 0),
                "unit_price": float(item.unit_price or 0),
                "gst_rate": float(item.gst_rate or 0),
                "gst_amount": float(item.gst_amount or 0),
                "line_total": float(item.line_total or 0),
                "line_total_with_tax": float(item.line_total_with_tax or 0),
            }
            for item in invoice.line_items
        ]
    return data


@router.post("/calculate")
async def calculate_gst(request: SimpleGSTRequest):
    rate = get_rate_for_category(request.category)
    result = GSTCalculator.calculate_forward_tax(request.amount, rate, request.is_interstate)
    return {
        "base_amount": float(result.taxable_value),
        "gst_rate": float(rate),
        "cgst_amount": float(result.cgst_amount),
        "sgst_amount": float(result.sgst_amount),
        "igst_amount": float(result.igst_amount),
        "total_gst": float(result.total_tax_amount),
        "total_with_gst": float(result.grand_total),
    }


@router.get("/rates")
async def get_all_rates():
    return {"category_rates": CATEGORY_GST_RATES, "standard_slabs": [0, 5, 12, 18, 28]}


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: CreateInvoiceRequest,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db_sync_dependency),
):
    allowed = _allowed_outlets(current_user, db)
    if request.outlet_id not in allowed:
        raise HTTPException(status_code=403, detail="Access denied to this outlet")

    customer = None
    if request.customer_id is not None:
        customer = (
            db.query(Customer)
            .filter(
                Customer.id == request.customer_id,
                Customer.organization_id == current_user.organization_id,
                Customer.is_deleted.is_(False),
            )
            .first()
        )
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")

    billed_name = request.customer_name or (customer.name if customer else "Walk-in Customer")
    billed_gstin = request.customer_gstin or (customer.gst_number if customer else None)
    billed_address = request.customer_address or (customer.address if customer else None)
    subtotal = sum((item.quantity * item.unit_price for item in request.items), Decimal("0"))
    if request.discount > subtotal:
        raise HTTPException(status_code=400, detail="Discount cannot exceed subtotal")
    taxable = subtotal - request.discount
    gross_tax = sum(
        (item.quantity * item.unit_price * item.gst_rate / Decimal("100") for item in request.items),
        Decimal("0"),
    )
    discount_ratio = taxable / subtotal if subtotal else Decimal("0")
    tax_amount = (gross_tax * discount_ratio).quantize(Decimal("0.01"))
    total = (taxable + tax_amount).quantize(Decimal("0.01"))
    today = datetime.now(timezone.utc)
    day_count = (
        db.query(Invoice.id)
        .filter(Invoice.invoice_date >= today.replace(hour=0, minute=0, second=0, microsecond=0))
        .count()
    )

    invoice = Invoice(
        invoice_number=f"INV-{today:%Y%m%d}-{day_count + 1:04d}",
        sale_id=None,
        organization_id=current_user.organization_id,
        outlet_id=request.outlet_id,
        customer_id=request.customer_id,
        billed_to_name=billed_name,
        billed_to_gstin=billed_gstin,
        billed_to_address=billed_address,
        invoice_type="tax_invoice",
        invoice_date=today,
        due_date=request.due_date or today + timedelta(days=30),
        subtotal=subtotal,
        discount=request.discount,
        tax_amount=tax_amount,
        total_amount=total,
        amount_paid=Decimal("0"),
        amount_due=total,
        payment_status="issued",
        notes=request.notes,
        cgst_amount=tax_amount / 2,
        sgst_amount=tax_amount / 2,
    )
    db.add(invoice)
    db.flush()
    for item in request.items:
        line_subtotal = (item.quantity * item.unit_price).quantize(Decimal("0.01"))
        line_tax = (line_subtotal * item.gst_rate / Decimal("100") * discount_ratio).quantize(Decimal("0.01"))
        db.add(
            InvoiceLineItem(
                invoice_id=invoice.id,
                product_id=item.product_id,
                product_name=item.description,
                description=item.description,
                quantity=float(item.quantity),
                unit_price=float(item.unit_price),
                line_total=float(line_subtotal),
                gst_rate=float(item.gst_rate),
                gst_amount=float(line_tax),
                line_total_with_tax=float(line_subtotal + line_tax),
            )
        )
    effective_rate = (tax_amount / taxable * 100).quantize(Decimal("0.01")) if taxable else Decimal("0")
    db.add(
        InvoiceTax(
            invoice_id=invoice.id,
            tax_name="GST",
            tax_rate=float(effective_rate),
            tax_amount=float(tax_amount),
            tax_type="gst",
        )
    )
    log_audit_action_sync(db, "create_invoice", current_user.id, {"invoice_id": invoice.id})
    db.commit()
    invoice = _invoice_query(db).filter(Invoice.id == invoice.id).one()
    return _serialize(invoice)


@router.get("/invoices")
async def list_invoices(
    outlet_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    allowed = _allowed_outlets(current_user, db)
    if outlet_id is not None and outlet_id not in allowed:
        raise HTTPException(status_code=403, detail="Access denied to this outlet")
    query = (
        _invoice_query(db).filter(
            Invoice.organization_id == current_user.organization_id,
            Invoice.outlet_id.in_([outlet_id] if outlet_id is not None else allowed),
        )
        if allowed
        else _invoice_query(db).filter(False)
    )
    total = query.count()
    invoices = query.order_by(Invoice.invoice_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"invoices": [_serialize(invoice) for invoice in invoices], "total": total, "page": page}


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    invoice = _invoice_query(db).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _require_invoice_access(invoice, current_user, db)
    return _serialize(invoice)


@router.post("/invoices/{invoice_id}/pay")
async def record_invoice_payment(
    invoice_id: int,
    request: Optional[InvoicePaymentRequest] = None,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db_sync_dependency),
):
    invoice = _invoice_query(db).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _require_invoice_access(invoice, current_user, db)
    request = request or InvoicePaymentRequest()
    amount_due = Decimal(invoice.amount_due or 0)
    amount = request.amount or amount_due
    if amount > amount_due:
        raise HTTPException(status_code=400, detail="Payment exceeds amount due")
    db.add(
        Payment(
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
            amount_paid=float(amount),
            payment_method=request.payment_method,
            reference_number=request.reference_number,
            notes=request.notes,
            created_by=current_user.id,
        )
    )
    invoice.amount_paid = Decimal(invoice.amount_paid or 0) + amount
    invoice.amount_due = max(Decimal("0"), Decimal(invoice.total_amount) - Decimal(invoice.amount_paid))
    invoice.payment_status = "paid" if invoice.amount_due <= 0 else "partially_paid"
    invoice.last_payment_at = datetime.now(timezone.utc)
    db.commit()
    return _serialize(invoice, include_items=False)


@router.patch("/invoices/{invoice_id}/cancel")
async def cancel_invoice(
    invoice_id: int,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db_sync_dependency),
):
    invoice = _invoice_query(db).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _require_invoice_access(invoice, current_user, db)
    if Decimal(invoice.amount_paid or 0) > 0:
        raise HTTPException(status_code=400, detail="Paid invoices cannot be cancelled")
    invoice.is_voided = True
    invoice.voided_at = datetime.now(timezone.utc)
    invoice.voided_by = current_user.id
    invoice.payment_status = "cancelled"
    db.commit()
    return _serialize(invoice, include_items=False)


@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    invoice = _invoice_query(db).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _require_invoice_access(invoice, current_user, db)
    data = _serialize(invoice)
    data.update(
        {
            "customer_email": invoice.customer.email if invoice.customer else "",
            "customer_phone": invoice.customer.phone if invoice.customer else "",
            "line_items": data.pop("items"),
            "gst_amount": data["tax_amount"],
            "balance_amount": data["amount_due"],
        }
    )
    pdf = generate_invoice_pdf(data).getvalue()
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'},
    )


@router.get("/gstr1")
async def get_gstr1(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    return generate_gstr1_report(db, month, year, current_user.organization_id, _allowed_outlets(current_user, db))


@router.get("/gstr1/validate")
async def validate_gstr1_endpoint(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    return validate_gstr1(db, month, year, current_user.organization_id, _allowed_outlets(current_user, db))
