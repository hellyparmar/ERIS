"""
E-Invoice Preparation Service
Generates GST-compliant E-Invoice JSON payload

Compliant with GST E-Invoice schema v1.1
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
import jsonschema
import logging

logger = logging.getLogger(__name__)


# ============================================================
# PYDANTIC MODELS FOR E-INVOICE
# ============================================================

class EInvoiceAddress(BaseModel):
    """Address model for E-Invoice"""
    Addr1: str = Field(..., max_length=100, description="Address Line 1")
    Addr2: Optional[str] = Field(None, max_length=100, description="Address Line 2")
    Loc: str = Field(..., max_length=50, description="Location/City")
    Pin: str = Field(..., regex=r'^\d{6}$', description="6-digit PIN code")
    Stcd: str = Field(..., regex=r'^\d{2}$', description="State Code")
    
    class Config:
        schema_extra = {
            "example": {
                "Addr1": "123 MG Road",
                "Addr2": "Koramangala",
                "Loc": "Bangalore",
                "Pin": "560001",
                "Stcd": "29"
            }
        }


class EInvoiceSellerDetails(BaseModel):
    """Seller details for E-Invoice"""
    Gstin: str = Field(..., regex=r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$')
    LglNm: str = Field(..., max_length=100, description="Legal Name")
    TrdNm: Optional[str] = Field(None, max_length=100, description="Trade Name")
    Addr1: str
    Addr2: Optional[str] = None
    Loc: str
    Pin: str = Field(..., regex=r'^\d{6}$')
    Stcd: str = Field(..., regex=r'^\d{2}$')
    Ph: Optional[str] = Field(None, max_length=15)
    Em: Optional[str] = Field(None, max_length=100)


class EInvoiceBuyerDetails(BaseModel):
    """Buyer details for E-Invoice"""
    Gstin: Optional[str] = Field(None, regex=r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$')
    LglNm: str = Field(..., max_length=100)
    TrdNm: Optional[str] = None
    Pos: str = Field(..., regex=r'^\d{2}$', description="Place of Supply")
    Addr1: str
    Addr2: Optional[str] = None
    Loc: str
    Pin: str = Field(..., regex=r'^\d{6}$')
    Stcd: str = Field(..., regex=r'^\d{2}$')
    Ph: Optional[str] = None
    Em: Optional[str] = None


class EInvoiceItemDetails(BaseModel):
    """Line item for E-Invoice"""
    SlNo: str = Field(..., description="Serial Number")
    PrdDesc: str = Field(..., max_length=300, description="Product Description")
    IsServc: str = Field(..., regex=r'^[NY]$', description="Is Service (Y/N)")
    HsnCd: str = Field(..., max_length=8, description="HSN/SAC Code")
    Barcde: Optional[str] = None
    Qty: Decimal = Field(..., description="Quantity")
    FreeQty: Optional[Decimal] = Field(0, description="Free Quantity")
    Unit: str = Field(..., max_length=8, description="Unit")
    UnitPrice: Decimal = Field(..., description="Unit Price")
    TotAmt: Decimal = Field(..., description="Total Amount before discount")
    Discount: Optional[Decimal] = Field(0, description="Discount Amount")
    PreTaxVal: Optional[Decimal] = None
    AssAmt: Decimal = Field(..., description="Taxable Value")
    GstRt: Decimal = Field(..., description="GST Rate %")
    IgstAmt: Optional[Decimal] = Field(0)
    CgstAmt: Optional[Decimal] = Field(0)
    SgstAmt: Optional[Decimal] = Field(0)
    CesRt: Optional[Decimal] = Field(0, description="Cess Rate %")
    CesAmt: Optional[Decimal] = Field(0, description="Cess Amount")
    CesNonAdvlAmt: Optional[Decimal] = Field(0)
    StateCesRt: Optional[Decimal] = Field(0)
    StateCesAmt: Optional[Decimal] = Field(0)
    StateCesNonAdvlAmt: Optional[Decimal] = Field(0)
    OthChrg: Optional[Decimal] = Field(0, description="Other Charges")
    TotItemVal: Decimal = Field(..., description="Total Item Value")


class EInvoiceValueDetails(BaseModel):
    """Value details for E-Invoice"""
    AssVal: Decimal = Field(..., description="Taxable Value")
    CgstVal: Optional[Decimal] = Field(0)
    SgstVal: Optional[Decimal] = Field(0)
    IgstVal: Optional[Decimal] = Field(0)
    CesVal: Optional[Decimal] = Field(0)
    StCesVal: Optional[Decimal] = Field(0)
    Discount: Optional[Decimal] = Field(0)
    OthChrg: Optional[Decimal] = Field(0)
    RndOffAmt: Optional[Decimal] = Field(0, description="Round Off Amount")
    TotInvVal: Decimal = Field(..., description="Total Invoice Value")
    TotInvValFc: Optional[Decimal] = None


class EInvoiceDocument(BaseModel):
    """Complete E-Invoice document"""
    Version: str = "1.1"
    
    # Transaction Details
    TranDtls: Dict[str, Any] = {
        "TaxSch": "GST",
        "SupTyp": "B2B",  # B2B, B2C, SEZWP, SEZWOP, EXPWP, EXPWOP, DEXP
        "RegRev": "N",     # Reverse Charge (Y/N)
        "EcmGstin": None,  # E-Commerce GSTIN
        "IgstOnIntra": "N" # IGST on intra-state
    }
    
    # Document Details
    DocDtls: Dict[str, str]
    
    # Seller Details
    SellerDtls: EInvoiceSellerDetails
    
    # Buyer Details
    BuyerDtls: EInvoiceBuyerDetails
    
    # Dispatch Details (optional)
    DispDtls: Optional[Dict] = None
    
    # Ship To Details (optional)
    ShipDtls: Optional[Dict] = None
    
    # Item List
    ItemList: List[EInvoiceItemDetails]
    
    # Value Details
    ValDtls: EInvoiceValueDetails
    
    # Payment Details (optional)
    PayDtls: Optional[Dict] = None
    
    # Reference Details (optional)
    RefDtls: Optional[Dict] = None
    
    # Additional Document Details (optional)
    AddlDocDtls: Optional[List[Dict]] = None
    
    # Export Details (optional)
    ExpDtls: Optional[Dict] = None
    
    # E-Way Bill Details (optional)
    EwbDtls: Optional[Dict] = None


# ============================================================
# E-INVOICE PREPARATION SERVICE
# ============================================================

class EInvoicePreparationService:
    """
    Service to prepare E-Invoice JSON from invoice data
    """
    
    def __init__(self):
        pass
    
    def prepare_einvoice(self,
                        invoice_data: Dict,
                        seller_data: Dict,
                        buyer_data: Dict,
                        line_items: List[Dict]) -> Dict:
        """
        Prepare E-Invoice JSON payload
        
        Args:
            invoice_data: Invoice header data
            seller_data: Seller/organization details
            buyer_data: Customer/buyer details
            line_items: Invoice line items with tax calculation
            
        Returns:
            E-Invoice JSON payload
        """
        # Transaction Details
        tran_dtls = self._prepare_transaction_details(invoice_data)
        
        # Document Details
        doc_dtls = self._prepare_document_details(invoice_data)
        
        # Seller Details
        seller_dtls = self._prepare_seller_details(seller_data)
        
        # Buyer Details
        buyer_dtls = self._prepare_buyer_details(buyer_data, invoice_data)
        
        # Item List
        item_list = self._prepare_item_list(line_items)
        
        # Value Details
        val_dtls = self._prepare_value_details(invoice_data, line_items)
        
        # Construct E-Invoice
        einvoice = {
            "Version": "1.1",
            "TranDtls": tran_dtls,
            "DocDtls": doc_dtls,
            "SellerDtls": seller_dtls,
            "BuyerDtls": buyer_dtls,
            "ItemList": item_list,
            "ValDtls": val_dtls
        }
        
        return einvoice
    
    def _prepare_transaction_details(self, invoice_data: Dict) -> Dict:
        """Prepare transaction details section"""
        supply_type = "B2B" if invoice_data.get('customer_gstin') else "B2C"
        
        return {
            "TaxSch": "GST",
            "SupTyp": supply_type,
            "RegRev": "Y" if invoice_data.get('reverse_charge') else "N",
            "EcmGstin": invoice_data.get('ecommerce_gstin'),
            "IgstOnIntra": "Y" if invoice_data.get('igst_on_intra') else "N"
        }
    
    def _prepare_document_details(self, invoice_data: Dict) -> Dict:
        """Prepare document details section"""
        invoice_date = invoice_data['invoice_date']
        
        if isinstance(invoice_date, str):
            invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d')
        
        return {
            "Typ": "INV",  # Invoice type
            "No": invoice_data['invoice_number'],
            "Dt": invoice_date.strftime('%d/%m/%Y')
        }
    
    def _prepare_seller_details(self, seller_data: Dict) -> Dict:
        """Prepare seller details section"""
        address = seller_data.get('address', {})
        
        return {
            "Gstin": seller_data['gstin'],
            "LglNm": seller_data['legal_name'],
            "TrdNm": seller_data.get('name', seller_data['legal_name']),
            "Addr1": address.get('line1', ''),
            "Addr2": address.get('line2'),
            "Loc": address.get('city', ''),
            "Pin": address.get('pincode', ''),
            "Stcd": address.get('state_code', ''),
            "Ph": seller_data.get('contact_phone'),
            "Em": seller_data.get('contact_email')
        }
    
    def _prepare_buyer_details(self, buyer_data: Dict, invoice_data: Dict) -> Dict:
        """Prepare buyer details section"""
        address = buyer_data.get('address', {})
        
        return {
            "Gstin": buyer_data.get('gstin'),
            "LglNm": buyer_data.get('name', 'Cash Customer'),
            "TrdNm": buyer_data.get('name'),
            "Pos": invoice_data.get('place_of_supply', address.get('state_code', '')),
            "Addr1": address.get('line1', 'Not Provided'),
            "Addr2": address.get('line2'),
            "Loc": address.get('city', 'Not Provided'),
            "Pin": address.get('pincode', '999999'),
            "Stcd": address.get('state_code', '99'),
            "Ph": buyer_data.get('phone'),
            "Em": buyer_data.get('email')
        }
    
    def _prepare_item_list(self, line_items: List[Dict]) -> List[Dict]:
        """Prepare item list section"""
        items = []
        
        for idx, item in enumerate(line_items, start=1):
            tax_breakdown = item.get('tax_breakdown', {})
            
            items.append({
                "SlNo": str(idx),
                "PrdDesc": item['name'],
                "IsServc": "N",  # "Y" for services, "N" for goods
                "HsnCd": item.get('hsn_code', ''),
                "Qty": float(item['quantity']),
                "Unit": item.get('unit', 'PCS'),
                "UnitPrice": float(item['unit_price']),
                "TotAmt": float(item['quantity']) * float(item['unit_price']),
                "Discount": float(tax_breakdown.get('discount_amount', 0)),
                "AssAmt": float(tax_breakdown['taxable_amount']),
                "GstRt": float(tax_breakdown.get('cgst_rate', 0)) + 
                         float(tax_breakdown.get('sgst_rate', 0)) +
                         float(tax_breakdown.get('igst_rate', 0)),
                "IgstAmt": float(tax_breakdown.get('igst_amount', 0)),
                "CgstAmt": float(tax_breakdown.get('cgst_amount', 0)),
                "SgstAmt": float(tax_breakdown.get('sgst_amount', 0)),
                "CesRt": float(tax_breakdown.get('cess_rate', 0)),
                "CesAmt": float(tax_breakdown.get('cess_amount', 0)),
                "TotItemVal": float(tax_breakdown['total_amount'])
            })
        
        return items
    
    def _prepare_value_details(self, invoice_data: Dict, line_items: List[Dict]) -> Dict:
        """Prepare value details section"""
        return {
            "AssVal": float(invoice_data['taxable_amount']),
            "CgstVal": float(invoice_data.get('cgst_amount', 0)),
            "SgstVal": float(invoice_data.get('sgst_amount', 0)),
            "IgstVal": float(invoice_data.get('igst_amount', 0)),
            "CesVal": float(invoice_data.get('cess_amount', 0)),
            "RndOffAmt": float(invoice_data.get('round_off', 0)),
            "TotInvVal": float(invoice_data['grand_total'])
        }
    
    def validate_einvoice(self, einvoice: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate E-Invoice JSON against schema
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic validation
            required_fields = ['Version', 'TranDtls', 'DocDtls', 'SellerDtls', 'BuyerDtls', 'ItemList', 'ValDtls']
            
            for field in required_fields:
                if field not in einvoice:
                    return False, f"Missing required field: {field}"
            
            # Validate GSTIN format
            seller_gstin = einvoice['SellerDtls'].get('Gstin')
            if not seller_gstin or len(seller_gstin) != 15:
                return False, "Invalid seller GSTIN"
            
            # Validate item list not empty
            if not einvoice['ItemList'] or len(einvoice['ItemList']) == 0:
                return False, "Invoice must have at least one item"
            
            # Validate totals match
            calculated_total = sum(float(item['TotItemVal']) for item in einvoice['ItemList'])
            declared_total = float(einvoice['ValDtls']['TotInvVal'])
            
            if abs(calculated_total - declared_total) > 0.01:  # Allow 1 paisa difference for rounding
                return False, f"Total mismatch: Calculated {calculated_total}, Declared {declared_total}"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    service = EInvoicePreparationService()
    
    # Sample data
    invoice_data = {
        'invoice_number': 'INV-2024-001',
        'invoice_date': '2024-01-15',
        'customer_gstin': '29ABCDE1234F1Z5',
        'reverse_charge': False,
        'place_of_supply': '29',
        'taxable_amount': 90000.00,
        'cgst_amount': 8100.00,
        'sgst_amount': 8100.00,
        'igst_amount': 0,
        'cess_amount': 0,
        'round_off': 0,
        'grand_total': 106200.00
    }
    
    seller_data = {
        'gstin': '29AABCT1332L1Z5',
        'legal_name': 'ABC Technologies Pvt Ltd',
        'name': 'ABC Tech',
        'address': {
            'line1': '123 MG Road',
            'line2': 'Koramangala',
            'city': 'Bangalore',
            'state_code': '29',
            'pincode': '560001'
        },
        'contact_phone': '+91-9876543210',
        'contact_email': 'sales@abctech.com'
    }
    
    buyer_data = {
        'gstin': '29XYZ DE5678P1ZA',
        'name': 'XYZ Corporation',
        'address': {
            'line1': '456 Brigade Road',
            'city': 'Bangalore',
            'state_code': '29',
            'pincode': '560025'
        },
        'phone': '+91-9988776655',
        'email': 'purchase@xyzcorp.com'
    }
    
    line_items = [
        {
            'name': 'Laptop - Dell Inspiron',
            'hsn_code': '8471',
            'quantity': 2,
            'unit': 'PCS',
            'unit_price': 50000,
            'tax_breakdown': {
                'taxable_amount': 90000,
                'cgst_rate': 9,
                'cgst_amount': 8100,
                'sgst_rate': 9,
                'sgst_amount': 8100,
                'igst_rate': 0,
                'igst_amount': 0,
                'cess_rate': 0,
                'cess_amount': 0,
                'total_amount': 106200
            }
        }
    ]
    
    # Generate E-Invoice
    einvoice = service.prepare_einvoice(invoice_data, seller_data, buyer_data, line_items)
    
    # Validate
    is_valid, error = service.validate_einvoice(einvoice)
    
    if is_valid:
        print("✓ E-Invoice generated successfully!")
        print(f"  Invoice: {einvoice['DocDtls']['No']}")
        print(f"  Total: ₹{einvoice['ValDtls']['TotInvVal']}")
    else:
        print(f"✗ E-Invoice validation failed: {error}")
