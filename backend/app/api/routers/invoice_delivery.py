"""
Invoice PDF Generation & Delivery API Routes
Endpoints for generating and delivering GST-compliant invoices
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr
from io import BytesIO

from app.api.services.gst_invoice_pdf import GSTInvoicePDF
from app.api.services.whatsapp_invoice_service import MockWhatsAppService
from app.api.dependencies import get_db, get_current_user
from app.api.middleware.tenant_context import require_organization

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoice PDF & Delivery"])


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class PDFGenerationRequest(BaseModel):
    """Request to generate PDF"""
    invoice_id: UUID


class EmailDeliveryRequest(BaseModel):
    """Request to email invoice"""
    invoice_id: UUID
    to_email: EmailStr
    cc: Optional[list[EmailStr]] = None


class WhatsAppDeliveryRequest(BaseModel):
    """Request to send invoice via WhatsApp"""
    invoice_id: UUID
    to_number: str  # Format: +91xxxxxxxxxx


# ============================================================
# PDF GENERATION ENDPOINTS
# ============================================================

@router.get("/{invoice_id}/pdf")
async def generate_invoice_pdf(
    invoice_id: UUID,
    download: bool = Query(False, description="Download as attachment"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate and return invoice PDF
    
    Query params:
    - download: If true, returns as attachment. If false, displays inline.
    """
    try:
        # Get invoice data
        invoice_query = """
            SELECT 
                i.*,
                o.name as seller_name,
                o.legal_name as seller_legal_name,
                o.gstin as seller_gstin,
                o.pan as seller_pan,
                o.address as seller_address,
                o.contact_phone as seller_phone,
                o.contact_email as seller_email,
                c.name as customer_name,
                c.gstin as customer_gstin,
                c.address as customer_address,
                c.phone as customer_phone,
                c.email as customer_email
            FROM invoices i
            LEFT JOIN organizations o ON i.organization_id = o.id
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.id = :invoice_id
              AND i.organization_id = :org_id
        """
        
        invoice = db.execute(invoice_query, {
            'invoice_id': str(invoice_id),
            'org_id': current_user['organization_id']
        }).fetchone()
        
        if not invoice:
            raise HTTPException(404, "Invoice not found")
        
        # Get line items
        items_query = """
            SELECT 
                ii.*,
                p.name as product_name,
                p.hsn_code
            FROM invoice_items ii
            LEFT JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = :invoice_id
            ORDER BY ii.id
        """
        
        line_items_raw = db.execute(items_query, {'invoice_id': str(invoice_id)}).fetchall()
        
        if not line_items_raw:
            raise HTTPException(400, "Invoice has no line items")
        
        # Prepare data structures
        invoice_data = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': str(invoice.invoice_date),
            'customer_gstin': invoice.customer_gstin,
            'place_of_supply': invoice.place_of_supply,
            'reverse_charge': invoice.reverse_charge,
            'is_interstate': invoice.is_interstate,
            'taxable_amount': float(invoice.taxable_amount),
            'cgst_amount': float(invoice.cgst_amount or 0),
            'sgst_amount': float(invoice.sgst_amount or 0),
            'igst_amount': float(invoice.igst_amount or 0),
            'cess_amount': float(invoice.cess_amount or 0),
            'total_tax': float(invoice.total_tax or 0),
            'round_off': float(invoice.round_off or 0),
            'grand_total': float(invoice.total_amount),
            'signed_qr_code': invoice.signed_qr_code
        }
        
        seller_data = {
            'name': invoice.seller_name,
            'legal_name': invoice.seller_legal_name,
            'gstin': invoice.seller_gstin,
            'pan': invoice.seller_pan,
            'address': invoice.seller_address or {},
            'contact_phone': invoice.seller_phone,
            'contact_email': invoice.seller_email
        }
        
        buyer_data = {
            'name': invoice.customer_name or 'Cash Customer',
            'gstin': invoice.customer_gstin,
            'address': invoice.customer_address or {},
            'phone': invoice.customer_phone,
            'email': invoice.customer_email
        }
        
        line_items = []
        for item in line_items_raw:
            line_items.append({
                'name': item.product_name or 'Product',
                'hsn_code': item.hsn_code or '',
                'quantity': float(item.quantity),
                'unit': item.unit or 'PCS',
                'unit_price': float(item.unit_price),
                'tax_breakdown': {
                    'discount_amount': float(item.discount_amount or 0),
                    'taxable_amount': float(item.taxable_amount),
                    'cgst_rate': float(item.cgst_rate or 0),
                    'cgst_amount': float(item.cgst_amount or 0),
                    'sgst_rate': float(item.sgst_rate or 0),
                    'sgst_amount': float(item.sgst_amount or 0),
                    'igst_rate': float(item.igst_rate or 0),
                    'igst_amount': float(item.igst_amount or 0),
                    'cess_rate': float(item.cess_rate or 0),
                    'cess_amount': float(item.cess_amount or 0),
                    'total_amount': float(item.total_amount)
                }
            })
        
        # Generate PDF
        pdf_generator = GSTInvoicePDF()
        pdf_bytes = pdf_generator.generate(
            invoice_data,
            seller_data,
            buyer_data,
            line_items
        )
        
        # Return PDF
        buffer = BytesIO(pdf_bytes)
        
        filename = f"Invoice_{invoice.invoice_number}.pdf"
        
        if download:
            content_disposition = f'attachment; filename="{filename}"'
        else:
            content_disposition = f'inline; filename="{filename}"'
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                'Content-Disposition': content_disposition
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {str(e)}")


# ============================================================
# EMAIL DELIVERY ENDPOINT
# ============================================================

@router.post("/{invoice_id}/email")
async def email_invoice(
    invoice_id: UUID,
    request: EmailDeliveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Email invoice PDF to customer
    
    NOTE: Requires SMTP configuration in environment
    """
    # TODO: Implement actual email sending
    # For now, return mock response
    
    return {
        'success': True,
        'invoice_id': str(invoice_id),
        'message': f'Email sent to {request.to_email}',
        'note': 'This is a mock response. Configure SMTP to enable actual email delivery.'
    }


# ============================================================
# WHATSAPP DELIVERY ENDPOINT
# ============================================================

@router.post("/{invoice_id}/whatsapp")
async def whatsapp_invoice(
    invoice_id: UUID,
    request: WhatsAppDeliveryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send invoice via WhatsApp
    
    NOTE: Requires Twilio WhatsApp Business API configuration
    """
    try:
        # Get basic invoice info
        invoice = db.execute("""
            SELECT invoice_number, total_amount
            FROM invoices
            WHERE id = :invoice_id
              AND organization_id = :org_id
        """, {
            'invoice_id': str(invoice_id),
            'org_id': current_user['organization_id']
        }).fetchone()
        
        if not invoice:
            raise HTTPException(404, "Invoice not found")
        
        # Use mock service (replace with actual Twilio service in production)
        whatsapp_service = MockWhatsAppService()
        
        invoice_data = {
            'customer_name': 'Customer',
            'invoice_number': invoice.invoice_number,
            'grand_total': float(invoice.total_amount)
        }
        
        # Mock PDF URL (in production, upload PDF to cloud storage first)
        pdf_url = f"https://example.com/invoices/{invoice.invoice_number}.pdf"
        
        success = whatsapp_service.send_invoice_whatsapp(
            to_number=f"whatsapp:{request.to_number}",
            invoice_number=invoice.invoice_number,
            pdf_url=pdf_url,
            invoice_data=invoice_data
        )
        
        if success:
            return {
                'success': True,
                'invoice_id': str(invoice_id),
                'to_number': request.to_number,
                'message': f'Invoice {invoice.invoice_number} sent via WhatsApp',
                'note': 'This is a mock response. Configure Twilio to enable actual WhatsApp delivery.'
            }
        else:
            raise HTTPException(500, "Failed to send WhatsApp message")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"WhatsApp delivery failed: {str(e)}")


# ============================================================
# BULK OPERATIONS
# ============================================================

@router.post("/bulk/email")
async def bulk_email_invoices(
    invoice_ids: list[UUID],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Email multiple invoices in bulk
    """
    return {
        'success': True,
        'total': len(invoice_ids),
        'message': f'{len(invoice_ids)} invoices queued for email delivery',
        'note': 'This is a mock response. Configure SMTP for actual bulk email.'
    }
