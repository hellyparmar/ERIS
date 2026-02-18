"""
Phase 2: Advanced Invoice Management Service

Enhanced invoicing with GST compliance, PDF generation, and delivery
Built on top of Phase 1 invoice foundation
"""

from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class InvoiceLineItem:
    """Invoice line item with tax calculation"""
    product_id: str
    product_name: str
    hsn_code: str
    quantity: Decimal
    unit_rate: Decimal
    tax_rate: Decimal  # 0, 5, 12, 18, 28
    description: Optional[str] = None
    unit: str = "PCS"
    discount_percentage: Decimal = Decimal("0")


class Phase2InvoiceService:
    """
    Phase 2 Invoice Service
    
    Enhanced features:
    - Multi-line GST calculation
    - PDF generation with QR codes
    - E-invoice support
    - WhatsApp/Email delivery
    - Credit notes and adjustments
    """
    
    def __init__(self):
        self.logger = logger
    
    def calculate_line_item(self, item: InvoiceLineItem) -> Dict:
        """
        Calculate tax and totals for line item
        
        Args:
            item: Line item details
            
        Returns:
            Dict: Calculated values (amount, tax, total)
        """
        # Calculate base amount
        line_amount = item.quantity * item.unit_rate
        
        # Apply discount
        discount = (line_amount * item.discount_percentage) / Decimal("100")
        taxable_amount = line_amount - discount
        
        # Calculate tax (18% = 9% CGST + 9% SGST for intra-state)
        tax_percentage = item.tax_rate / Decimal("2")  # Split for CGST/SGST
        cgst_amount = (taxable_amount * tax_percentage) / Decimal("100")
        sgst_amount = cgst_amount  # Same as CGST
        total_tax = cgst_amount + sgst_amount
        
        line_total = taxable_amount + total_tax
        
        return {
            "quantity": float(item.quantity),
            "unit_rate": float(item.unit_rate),
            "line_amount": float(line_amount),
            "discount": float(discount),
            "taxable_amount": float(taxable_amount),
            "tax_rate": float(item.tax_rate),
            "cgst": float(cgst_amount),
            "sgst": float(sgst_amount),
            "total_tax": float(total_tax),
            "line_total": float(line_total),
            "hsn_code": item.hsn_code,
            "product_name": item.product_name
        }
    
    def calculate_invoice_totals(
        self,
        line_items: List[InvoiceLineItem],
        shipping_charges: Decimal = Decimal("0"),
        other_charges: Decimal = Decimal("0")
    ) -> Dict:
        """
        Calculate complete invoice totals
        
        Args:
            line_items: List of line items
            shipping_charges: Shipping amount
            other_charges: Other charges
            
        Returns:
            Dict: Invoice totals (subtotal, tax breakdown, total)
        """
        calculated_items = []
        subtotal = Decimal("0")
        total_cgst = Decimal("0")
        total_sgst = Decimal("0")
        
        for item in line_items:
            calc = self.calculate_line_item(item)
            calculated_items.append(calc)
            
            subtotal += Decimal(str(calc["taxable_amount"]))
            total_cgst += Decimal(str(calc["cgst"]))
            total_sgst += Decimal(str(calc["sgst"]))
        
        # Add charges (no tax on charges typically)
        subtotal_with_charges = subtotal + shipping_charges + other_charges
        total_tax = total_cgst + total_sgst
        grand_total = subtotal_with_charges + total_tax
        
        return {
            "subtotal": float(subtotal),
            "shipping_charges": float(shipping_charges),
            "other_charges": float(other_charges),
            "subtotal_with_charges": float(subtotal_with_charges),
            "cgst_total": float(total_cgst),
            "sgst_total": float(total_sgst),
            "total_tax": float(total_tax),
            "grand_total": float(grand_total),
            "line_items": calculated_items
        }
    
    def create_gst_return_data(
        self,
        invoices: List[Dict],
        period_start: date,
        period_end: date
    ) -> Dict:
        """
        Create GST return (GSTR-1) data
        
        Args:
            invoices: List of invoices
            period_start: Period start date
            period_end: Period end date
            
        Returns:
            Dict: GST return data
        """
        intra_state_value = Decimal("0")
        intra_state_tax = Decimal("0")
        inter_state_value = Decimal("0")
        inter_state_tax = Decimal("0")
        
        for invoice in invoices:
            if invoice.get("is_inter_state"):
                inter_state_value += Decimal(str(invoice.get("subtotal", 0)))
                inter_state_tax += Decimal(str(invoice.get("igst", 0)))
            else:
                intra_state_value += Decimal(str(invoice.get("subtotal", 0)))
                intra_state_tax += Decimal(str(invoice.get("cgst", 0))) + Decimal(str(invoice.get("sgst", 0)))
        
        return {
            "period": f"{period_start.isoformat()} to {period_end.isoformat()}",
            "intra_state": {
                "value": float(intra_state_value),
                "tax": float(intra_state_tax)
            },
            "inter_state": {
                "value": float(inter_state_value),
                "tax": float(inter_state_tax)
            },
            "total": {
                "value": float(intra_state_value + inter_state_value),
                "tax": float(intra_state_tax + inter_state_tax)
            }
        }
    
    def generate_qr_code_data(self, invoice_number: str, amount: Decimal) -> str:
        """
        Generate QR code data for e-invoice
        
        Args:
            invoice_number: Invoice number
            amount: Invoice amount
            
        Returns:
            str: QR code data string
        """
        # Format: INV_NO|AMOUNT|TIMESTAMP
        timestamp = datetime.now().isoformat()
        qr_data = f"{invoice_number}|{amount}|{timestamp}"
        return qr_data
    
    def calculate_credit_score(
        self,
        total_transactions: int,
        on_time_payments: int,
        late_payments: int,
        missed_payments: int,
        days_since_first_transaction: int = 365
    ) -> int:
        """
        Calculate customer credit score (0-100)
        
        Args:
            total_transactions: Total transactions with customer
            on_time_payments: On-time payments
            late_payments: Late payments
            missed_payments: Missed payments
            days_since_first_transaction: Days of relationship
            
        Returns:
            int: Credit score (0-100)
        """
        score = 100
        
        # Deduct for late/missed payments
        score -= (late_payments * 3)  # -3 per late payment
        score -= (missed_payments * 10)  # -10 per missed payment
        
        # Add for on-time payments (bonus)
        if total_transactions > 0:
            on_time_ratio = on_time_payments / total_transactions
            score += int(on_time_ratio * 15)  # Up to +15 for consistency
        
        # Add for long-term relationship
        if days_since_first_transaction >= 365:
            score += 10
        
        # Clamp score to 0-100
        return max(0, min(100, score))
    
    def get_credit_rating(self, score: int) -> str:
        """
        Get credit rating from score
        
        Args:
            score: Credit score (0-100)
            
        Returns:
            str: Rating (EXCELLENT, GOOD, FAIR, POOR)
        """
        if score >= 85:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "FAIR"
        else:
            return "POOR"
    
    def can_give_credit(
        self,
        credit_score: int,
        requested_amount: Decimal,
        credit_limit: Decimal,
        current_balance: Decimal
    ) -> tuple:
        """
        Determine if credit should be given
        
        Args:
            credit_score: Customer credit score
            requested_amount: Requested credit amount
            credit_limit: Set credit limit
            current_balance: Current outstanding
            
        Returns:
            tuple: (can_give, reason, recommended_limit)
        """
        # Check credit limit
        available_limit = credit_limit - current_balance
        
        if requested_amount > available_limit:
            return (False, "Exceeds credit limit", float(available_limit))
        
        # Check credit score
        if credit_score < 40:
            return (False, "Poor credit score", float(credit_limit * Decimal("0.5")))
        
        # All checks passed
        return (True, "Approved", float(credit_limit))


# Initialize global service
phase2_invoice_service = Phase2InvoiceService()
