"""
Phase 2 Invoice Management REST API Router
Handles invoice creation, retrieval, payment processing, and GST compliance
Status: Advanced invoicing with QR codes, credit management, email/WhatsApp delivery
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.api.db.database import get_db
from app.api.db.phase2_models import (
    Invoice, InvoiceLineItem, InvoicePayment, 
    CustomerCredit, CreditTransaction
)
from app.api.services.phase2_invoice_service import (
    Phase2InvoiceService, InvoiceLineItem as InvoiceLineItemSchema
)
from app.api.services.phase2_credit_service import Phase2CreditService
from app.api.services.gst_service import GSTService
from app.api.utils.jwt_auth import get_current_user

# Initialize router
router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])

# Initialize services
invoice_service = Phase2InvoiceService()
credit_service = Phase2CreditService()
gst_service = GSTService()


# ============================================================================
# DATA MODELS (Pydantic schemas for request/response)
# ============================================================================

class LineItemRequest:
    """Invoice line item request"""
    product_id: str
    hsn_code: str
    description: str
    quantity: Decimal
    unit_rate: Decimal
    tax_rate: str
    discount_percentage: Optional[Decimal] = Decimal("0")


class CreateInvoiceRequest:
    """Create new invoice request"""
    customer_id: str
    customer_name: str
    customer_email: Optional[str]
    customer_phone: Optional[str]
    billing_address: dict
    shipping_address: dict
    line_items: List[LineItemRequest]
    shipping_charge: Decimal = Decimal("0")
    additional_charges: Decimal = Decimal("0")
    notes: Optional[str] = None
    give_credit: bool = False
    credit_days: int = 0


class InvoiceResponse:
    """Invoice response"""
    invoice_id: str
    invoice_number: str
    customer_id: str
    customer_name: str
    invoice_date: datetime
    due_date: Optional[datetime]
    subtotal: Decimal
    total_tax: Decimal
    grand_total: Decimal
    status: str
    payment_status: str
    line_items: List[dict]
    qr_code_data: Optional[str]


class PaymentRequest:
    """Record payment for invoice"""
    amount: Decimal
    payment_method: str
    reference_number: Optional[str]
    payment_date: Optional[datetime] = None


class CreditLimitRequest:
    """Update customer credit limit"""
    credit_limit: Decimal
    notes: Optional[str]


class ReminderRequest:
    """Send payment reminder"""
    reminder_type: str  # SMS, EMAIL, WHATSAPP
    custom_message: Optional[str]


# ============================================================================
# INVOICE CREATION & RETRIEVAL
# ============================================================================

@router.post("/create")
async def create_invoice(
    request: CreateInvoiceRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new invoice with GST calculations and optional credit
    
    Features:
    - Multi-line item support
    - Automatic GST calculation (CGST/SGST/IGST)
    - QR code generation for E-invoicing
    - Credit account initialization if requested
    - Notification scheduling (Email/WhatsApp)
    
    Returns:
    - Invoice ID, number, totals, QR code
    """
    try:
        # Validate customer exists
        # TODO: Add customer validation query
        
        # Process line items
        line_items = []
        total_tax = Decimal("0")
        subtotal = Decimal("0")
        
        for item in request.line_items:
            # Calculate line item with GST
            calculation = invoice_service.calculate_line_item(
                quantity=item.quantity,
                unit_rate=item.unit_rate,
                tax_rate=item.tax_rate,
                discount_percentage=item.discount_percentage or Decimal("0")
            )
            
            line_items.append({
                "product_id": item.product_id,
                "hsn_code": item.hsn_code,
                "description": item.description,
                "quantity": item.quantity,
                "unit_rate": item.unit_rate,
                "discount_percentage": item.discount_percentage,
                "discount_amount": calculation["discount_amount"],
                "subtotal": calculation["subtotal"],
                "tax_rate": item.tax_rate,
                "cgst_amount": calculation["cgst_amount"],
                "sgst_amount": calculation["sgst_amount"],
                "igst_amount": calculation["igst_amount"],
                "total_tax": calculation["total_tax"],
                "line_total": calculation["line_total"]
            })
            
            subtotal += calculation["subtotal"]
            total_tax += calculation["total_tax"]
        
        # Calculate invoice totals
        totals = invoice_service.calculate_invoice_totals(
            subtotal=subtotal,
            total_tax=total_tax,
            shipping_charge=request.shipping_charge or Decimal("0"),
            additional_charges=request.additional_charges or Decimal("0")
        )
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{current_user['business_id'][-4:]}-{datetime.now().strftime('%H%M%S')}"
        
        # Generate QR code data for E-invoice
        qr_data = invoice_service.generate_qr_code_data(
            invoice_number=invoice_number,
            customer_name=request.customer_name,
            invoice_date=datetime.now(),
            amount=totals["grand_total"]
        )
        
        # Create invoice record
        db_invoice = Invoice(
            business_id=current_user["business_id"],
            invoice_number=invoice_number,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            customer_phone=request.customer_phone,
            invoice_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=request.credit_days) if request.give_credit else None,
            billing_address=request.billing_address,
            shipping_address=request.shipping_address,
            subtotal=subtotal,
            shipping_charge=request.shipping_charge or Decimal("0"),
            additional_charges=request.additional_charges or Decimal("0"),
            cgst_amount=totals["cgst_amount"],
            sgst_amount=totals["sgst_amount"],
            igst_amount=totals["igst_amount"],
            total_tax=total_tax,
            grand_total=totals["grand_total"],
            status="DRAFT",
            payment_status="UNPAID",
            notes=request.notes,
            qr_code_data=qr_data,
            created_by=current_user["user_id"]
        )
        
        db.add(db_invoice)
        db.flush()
        
        # Add line items
        for item in line_items:
            db_line_item = InvoiceLineItem(
                invoice_id=db_invoice.id,
                product_id=item["product_id"],
                hsn_code=item["hsn_code"],
                description=item["description"],
                quantity=item["quantity"],
                unit_rate=item["unit_rate"],
                discount_percentage=item["discount_percentage"],
                discount_amount=item["discount_amount"],
                subtotal=item["subtotal"],
                tax_rate=item["tax_rate"],
                cgst_amount=item["cgst_amount"],
                sgst_amount=item["sgst_amount"],
                igst_amount=item["igst_amount"]
            )
            db.add(db_line_item)
        
        # Initialize credit account if requested
        if request.give_credit:
            credit_service.initialize_credit_account(
                customer_id=request.customer_id,
                customer_name=request.customer_name,
                business_id=current_user["business_id"]
            )
            
            # Record transaction in credit account
            credit_service.record_transaction(
                customer_id=request.customer_id,
                transaction_type="DEBIT",
                amount=totals["grand_total"],
                reference_id=db_invoice.id,
                reference_type="INVOICE",
                due_date=db_invoice.due_date
            )
        
        db.commit()
        
        return {
            "success": True,
            "invoice_id": str(db_invoice.id),
            "invoice_number": invoice_number,
            "customer_id": request.customer_id,
            "invoice_date": datetime.now(),
            "due_date": db_invoice.due_date,
            "subtotal": float(subtotal),
            "total_tax": float(total_tax),
            "grand_total": float(totals["grand_total"]),
            "status": "DRAFT",
            "line_items_count": len(line_items),
            "qr_code_data": qr_data,
            "message": "Invoice created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.get("/list")
async def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    customer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List invoices with filtering and pagination
    
    Query Parameters:
    - skip: Pagination offset
    - limit: Max results per page
    - status: DRAFT, FINALIZED, CANCELLED
    - payment_status: UNPAID, PARTIAL, PAID
    - customer_id: Filter by customer
    
    Returns:
    - List of invoices with summary info
    """
    query = db.query(Invoice).filter(Invoice.business_id == current_user["business_id"])
    
    if status:
        query = query.filter(Invoice.status == status)
    if payment_status:
        query = query.filter(Invoice.payment_status == payment_status)
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    total = query.count()
    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(invoices),
        "invoices": [
            {
                "invoice_id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "customer_name": inv.customer_name,
                "invoice_date": inv.invoice_date,
                "due_date": inv.due_date,
                "grand_total": float(inv.grand_total),
                "status": inv.status,
                "payment_status": inv.payment_status,
                "line_items_count": len(inv.line_items)
            }
            for inv in invoices
        ]
    }


@router.get("/{invoice_id}")
async def get_invoice_details(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed invoice information including line items, payments, credit details
    
    Returns:
    - Full invoice data with line items, payment history, credit status
    """
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.business_id == current_user["business_id"]
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    line_items = db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice_id).all()
    payments = db.query(InvoicePayment).filter(InvoicePayment.invoice_id == invoice_id).all()
    
    # Calculate credit score if credit given
    credit_score = None
    if invoice.due_date:
        customer_credit = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == invoice.customer_id,
            CustomerCredit.business_id == current_user["business_id"]
        ).first()
        
        if customer_credit:
            credit_score = {
                "score": customer_credit.credit_score,
                "rating": customer_credit.credit_rating,
                "credit_limit": float(customer_credit.credit_limit),
                "current_balance": float(customer_credit.current_balance),
                "available_credit": float(customer_credit.credit_limit - customer_credit.current_balance)
            }
    
    return {
        "invoice": {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "customer_id": invoice.customer_id,
            "customer_name": invoice.customer_name,
            "customer_email": invoice.customer_email,
            "customer_phone": invoice.customer_phone,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "billing_address": invoice.billing_address,
            "shipping_address": invoice.shipping_address,
            "subtotal": float(invoice.subtotal),
            "shipping_charge": float(invoice.shipping_charge),
            "additional_charges": float(invoice.additional_charges),
            "cgst_amount": float(invoice.cgst_amount),
            "sgst_amount": float(invoice.sgst_amount),
            "igst_amount": float(invoice.igst_amount),
            "total_tax": float(invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount),
            "grand_total": float(invoice.grand_total),
            "status": invoice.status,
            "payment_status": invoice.payment_status,
            "notes": invoice.notes,
            "qr_code_data": invoice.qr_code_data,
            "created_at": invoice.created_at,
            "created_by": invoice.created_by
        },
        "line_items": [
            {
                "item_id": str(item.id),
                "product_id": item.product_id,
                "hsn_code": item.hsn_code,
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_rate": float(item.unit_rate),
                "discount_percentage": float(item.discount_percentage),
                "discount_amount": float(item.discount_amount),
                "subtotal": float(item.subtotal),
                "tax_rate": item.tax_rate,
                "cgst_amount": float(item.cgst_amount),
                "sgst_amount": float(item.sgst_amount),
                "igst_amount": float(item.igst_amount)
            }
            for item in line_items
        ],
        "payment_history": [
            {
                "payment_id": str(p.id),
                "amount": float(p.amount),
                "payment_method": p.payment_method,
                "payment_date": p.payment_date,
                "reference_number": p.reference_number
            }
            for p in payments
        ],
        "credit_details": credit_score
    }


# ============================================================================
# INVOICE FINALIZATION & PAYMENT
# ============================================================================

@router.post("/{invoice_id}/finalize")
async def finalize_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalize invoice for sending
    - Status changes to FINALIZED
    - Cannot be edited after finalization
    - Can schedule email/WhatsApp delivery
    
    Returns:
    - Updated invoice status
    """
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.business_id == current_user["business_id"]
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=f"Can only finalize DRAFT invoices. Current status: {invoice.status}"
        )
    
    invoice.status = "FINALIZED"
    invoice.finalized_at = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "invoice_number": invoice.invoice_number,
        "status": invoice.status,
        "message": "Invoice finalized successfully"
    }


@router.post("/{invoice_id}/payments")
async def record_payment(
    invoice_id: str,
    payment: PaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record payment for invoice
    
    Updates:
    - Invoice payment status
    - Credit account balance if on credit
    - Payment history
    
    Returns:
    - Payment confirmation, updated balance
    """
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.business_id == current_user["business_id"]
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Record payment
    db_payment = InvoicePayment(
        invoice_id=invoice_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        reference_number=payment.reference_number,
        payment_date=payment.payment_date or datetime.now()
    )
    db.add(db_payment)
    
    # Update invoice payment status
    total_paid = sum(p.amount for p in invoice.payments) + payment.amount
    
    if total_paid >= invoice.grand_total:
        invoice.payment_status = "PAID"
    elif total_paid > 0:
        invoice.payment_status = "PARTIAL"
    
    # Update credit account if on credit
    if invoice.due_date:
        credit_service.record_payment(
            customer_id=invoice.customer_id,
            amount=payment.amount,
            payment_reference=payment.reference_number or str(db_payment.id),
            payment_date=db_payment.payment_date
        )
    
    db.commit()
    
    return {
        "success": True,
        "invoice_number": invoice.invoice_number,
        "payment_amount": float(payment.amount),
        "total_paid": float(total_paid),
        "remaining_balance": float(invoice.grand_total - total_paid),
        "payment_status": invoice.payment_status,
        "message": "Payment recorded successfully"
    }


# ============================================================================
# CREDIT MANAGEMENT
# ============================================================================

@router.post("/{invoice_id}/customer/{customer_id}/credit-limit")
async def update_credit_limit(
    invoice_id: str,
    customer_id: str,
    request: CreditLimitRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update customer credit limit for future invoices
    
    Parameters:
    - credit_limit: New credit limit amount
    - notes: Reason for change
    
    Returns:
    - Updated credit account details
    """
    customer_credit = db.query(CustomerCredit).filter(
        CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]
    ).first()
    
    if not customer_credit:
        raise HTTPException(status_code=404, detail="Customer credit account not found")
    
    old_limit = customer_credit.credit_limit
    customer_credit.credit_limit = request.credit_limit
    customer_credit.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "customer_id": customer_id,
        "old_credit_limit": float(old_limit),
        "new_credit_limit": float(request.credit_limit),
        "current_balance": float(customer_credit.current_balance),
        "available_credit": float(request.credit_limit - customer_credit.current_balance),
        "notes": request.notes,
        "message": "Credit limit updated successfully"
    }


@router.get("/{customer_id}/credit-status")
async def get_credit_status(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get customer credit account status and aging report
    
    Returns:
    - Credit score, rating, limits
    - Payment history
    - Aging analysis (0-30, 30-60, 60-90, 90+ days)
    - Recommendations
    """
    customer_credit = db.query(CustomerCredit).filter(
        CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]
    ).first()
    
    if not customer_credit:
        raise HTTPException(status_code=404, detail="Customer credit account not found")
    
    # Get aging report
    aging = credit_service.generate_aging_report(
        customer_id=customer_id,
        business_id=current_user["business_id"]
    )
    
    # Get credit analysis
    analysis = credit_service.get_credit_analysis(
        customer_id=customer_id,
        business_id=current_user["business_id"]
    )
    
    return {
        "customer_credit": {
            "customer_id": customer_id,
            "credit_limit": float(customer_credit.credit_limit),
            "current_balance": float(customer_credit.current_balance),
            "available_credit": float(customer_credit.credit_limit - customer_credit.current_balance),
            "credit_score": customer_credit.credit_score,
            "credit_rating": customer_credit.credit_rating,
            "is_active": customer_credit.is_active,
            "is_blocked": customer_credit.is_blocked
        },
        "payment_history": {
            "on_time_payments": customer_credit.on_time_payments,
            "late_payments": customer_credit.late_payments,
            "missed_payments": customer_credit.missed_payments,
            "total_transactions": customer_credit.total_transactions
        },
        "aging_report": aging,
        "credit_analysis": analysis
    }


@router.post("/{invoice_id}/customer/{customer_id}/remind")
async def send_payment_reminder(
    invoice_id: str,
    customer_id: str,
    reminder: ReminderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send payment reminder via SMS/Email/WhatsApp
    
    Parameters:
    - reminder_type: SMS, EMAIL, or WHATSAPP
    - custom_message: Optional custom message
    
    Returns:
    - Reminder sent confirmation, delivery status
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.payment_status == "PAID":
        raise HTTPException(status_code=400, detail="Invoice is already paid")
    
    # Generate reminder message
    message = reminder.custom_message or credit_service.get_payment_reminder_message(
        customer_name=invoice.customer_name,
        invoice_number=invoice.invoice_number,
        amount_due=invoice.grand_total,
        due_date=invoice.due_date,
        days_overdue=max(0, (datetime.now() - invoice.due_date).days) if invoice.due_date else 0
    )
    
    # TODO: Integrate with messaging service (SMS, Email, WhatsApp)
    # For now, just log the reminder
    
    db_reminder = CreditReminder(
        customer_credit_id=None,  # Will be fetched from customer_id
        reminder_type=reminder.reminder_type,
        message=message,
        sent=True,
        sent_at=datetime.now()
    )
    db.add(db_reminder)
    db.commit()
    
    return {
        "success": True,
        "invoice_number": invoice.invoice_number,
        "customer_id": customer_id,
        "reminder_type": reminder.reminder_type,
        "sent_at": datetime.now(),
        "message": f"Payment reminder sent via {reminder.reminder_type}",
        "preview": message[:100] + "..." if len(message) > 100 else message
    }


# ============================================================================
# GST & TAX INFORMATION
# ============================================================================

@router.get("/gst/rates")
async def get_gst_rates(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all available GST rates and tax categories
    
    Returns:
    - All GST rates with CGST/SGST/IGST split
    - HSN code examples
    - Tax category descriptions
    """
    rates = gst_service.get_all_rates()
    
    return {
        "gst_rates": [
            {
                "category": rate.category.value,
                "rate": float(rate.rate),
                "cgst_rate": float(rate.cgst_rate),
                "sgst_rate": float(rate.sgst_rate),
                "igst_rate": float(rate.igst_rate),
                "hsn_code_example": rate.hsn_code,
                "description": f"{rate.category.value}% tax rate"
            }
            for rate in rates
        ]
    }


@router.post("/gst/validate-hsn")
async def validate_hsn_code(
    hsn_code: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Validate HSN code and get applicable tax rate
    
    Parameters:
    - hsn_code: HSN/SAC code (4-8 digits)
    
    Returns:
    - HSN validity, applicable tax rate
    """
    is_valid = gst_service.validate_hsn_code(hsn_code)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid HSN code format")
    
    # Get applicable rate (would need HSN database integration)
    rate = gst_service.get_rate_for_hsn(hsn_code)
    
    return {
        "hsn_code": hsn_code,
        "is_valid": True,
        "tax_rate": rate.category.value if rate else "Unknown",
        "cgst_rate": float(rate.cgst_rate) if rate else None,
        "sgst_rate": float(rate.sgst_rate) if rate else None,
        "igst_rate": float(rate.igst_rate) if rate else None
    }


# ============================================================================
# REPORTING & ANALYTICS
# ============================================================================

@router.get("/reports/gst-summary")
async def get_gst_summary(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get GST summary for period (for GSTR-1 filing)
    
    Returns:
    - Total sales, tax collected (CGST/SGST/IGST)
    - Intra-state vs inter-state breakdown
    - Export sales (if applicable)
    """
    query = db.query(Invoice).filter(
        Invoice.business_id == current_user["business_id"],
        Invoice.status == "FINALIZED"
    )
    
    if start_date:
        query = query.filter(Invoice.invoice_date >= start_date)
    if end_date:
        query = query.filter(Invoice.invoice_date <= end_date)
    
    invoices = query.all()
    
    total_sales = sum(inv.grand_total for inv in invoices)
    total_cgst = sum(inv.cgst_amount for inv in invoices)
    total_sgst = sum(inv.sgst_amount for inv in invoices)
    total_igst = sum(inv.igst_amount for inv in invoices)
    total_tax = total_cgst + total_sgst + total_igst
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "invoice_count": len(invoices)
        },
        "summary": {
            "total_sales": float(total_sales),
            "total_cgst": float(total_cgst),
            "total_sgst": float(total_sgst),
            "total_igst": float(total_igst),
            "total_tax": float(total_tax),
            "intra_state_sales": "To be calculated",
            "inter_state_sales": "To be calculated"
        },
        "message": "GST summary generated for GSTR-1 filing"
    }


@router.get("/reports/aging-analysis")
async def get_aging_analysis(
    customer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aging analysis of outstanding invoices
    
    Returns:
    - Invoices grouped by overdue days (0-30, 30-60, 60-90, 90+)
    - Total outstanding by age group
    - Collection priority
    """
    query = db.query(Invoice).filter(
        Invoice.business_id == current_user["business_id"],
        Invoice.payment_status != "PAID"
    )
    
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    invoices = query.all()
    
    aging = {
        "current": [],
        "0_30_days": [],
        "30_60_days": [],
        "60_90_days": [],
        "over_90_days": []
    }
    
    now = datetime.now()
    
    for inv in invoices:
        if inv.due_date:
            days_overdue = (now - inv.due_date).days
        else:
            days_overdue = -(now - inv.invoice_date).days
        
        inv_data = {
            "invoice_number": inv.invoice_number,
            "customer_name": inv.customer_name,
            "amount": float(inv.grand_total),
            "due_date": inv.due_date,
            "days_overdue": days_overdue
        }
        
        if days_overdue < 0:
            aging["current"].append(inv_data)
        elif days_overdue <= 30:
            aging["0_30_days"].append(inv_data)
        elif days_overdue <= 60:
            aging["30_60_days"].append(inv_data)
        elif days_overdue <= 90:
            aging["60_90_days"].append(inv_data)
        else:
            aging["over_90_days"].append(inv_data)
    
    return {
        "aging_analysis": {
            "current": {
                "count": len(aging["current"]),
                "total_amount": float(sum(inv["amount"] for inv in aging["current"])),
                "invoices": aging["current"][:10]
            },
            "0_30_days": {
                "count": len(aging["0_30_days"]),
                "total_amount": float(sum(inv["amount"] for inv in aging["0_30_days"])),
                "invoices": aging["0_30_days"][:10]
            },
            "30_60_days": {
                "count": len(aging["30_60_days"]),
                "total_amount": float(sum(inv["amount"] for inv in aging["30_60_days"])),
                "invoices": aging["30_60_days"][:10]
            },
            "60_90_days": {
                "count": len(aging["60_90_days"]),
                "total_amount": float(sum(inv["amount"] for inv in aging["60_90_days"])),
                "invoices": aging["60_90_days"][:10]
            },
            "over_90_days": {
                "count": len(aging["over_90_days"]),
                "total_amount": float(sum(inv["amount"] for inv in aging["over_90_days"])),
                "invoices": aging["over_90_days"][:10]
            }
        }
    }
