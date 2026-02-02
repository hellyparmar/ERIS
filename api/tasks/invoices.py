"""
Celery Tasks - Invoice Processing
Async tasks for PDF generation, bulk operations, reminders
"""

from celery import shared_task
from datetime import datetime, timedelta
import logging

from api.db.database import SessionLocal
from api.services.invoice_service import InvoiceService
from api.services.whatsapp_service import WhatsAppReceiptService

logger = logging.getLogger(__name__)

@shared_task(name='api.tasks.invoices.generate_pdf_async')
def generate_pdf_async(invoice_id: int):
    """
    Generate invoice PDF asynchronously
    Prevents blocking the API
    """
    db = SessionLocal()
    try:
        from api.services.invoice_pdf_generator import InvoicePDFGenerator
        
        generator = InvoicePDFGenerator(db)
        pdf_path = generator.generate_pdf(invoice_id)
        
        logger.info(f"✅ PDF generated for invoice {invoice_id}: {pdf_path}")
        return {"status": "success", "invoice_id": invoice_id, "pdf_path": pdf_path}
        
    except Exception as e:
        logger.error(f"Error generating PDF for invoice {invoice_id}: {e}")
        return {"status": "error", "invoice_id": invoice_id, "message": str(e)}
    finally:
        db.close()

@shared_task(name='api.tasks.invoices.send_receipt_async')
def send_receipt_async(invoice_id: int, customer_id: int, whatsapp: str, email: str):
    """
    Send invoice receipt via WhatsApp/Email asynchronously
    """
    db = SessionLocal()
    try:
        from api.db.models import Invoice
        
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {"status": "error", "message": "Invoice not found"}
        
        whatsapp_service = WhatsAppReceiptService()
        result = whatsapp_service.send_invoice_receipt(
            customer_whatsapp=whatsapp,
            invoice_number=invoice.invoice_number,
            total_amount=float(invoice.total_amount),
            amount_due=float(invoice.amount_due),
            payment_status=invoice.payment_status,
            customer_id=customer_id,
            customer_email=email
        )
        
        logger.info(f"✅ Receipt sent for invoice {invoice_id}: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending receipt for invoice {invoice_id}: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@shared_task(name='api.tasks.invoices.mark_overdue_invoices')
def mark_overdue_invoices():
    """
    Mark invoices as overdue if past due date
    Runs daily at 12:30 AM
    """
    db = SessionLocal()
    try:
        service = InvoiceService(db)
        count = service.mark_overdue_invoices_batch()
        
        logger.info(f"✅ Marked {count} invoices as overdue")
        return {"status": "success", "count": count}
        
    except Exception as e:
        logger.error(f"Error marking overdue invoices: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@shared_task(name='api.tasks.invoices.send_payment_reminders')
def send_payment_reminders(days_overdue: int = 7):
    """
    Send payment reminders for overdue invoices
    Runs daily at 10 AM
    """
    db = SessionLocal()
    try:
        service = InvoiceService(db)
        overdue_invoices = service.get_overdue_invoices(days_overdue=days_overdue)
        
        whatsapp_service = WhatsAppReceiptService()
        
        reminders = []
        for invoice in overdue_invoices:
            if invoice.customer.whatsapp_number:
                reminders.append({
                    'whatsapp': invoice.customer.whatsapp_number,
                    'email': invoice.customer.email,  # Fallback
                    'invoice_number': invoice.invoice_number,
                    'amount_due': float(invoice.amount_due),
                    'days_overdue': (datetime.now().date() - invoice.due_date).days
                })
        
        results = whatsapp_service.send_bulk_reminders(reminders)
        
        logger.info(f"✅ Sent {results['sent']} reminders, {results['failed']} failed")
        return {
            "status": "success",
            "sent": results['sent'],
            "failed": results['failed'],
            "simulated": results.get('simulated', 0)
        }
        
    except Exception as e:
        logger.error(f"Error sending reminders: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@shared_task(name='api.tasks.invoices.bulk_invoice_generation')
def bulk_invoice_generation(sale_ids: list):
    """
    Generate invoices for multiple sales in bulk
    """
    db = SessionLocal()
    try:
        service = InvoiceService(db)
        results = []
        
        for sale_id in sale_ids:
            try:
                invoice = service.create_invoice_from_sale(sale_id)
                results.append({
                    "sale_id": sale_id,
                    "invoice_id": invoice.id,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "sale_id": sale_id,
                    "status": "error",
                    "message": str(e)
                })
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"✅ Generated {success_count}/{len(sale_ids)} invoices")
        
        return {
            "status": "complete",
            "total": len(sale_ids),
            "success": success_count,
            "failed": len(sale_ids) - success_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in bulk generation: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
