"""
GST Calculator — Consolidated tax math hub.

Consolidates:
  - app/api/gst/calculator.py       (GSTCalculator — best precision, 1¢ split)
  - app/services/phase2_gst_service.py  (dataclass rate system)
  - app/services/gst_service.py         (rate map + calculate_gst)
  - app/services/gst_invoice_service.py (line-item calc)
  - app/services/invoice_service.py     (InvoiceService.calculate_gst)
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel


# ──────────────────────────────────────────────
# Enums & constants
# ──────────────────────────────────────────────

class TaxSlab(str, Enum):
    EXEMPT = "0"
    FIVE = "5"
    TWELVE = "12"
    EIGHTEEN = "18"
    TWENTYEIGHT = "28"


class GSTType(str, Enum):
    INTRA_STATE = "CGST+SGST"
    INTER_STATE = "IGST"


# ──────────────────────────────────────────────
# Dataclass / models
# ──────────────────────────────────────────────

class TaxCalculationResult(BaseModel):
    taxable_value: Decimal
    gst_rate: Decimal
    is_interstate: bool
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    cess_amount: Decimal = Decimal("0")
    total_tax_amount: Decimal = Decimal("0")
    grand_total: Decimal = Decimal("0")


class LineItemTaxBreakdown(BaseModel):
    product_id: Optional[str] = None
    product_name: str = ""
    hsn_code: str = ""
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal = Decimal("0")
    taxable_amount: Decimal
    cgst_rate: Decimal = Decimal("0")
    sgst_rate: Decimal = Decimal("0")
    igst_rate: Decimal = Decimal("0")
    cess_rate: Decimal = Decimal("0")
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    cess_amount: Decimal = Decimal("0")
    total_tax: Decimal = Decimal("0")
    line_total: Decimal = Decimal("0")


# ──────────────────────────────────────────────
# GST rate catalogue
# ──────────────────────────────────────────────

# Category → GST rate (%) for common retail categories
CATEGORY_GST_RATES: Dict[str, float] = {
    "food": 5, "beverages": 12, "dairy": 5, "snacks": 12,
    "groceries": 0, "vegetables": 0, "fruits": 0,
    "electronics": 18, "mobile": 18, "clothing": 12, "footwear": 12,
    "furniture": 18, "pharma": 12, "toys": 12, "stationery": 12,
    "cleaning": 18, "luxury": 28, "tobacco": 28, "default": 18,
}

# HSN → GST rate fallback catalogue
HSN_GST_RATES: Dict[str, float] = {
    "8471": 18, "8517": 18, "847190": 18, "997331": 18,
    "0401": 5, "6109": 12, "3004": 12, "9999": 18,
}


# ──────────────────────────────────────────────
# Core calculator (preserves original GSTCalculator contract)
# ──────────────────────────────────────────────

class GSTCalculator:
    @staticmethod
    def _round(val: Decimal) -> Decimal:
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_forward_tax(
        taxable_value: Union[float, str, Decimal],
        gst_rate: Union[float, str, Decimal],
        is_interstate: bool = False,
        cess_rate: Union[float, str, Decimal] = 0,
    ) -> TaxCalculationResult:
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
            grand_total=GSTCalculator._round(tv + total_tax + cess_amt),
        )

        if is_interstate:
            res.igst_amount = total_tax
        else:
            res.cgst_amount = GSTCalculator._round(total_tax / 2)
            res.sgst_amount = total_tax - res.cgst_amount  # avoid 1¢ split error

        return res

    @staticmethod
    def calculate_reverse_tax(
        inclusive_total: Union[float, str, Decimal],
        gst_rate: Union[float, str, Decimal],
        is_interstate: bool = False,
    ) -> TaxCalculationResult:
        total = Decimal(str(inclusive_total))
        rate = Decimal(str(gst_rate))

        if rate == Decimal("0"):
            return TaxCalculationResult(
                taxable_value=total, gst_rate=rate,
                is_interstate=is_interstate, grand_total=total,
            )

        tv = GSTCalculator._round((total / (Decimal("100") + rate)) * 100)
        return GSTCalculator.calculate_forward_tax(tv, rate, is_interstate)

    @staticmethod
    def is_same_state(seller_gstin: str, buyer_gstin: str) -> bool:
        if not seller_gstin or not buyer_gstin:
            return False
        if len(seller_gstin) < 2 or len(buyer_gstin) < 2:
            return False
        return seller_gstin[:2] == buyer_gstin[:2]

    @staticmethod
    def get_rate_for_category(category: str) -> float:
        return CATEGORY_GST_RATES.get(category.lower(), 18.0)

    @staticmethod
    def get_rate_for_hsn(hsn_code: str) -> float:
        return HSN_GST_RATES.get(hsn_code, 18.0)

    @staticmethod
    def calculate_line_item(
        unit_price: Decimal,
        quantity: Decimal,
        gst_rate: Decimal = Decimal("18"),
        discount_pct: Decimal = Decimal("0"),
        is_interstate: bool = False,
        cess_rate: Decimal = Decimal("0"),
        product_id: Optional[str] = None,
        product_name: str = "",
        hsn_code: str = "",
    ) -> LineItemTaxBreakdown:
        gross = unit_price * quantity
        discount = GSTCalculator._round(gross * (discount_pct / Decimal("100")))
        taxable = gross - discount

        tax_res = GSTCalculator.calculate_forward_tax(
            taxable_value=taxable,
            gst_rate=gst_rate,
            is_interstate=is_interstate,
            cess_rate=cess_rate,
        )

        half = gst_rate / Decimal("2") if not is_interstate else Decimal("0")

        return LineItemTaxBreakdown(
            product_id=product_id,
            product_name=product_name,
            hsn_code=hsn_code,
            quantity=quantity,
            unit_price=unit_price,
            discount_percentage=discount_pct,
            taxable_amount=taxable,
            cgst_rate=half if not is_interstate else Decimal("0"),
            sgst_rate=half if not is_interstate else Decimal("0"),
            igst_rate=gst_rate if is_interstate else Decimal("0"),
            cess_rate=cess_rate,
            cgst_amount=tax_res.cgst_amount,
            sgst_amount=tax_res.sgst_amount,
            igst_amount=tax_res.igst_amount,
            cess_amount=tax_res.cess_amount,
            total_tax=tax_res.total_tax_amount,
            line_total=tax_res.grand_total,
        )

    @staticmethod
    def calculate_line_items(
        items: List[Dict],
        is_interstate: bool = False,
    ) -> Tuple[List[LineItemTaxBreakdown], Dict[str, Decimal]]:
        breakdowns: List[LineItemTaxBreakdown] = []
        totals: Dict[str, Decimal] = {
            "subtotal": Decimal("0"), "discount": Decimal("0"),
            "taxable": Decimal("0"), "cgst": Decimal("0"),
            "sgst": Decimal("0"), "igst": Decimal("0"),
            "cess": Decimal("0"), "total_tax": Decimal("0"),
            "grand_total": Decimal("0"),
        }

        for item in items:
            b = GSTCalculator.calculate_line_item(
                unit_price=Decimal(str(item.get("unit_price", 0))),
                quantity=Decimal(str(item.get("quantity", 1))),
                gst_rate=Decimal(str(item.get("gst_rate", 18))),
                discount_pct=Decimal(str(item.get("discount_percentage", 0))),
                is_interstate=is_interstate,
                cess_rate=Decimal(str(item.get("cess_rate", 0))),
                product_id=item.get("product_id"),
                product_name=item.get("product_name", ""),
                hsn_code=item.get("hsn_code", ""),
            )
            breakdowns.append(b)
            totals["subtotal"] += b.unit_price * b.quantity
            totals["discount"] += b.unit_price * b.quantity - b.taxable_amount
            totals["taxable"] += b.taxable_amount
            totals["cgst"] += b.cgst_amount
            totals["sgst"] += b.sgst_amount
            totals["igst"] += b.igst_amount
            totals["cess"] += b.cess_amount
            totals["total_tax"] += b.total_tax
            totals["grand_total"] += b.line_total

        for k in totals:
            totals[k] = GSTCalculator._round(totals[k])

        return breakdowns, totals


# Convenience aliases
calculate_forward_tax = GSTCalculator.calculate_forward_tax
calculate_reverse_tax = GSTCalculator.calculate_reverse_tax
is_same_state = GSTCalculator.is_same_state
get_rate_for_category = GSTCalculator.get_rate_for_category
get_rate_for_hsn = GSTCalculator.get_rate_for_hsn
calculate_line_item = GSTCalculator.calculate_line_item
calculate_line_items = GSTCalculator.calculate_line_items


def calculate_line_item_gst(
    unit_price: float, quantity: int, gst_rate: float,
    discount_pct: float = 0.0, inter_state: bool = False,
) -> Dict[str, float]:
    """Backward-compat wrapper matching old gst_invoice_service API."""
    b = GSTCalculator.calculate_line_item(
        unit_price=Decimal(str(unit_price)),
        quantity=Decimal(str(quantity)),
        gst_rate=Decimal(str(gst_rate)),
        discount_pct=Decimal(str(discount_pct)),
        is_interstate=inter_state,
    )
    return {
        "subtotal": float(b.unit_price * b.quantity),
        "discount": float(b.discount_percentage),
        "taxable_value": float(b.taxable_amount),
        "cgst_rate": float(b.cgst_rate),
        "sgst_rate": float(b.sgst_rate),
        "igst_rate": float(b.igst_rate),
        "cgst_amount": float(b.cgst_amount),
        "sgst_amount": float(b.sgst_amount),
        "igst_amount": float(b.igst_amount),
        "total_gst": float(b.total_tax),
        "line_total": float(b.line_total),
    }
