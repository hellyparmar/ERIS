"""
Invoice & Billing Router - Phase 2B
Complete invoicing system with GST, TDS, and payment management
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from app.api.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/invoicing", tags=["Invoicing"])


# ============================================================
# PYDANTIC MODELS
# ============================================================

class InvoiceLineItemRequest(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    quantity: float
    unit_price: float
    gst_rate: float = 18.0
    description: Optional[str] = None


class CreateInvoiceRequest(BaseModel):
    customer_id: int
    customer_name: str
    customer_email: str
    line_items: List[InvoiceLineItemRequest]
    gst_rate: float = 18.0
    tds_rate: float = 0
    notes: Optional[str] = None
    due_days: int = 30


class PaymentRequest(BaseModel):
    amount: float
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# INVOICE ENDPOINTS
# ============================================================

@router.post("/invoices")
async def create_invoice(
    request: CreateInvoiceRequest,
    db: Session = Depends(get_db)
):
    """Create a new invoice with automatic GST and TDS calculation"""
    from app.api.db.invoicing_models import Invoice, InvoiceLineItem, InvoiceTax
    
    try:
        # Generate invoice number
        invoice_query = "SELECT COUNT(*) as count FROM invoices WHERE DATE(invoice_date) = DATE('now')"
        result = db.execute(text(invoice_query)).fetchone()
        daily_count = result[0] + 1 if result else 1
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{daily_count:04d}"
        
        # Calculate line totals and subtotal
        subtotal = 0
        gst_total = 0
        line_items_data = []
        
        for item in request.line_items:
            line_total = item.quantity * item.unit_price
            item_gst = line_total * (item.gst_rate / 100)
            
            line_items_data.append({
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "line_total": line_total,
                "gst_rate": item.gst_rate,
                "gst_amount": item_gst,
                "line_total_with_tax": line_total + item_gst
            })
            
            subtotal += line_total
            gst_total += item_gst
        
        # Calculate TDS
        tds_amount = (subtotal + gst_total) * (request.tds_rate / 100) if request.tds_rate > 0 else 0
        
        # Total invoice amount
        total_amount = subtotal + gst_total - tds_amount
        
        # Create invoice
        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            subtotal=subtotal,
            gst_amount=gst_total,
            gst_rate=request.gst_rate,
            tds_amount=tds_amount,
            tds_rate=request.tds_rate,
            total_amount=total_amount,
            balance_amount=total_amount,
            status="draft",
            payment_status="unpaid",
            notes=request.notes,
            due_date=datetime.now() + timedelta(days=request.due_days),
            created_by="system"
        )
        
        db.add(invoice)
        db.flush()  # Get the invoice ID
        
        # Add line items
        for item_data in line_items_data:
            line_item = InvoiceLineItem(
                invoice_id=invoice.id,
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                line_total=item_data['line_total'],
                gst_rate=item_data['gst_rate'],
                gst_amount=item_data['gst_amount'],
                line_total_with_tax=item_data['line_total_with_tax']
            )
            db.add(line_item)
        
        # Add tax breakdown
        if gst_total > 0:
            gst_tax = InvoiceTax(
                invoice_id=invoice.id,
                tax_name="GST",
                tax_rate=request.gst_rate,
                tax_amount=gst_total,
                tax_type="gst"
            )
            db.add(gst_tax)
        
        if tds_amount > 0:
            tds_tax = InvoiceTax(
                invoice_id=invoice.id,
                tax_name="TDS",
                tax_rate=request.tds_rate,
                tax_amount=tds_amount,
                tax_type="tds"
            )
            db.add(tds_tax)
        
        db.commit()
        db.refresh(invoice)
        
        return {
            "success": True,
            "data": {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "status": invoice.status,
                "total_amount": invoice.total_amount,
                "due_date": invoice.due_date.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Invoice creation error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed invoice information"""
    from app.api.db.invoicing_models import Invoice
    
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            return {"success": False, "error": "Invoice not found"}
        
        line_items = [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "line_total": item.line_total,
                "gst_amount": item.gst_amount,
                "line_total_with_tax": item.line_total_with_tax
            }
            for item in invoice.line_items
        ]
        
        payments = [
            {
                "payment_date": p.payment_date.isoformat(),
                "amount": p.amount_paid,
                "method": p.payment_method,
                "reference": p.reference_number
            }
            for p in invoice.payments
        ]
        
        taxes = [
            {
                "tax_name": t.tax_name,
                "tax_rate": t.tax_rate,
                "tax_amount": t.tax_amount
            }
            for t in invoice.taxes
        ]
        
        return {
            "success": True,
            "data": {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date.isoformat(),
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "customer_name": invoice.customer_name,
                "customer_email": invoice.customer_email,
                "subtotal": invoice.subtotal,
                "gst_amount": invoice.gst_amount,
                "tds_amount": invoice.tds_amount,
                "total_amount": invoice.total_amount,
                "amount_paid": invoice.amount_paid,
                "balance_amount": invoice.balance_amount,
                "status": invoice.status,
                "payment_status": invoice.payment_status,
                "line_items": line_items,
                "taxes": taxes,
                "payments": payments,
                "notes": invoice.notes
            }
        }
        
    except Exception as e:
        logger.error(f"Get invoice error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/invoices")
async def list_invoices(
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List invoices with filters and pagination"""
    from app.api.db.invoicing_models import Invoice
    
    try:
        query = db.query(Invoice)
        
        if status:
            query = query.filter(Invoice.status == status)
        if payment_status:
            query = query.filter(Invoice.payment_status == payment_status)
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        
        total = query.count()
        
        invoices = query.order_by(Invoice.invoice_date.desc())\
            .limit(per_page)\
            .offset((page - 1) * per_page)\
            .all()
        
        data = [
            {
                "invoice_id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_name": inv.customer_name,
                "invoice_date": inv.invoice_date.isoformat(),
                "total_amount": inv.total_amount,
                "amount_paid": inv.amount_paid,
                "balance_amount": inv.balance_amount,
                "status": inv.status,
                "payment_status": inv.payment_status
            }
            for inv in invoices
        ]
        
        return {
            "success": True,
            "data": {
                "invoices": data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page
                }
            }
        }
        
    except Exception as e:
        logger.error(f"List invoices error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/invoices/{invoice_id}/pay")
async def record_payment(
    invoice_id: int,
    request: PaymentRequest,
    db: Session = Depends(get_db)
):
    """Record a payment for an invoice"""
    from app.api.db.invoicing_models import Invoice, Payment
    
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            return {"success": False, "error": "Invoice not found"}
        
        # Create payment record
        payment = Payment(
            invoice_id=invoice_id,
            amount_paid=request.amount,
            payment_method=request.payment_method,
            reference_number=request.reference_number,
            notes=request.notes,
            created_by="system"
        )
        
        db.add(payment)
        
        # Update invoice payment status
        invoice.amount_paid += request.amount
        invoice.balance_amount = invoice.total_amount - invoice.amount_paid
        
        if invoice.balance_amount <= 0:
            invoice.payment_status = "paid"
            invoice.status = "paid"
            invoice.payment_date = datetime.now()
        elif invoice.amount_paid > 0:
            invoice.payment_status = "partially_paid"
        
        db.commit()
        
        return {
            "success": True,
            "data": {
                "payment_id": payment.id,
                "amount_paid": payment.amount_paid,
                "total_paid": invoice.amount_paid,
                "remaining_balance": invoice.balance_amount,
                "payment_status": invoice.payment_status
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Payment recording error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# BILLING ANALYTICS
# ============================================================

@router.get("/analytics/gst-summary")
async def get_gst_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get GST collection summary for tax compliance"""
    
    try:
        query = """
            SELECT 
                CAST(STRFTIME('%Y-%m', i.invoice_date) as TEXT) as month,
                SUM(i.gst_amount) as total_gst,
                COUNT(*) as invoice_count,
                SUM(i.subtotal) as taxable_amount
            FROM invoices i
            WHERE 1=1
        """
        
        params = {}
        if start_date:
            query += " AND i.invoice_date >= :start_date"
            params['start_date'] = start_date
        if end_date:
            query += " AND i.invoice_date <= :end_date"
            params['end_date'] = end_date
        
        query += " GROUP BY STRFTIME('%Y-%m', i.invoice_date) ORDER BY month DESC"
        
        results = db.execute(text(query), params).fetchall()
        
        gst_data = [
            {
                "month": row[0],
                "total_gst": round(float(row[1] or 0), 2),
                "invoice_count": row[2],
                "taxable_amount": round(float(row[3] or 0), 2)
            }
            for row in results
        ]
        
        total_gst = sum(x['total_gst'] for x in gst_data)
        
        return {
            "success": True,
            "data": {
                "gst_summary": gst_data,
                "total_gst_collected": round(total_gst, 2),
                "tax_compliance_ready": True
            }
        }
        
    except Exception as e:
        logger.error(f"GST summary error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/analytics/payment-summary")
async def get_payment_summary(
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """Get payment collection analytics"""
    
    try:
        query = """
            SELECT 
                i.payment_status,
                COUNT(*) as invoice_count,
                SUM(i.total_amount) as total_value,
                SUM(i.amount_paid) as amount_collected,
                SUM(i.balance_amount) as balance_pending
            FROM invoices i
            WHERE i.invoice_date >= datetime('now', '-' || :days || ' days')
            GROUP BY i.payment_status
        """
        
        results = db.execute(text(query), {'days': days}).fetchall()
        
        summary = {
            "unpaid": {"count": 0, "value": 0, "collected": 0, "pending": 0},
            "partially_paid": {"count": 0, "value": 0, "collected": 0, "pending": 0},
            "paid": {"count": 0, "value": 0, "collected": 0, "pending": 0}
        }
        
        for row in results:
            status = row[0]
            if status in summary:
                summary[status] = {
                    "count": row[1],
                    "value": round(float(row[2] or 0), 2),
                    "collected": round(float(row[3] or 0), 2),
                    "pending": round(float(row[4] or 0), 2)
                }
        
        total_value = sum(x['value'] for x in summary.values())
        total_collected = sum(x['collected'] for x in summary.values())
        collection_rate = (total_collected / total_value * 100) if total_value > 0 else 0
        
        return {
            "success": True,
            "data": {
                "summary_by_status": summary,
                "total_invoiced": round(total_value, 2),
                "total_collected": round(total_collected, 2),
                "collection_rate": round(collection_rate, 2),
                "aging": {
                    "0_30_days": 0,
                    "31_60_days": 0,
                    "61_90_days": 0,
                    "over_90_days": 0
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Payment summary error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/analytics/revenue-by-customer")
async def get_revenue_by_customer(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Top customers by invoice value"""
    
    try:
        query = """
            SELECT 
                i.customer_name,
                COUNT(*) as invoice_count,
                SUM(i.total_amount) as total_revenue
            FROM invoices i
            WHERE i.status != 'cancelled'
            GROUP BY i.customer_id, i.customer_name
            ORDER BY total_revenue DESC
            LIMIT :limit
        """
        
        results = db.execute(text(query), {'limit': limit}).fetchall()
        
        customers = [
            {
                "customer_name": row[0],
                "invoice_count": row[1],
                "total_revenue": round(float(row[2] or 0), 2)
            }
            for row in results
        ]
        
        return {
            "success": True,
            "data": {
                "top_customers": customers,
                "count": len(customers)
            }
        }
        
    except Exception as e:
        logger.error(f"Revenue by customer error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/analytics/overdue-invoices")
async def get_overdue_invoices(
    db: Session = Depends(get_db)
):
    """Get overdue invoices for collection follow-up"""
    from app.api.db.invoicing_models import Invoice
    
    try:
        today = datetime.now()
        
        query = db.query(Invoice).filter(
            Invoice.due_date < today,
            Invoice.payment_status != "paid",
            Invoice.status != "cancelled"
        ).order_by(Invoice.due_date.asc()).all()
        
        overdue = [
            {
                "invoice_number": inv.invoice_number,
                "customer_name": inv.customer_name,
                "due_date": inv.due_date.isoformat(),
                "days_overdue": (today - inv.due_date).days,
                "balance_amount": inv.balance_amount,
                "total_amount": inv.total_amount
            }
            for inv in query
        ]
        
        total_overdue = sum(x['balance_amount'] for x in overdue)
        
        return {
            "success": True,
            "data": {
                "overdue_invoices": overdue,
                "count": len(overdue),
                "total_overdue_amount": round(total_overdue, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Overdue invoices error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# PDF & EMAIL ENDPOINTS (Phase 2B Continuation)
# ============================================================

@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Generate and download invoice as PDF"""
    from app.api.db.invoicing_models import Invoice
    from app.api.services.invoice_pdf_service import generate_invoice_pdf
    from fastapi.responses import StreamingResponse
    
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            return {"success": False, "error": "Invoice not found"}
        
        # Prepare invoice data for PDF
        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
            "due_date": invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
            "status": invoice.status,
            "payment_status": invoice.payment_status,
            "customer_name": invoice.customer_name,
            "customer_email": invoice.customer_email,
            "customer_phone": invoice.customer_phone or '',
            "subtotal": invoice.subtotal,
            "gst_amount": invoice.gst_amount,
            "gst_rate": invoice.gst_rate,
            "tds_amount": invoice.tds_amount,
            "tds_rate": invoice.tds_rate,
            "total_amount": invoice.total_amount,
            "amount_paid": invoice.amount_paid,
            "balance_amount": invoice.balance_amount,
            "notes": invoice.notes or '',
            "line_items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "gst_rate": item.gst_rate,
                    "line_total": item.line_total,
                    "gst_amount": item.gst_amount
                }
                for item in invoice.line_items
            ]
        }
        
        # Generate PDF
        pdf_file = generate_invoice_pdf(invoice_data)
        
        # Return as download
        return StreamingResponse(
            iter([pdf_file.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Invoice_{invoice.invoice_number}.pdf"}
        )
        
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/invoices/{invoice_id}/email")
async def email_invoice(
    invoice_id: int,
    recipient_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Send invoice via email with PDF attachment"""
    from app.api.db.invoicing_models import Invoice
    from app.api.services.invoice_pdf_service import generate_invoice_pdf
    from app.api.services.invoice_email_service import send_invoice_email
    
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            return {"success": False, "error": "Invoice not found"}
        
        # Prepare invoice data
        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
            "due_date": invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
            "status": invoice.status,
            "payment_status": invoice.payment_status,
            "customer_name": invoice.customer_name,
            "customer_email": invoice.customer_email,
            "customer_phone": invoice.customer_phone or '',
            "subtotal": invoice.subtotal,
            "gst_amount": invoice.gst_amount,
            "gst_rate": invoice.gst_rate,
            "tds_amount": invoice.tds_amount,
            "tds_rate": invoice.tds_rate,
            "total_amount": invoice.total_amount,
            "amount_paid": invoice.amount_paid,
            "balance_amount": invoice.balance_amount,
            "notes": invoice.notes or '',
            "line_items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "gst_rate": item.gst_rate,
                    "line_total": item.line_total
                }
                for item in invoice.line_items
            ]
        }
        
        # Generate PDF
        pdf_file = generate_invoice_pdf(invoice_data)
        
        # Send email
        result = send_invoice_email(
            invoice_data,
            pdf_file,
            recipient_email or invoice.customer_email
        )
        
        if result.get("success"):
            # Update invoice status
            invoice.status = "sent"
            db.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return {"success": False, "error": str(e)}
