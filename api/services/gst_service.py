"""
GST (Goods and Services Tax) Compliance Service

Handles tax calculation, GST configuration, and tax-related operations
for the Enterprise Retail Intelligence System v3.0
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, date


class GSTCategory(str, Enum):
    """GST tax categories in India"""
    ZERO = "0"  # 0% (Essential goods)
    FIVE = "5"  # 5% (Common items)
    TWELVE = "12"  # 12% (Mid-tier products)
    EIGHTEEN = "18"  # 18% (Most products)
    TWENTY_EIGHT = "28"  # 28% (Luxury items)


class GSTType(str, Enum):
    """GST composition types"""
    INTRA_STATE = "IGST"  # Integrated GST (inter-state)
    INTRA_CGST = "CGST"  # Central GST (intra-state)
    INTRA_SGST = "SGST"  # State GST (intra-state)


@dataclass
class TaxRate:
    """Tax rate configuration"""
    category: GSTCategory
    cgst_rate: Decimal
    sgst_rate: Decimal
    igst_rate: Decimal
    hsn_code: Optional[str] = None
    description: str = ""
    effective_from: date = None
    effective_to: Optional[date] = None


@dataclass
class TaxCalculation:
    """Tax calculation result"""
    base_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_tax: Decimal
    total_amount: Decimal
    tax_type: GSTType
    tax_rate: Decimal


class GSTService:
    """
    GST Compliance Service
    
    Handles all GST-related operations including:
    - Tax rate configuration
    - Tax calculations
    - GST return generation
    - Compliance reporting
    """
    
    # Standard GST rates in India (as of 2026)
    STANDARD_RATES = {
        GSTCategory.ZERO: TaxRate(
            category=GSTCategory.ZERO,
            cgst_rate=Decimal("0"),
            sgst_rate=Decimal("0"),
            igst_rate=Decimal("0"),
            description="0% - Essential goods (food, medicines)"
        ),
        GSTCategory.FIVE: TaxRate(
            category=GSTCategory.FIVE,
            cgst_rate=Decimal("2.5"),
            sgst_rate=Decimal("2.5"),
            igst_rate=Decimal("5"),
            description="5% - Common items"
        ),
        GSTCategory.TWELVE: TaxRate(
            category=GSTCategory.TWELVE,
            cgst_rate=Decimal("6"),
            sgst_rate=Decimal("6"),
            igst_rate=Decimal("12"),
            description="12% - Mid-tier products"
        ),
        GSTCategory.EIGHTEEN: TaxRate(
            category=GSTCategory.EIGHTEEN,
            cgst_rate=Decimal("9"),
            sgst_rate=Decimal("9"),
            igst_rate=Decimal("18"),
            description="18% - Most products"
        ),
        GSTCategory.TWENTY_EIGHT: TaxRate(
            category=GSTCategory.TWENTY_EIGHT,
            cgst_rate=Decimal("14"),
            sgst_rate=Decimal("14"),
            igst_rate=Decimal("28"),
            description="28% - Luxury items"
        ),
    }
    
    def __init__(self):
        """Initialize GST Service"""
        self.tax_rates = self.STANDARD_RATES.copy()
        self.custom_rates: Dict[str, TaxRate] = {}
    
    def get_tax_rate(self, category: GSTCategory) -> TaxRate:
        """
        Get tax rate for a GST category
        
        Args:
            category: GST category (0%, 5%, 12%, 18%, 28%)
            
        Returns:
            TaxRate: Tax rate configuration
        """
        return self.tax_rates.get(category)
    
    def set_custom_rate(self, hsn_code: str, rate: TaxRate) -> bool:
        """
        Set a custom GST rate for specific HSN code
        
        Args:
            hsn_code: HSN/SAC code
            rate: Custom tax rate
            
        Returns:
            bool: Success status
        """
        if not hsn_code or len(hsn_code) < 4:
            raise ValueError("Invalid HSN code")
        
        self.custom_rates[hsn_code] = rate
        return True
    
    def get_rate_for_hsn(self, hsn_code: str) -> TaxRate:
        """
        Get tax rate for a specific HSN code
        
        Args:
            hsn_code: HSN/SAC code
            
        Returns:
            TaxRate: Applicable tax rate
        """
        # Check custom rates first
        if hsn_code in self.custom_rates:
            return self.custom_rates[hsn_code]
        
        # Default to 18% if not found
        return self.STANDARD_RATES[GSTCategory.EIGHTEEN]
    
    def calculate_tax_intra_state(
        self,
        base_amount: Decimal,
        tax_rate: Decimal
    ) -> TaxCalculation:
        """
        Calculate tax for intra-state transaction
        (CGST + SGST split 50-50)
        
        Args:
            base_amount: Base amount before tax
            tax_rate: Total tax rate (e.g., 18 for 18%)
            
        Returns:
            TaxCalculation: Tax calculation details
        """
        base = Decimal(str(base_amount))
        rate = Decimal(str(tax_rate))
        
        # Split rate equally between CGST and SGST
        half_rate = rate / Decimal("2")
        
        # Calculate tax components
        total_tax = (base * rate) / Decimal("100")
        cgst_amount = (base * half_rate) / Decimal("100")
        sgst_amount = (base * half_rate) / Decimal("100")
        
        # Round to 2 decimal places
        cgst_amount = cgst_amount.quantize(Decimal("0.01"))
        sgst_amount = sgst_amount.quantize(Decimal("0.01"))
        total_tax = total_tax.quantize(Decimal("0.01"))
        total_amount = base + total_tax
        
        return TaxCalculation(
            base_amount=base,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            igst_amount=Decimal("0"),
            total_tax=total_tax,
            total_amount=total_amount.quantize(Decimal("0.01")),
            tax_type=GSTType.INTRA_CGST,
            tax_rate=rate
        )
    
    def calculate_tax_inter_state(
        self,
        base_amount: Decimal,
        tax_rate: Decimal
    ) -> TaxCalculation:
        """
        Calculate tax for inter-state transaction
        (IGST only, no CGST/SGST split)
        
        Args:
            base_amount: Base amount before tax
            tax_rate: Tax rate (e.g., 18 for 18%)
            
        Returns:
            TaxCalculation: Tax calculation details
        """
        base = Decimal(str(base_amount))
        rate = Decimal(str(tax_rate))
        
        # Calculate IGST
        total_tax = (base * rate) / Decimal("100")
        total_tax = total_tax.quantize(Decimal("0.01"))
        total_amount = (base + total_tax).quantize(Decimal("0.01"))
        
        return TaxCalculation(
            base_amount=base,
            cgst_amount=Decimal("0"),
            sgst_amount=Decimal("0"),
            igst_amount=total_tax,
            total_tax=total_tax,
            total_amount=total_amount,
            tax_type=GSTType.INTRA_CGST,
            tax_rate=rate
        )
    
    def calculate_for_product(
        self,
        product_id: str,
        base_amount: Decimal,
        is_inter_state: bool = False,
        hsn_code: Optional[str] = None
    ) -> TaxCalculation:
        """
        Calculate tax for a product
        
        Args:
            product_id: Product identifier
            base_amount: Base amount
            is_inter_state: Inter-state transaction?
            hsn_code: HSN code (optional)
            
        Returns:
            TaxCalculation: Tax calculation
        """
        # Get tax rate for HSN code
        if hsn_code:
            tax_rate = self.get_rate_for_hsn(hsn_code)
            rate_value = float(tax_rate.igst_rate)
        else:
            rate_value = 18  # Default to 18%
        
        # Calculate based on transaction type
        if is_inter_state:
            return self.calculate_tax_inter_state(base_amount, Decimal(str(rate_value)))
        else:
            return self.calculate_tax_intra_state(base_amount, Decimal(str(rate_value)))
    
    def calculate_line_items(
        self,
        items: List[Dict],
        is_inter_state: bool = False
    ) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        """
        Calculate tax for multiple line items
        
        Args:
            items: List of items with quantity, rate, hsn_code
            is_inter_state: Inter-state transaction?
            
        Returns:
            Tuple: (subtotal, cgst, sgst/igst, total)
        """
        subtotal = Decimal("0")
        total_cgst = Decimal("0")
        total_sgst_igst = Decimal("0")
        
        for item in items:
            base_amount = Decimal(str(item["quantity"])) * Decimal(str(item["rate"]))
            hsn_code = item.get("hsn_code")
            
            # Calculate tax for this item
            tax_calc = self.calculate_for_product(
                item.get("product_id", ""),
                base_amount,
                is_inter_state,
                hsn_code
            )
            
            subtotal += tax_calc.base_amount
            total_cgst += tax_calc.cgst_amount
            total_sgst_igst += tax_calc.sgst_amount + tax_calc.igst_amount
        
        total = subtotal + total_cgst + total_sgst_igst
        
        return (
            subtotal.quantize(Decimal("0.01")),
            total_cgst.quantize(Decimal("0.01")),
            total_sgst_igst.quantize(Decimal("0.01")),
            total.quantize(Decimal("0.01"))
        )
    
    def get_gst_return_summary(
        self,
        start_date: date,
        end_date: date,
        transactions: List[Dict]
    ) -> Dict:
        """
        Generate GST return summary (GSTR-1 equivalent)
        
        Args:
            start_date: Period start date
            end_date: Period end date
            transactions: List of transactions
            
        Returns:
            Dict: GST return summary
        """
        intra_state_value = Decimal("0")
        inter_state_value = Decimal("0")
        total_cgst = Decimal("0")
        total_sgst = Decimal("0")
        total_igst = Decimal("0")
        total_gst = Decimal("0")
        
        for txn in transactions:
            base = Decimal(str(txn.get("base_amount", 0)))
            cgst = Decimal(str(txn.get("cgst", 0)))
            sgst = Decimal(str(txn.get("sgst", 0)))
            igst = Decimal(str(txn.get("igst", 0)))
            
            if txn.get("is_inter_state"):
                inter_state_value += base
                total_igst += igst
            else:
                intra_state_value += base
                total_cgst += cgst
                total_sgst += sgst
            
            total_gst += cgst + sgst + igst
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "intra_state": {
                "value": float(intra_state_value),
                "cgst": float(total_cgst),
                "sgst": float(total_sgst)
            },
            "inter_state": {
                "value": float(inter_state_value),
                "igst": float(total_igst)
            },
            "summary": {
                "total_value": float(intra_state_value + inter_state_value),
                "total_gst": float(total_gst),
                "total_cgst": float(total_cgst),
                "total_sgst": float(total_sgst),
                "total_igst": float(total_igst)
            }
        }
    
    def validate_hsn_code(self, hsn_code: str) -> bool:
        """
        Validate HSN code format
        
        Args:
            hsn_code: HSN code to validate
            
        Returns:
            bool: Valid HSN code?
        """
        # HSN codes are 4, 6, or 8 digits
        if not hsn_code or not hsn_code.isdigit():
            return False
        
        return len(hsn_code) in [4, 6, 8]
    
    def get_all_rates(self) -> Dict[str, Dict]:
        """
        Get all configured tax rates
        
        Returns:
            Dict: All tax rates with details
        """
        rates = {}
        
        for category, rate in self.STANDARD_RATES.items():
            rates[category.value] = {
                "category": category.value,
                "description": rate.description,
                "cgst": float(rate.cgst_rate),
                "sgst": float(rate.sgst_rate),
                "igst": float(rate.igst_rate)
            }
        
        return rates


# Initialize global GST service
gst_service = GSTService()
