"""
GST Calculator
Handles logic for intra-state (CGST/SGST) and inter-state (IGST) calculations.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class TaxSlab(str, Enum):
    """Standard Indian GST brackets."""
    EXEMPT = "0"
    FIVE = "5"
    TWELVE = "12"
    EIGHTEEN = "18"
    TWENTYEIGHT = "28"


class TaxCalculationResult(BaseModel):
    """Result of a single line item tax calculation."""
    taxable_value: Decimal
    gst_rate: Decimal
    is_interstate: bool

    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    cess_amount: Decimal = Decimal("0")
    
    total_tax_amount: Decimal = Decimal("0")
    grand_total: Decimal = Decimal("0")


class GSTCalculator:
    """Utility class for GST computations."""

    @staticmethod
    def _round(val: Decimal) -> Decimal:
        """Round to 2 decimal places as per accounting standards."""
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_forward_tax(
        taxable_value: float | str | Decimal,
        gst_rate: float | str | Decimal,
        is_interstate: bool = False,
        cess_rate: float | str | Decimal = 0,
    ) -> TaxCalculationResult:
        """
        Calculate tax amount on top of the base taxable value.
        e.g. 100 + 18% GST -> 18 Tax -> Total 118
        """
        tv = Decimal(str(taxable_value))
        rate = Decimal(str(gst_rate))
        cess_pct = Decimal(str(cess_rate))

        total_tax = GSTCalculator._round(tv * (rate / Decimal("100")))
        cess_amt = GSTCalculator._round(tv * (cess_pct / Decimal("100")))

        res = TaxCalculationResult(
            taxable_value=tv,
            gst_rate=rate,
            is_interstate=is_interstate,
            cess_amount=cess_amt,
            total_tax_amount=total_tax,
            grand_total=tv + total_tax + cess_amt
        )

        if is_interstate:
            res.igst_amount = total_tax
        else:
            res.cgst_amount = GSTCalculator._round(total_tax / 2)
            res.sgst_amount = total_tax - res.cgst_amount  # Avoid 1-cent split errors

        return res

    @staticmethod
    def calculate_reverse_tax(
        inclusive_total: float | str | Decimal,
        gst_rate: float | str | Decimal,
        is_interstate: bool = False,
    ) -> TaxCalculationResult:
        """
        Extract base taxable value and tax from an inclusive total.
        e.g. 118 inclusive of 18% GST -> 100 Base -> 18 Tax
        
        Formula: Taxable Value = (Inclusive Total / (100 + GST%)) * 100
        """
        total = Decimal(str(inclusive_total))
        rate = Decimal(str(gst_rate))

        if rate == Decimal("0"):
            return TaxCalculationResult(
                taxable_value=total,
                gst_rate=rate,
                is_interstate=is_interstate,
                grand_total=total
            )

        tv = GSTCalculator._round((total / (Decimal("100") + rate)) * 100)
        
        # Calculate tax forward from the extracted TV to ensure exact matching
        return GSTCalculator.calculate_forward_tax(
            taxable_value=tv,
            gst_rate=rate,
            is_interstate=is_interstate
        )

    @staticmethod
    def is_same_state(seller_gstin: str, buyer_gstin: str) -> bool:
        """
        Determine if a transaction is intra-state (same state) or inter-state.
        Indian GSTINs start with a 2-digit state code.
        """
        if not seller_gstin or not buyer_gstin:
            return False  # Assume local B2C if missing
        
        if len(seller_gstin) < 2 or len(buyer_gstin) < 2:
            return False

        return seller_gstin[:2] == buyer_gstin[:2]
