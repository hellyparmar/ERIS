"""
Phase 2: Invoice Management REST API Endpoints with Database Integration

Complete invoice lifecycle management with GST compliance and database persistence
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import requests
import logging

from app.api.db.database import get_db
from app.api.db.phase2_models import (
    Invoice, InvoiceLineItem as InvoiceLineItemModel, InvoicePayment
)
from app.api.services.phase2_invoice_service import phase2_invoice_service, InvoiceLineItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/invoice", tags=["invoices"])


# ==================== Request Models ====================

class LineItemRequest(BaseModel):
    """Line item in invoice"""
    product_id: Optional[str] = None
    product_name: str
    hsn_code: str
    quantity: Decimal
    unit_rate: Decimal
    tax_rate: Decimal


class InvoiceCreateRequest(BaseModel):
    """Invoice creation request"""
    business_id: int
    customer_id: int
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_gst_number: Optional[str] = None
    billing_address: str
    shipping_address: Optional[str] = None
    line_items: List[LineItemRequest]
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    is_intra_state: bool = True


# ==================== Helper Functions ====================

def generate_invoice_number(business_id: str, db: Session) -> str:
    """Generate unique invoice number"""
    from datetime import datetime
    today = date.today()
    count = db.query(Invoice).filter(
        Invoice.business_id == business_id,
        Invoice.invoice_date == today
    ).count()
    return f"INV-{business_id}-{today.strftime('%Y%m%d')}-{count+1:04d}"


def calculate_invoice_totals(line_items_data: List[dict]) -> dict:
    """Calculate invoice totals using service"""
    items = [
        InvoiceLineItem(
            product_id=item.get("product_id", ""),
            product_name=item.get("product_name"),
            hsn_code=item.get("hsn_code"),
            quantity=Decimal(str(item.get("quantity", 1))),
            unit_rate=Decimal(str(item.get("unit_rate", 0))),
            tax_rate=Decimal(str(item.get("tax_rate", 18))),
            description=item.get("description"),
            discount_percentage=Decimal(str(item.get("discount_percentage", 0)))
        )
        for item in line_items_data
    ]
    return phase2_invoice_service.calculate_invoice_totals(items)


# ==================== Invoice Creation & Management ====================

@router.post("/create")
def create_invoice(
    request: InvoiceCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new GST-compliant invoice
    
    Args:
        request: Invoice creation request with line items
        
    Returns:
        Created invoice with all calculations
    """
    try:
        if not request.line_items:
            raise ValueError("At least one line item required")
        
        # Convert line items to dicts for calculation
        line_items_data = [item.dict() for item in request.line_items]
        
        # Calculate totals using service
        totals = calculate_invoice_totals(line_items_data)
        
        # Generate invoice number
        invoice_number = generate_invoice_number(str(request.business_id), db)
        
        # Create invoice record
        invoice = Invoice(
            invoice_number=invoice_number,
            business_id=request.business_id,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            customer_gst_number=request.customer_gst_number,
            billing_address=request.billing_address,
            shipping_address=request.shipping_address,
            invoice_date=date.today(),
            subtotal=Decimal(str(totals.get("subtotal", 0))),
            cgst_amount=Decimal(str(totals.get("cgst", 0))) if request.is_intra_state else Decimal(0),
            sgst_amount=Decimal(str(totals.get("sgst", 0))) if request.is_intra_state else Decimal(0),
            igst_amount=Decimal(str(totals.get("igst", 0))) if not request.is_intra_state else Decimal(0),
            total_tax=Decimal(str(totals.get("total_tax", 0))),
            grand_total=Decimal(str(totals.get("final_amount", 0))),
            payment_terms=request.payment_terms,
            notes=request.notes,
            is_inter_state=not request.is_intra_state,
            payment_status="UNPAID"
        )
        db.add(invoice)
        db.flush()  # Get the invoice ID
        
        # Create line items
        for item_data in request.line_items:
            quantity = Decimal(str(item_data.quantity))
            unit_rate = Decimal(str(item_data.unit_rate))
            tax_rate = Decimal(str(item_data.tax_rate))
            
            line_amount = quantity * unit_rate
            tax_amount = line_amount * (tax_rate / Decimal(100))
            line_total = line_amount + tax_amount
            
            line_item = InvoiceLineItemModel(
                invoice_id=invoice.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                hsn_code=item_data.hsn_code,
                quantity=quantity,
                unit_rate=unit_rate,
                tax_rate=tax_rate,
                line_amount=line_amount,
                line_total=line_total,
                discount_percentage=Decimal("0"),
                description=None
            )
            db.add(line_item)
        
        db.commit()
        
        return {
            "status": "success",
            "invoice": {
                "id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "business_id": invoice.business_id,
                "customer_name": invoice.customer_name,
                "subtotal": float(invoice.subtotal),
                "total_tax": float(invoice.total_tax),
                "total_amount": float(invoice.total_amount),
                "payment_status": invoice.payment_status,
                "created_at": invoice.created_at.isoformat()
            }
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """Get invoice details with line items"""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Get line items
        line_items = db.query(InvoiceLineItemModel).filter(
            InvoiceLineItemModel.invoice_id == invoice_id
        ).all()
        
        return {
            "status": "success",
            "invoice": {
                "id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "business_id": invoice.business_id,
                "customer_name": invoice.customer_name,
                "customer_email": invoice.customer_email,
                "total_taxable": float(invoice.total_taxable),
                "total_tax": float(invoice.total_tax),
                "total_amount": float(invoice.total_amount),
                "payment_status": invoice.payment_status,
                "line_items": [
                    {
                        "product_name": item.product_name,
                        "quantity": float(item.quantity),
                        "unit_rate": float(item.unit_rate),
                        "tax_rate": float(item.tax_rate),
                        "line_total": float(item.line_total)
                    }
                    for item in line_items
                ],
                "created_at": invoice.created_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: str, db: Session = Depends(get_db)):
    """Download invoice as PDF with QR code"""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Get line items for PDF
        line_items = db.query(InvoiceLineItemModel).filter(
            InvoiceLineItemModel.invoice_id == invoice_id
        ).all()
        
        # Prepare PDF data
        pdf_data = {
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "business_details": {
                "name": "Your Business Name",
                "address": "Business Address",
                "gst_number": "27ABCPA1234A1Z0",
                "phone": "9876543210"
            },
            "customer_details": {
                "name": invoice.customer_name,
                "address": invoice.billing_address,
                "email": invoice.customer_email,
                "phone": invoice.customer_phone,
                "gst_number": invoice.customer_gst_number
            },
            "shipping_address": invoice.shipping_address,
            "line_items": [
                {
                    "product_name": item.product_name,
                    "hsn_code": item.hsn_code,
                    "quantity": float(item.quantity),
                    "unit_rate": float(item.unit_rate),
                    "tax_rate": float(item.tax_rate),
                    "discount_percentage": float(item.discount_percentage or 0)
                }
                for item in line_items
            ],
            "is_inter_state": invoice.is_inter_state,
            "payment_terms": invoice.payment_terms,
            "notes": invoice.notes,
            "qr_code_data": f"UPI://pay?pa=business@bank&pn=YourBusiness&am={invoice.total_amount}&tn=Invoice%20{invoice.invoice_number}"
        }
        
        # Generate PDF
        from app.api.services.pdf_invoice_generator import pdf_invoice_generator
        pdf_buffer = pdf_invoice_generator.generate_invoice_pdf(pdf_data)
        
        return {
            "status": "success",
            "message": f"PDF for invoice {invoice_id} ready",
            "pdf_url": f"/files/invoices/{invoice_id}.pdf",
            "size_bytes": len(pdf_buffer.getvalue())
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{invoice_id}/send-whatsapp")
def send_invoice_whatsapp(
    invoice_id: str,
    customer_phone: str,
    message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Send invoice via WhatsApp"""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Send invoice via WhatsApp using MSG91
        msg91_api_key = os.getenv('MSG91_API_KEY')
        msg91_sender_id = os.getenv('MSG91_SENDER_ID', 'ERISAL')
        
        if not msg91_api_key:
            raise HTTPException(
                status_code=500, 
                detail="WhatsApp service not configured. MSG91_API_KEY not set."
            )
        
        try:
            # Format invoice message
            invoice_message = f"""
🧾 *ERIS Invoice #{invoice.invoice_number}*

📅 Date: {invoice.created_at.strftime('%d/%m/%Y')}
👤 Customer: {invoice.customer_name or 'Walk-in Customer'}
📞 Phone: {customer_phone}

📋 Items:
"""
            
            # Add line items
            for item in invoice.line_items:
                invoice_message += f"• {item.product_name} (x{item.quantity}) - ₹{item.total:.2f}\n"
            
            invoice_message += f"""
💰 Subtotal: ₹{invoice.subtotal:.2f}
📊 GST: ₹{invoice.gst_amount:.2f}
💵 Total: ₹{invoice.total:.2f}

Thank you for your business! 🛒
*Enterprise Retail Intelligence System*
"""
            
            # Send via MSG91 WhatsApp API
            response = requests.post(
                'https://api.msg91.com/api/v2/sendsms',
                json={
                    'sender': msg91_sender_id,
                    'route': '4',  # WhatsApp route
                    'country': '91',  # India
                    'sms': [{
                        'message': invoice_message,
                        'to': [customer_phone.lstrip('+')]
                    }]
                },
                headers={
                    'authkey': msg91_api_key,
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"WhatsApp invoice sent to {customer_phone} for invoice {invoice_id}")
                return {
                    "status": "success",
                    "message": f"Invoice {invoice.invoice_number} sent via WhatsApp to {customer_phone}",
                    "sent_at": datetime.utcnow().isoformat(),
                    "provider": "MSG91"
                }
            else:
                logger.error(f"MSG91 WhatsApp API error: {response.text}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to send WhatsApp message: {response.text}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending WhatsApp invoice: {e}")
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp invoice: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{invoice_id}")
def update_invoice(
    invoice_id: str,
    payment_status: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update invoice details"""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if payment_status:
            invoice.payment_status = payment_status
        if notes is not None:
            invoice.notes = notes
        
        invoice.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "invoice": {
                "id": str(invoice.id),
                "payment_status": invoice.payment_status,
                "updated_at": invoice.updated_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{invoice_id}")
def cancel_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """Cancel invoice"""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        invoice.payment_status = "CANCELLED"
        invoice.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "message": f"Invoice {invoice_id} cancelled",
            "cancelled_at": invoice.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Invoice Listing & Search ====================

@router.get("")
def list_invoices(
    business_id: str,
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List invoices with filtering
    
    Query Parameters:
        business_id: Business ID
        payment_status: UNPAID, PARTIAL, PAID, CANCELLED
        start_date: Period start
        end_date: Period end
    """
    try:
        query = db.query(Invoice).filter(Invoice.business_id == business_id)
        
        if payment_status:
            query = query.filter(Invoice.payment_status == payment_status)
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        if start_date:
            query = query.filter(Invoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(Invoice.invoice_date <= end_date)
        
        total = query.count()
        invoices = query.offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "total": total,
            "invoices": [
                {
                    "id": str(inv.id),
                    "invoice_number": inv.invoice_number,
                    "customer_name": inv.customer_name,
                    "total_amount": float(inv.total_amount),
                    "payment_status": inv.payment_status,
                    "invoice_date": inv.invoice_date.isoformat()
                }
                for inv in invoices
            ],
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Invoice Analytics ====================

@router.get("/analytics/summary")
def invoice_analytics_summary(business_id: str, period_days: int = 30, db: Session = Depends(get_db)):
    """Get invoice analytics summary"""
    try:
        from datetime import timedelta
        start_date = date.today() - timedelta(days=period_days)
        
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            Invoice.invoice_date >= start_date
        ).all()
        
        total_value = sum(Decimal(str(inv.total_amount)) for inv in invoices)
        paid = [inv for inv in invoices if inv.payment_status == "PAID"]
        unpaid = [inv for inv in invoices if inv.payment_status == "UNPAID"]
        
        return {
            "status": "success",
            "summary": {
                "total_invoices": len(invoices),
                "total_value": float(total_value),
                "paid_invoices": len(paid),
                "unpaid_invoices": len(unpaid),
                "paid_value": float(sum(Decimal(str(inv.total_amount)) for inv in paid)),
                "unpaid_value": float(sum(Decimal(str(inv.total_amount)) for inv in unpaid))
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
