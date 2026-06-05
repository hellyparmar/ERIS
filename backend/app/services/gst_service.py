"""
GST (Goods and Services Tax) Service

Implements GST calculation logic for India (HSN-based categorization).
Generates GSTR-1 (outward supplies) and GSTR-3B (monthly returns) reports.

GST Structure in India:
- CGST (Central GST): Central government tax
- SGST (State GST): State government tax
- IGST (Integrated GST): Applied to inter-state supplies
- For intra-state: CGST + SGST = Total GST
- For inter-state: IGST = Total GST

HSN (Harmonized System of Nomenclature) is used for product categorization.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class GSTService:
    """
    Service for GST calculation and report generation.
    
    Supports:
    - GST rate lookup by product category
    - GST amount calculation (CGST/SGST split)
    - GSTR-1 return generation (outward supplies)
    - GSTR-3B return generation (monthly summary)
    - Tax liability calculation
    """
    
    # GST rate map by product category (Indian HSN-based approximations)
    # These are typical rates; actual rates depend on product classification
    GST_RATES = {
        "Beverages": 0.12,      # 12% - Soft drinks, juices
        "Snacks": 0.12,         # 12% - Packaged snacks
        "Dairy": 0.05,          # 5% - Milk, yogurt, butter
        "Bakery": 0.05,         # 5% - Bread, pastries
        "Personal Care": 0.18,  # 18% - Soaps, shampoo, cosmetics
        "Cleaning": 0.18,       # 18% - Detergents, disinfectants
        "Frozen Foods": 0.12,   # 12% - Frozen vegetables, meat
        "Staples": 0.05,        # 5% - Rice, flour, pulses, salt
    }
    
    # Rate slabs for GSTR reports
    RATE_SLABS = [0.05, 0.12, 0.18, 0.28]
    
    def __init__(self, session: Optional[AsyncSession] = None):
        """
        Initialize GST Service.
        
        Args:
            session: SQLAlchemy async session for database queries
        """
        self.session = session
        self.logger = logger
    
    def get_gst_rate(self, category: str) -> float:
        """
        Get GST rate for a product category.
        
        Args:
            category: Product category (key from GST_RATES)
        
        Returns:
            GST rate as decimal (e.g., 0.05 for 5%)
        
        Raises:
            ValueError: If category not found, returns 18% as default
        """
        rate = self.GST_RATES.get(category, 0.18)  # Default to 18%
        self.logger.debug(f"GST rate for {category}: {rate*100}%")
        return rate
    
    def calculate_gst(self, amount: float, category: str, 
                     is_interstate: bool = False) -> Dict[str, Any]:
        """
        Calculate GST amount for a product.
        
        For intra-state sales (is_interstate=False):
            - CGST = Total GST / 2
            - SGST = Total GST / 2
        
        For inter-state sales (is_interstate=True):
            - IGST = Total GST (no CGST/SGST split)
        
        Args:
            amount: Base amount before GST (in INR)
            category: Product category (from GST_RATES)
            is_interstate: True for inter-state, False for intra-state
        
        Returns:
            Dictionary with structure:
            {
                'base_amount': float,           # Original amount
                'gst_rate': float,              # Rate as decimal (0.05 = 5%)
                'gst_rate_percent': str,        # Rate as percentage string (e.g., "5%")
                'cgst_rate': float,             # CGST rate (0 for interstate)
                'sgst_rate': float,             # SGST rate (0 for interstate)
                'igst_rate': float,             # IGST rate (0 for intrastate)
                'cgst_amount': float,           # CGST amount (0 for interstate)
                'sgst_amount': float,           # SGST amount (0 for interstate)
                'igst_amount': float,           # IGST amount (0 for intrastate)
                'total_gst': float,             # Total tax amount
                'total_with_gst': float,        # Amount including GST
                'is_interstate': bool,          # Sales type
            }
        """
        try:
            gst_rate = self.get_gst_rate(category)
            total_gst = amount * gst_rate
            
            if is_interstate:
                # Inter-state: IGST = Total GST
                return {
                    'base_amount': round(amount, 2),
                    'gst_rate': gst_rate,
                    'gst_rate_percent': f"{int(gst_rate * 100)}%",
                    'cgst_rate': 0.0,
                    'sgst_rate': 0.0,
                    'igst_rate': gst_rate,
                    'cgst_amount': 0.0,
                    'sgst_amount': 0.0,
                    'igst_amount': round(total_gst, 2),
                    'total_gst': round(total_gst, 2),
                    'total_with_gst': round(amount + total_gst, 2),
                    'is_interstate': True,
                }
            else:
                # Intra-state: CGST + SGST = Total GST
                cgst_amount = total_gst / 2
                sgst_amount = total_gst / 2
                return {
                    'base_amount': round(amount, 2),
                    'gst_rate': gst_rate,
                    'gst_rate_percent': f"{int(gst_rate * 100)}%",
                    'cgst_rate': gst_rate / 2,
                    'sgst_rate': gst_rate / 2,
                    'igst_rate': 0.0,
                    'cgst_amount': round(cgst_amount, 2),
                    'sgst_amount': round(sgst_amount, 2),
                    'igst_amount': 0.0,
                    'total_gst': round(total_gst, 2),
                    'total_with_gst': round(amount + total_gst, 2),
                    'is_interstate': False,
                }
        
        except Exception as e:
            self.logger.error(f"Error calculating GST: {str(e)}")
            raise
    
    def _fetch_sales_data(self, outlet_id: str, month: int, year: int) -> List[Dict[str, Any]]:
        """
        Fetch sales data for a period from database.
        
        Args:
            outlet_id: Outlet identifier
            month: Month number (1-12)
            year: Year
        
        Returns:
            List of sales records with amount and category
        
        Note:
            This is a stub implementation. In production, would query
            actual sales/invoice data from database.
        """
        # Stub: Return sample data for testing
        # In production, this would query Sales and Invoice tables
        return [
            {
                'invoice_id': 'INV001',
                'amount': 1000.0,
                'category': 'Beverages',
                'invoice_date': date(year, month, 1),
            },
            {
                'invoice_id': 'INV002',
                'amount': 500.0,
                'category': 'Dairy',
                'invoice_date': date(year, month, 5),
            },
            {
                'invoice_id': 'INV003',
                'amount': 750.0,
                'category': 'Personal Care',
                'invoice_date': date(year, month, 10),
            },
        ]
    
    def generate_gstr1_summary(self, outlet_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Generate GSTR-1 return summary (outward supplies).
        
        GSTR-1 is a monthly return filed by suppliers showing:
        - Details of outward supplies (sales)
        - HSN-wise breakdown
        - Taxable value and tax amounts
        
        Args:
            outlet_id: Outlet identifier
            month: Month number (1-12)
            year: Year
        
        Returns:
            Dictionary with structure:
            {
                'return_type': 'GSTR-1',
                'outlet_id': str,
                'period': 'YYYY-MM',
                'generated_date': str (ISO format),
                'summary_by_rate': {
                    '5%': {
                        'rate': 0.05,
                        'taxable_value': float,
                        'cgst': float,
                        'sgst': float,
                        'igst': float,
                        'total_tax': float,
                    },
                    ...
                },
                'total_summary': {
                    'total_taxable_value': float,
                    'total_cgst': float,
                    'total_sgst': float,
                    'total_igst': float,
                    'total_tax': float,
                    'grand_total': float,
                },
                'invoices': [
                    {
                        'invoice_no': str,
                        'invoice_date': str,
                        'category': str,
                        'taxable_value': float,
                        'gst_rate': str,
                        'cgst': float,
                        'sgst': float,
                        'igst': float,
                        'total_amount': float,
                    },
                    ...
                ],
                'notes': str,
            }
        """
        try:
            sales_data = self._fetch_sales_data(outlet_id, month, year)
            
            # Initialize summary structure by rate slab
            summary_by_rate = {
                '5%': {
                    'rate': 0.05,
                    'taxable_value': 0.0,
                    'cgst': 0.0,
                    'sgst': 0.0,
                    'igst': 0.0,
                    'total_tax': 0.0,
                },
                '12%': {
                    'rate': 0.12,
                    'taxable_value': 0.0,
                    'cgst': 0.0,
                    'sgst': 0.0,
                    'igst': 0.0,
                    'total_tax': 0.0,
                },
                '18%': {
                    'rate': 0.18,
                    'taxable_value': 0.0,
                    'cgst': 0.0,
                    'sgst': 0.0,
                    'igst': 0.0,
                    'total_tax': 0.0,
                },
                '28%': {
                    'rate': 0.28,
                    'taxable_value': 0.0,
                    'cgst': 0.0,
                    'sgst': 0.0,
                    'igst': 0.0,
                    'total_tax': 0.0,
                },
            }
            
            invoices = []
            total_taxable = 0.0
            total_cgst = 0.0
            total_sgst = 0.0
            total_igst = 0.0
            
            # Process each sale
            for sale in sales_data:
                gst_calc = self.calculate_gst(
                    sale['amount'],
                    sale['category'],
                    is_interstate=False  # Assuming intra-state
                )
                
                rate_key = gst_calc['gst_rate_percent']
                
                # Update summary
                if rate_key in summary_by_rate:
                    summary_by_rate[rate_key]['taxable_value'] += gst_calc['base_amount']
                    summary_by_rate[rate_key]['cgst'] += gst_calc['cgst_amount']
                    summary_by_rate[rate_key]['sgst'] += gst_calc['sgst_amount']
                    summary_by_rate[rate_key]['igst'] += gst_calc['igst_amount']
                    summary_by_rate[rate_key]['total_tax'] += gst_calc['total_gst']
                
                # Track totals
                total_taxable += gst_calc['base_amount']
                total_cgst += gst_calc['cgst_amount']
                total_sgst += gst_calc['sgst_amount']
                total_igst += gst_calc['igst_amount']
                
                # Add invoice detail
                invoices.append({
                    'invoice_no': sale.get('invoice_id', ''),
                    'invoice_date': sale.get('invoice_date', '').isoformat(),
                    'category': sale.get('category', ''),
                    'taxable_value': gst_calc['base_amount'],
                    'gst_rate': gst_calc['gst_rate_percent'],
                    'cgst': gst_calc['cgst_amount'],
                    'sgst': gst_calc['sgst_amount'],
                    'igst': gst_calc['igst_amount'],
                    'total_amount': gst_calc['total_with_gst'],
                })
            
            # Round totals
            total_tax = total_cgst + total_sgst + total_igst
            
            return {
                'return_type': 'GSTR-1',
                'outlet_id': outlet_id,
                'period': f"{year}-{month:02d}",
                'generated_date': datetime.now().isoformat(),
                'summary_by_rate': {k: {
                    'rate': v['rate'],
                    'rate_percent': k,
                    'taxable_value': round(v['taxable_value'], 2),
                    'cgst': round(v['cgst'], 2),
                    'sgst': round(v['sgst'], 2),
                    'igst': round(v['igst'], 2),
                    'total_tax': round(v['total_tax'], 2),
                } for k, v in summary_by_rate.items()},
                'total_summary': {
                    'total_taxable_value': round(total_taxable, 2),
                    'total_cgst': round(total_cgst, 2),
                    'total_sgst': round(total_sgst, 2),
                    'total_igst': round(total_igst, 2),
                    'total_tax': round(total_tax, 2),
                    'grand_total': round(total_taxable + total_tax, 2),
                },
                'invoices': invoices,
                'invoice_count': len(invoices),
                'notes': f'GSTR-1 return for {year}-{month:02d}. {len(invoices)} invoices processed.',
            }
        
        except Exception as e:
            self.logger.error(f"Error generating GSTR-1: {str(e)}")
            raise
    
    def generate_gstr3b_summary(self, outlet_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Generate GSTR-3B return summary (monthly return).
        
        GSTR-3B is a monthly return showing:
        - Outward supplies (from GSTR-1)
        - Tax liability
        - Input Tax Credit (ITC) eligibility
        - Net tax payable
        
        Args:
            outlet_id: Outlet identifier
            month: Month number (1-12)
            year: Year
        
        Returns:
            Dictionary with structure:
            {
                'return_type': 'GSTR-3B',
                'outlet_id': str,
                'period': 'YYYY-MM',
                'generated_date': str (ISO format),
                'outward_supplies': {
                    'taxable_supplies': float,
                    'non_taxable_supplies': float,
                    'total_supplies': float,
                },
                'tax_liability': {
                    'cgst_liability': float,
                    'sgst_liability': float,
                    'igst_liability': float,
                    'total_tax_liability': float,
                },
                'itc_eligibility': {
                    'cgst_itc': float,
                    'sgst_itc': float,
                    'igst_itc': float,
                    'total_itc': float,
                },
                'net_payable': {
                    'cgst_payable': float,
                    'sgst_payable': float,
                    'igst_payable': float,
                    'total_payable': float,
                },
                'summary_by_rate': {
                    rate_slab: {
                        'taxable_value': float,
                        'tax': float,
                    },
                    ...
                },
            }
        """
        try:
            # Get GSTR-1 data
            gstr1 = self.generate_gstr1_summary(outlet_id, month, year)
            
            # Calculate net payable (for now, assuming no ITC)
            # In production, would fetch actual ITC from purchase invoices
            total_supply = gstr1['total_summary']['total_taxable_value']
            total_tax_liability = gstr1['total_summary']['total_tax']
            
            cgst_liability = gstr1['total_summary']['total_cgst']
            sgst_liability = gstr1['total_summary']['total_sgst']
            igst_liability = gstr1['total_summary']['total_igst']
            
            # ITC (stub - typically 40-60% of outgoing tax for input goods)
            itc_rate = 0.5  # 50% assumption
            cgst_itc = cgst_liability * itc_rate
            sgst_itc = sgst_liability * itc_rate
            igst_itc = igst_liability * itc_rate
            total_itc = cgst_itc + sgst_itc + igst_itc
            
            # Net payable = Liability - ITC
            cgst_payable = max(0, cgst_liability - cgst_itc)
            sgst_payable = max(0, sgst_liability - sgst_itc)
            igst_payable = max(0, igst_liability - igst_itc)
            total_payable = cgst_payable + sgst_payable + igst_payable
            
            # Rate-wise summary
            summary_by_rate = {}
            for rate_key, rate_data in gstr1['summary_by_rate'].items():
                if rate_data['taxable_value'] > 0:  # Only include non-zero rates
                    summary_by_rate[rate_key] = {
                        'taxable_value': rate_data['taxable_value'],
                        'tax': rate_data['total_tax'],
                    }
            
            return {
                'return_type': 'GSTR-3B',
                'outlet_id': outlet_id,
                'period': f"{year}-{month:02d}",
                'generated_date': datetime.now().isoformat(),
                'outward_supplies': {
                    'taxable_supplies': round(total_supply, 2),
                    'non_taxable_supplies': 0.0,
                    'total_supplies': round(total_supply, 2),
                },
                'tax_liability': {
                    'cgst_liability': round(cgst_liability, 2),
                    'sgst_liability': round(sgst_liability, 2),
                    'igst_liability': round(igst_liability, 2),
                    'total_tax_liability': round(total_tax_liability, 2),
                },
                'itc_eligibility': {
                    'cgst_itc': round(cgst_itc, 2),
                    'sgst_itc': round(sgst_itc, 2),
                    'igst_itc': round(igst_itc, 2),
                    'total_itc': round(total_itc, 2),
                },
                'net_payable': {
                    'cgst_payable': round(cgst_payable, 2),
                    'sgst_payable': round(sgst_payable, 2),
                    'igst_payable': round(igst_payable, 2),
                    'total_payable': round(total_payable, 2),
                },
                'summary_by_rate': summary_by_rate,
                'notes': f'GSTR-3B return for {year}-{month:02d}. Calculated based on {len(gstr1["invoices"])} invoices.',
            }
        
        except Exception as e:
            self.logger.error(f"Error generating GSTR-3B: {str(e)}")
            raise
    
    def export_to_csv(self, data: Dict[str, Any], report_type: str = 'GSTR-1') -> str:
        """
        Convert report to CSV format.
        
        Args:
            data: Report data dictionary
            report_type: Type of report ('GSTR-1' or 'GSTR-3B')
        
        Returns:
            CSV string ready for download
        """
        try:
            lines = []
            
            # Header
            lines.append(f"{report_type} Report")
            lines.append(f"Period: {data['period']}")
            lines.append(f"Generated: {data['generated_date']}")
            lines.append("")
            
            if report_type == 'GSTR-1':
                # Summary by rate slab
                lines.append("Summary by GST Rate Slab")
                lines.append("Rate,Taxable Value,CGST,SGST,IGST,Total Tax")
                for rate, summary in data['summary_by_rate'].items():
                    lines.append(
                        f"{rate},"
                        f"{summary['taxable_value']},"
                        f"{summary['cgst']},"
                        f"{summary['sgst']},"
                        f"{summary['igst']},"
                        f"{summary['total_tax']}"
                    )
                
                # Total
                total = data['total_summary']
                lines.append("")
                lines.append("Total")
                lines.append(f"Taxable Value,{total['total_taxable_value']}")
                lines.append(f"CGST,{total['total_cgst']}")
                lines.append(f"SGST,{total['total_sgst']}")
                lines.append(f"IGST,{total['total_igst']}")
                lines.append(f"Total Tax,{total['total_tax']}")
                lines.append(f"Grand Total,{total['grand_total']}")
                
                # Invoice details
                lines.append("")
                lines.append("Invoice Details")
                lines.append(
                    "Invoice No,Invoice Date,Category,Taxable Value,"
                    "GST Rate,CGST,SGST,IGST,Total Amount"
                )
                for invoice in data['invoices']:
                    lines.append(
                        f"{invoice['invoice_no']},"
                        f"{invoice['invoice_date']},"
                        f"{invoice['category']},"
                        f"{invoice['taxable_value']},"
                        f"{invoice['gst_rate']},"
                        f"{invoice['cgst']},"
                        f"{invoice['sgst']},"
                        f"{invoice['igst']},"
                        f"{invoice['total_amount']}"
                    )
            
            elif report_type == 'GSTR-3B':
                # Outward supplies
                lines.append("Outward Supplies")
                outbound = data['outward_supplies']
                lines.append(f"Taxable Supplies,{outbound['taxable_supplies']}")
                lines.append(f"Non-Taxable Supplies,{outbound['non_taxable_supplies']}")
                lines.append(f"Total Supplies,{outbound['total_supplies']}")
                
                # Tax liability
                lines.append("")
                lines.append("Tax Liability")
                liability = data['tax_liability']
                lines.append(f"CGST Liability,{liability['cgst_liability']}")
                lines.append(f"SGST Liability,{liability['sgst_liability']}")
                lines.append(f"IGST Liability,{liability['igst_liability']}")
                lines.append(f"Total Tax Liability,{liability['total_tax_liability']}")
                
                # ITC
                lines.append("")
                lines.append("Input Tax Credit (ITC)")
                itc = data['itc_eligibility']
                lines.append(f"CGST ITC,{itc['cgst_itc']}")
                lines.append(f"SGST ITC,{itc['sgst_itc']}")
                lines.append(f"IGST ITC,{itc['igst_itc']}")
                lines.append(f"Total ITC,{itc['total_itc']}")
                
                # Net payable
                lines.append("")
                lines.append("Net Payable")
                payable = data['net_payable']
                lines.append(f"CGST Payable,{payable['cgst_payable']}")
                lines.append(f"SGST Payable,{payable['sgst_payable']}")
                lines.append(f"IGST Payable,{payable['igst_payable']}")
                lines.append(f"Total Payable,{payable['total_payable']}")
            
            return "\n".join(lines)
        
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
            raise
