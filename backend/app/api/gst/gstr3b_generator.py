"""
GSTR-3B Generator
Compiles sales and purchases data into the summary return format.
"""

from __future__ import annotations
from typing import Dict, List, Any
from decimal import Decimal


class GSTR3BGenerator:
    """
    Generates GSTR-3B JSON summary structure.
    Used for monthly tax payment returns (Total Liability & ITC).
    """

    @staticmethod
    def generate_report(
        period: str,
        gstin: str,
        legal_name: str,
        sales: List[Dict],
        purchases: List[Dict] = []
    ) -> Dict[str, Any]:
        """
        Main entry point to compile the GSTR-3B summary.
        """
        # Section 3.1: Details of Outward Supplies
        outward_taxable = {"txval": Decimal("0"), "iamt": Decimal("0"), "camt": Decimal("0"), "samt": Decimal("0"), "csamt": Decimal("0")}
        outward_zero_rated = {"txval": Decimal("0"), "iamt": Decimal("0"), "csamt": Decimal("0")}
        outward_nil_exempt = {"txval": Decimal("0")}

        for sale in sales:
            taxable = Decimal(str(sale.get("taxable_amount", 0)))
            igst = Decimal(str(sale.get("igst_amount", 0)))
            cgst = Decimal(str(sale.get("cgst_amount", 0)))
            sgst = Decimal(str(sale.get("sgst_amount", 0)))

            # If export / zero rated shape is needed we capture it, else assume std outward
            if sale.get("is_export", False):
                outward_zero_rated["txval"] += taxable
                outward_zero_rated["iamt"] += igst
            elif sale.get("gst_rate", -1) == 0:
                outward_nil_exempt["txval"] += taxable
            else:
                outward_taxable["txval"] += taxable
                outward_taxable["iamt"] += igst
                outward_taxable["camt"] += cgst
                outward_taxable["samt"] += sgst


        # Section 4: Eligible ITC (Input Tax Credit)
        itc_all_other = {"iamt": Decimal("0"), "camt": Decimal("0"), "samt": Decimal("0"), "csamt": Decimal("0")}
        
        for purchase in purchases:
            # For simplicity, assume all purchases are eligible for "All Other ITC"
            itc_all_other["iamt"] += Decimal(str(purchase.get("igst_amount", 0)))
            itc_all_other["camt"] += Decimal(str(purchase.get("cgst_amount", 0)))
            itc_all_other["samt"] += Decimal(str(purchase.get("sgst_amount", 0)))

        # Final Payload Structure
        return {
            "gstin": gstin,
            "ret_period": period,
            "legal_name": legal_name,
            
            # 3.1 Details of Outward Supplies and inward supplies liable to reverse charge
            "sup_details": {
                "osup_det": {      # (a) Outward taxable supplies (other than zero rated, nil rated and exempted)
                    "txval": float(outward_taxable["txval"]),
                    "iamt": float(outward_taxable["iamt"]),
                    "camt": float(outward_taxable["camt"]),
                    "samt": float(outward_taxable["samt"]),
                    "csamt": 0.0
                },
                "osup_zero": {     # (b) Outward taxable supplies (zero rated)
                    "txval": float(outward_zero_rated["txval"]),
                    "iamt": float(outward_zero_rated["iamt"]),
                    "csamt": 0.0
                },
                "osup_nil_exmp": { # (c) Other outward supplies (Nil rated, exempted)
                    "txval": float(outward_nil_exempt["txval"])
                },
                "isup_rev": {      # (d) Inward supplies (liable to reverse charge)
                    "txval": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0
                },
                "osup_non_gst": {  # (e) Non-GST outward supplies
                    "txval": 0.0
                }
            },
            
            # 3.2 Of the supplies shown in 3.1 (a) above, details of inter-State supplies made to unregistered persons
            "inter_sup": {
                "unreg_details": [] # Would group B2CS interstate by POS
            },

            # 4. Eligible ITC
            "itc_elg": {
                "itc_avl": [
                    {
                        "ty": "IMPG", # Import of goods
                        "iamt": 0.0, "csamt": 0.0
                    },
                    {
                        "ty": "IMPS", # Import of services
                        "iamt": 0.0, "csamt": 0.0
                    },
                    {
                        "ty": "OTH",  # All other ITC
                        "iamt": float(itc_all_other["iamt"]),
                        "camt": float(itc_all_other["camt"]),
                        "samt": float(itc_all_other["samt"]),
                        "csamt": 0.0
                    }
                ],
                "itc_rev": [],    # ITC Reversed
                "itc_net": {      # Net ITC Available (avl - rev)
                    "iamt": float(itc_all_other["iamt"]),
                    "camt": float(itc_all_other["camt"]),
                    "samt": float(itc_all_other["samt"]),
                    "csamt": 0.0
                }
            }
        }
