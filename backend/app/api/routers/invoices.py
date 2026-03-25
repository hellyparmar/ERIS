"""
Invoice Management Router
GST-compliant invoicing, payments, Khata tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field

from app.api.db import get_db
from app.api.db.models import PaymentStatus, User
from app.api.services.invoice_service import InvoiceService
from app.api.services.invoice_pdf_generator import InvoicePDFGenerator
from app.api.services.whatsapp_service import WhatsAppReceiptService
from app.api.auth.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

# ==================== REQUEST/RESPONSE MODELS ====================

class CreateInvoiceRequest(BaseModel):
    sale_id: int
    payment_terms_days: int = Field(default=30, ge=1, le=365)
    send_whatsapp_receipt: bool = False

class RecordPaymentRequest(BaseModel):
    invoice_id: int
    amount: float = Field(gt=0)
    payment_method: str = Field(..., min_length=1)
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    send_receipt: bool = True

class SendInvoiceRequest(BaseModel):
    method: str = Field(..., description="'whatsapp' or 'email'")

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    invoice_date: datetime
    due_date: Optional[datetime]
    total_amount: float
    amount_paid: float
    amount_due: float
    payment_status: str
    hsn_code: Optional[str]
    tax_rate: float
    
    class Config:
        from_attributes = True

class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount_paid: float
    payment_method: str
    payment_date: datetime
    reference_number: Optional[str]
    
    class Config:
        from_attributes = True

# ==================== ENDPOINTS ====================

@router.post("/create", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    request: CreateInvoiceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create invoice from a sale transaction
    
    - **sale_id**: ID of the sale to generate invoice for
    - **payment_terms_days**: Payment due in X days (default 30)
    - **send_whatsapp_receipt**: Send invoice via WhatsApp to customer
    """
    try:
        service = InvoiceService(db)
        invoice = service.create_invoice_from_sale(
            sale_id=request.sale_id,
            payment_terms_days=request.payment_terms_days
        )
        
        # Send WhatsApp receipt if requested
        if request.send_whatsapp_receipt:
            customer = invoice.customer
            if customer and customer.whatsapp_number:
                whatsapp_service = WhatsAppReceiptService()
                whatsapp_service.send_invoice_receipt(
                    customer_whatsapp=customer.whatsapp_number,
                    invoice_number=invoice.invoice_number,
                    total_amount=float(invoice.total_amount),
                    amount_due=float(invoice.amount_due),
                    payment_status=invoice.payment_status.value
                )
                invoice.receipt_sent_via = "whatsapp"
                db.commit()
        
        return invoice
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating invoice: {str(e)}")

@router.post("/record-payment", response_model=PaymentResponse, status_code=201)
async def record_payment(
    request: RecordPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Record a payment against an invoice (Khata tracking)
    
    - **invoice_id**: Invoice to pay
    - **amount**: Payment amount
    - **payment_method**: cash, card, upi, neft, etc.
    - **reference_number**: Transaction reference
    - **send_receipt**: Send WhatsApp receipt confirmation
    """
    try:
        service = InvoiceService(db)
        payment = service.record_payment(
            invoice_id=request.invoice_id,
            amount=Decimal(str(request.amount)),
            payment_method=request.payment_method,
            reference_number=request.reference_number,
            notes=request.notes
        )
        
        # Send receipt if requested
        if request.send_receipt:
            invoice = service.db.query(service.db.query(payment).first().invoice).first()
            if invoice and invoice.customer and invoice.customer.whatsapp_number:
                whatsapp_service = WhatsAppReceiptService()
                whatsapp_service.send_invoice_receipt(
                    customer_whatsapp=invoice.customer.whatsapp_number,
                    invoice_number=invoice.invoice_number,
                    total_amount=float(invoice.total_amount),
                    amount_due=float(invoice.amount_due),
                    payment_status=invoice.payment_status.value
                )
        
        return payment
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording payment: {str(e)}")

@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    status: Optional[str] = Query(None, description="Filter by payment status"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all invoices with optional filters and pagination"""
    from app.api.db.models import Invoice
    query = db.query(Invoice)
    
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    if status:
        try:
            status_enum = PaymentStatus[status.upper()]
            query = query.filter(Invoice.payment_status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            
    invoices = query.order_by(Invoice.invoice_date.desc()).offset((page - 1) * limit).limit(limit).all()
    return invoices

@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: int,
    request: SendInvoiceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send invoice receipt via WhatsApp or Email"""
    try:
        service = InvoiceService(db)
        success = service.send_invoice(invoice_id, request.method)
        if success:
            return {"success": True, "message": f"Invoice sent successfully via {request.method}"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to send invoice via {request.method}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending invoice: {str(e)}")

@router.get("/{invoice_id}/summary")
async def get_invoice_summary(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed invoice summary with payment history"""
    try:
        service = InvoiceService(db)
        summary = service.get_invoice_summary(invoice_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Generate and download invoice PDF"""
    from fastapi.responses import Response
    
    try:
        service = InvoiceService(db)
        summary = service.get_invoice_summary(invoice_id)
        
        pdf_generator = InvoicePDFGenerator()
        pdf_bytes = pdf_generator.generate_invoice_pdf(summary)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice_{summary['invoice']['invoice_number']}.pdf"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=503, detail="PDF generation not available. Install reportlab.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@router.get("/customer/{customer_id}")
async def get_customer_invoices(
    customer_id: int,
    status: Optional[str] = Query(None, description="Filter by payment status"),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all invoices for a customer"""
    service = InvoiceService(db)
    
    status_enum = None
    if status:
        try:
            status_enum = PaymentStatus[status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    invoices = service.get_customer_invoices(customer_id, status_enum, limit)
    return [InvoiceResponse.from_orm(inv) for inv in invoices]

@router.get("/customer/{customer_id}/khata")
async def get_khata_summary(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get Khata (credit ledger) summary for customer"""
    service = InvoiceService(db)
    return service.get_khata_summary(customer_id)

@router.get("/overdue")
async def get_overdue_invoices(
    days: int = Query(0, ge=0, description="Minimum days overdue"),
    db: Session = Depends(get_db)
):
    """Get overdue invoices"""
    service = InvoiceService(db)
    overdue = service.get_overdue_invoices(days)
    return [InvoiceResponse.from_orm(inv) for inv in overdue]

@router.post("/mark-overdue")
async def mark_overdue_invoices(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Mark invoices as overdue if past due date"""
    service = InvoiceService(db)
    count = service.mark_overdue_invoices()
    return {"marked_overdue": count, "message": f"Marked {count} invoices as overdue"}

@router.post("/send-reminders")
async def send_payment_reminders(
    min_days_overdue: int = Query(1, ge=0),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Send WhatsApp payment reminders for overdue invoices"""
    service = InvoiceService(db)
    overdue = service.get_overdue_invoices(min_days_overdue)
    
    # Prepare reminder data
    reminders = []
    for invoice in overdue:
        if invoice.customer and invoice.customer.whatsapp_number:
            days_overdue = (datetime.now() - invoice.due_date).days if invoice.due_date else 0
            reminders.append({
                "whatsapp": invoice.customer.whatsapp_number,
                "invoice_number": invoice.invoice_number,
                "amount_due": float(invoice.amount_due),
                "days_overdue": days_overdue
            })
    
    # Send bulk reminders
    whatsapp_service = WhatsAppReceiptService()
    results = whatsapp_service.send_bulk_reminders(reminders)
    
    return {
        "total_overdue": len(overdue),
        "reminders_attempted": len(reminders),
        "results": results
    }

@router.get("/stats/summary")
async def get_invoice_stats(db: Session = Depends(get_db)):
    """Get overall invoice statistics"""
    from app.api.db.models import Invoice
    
    total = db.query(Invoice).count()
    paid = db.query(Invoice).filter(Invoice.payment_status == PaymentStatus.PAID).count()
    partial = db.query(Invoice).filter(Invoice.payment_status == PaymentStatus.PARTIAL).count()
    pending = db.query(Invoice).filter(Invoice.payment_status == PaymentStatus.PENDING).count()
    overdue = db.query(Invoice).filter(Invoice.payment_status == PaymentStatus.OVERDUE).count()
    
    total_revenue = db.query(func.sum(Invoice.total_amount)).scalar() or 0
    total_collected = db.query(func.sum(Invoice.amount_paid)).scalar() or 0
    total_outstanding = db.query(func.sum(Invoice.amount_due)).scalar() or 0
    
    return {
        "total_invoices": total,
        "by_status": {
            "paid": paid,
            "partial": partial,
            "pending": pending,
            "overdue": overdue
        },
        "financials": {
            "total_revenue": float(total_revenue),
            "total_collected": float(total_collected),
            "total_outstanding": float(total_outstanding),
            "collection_rate": (float(total_collected) / float(total_revenue) * 100) if total_revenue > 0 else 0
        }
    }
