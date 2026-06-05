"""
Invoice Service - Transaction Engine Core
Handles invoice generation, GST calculation, and Khata/credit management
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

Invoice = None
InvoicePayment = None
Customer = None
Product = None

def _load_phase2_models():
    global Invoice, InvoicePayment, Customer, Product
    if Invoice is None:
        from app.models.phase2_models import Invoice as Phase2Invoice, InvoicePayment as Phase2InvoicePayment, Customer as Phase2Customer, Product as Phase2Product
        Invoice = Phase2Invoice
        InvoicePayment = Phase2InvoicePayment
        Customer = Phase2Customer
        Product = Phase2Product

from app.models.sale import Sale
from app.models.schema import PaymentStatusEnum as PaymentStatus
from app.services.base_service import OutletIsolatedService
from app.models.users import User

class InvoiceService(OutletIsolatedService):
    """Service for invoice operations with GST automation"""
    
    def __init__(self, db: Session, current_user: User):
        _load_phase2_models()
        super().__init__(db, current_user)
    
    def generate_invoice_number(self) -> str:
        """Generate unique invoice number: INV-YYYYMMDD-XXXX"""
        today = datetime.now()
        date_prefix = today.strftime("%Y%m%d")
        
        # Get count of invoices created today
        count = self.db.query(Invoice).filter(
            func.date(Invoice.invoice_date) == today.date()
        ).count()
        
        sequence = str(count + 1).zfill(4)
        return f"INV-{date_prefix}-{sequence}"
    
    def calculate_gst(self, amount: Decimal, gst_rate: Decimal) -> Dict[str, Decimal]:
        """
        Calculate GST breakdown
        
        Returns:
            taxable_amount: Amount before tax
            tax_amount: GST amount
            total_amount: Amount including tax
        """
        # Amount is inclusive of GST
        taxable_amount = amount / (1 + (gst_rate / 100))
        tax_amount = amount - taxable_amount
        
        return {
            "taxable_amount": round(taxable_amount, 2),
            "tax_amount": round(tax_amount, 2),
            "total_amount": round(amount, 2)
        }
    
    def create_invoice_from_sale(
        self, 
        sale_id: int,
        payment_terms_days: int = 30
    ) -> Invoice:
        """
        Create invoice from a sale transaction
        
        Args:
            sale_id: ID of the sale
            payment_terms_days: Payment due in X days (default 30)
        
        Returns:
            Created invoice
        """
        # Get sale with product and customer
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise ValueError(f"Sale {sale_id} not found")
        
        product = self.db.query(Product).filter(Product.id == sale.product_id).first()
        customer = self.db.query(Customer).filter(Customer.id == sale.customer_id).first()
        
        if not product:
            raise ValueError(f"Product {sale.product_id} not found")
        
        # Calculate GST breakdown
        gst_rate = product.gst_rate or Decimal("18.0")
        gst_breakdown = self.calculate_gst(
            Decimal(str(sale.total_amount)),
            gst_rate
        )
        
        # Create invoice
        invoice = Invoice(
            invoice_number=self.generate_invoice_number(),
            customer_id=sale.customer_id,
            hsn_code=product.hsn_code,
            tax_rate=gst_rate,
            taxable_amount=gst_breakdown["taxable_amount"],
            tax_amount=gst_breakdown["tax_amount"],
            total_amount=gst_breakdown["total_amount"],
            payment_status=sale.payment_status or PaymentStatus.PENDING,
            amount_paid=Decimal("0.0") if sale.payment_status == PaymentStatus.PENDING else gst_breakdown["total_amount"],
            amount_due=gst_breakdown["total_amount"] if sale.payment_status == PaymentStatus.PENDING else Decimal("0.0"),
            invoice_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=payment_terms_days)
        )
        
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        
        # Update sale with invoice reference
        sale.invoice_id = invoice.id
        self.db.commit()
        
        # Handle partial payment setup
        if sale.payment_status == PaymentStatus.PARTIAL and sale.installments:
            self._setup_installment_plan(invoice, sale.installments)
        
        return invoice
    
    def _setup_installment_plan(self, invoice: Invoice, num_installments: int):
        """Setup installment plan for Khata customers"""
        amount_per_installment = invoice.total_amount / num_installments
        
        # Record first installment as paid
        first_payment = InvoicePayment(
            invoice_id=invoice.id,
            amount_paid=amount_per_installment,
            payment_method="initial",
            notes=f"First installment of {num_installments}"
        )
        self.db.add(first_payment)
        
        # Update invoice amounts
        invoice.amount_paid = amount_per_installment
        invoice.amount_due = invoice.total_amount - amount_per_installment
        invoice.payment_status = PaymentStatus.PARTIAL
        
        self.db.commit()
    
    def record_payment(
        self,
        invoice_id: int,
        amount: Decimal,
        payment_method: str,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> InvoicePayment:
        """
        Record a payment against an invoice (Khata tracking)
        
        Args:
            invoice_id: Invoice ID
            amount: Payment amount
            payment_method: cash, card, upi, neft, etc.
            reference_number: Transaction reference
            notes: Additional notes
        
        Returns:
            Created payment record
        """
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Validate payment amount
        if amount > invoice.amount_due:
            raise ValueError(f"Payment amount ₹{amount} exceeds due amount ₹{invoice.amount_due}")
        
        # Create payment record
        payment = InvoicePayment(
            invoice_id=invoice_id,
            amount_paid=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes
        )
        self.db.add(payment)
        
        # Update invoice
        invoice.amount_paid += amount
        invoice.amount_due -= amount
        
        # Update payment status
        if invoice.amount_due <= 0:
            invoice.payment_status = PaymentStatus.PAID
        else:
            invoice.payment_status = PaymentStatus.PARTIAL
        
        # Update customer credit if applicable
        if invoice.customer.credit_allowed:
            self._update_customer_credit(invoice.customer_id, -amount)
        
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def _update_customer_credit(self, customer_id: int, amount_change: Decimal):
        """Update customer credit balance"""
        credit = self.db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if not credit:
            # Create credit account if doesn't exist
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            credit = CustomerCredit(
                customer_id=customer_id,
                credit_limit=Decimal("50000.0"),  # Default ₹50k
                current_balance=Decimal("0.0"),
                credit_score=70
            )
            self.db.add(credit)
        
        # Update balance
        credit.current_balance += amount_change
        if amount_change < 0:  # Payment made
            credit.last_payment_date = datetime.now()
        
        # Update credit score
        utilization = (credit.current_balance / credit.credit_limit * 100) if credit.credit_limit > 0 else 0
        if utilization < 30:
            credit.credit_score = min(100, credit.credit_score + 1)
        elif utilization > 80:
            credit.credit_score = max(0, credit.credit_score - 2)
        
        self.db.commit()
    
    def get_customer_invoices(
        self,
        customer_id: int,
        status: Optional[PaymentStatus] = None,
        limit: int = 50
    ) -> List[Invoice]:
        """Get invoices for a customer"""
        query = self.db.query(Invoice).filter(Invoice.customer_id == customer_id)
        
        if status:
            query = query.filter(Invoice.payment_status == status)
        
        return query.order_by(Invoice.invoice_date.desc()).limit(limit).all()
    
    def get_overdue_invoices(self, days_overdue: int = 0) -> List[Invoice]:
        """Get overdue invoices"""
        cutoff_date = datetime.now() - timedelta(days=days_overdue)
        
        return self.db.query(Invoice).filter(
            and_(
                Invoice.due_date < cutoff_date,
                Invoice.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.PARTIAL, PaymentStatus.OVERDUE])
            )
        ).all()
    
    def mark_overdue_invoices(self):
        """Mark invoices as overdue if past due date"""
        overdue = self.db.query(Invoice).filter(
            and_(
                Invoice.due_date < datetime.now(),
                Invoice.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.PARTIAL])
            )
        ).all()
        
        for invoice in overdue:
            invoice.payment_status = PaymentStatus.OVERDUE
        
        self.db.commit()
        return len(overdue)
    
    def get_invoice_summary(self, invoice_id: int) -> Dict:
        """Get detailed invoice summary with payments"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        payments = self.db.query(InvoicePayment).filter(
            InvoicePayment.invoice_id == invoice_id
        ).order_by(InvoicePayment.payment_date.desc()).all()
        
        return {
            "invoice": {
                "invoice_number": invoice.invoice_number,
                "customer_id": invoice.customer_id,
                "invoice_date": invoice.invoice_date.isoformat(),
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "hsn_code": invoice.hsn_code,
                "tax_rate": float(invoice.tax_rate),
                "taxable_amount": float(invoice.taxable_amount),
                "tax_amount": float(invoice.tax_amount),
                "total_amount": float(invoice.total_amount),
                "amount_paid": float(invoice.amount_paid),
                "amount_due": float(invoice.amount_due),
                "payment_status": invoice.payment_status.value,
                "receipt_sent_via": invoice.receipt_sent_via,
            },
            "payments": [
                {
                    "id": p.id,
                    "amount": float(p.amount_paid),
                    "method": p.payment_method,
                    "reference": p.reference_number,
                    "date": p.payment_date.isoformat(),
                    "notes": p.notes
                }
                for p in payments
            ],
            "payment_count": len(payments),
            "is_overdue": invoice.payment_status == PaymentStatus.OVERDUE
        }
    
    def get_khata_summary(self, customer_id: int) -> Dict:
        """Get Khata (credit ledger) summary for customer"""
        credit = self.db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        pending_invoices = self.get_customer_invoices(
            customer_id,
            status=PaymentStatus.PENDING
        )
        
        partial_invoices = self.get_customer_invoices(
            customer_id,
            status=PaymentStatus.PARTIAL
        )
        
        return {
            "customer_id": customer_id,
            "credit_limit": float(credit.credit_limit) if credit else 0.0,
            "current_balance": float(credit.current_balance) if credit else 0.0,
            "available_credit": float(credit.credit_limit - credit.current_balance) if credit else 0.0,
            "credit_score": credit.credit_score if credit else 0,
            "last_payment_date": credit.last_payment_date.isoformat() if credit and credit.last_payment_date else None,
            "pending_invoices_count": len(pending_invoices),
            "partial_invoices_count": len(partial_invoices),
            "total_outstanding": sum(inv.amount_due for inv in pending_invoices + partial_invoices)
        }

    def generate_pdf(self, invoice_id: int) -> bytes:
        from app.api.gst.invoice_generator import GSTInvoiceGenerator
        from app.models.multitenant_models import Organization
        
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
            
        org = self.db.query(Organization).filter(Organization.id == invoice.organization_id).first()
        customer = self.db.query(Customer).filter(Customer.id == invoice.customer_id).first()
        sale = self.db.query(Sale).filter(Sale.invoice_id == invoice.id).first()
        
        company_config = {
            "name": org.name if org else "Retail Store",
            "address": org.address.get('line1', '') if org and org.address else "",
            "gstin": org.gstin if org else "",
            "state_code": org.address.get('state_code', '27') if org and org.address else '27'
        }
        
        generator = GSTInvoiceGenerator(company_config=company_config)
        
        items_data = []
        if sale and sale.items:
            for item in sale.items:
                product = self.db.query(Product).filter(Product.id == item.product_id).first()
                hsn = getattr(product, 'hsn_code', '') if product else ''
                gst_r = float(product.gst_rate) if product and product.gst_rate else 18.0
                qty = item.quantity
                rate = float(item.unit_price)
                amount = float(item.line_total)
                taxable = amount / (1 + (gst_r / 100))
                
                items_data.append({
                    "name": product.name if product else "Item",
                    "hsn": hsn,
                    "qty": qty,
                    "rate": rate,
                    "amount": taxable,
                    "gst_rate": gst_r,
                    "cgst": (amount - taxable) / 2.0,
                    "sgst": (amount - taxable) / 2.0,
                    "total": amount
                })
        else:
            items_data.append({
                "name": "General Items",
                "hsn": invoice.hsn_code or "",
                "qty": 1,
                "rate": float(invoice.total_amount),
                "amount": float(invoice.taxable_amount),
                "gst_rate": float(invoice.tax_rate),
                "cgst": float(invoice.tax_amount) / 2.0,
                "sgst": float(invoice.tax_amount) / 2.0,
                "total": float(invoice.total_amount)
            })
            
        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "date": invoice.invoice_date.strftime("%d-%b-%Y"),
            "customer": {
                "name": customer.name if customer else "Customer",
                "address": getattr(customer, 'address', "") or "",
                "gstin": getattr(customer, 'gstin', ''),
                "state_code": getattr(customer, 'state_code', '27')
            },
            "items": items_data,
            "totals": {
                "taxable": float(invoice.taxable_amount),
                "cgst": float(invoice.tax_amount) / 2.0,
                "sgst": float(invoice.tax_amount) / 2.0,
                "igst": 0.0,
                "grand_total": float(invoice.total_amount),
                "amount_in_words": "Rupees ONLY"
            },
            "is_interstate": False
        }
        return generator.generate_pdf(invoice_data)

    def send_invoice(self, invoice_id: int, method: str) -> bool:
        from app.api.notifications.notification_service import NotificationService
        from app.api.notifications.templates import TemplateType
        from app.models.multitenant_models import Organization
        
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
            
        customer = self.db.query(Customer).filter(Customer.id == invoice.customer_id).first()
        org = self.db.query(Organization).filter(Organization.id == invoice.organization_id).first()
        
        if method == "whatsapp":
            phone = getattr(customer, 'whatsapp_number', None) or getattr(customer, 'phone', None)
            if not phone:
                raise ValueError("Customer has no phone number")
                
            svc = NotificationService()
            template_kwargs = {
                "customer_name": customer.name if customer else "Customer",
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date.strftime("%d %b %Y"),
                "total_amount": f"{invoice.total_amount:.2f}",
                "app_name": org.name if org else "Retail Store",
                "contact_number": org.contact_phone if org else "Support"
            }
            
            try:
                svc.send_notification(
                    phone_number=phone,
                    template_type=getattr(TemplateType, 'INVOICE_GENERATED', TemplateType.SALE_COMPLETED),
                    template_kwargs=template_kwargs
                )
                invoice.receipt_sent_via = "whatsapp"
                self.db.commit()
                return True
            except Exception as e:
                raise ValueError(str(e))
                
        return False
