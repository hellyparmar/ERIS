"""
Invoice Service

Shared invoice service for sales-to-invoice workflows, GST calculations,
PDF generation, GSTR-1 export and Tally XML export.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import Invoice, SaleTransaction
from app.models.sale import SaleItem
from app.models.product import Product
from app.models.users import User
from app.models.invoicing import InvoiceStatus, InvoiceType
from app.services.base_service import OutletIsolatedService
from app.api.services.invoice_pdf_generator import InvoicePDFGenerator
from app.api.services.invoice_email_service import InvoiceEmailService
from app.api.services.tally_connector import TallyConnector
from app.api.services import gstr1_service


class InvoiceService(OutletIsolatedService):
    """Invoice service for generating invoices from sales and exporting billing data."""

    def __init__(self, db: Session, current_user: User):
        super().__init__(db, current_user)

    def generate_invoice_number(self) -> str:
        """Generate a unique invoice number using today's date and sequence."""
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        start_of_next_day = start_of_day + timedelta(days=1)

        existing_count = self.db.query(func.count(Invoice.id)).filter(
            and_(
                Invoice.invoice_date >= start_of_day,
                Invoice.invoice_date < start_of_next_day,
            )
        ).scalar() or 0

        return f"INV-{today.strftime('%Y%m%d')}-{int(existing_count) + 1:04d}"

    def calculate_gst(
        self,
        amount: Decimal,
        gst_rate: Decimal,
        inter_state: bool = False
    ) -> Dict[str, Any]:
        """Calculate GST breakdown from a taxable amount."""
        taxable_amount = Decimal(amount).quantize(Decimal("0.01"))
        gst_rate = Decimal(gst_rate).quantize(Decimal("0.01"))

        total_tax = (taxable_amount * gst_rate / Decimal("100")).quantize(Decimal("0.01"))
        if inter_state:
            return {
                "taxable_amount": taxable_amount,
                "cgst_amount": Decimal("0.00"),
                "sgst_amount": Decimal("0.00"),
                "igst_amount": total_tax,
                "total_amount": (taxable_amount + total_tax).quantize(Decimal("0.01")),
                "tax_rate": gst_rate,
                "gst_type": "IGST",
            }

        half_tax = (total_tax / Decimal("2")).quantize(Decimal("0.01"))
        return {
            "taxable_amount": taxable_amount,
            "cgst_amount": half_tax,
            "sgst_amount": half_tax,
            "igst_amount": Decimal("0.00"),
            "total_amount": (taxable_amount + total_tax).quantize(Decimal("0.01")),
            "tax_rate": gst_rate,
            "gst_type": "CGST+SGST",
        }

    def create_invoice_from_sale(self, sale_id: Any, payment_terms_days: int = 30) -> Invoice:
        """Create a new invoice record from an existing sale."""
        sale = self.db.query(SaleTransaction).filter(SaleTransaction.id == sale_id).first()
        if not sale:
            raise ValueError(f"Sale {sale_id} not found")
        if sale.invoice_id is not None:
            raise ValueError(f"Sale {sale_id} is already invoiced")

        customer = sale.customer
        customer_name = getattr(customer, "name", "Walk-in Customer")
        customer_gstin = getattr(customer, "gstin", "")
        customer_address = getattr(customer, "address", "")

        invoice_number = self.generate_invoice_number()
        amount_paid = Decimal(sale.amount_paid or 0).quantize(Decimal("0.01"))
        total_amount = Decimal(sale.total_amount or 0).quantize(Decimal("0.01"))
        amount_due = (total_amount - amount_paid).quantize(Decimal("0.01"))
        payment_status = InvoiceStatus.PAID.value if amount_due <= 0 else (
            InvoiceStatus.PARTIALLY_PAID.value if amount_paid > 0 else InvoiceStatus.ISSUED.value
        )

        invoice = Invoice(
            invoice_number=invoice_number,
            organization_id=sale.organization_id,
            store_id=sale.store_id,
            customer_id=sale.customer_id,
            billed_to_name=customer_name,
            billed_to_gstin=customer_gstin or None,
            billed_to_address=customer_address,
            invoice_type=InvoiceType.TAX_INVOICE.value,
            invoice_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=payment_terms_days),
            subtotal=Decimal(sale.subtotal or 0).quantize(Decimal("0.01")),
            discount=Decimal(sale.discount or 0).quantize(Decimal("0.01")),
            tax_amount=Decimal(sale.tax_amount or 0).quantize(Decimal("0.01")),
            total_amount=total_amount,
            amount_paid=amount_paid,
            amount_due=amount_due,
            payment_status=payment_status,
            payment_terms=f"Net {payment_terms_days}",
            notes=f"Invoice generated from sale {sale.transaction_id}",
        )

        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)

        sale.invoice_id = invoice.id
        self.db.commit()

        return invoice

    def get_invoice_detail(self, invoice_id: int) -> Dict[str, Any]:
        """Return full invoice detail including linked sale line items and payments."""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        sale = self.db.query(SaleTransaction).filter(SaleTransaction.invoice_id == invoice.id).first()
        line_items: List[Dict[str, Any]] = []

        if sale:
            for item in sale.items:
                product_name = item.product_name or getattr(item.product, "name", "Item")
                hsn_code = getattr(item.product, "hsn_code", None) or ""
                line_items.append({
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "product_name": product_name,
                    "hsn_code": hsn_code,
                    "quantity": int(item.quantity),
                    "unit_price": float(item.unit_price),
                    "tax_rate": float(item.tax_rate),
                    "tax_amount": float(item.tax_amount),
                    "discount": float(item.discount or 0),
                    "line_total": float(item.line_total),
                })

        payments = []
        for payment in getattr(invoice, "payments", []):
            payment_date = getattr(payment, "payment_date", None)
            payments.append({
                "id": payment.id,
                "amount": float(getattr(payment, "amount", 0)),
                "payment_method": getattr(payment, "payment_method", ""),
                "reference_number": getattr(payment, "reference_number", None),
                "payment_date": payment_date.isoformat() if payment_date else None,
            })

        return {
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "organization_id": str(invoice.organization_id),
                "store_id": str(invoice.store_id),
                "customer_id": str(invoice.customer_id) if invoice.customer_id else None,
                "billed_to_name": invoice.billed_to_name,
                "billed_to_gstin": invoice.billed_to_gstin,
                "billed_to_address": invoice.billed_to_address,
                "invoice_type": invoice.invoice_type,
                "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "subtotal": float(invoice.subtotal or 0),
                "discount": float(invoice.discount or 0),
                "tax_amount": float(invoice.tax_amount or 0),
                "total_amount": float(invoice.total_amount or 0),
                "amount_paid": float(invoice.amount_paid or 0),
                "amount_due": float(invoice.amount_due or 0),
                "payment_status": invoice.payment_status,
                "payment_terms": invoice.payment_terms,
                "notes": invoice.notes,
            },
            "line_items": line_items,
            "payments": payments,
            "sale_id": str(sale.id) if sale else None,
            "customer_name": invoice.billed_to_name,
            "customer_gstin": invoice.billed_to_gstin,
        }

    def generate_pdf_invoice(self, invoice_id: int) -> bytes:
        """Generate PDF bytes for a stored invoice."""
        invoice_data = self.get_invoice_detail(invoice_id)
        generator = InvoicePDFGenerator()
        return generator.generate_invoice_pdf(invoice_data)

    def send_invoice_email(self, invoice_id: int, recipient_email: Optional[str] = None) -> Dict[str, Any]:
        """Send invoice copy via email with PDF attachment."""
        invoice_data = self.get_invoice_detail(invoice_id)
        if recipient_email:
            invoice_data["customer_email"] = recipient_email

        pdf_bytes = self.generate_pdf_invoice(invoice_id)
        pdf_buffer = BytesIO(pdf_bytes)

        email_service = InvoiceEmailService()
        return email_service.send_invoice(invoice_data, pdf_buffer, recipient_email)

    def export_gstr1_data(self, month: int, year: int) -> Dict[str, Any]:
        """Export GSTR-1 JSON-ready reporting data for a month."""
        return gstr1_service.generate_gstr1_report(self.db, month, year)

    def export_tally_xml(self, invoice_id: int) -> str:
        """Build Tally-compatible XML for a single invoice."""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        sale = self.db.query(SaleTransaction).filter(SaleTransaction.invoice_id == invoice.id).first()
        items = []

        if sale:
            for item in sale.items:
                product_name = item.product_name or getattr(item.product, "name", "Item")
                items.append({
                    "product_name": product_name,
                    "unit_price": float(item.unit_price),
                    "total": float(item.line_total),
                })

        if not items:
            items.append({
                "product_name": invoice.billed_to_name or "Product Sale",
                "unit_price": float(invoice.subtotal or 0),
                "total": float(invoice.total_amount or 0),
            })

        tally_payload = {
            "date": invoice.invoice_date,
            "invoice_number": invoice.invoice_number,
            "customer_ledger_name": invoice.billed_to_name or "Cash Customer",
            "total_amount": float(invoice.total_amount or 0),
            "items": items,
        }

        return TallyConnector._create_voucher_xml(tally_payload)
