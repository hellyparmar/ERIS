"""
GST Tax Calculation Engine
Comprehensive tax calculator for Indian GST compliance

Features:
- CGST/SGST calculation for intra-state transactions
- IGST calculation for inter-state transactions
- Cess calculation
- Reverse charge mechanism
- Tax exemption handling
- Invoice-level and line-item level calculations
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaxType(Enum):
    """GST tax types"""
    GST = "GST"
    EXEMPT = "EXEMPT"
    NIL_RATED = "NIL_RATED"
    NON_GST = "NON_GST"


class TransactionType(Enum):
    """Transaction types for GST"""
    INTRASTATE = "intrastate"  # Within same state (CGST + SGST)
    INTERSTATE = "interstate"   # Between different states (IGST)
    EXPORT = "export"           # Export (zero-rated)
    IMPORT = "import"           # Import


@dataclass
class TaxBreakdown:
    """Tax calculation breakdown"""
    taxable_amount: Decimal
    cgst_rate: Decimal
    cgst_amount: Decimal
    sgst_rate: Decimal
    sgst_amount: Decimal
    igst_rate: Decimal
    igst_amount: Decimal
    cess_rate: Decimal
    cess_amount: Decimal
    total_tax: Decimal
    total_amount: Decimal
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'taxable_amount': float(self.taxable_amount),
            'cgst_rate': float(self.cgst_rate),
            'cgst_amount': float(self.cgst_amount),
            'sgst_rate': float(self.sgst_rate),
            'sgst_amount': float(self.sgst_amount),
            'igst_rate': float(self.igst_rate),
            'igst_amount': float(self.igst_amount),
            'cess_rate': float(self.cess_rate),
            'cess_amount': float(self.cess_amount),
            'total_tax': float(self.total_tax),
            'total_amount': float(self.total_amount)
        }


@dataclass
class LineItem:
    """Invoice line item"""
    product_id: str
    name: str
    hsn_code: str
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal = Decimal('0')
    
    # Tax rates (from product master)
    cgst_rate: Decimal = Decimal('0')
    sgst_rate: Decimal = Decimal('0')
    igst_rate: Decimal = Decimal('0')
    cess_rate: Decimal = Decimal('0')
    
    # Flags
    is_taxable: bool = True
    tax_type: TaxType = TaxType.GST


class GSTCalculator:
    """
    GST Tax Calculation Engine
    
    Handles all GST calculations according to Indian tax laws
    """
    
    # Rounding precision
    AMOUNT_PRECISION = 2
    RATE_PRECISION = 2
    
    def __init__(self, 
                 seller_state_code: str,
                 buyer_state_code: Optional[str] = None,
                 reverse_charge: bool = False):
        """
        Initialize GST calculator
        
        Args:
            seller_state_code: 2-digit state code of seller
            buyer_state_code: 2-digit state code of buyer (None for B2C)
            reverse_charge: True if reverse charge applies
        """
        self.seller_state_code = seller_state_code
        self.buyer_state_code = buyer_state_code or seller_state_code
        self.reverse_charge = reverse_charge
        
        # Determine transaction type
        if seller_state_code == self.buyer_state_code:
            self.transaction_type = TransactionType.INTRASTATE
        else:
            self.transaction_type = TransactionType.INTERSTATE
    
    def calculate_line_item_tax(self, item: LineItem) -> TaxBreakdown:
        """
        Calculate tax for a single line item
        
        Args:
            item: LineItem with product details
            
        Returns:
            TaxBreakdown with calculated amounts
        """
        # Calculate base amounts
        gross_amount = item.quantity * item.unit_price
        
        # Apply discount
        discount_amount = gross_amount * (item.discount_percentage / Decimal('100'))
        taxable_amount = gross_amount - discount_amount
        
        # Round taxable amount
        taxable_amount = self._round_amount(taxable_amount)
        
        # Check if taxable
        if not item.is_taxable or item.tax_type != TaxType.GST:
            return TaxBreakdown(
                taxable_amount=taxable_amount,
                cgst_rate=Decimal('0'),
                cgst_amount=Decimal('0'),
                sgst_rate=Decimal('0'),
                sgst_amount=Decimal('0'),
                igst_rate=Decimal('0'),
                igst_amount=Decimal('0'),
                cess_rate=Decimal('0'),
                cess_amount=Decimal('0'),
                total_tax=Decimal('0'),
                total_amount=taxable_amount
            )
        
        # Calculate tax based on transaction type
        if self.transaction_type == TransactionType.INTRASTATE:
            # CGST + SGST
            cgst_rate = item.cgst_rate
            sgst_rate = item.sgst_rate
            igst_rate = Decimal('0')
            
            cgst_amount = self._calculate_tax_amount(taxable_amount, cgst_rate)
            sgst_amount = self._calculate_tax_amount(taxable_amount, sgst_rate)
            igst_amount = Decimal('0')
            
        else:  # INTERSTATE
            # IGST only
            cgst_rate = Decimal('0')
            sgst_rate = Decimal('0')
            igst_rate = item.igst_rate
            
            cgst_amount = Decimal('0')
            sgst_amount = Decimal('0')
            igst_amount = self._calculate_tax_amount(taxable_amount, igst_rate)
        
        # Calculate cess
        cess_rate = item.cess_rate
        cess_amount = self._calculate_tax_amount(taxable_amount, cess_rate)
        
        # Total tax
        total_tax = cgst_amount + sgst_amount + igst_amount + cess_amount
        total_amount = taxable_amount + total_tax
        
        return TaxBreakdown(
            taxable_amount=taxable_amount,
            cgst_rate=cgst_rate,
            cgst_amount=cgst_amount,
            sgst_rate=sgst_rate,
            sgst_amount=sgst_amount,
            igst_rate=igst_rate,
            igst_amount=igst_amount,
            cess_rate=cess_rate,
            cess_amount=cess_amount,
            total_tax=total_tax,
            total_amount=total_amount
        )
    
    def calculate_invoice_tax(self, 
                              items: List[LineItem],
                              apply_round_off: bool = True) -> Dict:
        """
        Calculate tax for entire invoice
        
        Args:
            items: List of LineItem objects
            apply_round_off: Whether to apply round-off to grand total
            
        Returns:
            Dictionary with invoice-level tax summary
        """
        # Calculate each line item
        line_item_taxes = []
        
        for item in items:
            tax = self.calculate_line_item_tax(item)
            line_item_taxes.append({
                'product_id': item.product_id,
                'name': item.name,
                'hsn_code': item.hsn_code,
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'discount_percentage': float(item.discount_percentage),
                'taxable_amount': tax.taxable_amount,
                'tax_breakdown': tax.to_dict()
            })
        
        # Aggregate totals
        subtotal = sum(
            item.quantity * item.unit_price 
            for item in items
        )
        
        total_discount = sum(
            (item.quantity * item.unit_price) * (item.discount_percentage / Decimal('100'))
            for item in items
        )
        
        taxable_amount = sum(
            self.calculate_line_item_tax(item).taxable_amount
            for item in items
        )
        
        total_cgst = sum(
            self.calculate_line_item_tax(item).cgst_amount
            for item in items
        )
        
        total_sgst = sum(
            self.calculate_line_item_tax(item).sgst_amount
            for item in items
        )
        
        total_igst = sum(
            self.calculate_line_item_tax(item).igst_amount
            for item in items
        )
        
        total_cess = sum(
            self.calculate_line_item_tax(item).cess_amount
            for item in items
        )
        
        total_tax = total_cgst + total_sgst + total_igst + total_cess
        
        # Grand total before round-off
        grand_total_before_round = taxable_amount + total_tax
        
        # Apply round-off
        if apply_round_off:
            grand_total = self._round_to_nearest_rupee(grand_total_before_round)
            round_off = grand_total - grand_total_before_round
        else:
            grand_total = grand_total_before_round
            round_off = Decimal('0')
        
        return {
            'transaction_type': self.transaction_type.value,
            'is_interstate': self.transaction_type == TransactionType.INTERSTATE,
            'reverse_charge': self.reverse_charge,
            
            # Amounts
            'subtotal': float(self._round_amount(subtotal)),
            'total_discount': float(self._round_amount(total_discount)),
            'taxable_amount': float(self._round_amount(taxable_amount)),
            
            # Tax breakdown
            'cgst_amount': float(self._round_amount(total_cgst)),
            'sgst_amount': float(self._round_amount(total_sgst)),
            'igst_amount': float(self._round_amount(total_igst)),
            'cess_amount': float(self._round_amount(total_cess)),
            'total_tax': float(self._round_amount(total_tax)),
            
            # Totals
            'round_off': float(round_off),
            'grand_total': float(grand_total),
            
            # Line items
            'line_items': line_item_taxes,
            
            # Metadata
            'seller_state': self.seller_state_code,
            'buyer_state': self.buyer_state_code
        }
    
    def get_hsn_summary(self, items: List[LineItem]) -> List[Dict]:
        """
        Generate HSN-wise summary (required for GSTR-1)
        
        Args:
            items: List of LineItem objects
            
        Returns:
            List of HSN summaries
        """
        hsn_map = {}
        
        for item in items:
            tax = self.calculate_line_item_tax(item)
            
            if item.hsn_code not in hsn_map:
                hsn_map[item.hsn_code] = {
                    'hsn_code': item.hsn_code,
                    'description': item.name,
                    'quantity': Decimal('0'),
                    'taxable_amount': Decimal('0'),
                    'cgst_amount': Decimal('0'),
                    'sgst_amount': Decimal('0'),
                    'igst_amount': Decimal('0'),
                    'cess_amount': Decimal('0'),
                    'total_tax': Decimal('0'),
                    'gst_rate': tax.cgst_rate + tax.sgst_rate + tax.igst_rate
                }
            
            hsn_map[item.hsn_code]['quantity'] += item.quantity
            hsn_map[item.hsn_code]['taxable_amount'] += tax.taxable_amount
            hsn_map[item.hsn_code]['cgst_amount'] += tax.cgst_amount
            hsn_map[item.hsn_code]['sgst_amount'] += tax.sgst_amount
            hsn_map[item.hsn_code]['igst_amount'] += tax.igst_amount
            hsn_map[item.hsn_code]['cess_amount'] += tax.cess_amount
            hsn_map[item.hsn_code]['total_tax'] += tax.total_tax
        
        # Convert to list and round
        summary = []
        for hsn_data in hsn_map.values():
            summary.append({
                'hsn_code': hsn_data['hsn_code'],
                'description': hsn_data['description'],
                'quantity': float(hsn_data['quantity']),
                'taxable_amount': float(self._round_amount(hsn_data['taxable_amount'])),
                'cgst_amount': float(self._round_amount(hsn_data['cgst_amount'])),
                'sgst_amount': float(self._round_amount(hsn_data['sgst_amount'])),
                'igst_amount': float(self._round_amount(hsn_data['igst_amount'])),
                'cess_amount': float(self._round_amount(hsn_data['cess_amount'])),
                'total_tax': float(self._round_amount(hsn_data['total_tax'])),
                'gst_rate': float(hsn_data['gst_rate'])
            })
        
        return summary
    
    def _calculate_tax_amount(self, taxable_amount: Decimal, rate: Decimal) -> Decimal:
        """Calculate tax amount from taxable amount and rate"""
        tax = taxable_amount * (rate / Decimal('100'))
        return self._round_amount(tax)
    
    def _round_amount(self, amount: Decimal) -> Decimal:
        """Round amount to 2 decimal places"""
        return amount.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
    
    def _round_to_nearest_rupee(self, amount: Decimal) -> Decimal:
        """Round to nearest rupee (for invoice total)"""
        return amount.quantize(
            Decimal('1'),
            rounding=ROUND_HALF_UP
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def split_gst_rate(total_gst_rate: Decimal, is_interstate: bool = False) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Split total GST rate into CGST, SGST, IGST
    
    Args:
        total_gst_rate: Total GST rate (e.g., 18)
        is_interstate: True for IGST, False for CGST+SGST
        
    Returns:
        Tuple of (cgst_rate, sgst_rate, igst_rate)
    """
    if is_interstate:
        return (Decimal('0'), Decimal('0'), total_gst_rate)
    else:
        half_rate = total_gst_rate / Decimal('2')
        return (half_rate, half_rate, Decimal('0'))


def get_state_code_from_gstin(gstin: str) -> str:
    """
    Extract state code from GSTIN
    
    Args:
        gstin: 15-digit GSTIN
        
    Returns:
        2-digit state code
    """
    if not gstin or len(gstin) < 2:
        raise ValueError("Invalid GSTIN")
    
    return gstin[:2]


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Example: Intra-state invoice (Karnataka)
    calculator = GSTCalculator(
        seller_state_code='29',  # Karnataka
        buyer_state_code='29'    # Karnataka
    )
    
    items = [
        LineItem(
            product_id='prod-1',
            name='Laptop',
            hsn_code='8471',
            quantity=Decimal('2'),
            unit_price=Decimal('50000'),
            discount_percentage=Decimal('10'),
            cgst_rate=Decimal('9'),
            sgst_rate=Decimal('9'),
            igst_rate=Decimal('18')
        ),
        LineItem(
            product_id='prod-2',
            name='Mouse',
            hsn_code='8471',
            quantity=Decimal('5'),
            unit_price=Decimal('500'),
            cgst_rate=Decimal('9'),
            sgst_rate=Decimal('9'),
            igst_rate=Decimal('18')
        )
    ]
    
    result = calculator.calculate_invoice_tax(items)
    
    print("Invoice Calculation:")
    print(f"  Subtotal: ₹{result['subtotal']}")
    print(f"  Discount: ₹{result['total_discount']}")
    print(f"  Taxable: ₹{result['taxable_amount']}")
    print(f"  CGST (9%): ₹{result['cgst_amount']}")
    print(f"  SGST (9%): ₹{result['sgst_amount']}")
    print(f"  Total Tax: ₹{result['total_tax']}")
    print(f"  Round Off: ₹{result['round_off']}")
    print(f"  Grand Total: ₹{result['grand_total']}")
    
    # HSN Summary
    hsn_summary = calculator.get_hsn_summary(items)
    print("\nHSN Summary:")
    for hsn in hsn_summary:
        print(f"  HSN {hsn['hsn_code']}: ₹{hsn['taxable_amount']} (Tax: ₹{hsn['total_tax']})")
