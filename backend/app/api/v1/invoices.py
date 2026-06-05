"""
API v1 Invoice Router

Provides invoice creation, listing, detail, PDF download, email delivery,
GSTR-1 export and Tally XML export endpoints.
"""

from datetime import datetime, date
from sqlalchemy import select
from io import BytesIO
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.users import User
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


class CreateInvoiceFromSaleRequest(BaseModel):
    sale_id: UUID = Field(..., description="Sale transaction ID to invoice")
    payment_terms_days: int = Field(30, ge=1, le=365, description="Payment due in X days")


class InvoiceLineItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    hsn_code: Optional[str]
    quantity: int
    unit_price: float
    tax_rate: float
    tax_amount: float
    discount: float
    line_total: float


class InvoicePaymentResponse(BaseModel):
    id: int
    amount: float
    payment_method: str
    reference_number: Optional[str]
    payment_date: Optional[str]


class InvoiceSummaryResponse(BaseModel):
    id: int
    invoice_number: str
    invoice_date: Optional[str]
    due_date: Optional[str]
    subtotal: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    amount_due: float
    payment_status: str
    billed_to_name: Optional[str]
    billed_to_gstin: Optional[str]


class InvoiceDetailResponse(BaseModel):
    invoice: InvoiceSummaryResponse
    line_items: List[InvoiceLineItemResponse]
    payments: List[InvoicePaymentResponse]
    sale_id: Optional[str]
    customer_name: Optional[str]
    customer_gstin: Optional[str]


class InvoiceEmailRequest(BaseModel):
    recipient_email: Optional[EmailStr] = Field(None, description="Optional recipient email address")


class InvoiceListResponse(BaseModel):
    items: List[InvoiceSummaryResponse]
    total: int
    page: int
    per_page: int


@router.post("/create", response_model=InvoiceDetailResponse, status_code=201)
async def create_invoice_from_sale(
    payload: CreateInvoiceFromSaleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    try:
        service = InvoiceService(db, current_user)
        invoice = service.create_invoice_from_sale(
            sale_id=payload.sale_id,
            payment_terms_days=payload.payment_terms_days,
        )
        return service.get_invoice_detail(invoice.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Invoice creation failed: {exc}")


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    status: Optional[str] = Query(None, description="Filter by invoice payment status"),
    customer_name: Optional[str] = Query(None, description="Filter by billed-to customer name"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    from app.models import Invoice

    invoice_query = db.query(Invoice)
    if status:
        invoice_query = invoice_query.filter(Invoice.payment_status == status)
    if customer_name:
        invoice_query = invoice_query.filter(Invoice.billed_to_name.ilike(f"%{customer_name}%"))
    if date_from:
        invoice_query = invoice_query.filter(Invoice.invoice_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        invoice_query = invoice_query.filter(Invoice.invoice_date <= datetime.combine(date_to, datetime.max.time()))

    total = invoice_query.count()
    results = invoice_query.order_by(Invoice.invoice_date.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return InvoiceListResponse(
        items=[
            InvoiceSummaryResponse(
                id=inv.id,
                invoice_number=inv.invoice_number,
                invoice_date=inv.invoice_date.isoformat() if inv.invoice_date else None,
                due_date=inv.due_date.isoformat() if inv.due_date else None,
                subtotal=float(inv.subtotal or 0),
                tax_amount=float(inv.tax_amount or 0),
                total_amount=float(inv.total_amount or 0),
                amount_paid=float(inv.amount_paid or 0),
                amount_due=float(inv.amount_due or 0),
                payment_status=inv.payment_status,
                billed_to_name=inv.billed_to_name,
                billed_to_gstin=inv.billed_to_gstin,
            )
            for inv in results
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    try:
        service = InvoiceService(db, current_user)
        return service.get_invoice_detail(invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    try:
        service = InvoiceService(db, current_user)
        pdf_bytes = service.generate_pdf_invoice(invoice_id)
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"}
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")


@router.post("/{invoice_id}/email")
async def email_invoice_pdf(
    invoice_id: int,
    payload: InvoiceEmailRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    try:
        service = InvoiceService(db, current_user)
        result = service.send_invoice_email(invoice_id, payload.recipient_email)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Email sending failed"))
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {exc}")


@router.get("/gstr1/export")
async def export_gstr1(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    try:
        service = InvoiceService(db, current_user)
        return service.export_gstr1_data(month, year)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"GSTR-1 export failed: {exc}")


@router.get("/{invoice_id}/tally/xml")
async def export_tally_xml(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Response:
    try:
        service = InvoiceService(db, current_user)
        xml_payload = service.export_tally_xml(invoice_id)
        return Response(content=xml_payload, media_type="application/xml")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tally XML export failed: {exc}")
