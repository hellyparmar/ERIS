"""
GSTR-1 (Outward Supplies) Generator
Compiles sales data into the official GST reporting format.
"""

from __future__ import annotations

from typing import Dict, List, Any
from datetime import date
from decimal import Decimal
from collections import defaultdict


class GSTR1Generator:
    """
    Generates GSTR-1 JSON payload structure from R-DIOS sales data.
    """

    @staticmethod
    def generate_report(
        period: str,           # e.g., "052024" for May 2024
        gstin: str,            # Seller's GSTIN
        gross_turnover: float, # Previous financial year turnover
        sales: List[Dict]      # Raw sales dictionaries
    ) -> Dict[str, Any]:
        """
        Main entry point to compile the full GSTR-1 report.
        """
        b2b: List[Dict] = []
        b2cl: List[Dict] = []
        b2cs: List[Dict] = []
        hsn_data = defaultdict(lambda: {"qty": 0, "val": Decimal("0"), "txval": Decimal("0"),
                                        "iamt": Decimal("0"), "camt": Decimal("0"), "samt": Decimal("0")})

        for sale in sales:
            invoice_val = Decimal(str(sale.get("grand_total", 0)))
            is_interstate = sale.get("is_interstate", False)
            buyer_gstin = sale.get("customer_gstin", "")

            # 1. B2B (Business to Business)
            if buyer_gstin:
                b2b.append(GSTR1Generator._format_b2b_inv(buyer_gstin, sale))
            
            # 2. B2C Large (Inter-state sale > ₹2.5 Lakhs)
            elif is_interstate and invoice_val > Decimal("250000"):
                b2cl.append(GSTR1Generator._format_b2cl_inv(sale))
            
            # 3. B2C Small (Local sales or Inter-state <= ₹2.5 Lakhs)
            else:
                pos = sale.get("place_of_supply", "27")  # Default to seller state code
                rate = str(sale.get("gst_rate", 0))
                
                # Append to B2CS aggregate
                match_found = False
                for item in b2cs:
                    if item["pos"] == pos and item["rt"] == rate:
                        item["txval"] += float(sale.get("taxable_amount", 0))
                        if is_interstate:
                            item["iamt"] += float(sale.get("igst_amount", 0))
                        else:
                            item["camt"] += float(sale.get("cgst_amount", 0))
                            item["samt"] += float(sale.get("sgst_amount", 0))
                        match_found = True
                        break
                
                if not match_found:
                    b2cs.append({
                        "sply_ty": "INTER" if is_interstate else "INTRA",
                        "pos": pos,
                        "typ": "OE", # Other than E-commerce
                        "rt": rate,
                        "txval": float(sale.get("taxable_amount", 0)),
                        "iamt": float(sale.get("igst_amount", 0)) if is_interstate else 0,
                        "camt": float(sale.get("cgst_amount", 0)) if not is_interstate else 0,
                        "samt": float(sale.get("sgst_amount", 0)) if not is_interstate else 0,
                        "csamt": 0
                    })

            # 4. HSN Summary
            for item in sale.get("items", []):
                hsn = item.get("hsn_code", "0000")
                hsn_data[hsn]["qty"] += item.get("quantity", 1)
                hsn_data[hsn]["val"] += Decimal(str(item.get("total", 0)))
                hsn_data[hsn]["txval"] += Decimal(str(item.get("taxable_amount", 0)))
                
                if is_interstate:
                    hsn_data[hsn]["iamt"] += Decimal(str(item.get("igst_amount", 0)))
                else:
                    hsn_data[hsn]["camt"] += Decimal(str(item.get("cgst_amount", 0)))
                    hsn_data[hsn]["samt"] += Decimal(str(item.get("sgst_amount", 0)))
                hsn_data[hsn]["uqc"] = item.get("unit", "NOS")

        # Format HSN out array
        hsn_out = {
            "data": [
                {
                    "num": i + 1,
                    "hsn_sc": k,
                    "desc": "Goods",
                    "uqc": v["uqc"],
                    "qty": float(v["qty"]),
                    "val": float(v["val"]),
                    "txval": float(v["txval"]),
                    "iamt": float(v["iamt"]),
                    "camt": float(v["camt"]),
                    "samt": float(v["samt"]),
                }
                for i, (k, v) in enumerate(hsn_data.items())
            ]
        }

        # Final Payload Structure
        return {
            "gstin": gstin,
            "fp": period,
            "gt": float(gross_turnover),
            "b2b": GSTR1Generator._group_b2b(b2b),
            "b2cl": b2cl,
            "b2cs": b2cs,
            "hsn": hsn_out,
            "doc_issue": {"doc_det": []} # Placeholder for document sequences
        }

    @staticmethod
    def _format_b2b_inv(buyer_gstin: str, sale: Dict) -> Dict:
        """Format a single B2B invoice object."""
        return {
            "ctin": buyer_gstin,
            "inv": [{
                "inum": sale["invoice_number"],
                "idt": sale["invoice_date"].replace("-", ""),  # YYYY-MM-DD -> YYYYMMDD typically not used, DD-MM-YYYY is std
                "val": float(sale.get("grand_total", 0)),
                "pos": buyer_gstin[:2],
                "rchrg": "N",
                "inv_typ": "R",  # Regular
                "itms": [
                    {
                        "num": 1,
                        "itm_det": {
                            "rt": float(sale.get("gst_rate", 0)),
                            "txval": float(sale.get("taxable_amount", 0)),
                            "iamt": float(sale.get("igst_amount", 0)),
                            "camt": float(sale.get("cgst_amount", 0)),
                            "samt": float(sale.get("sgst_amount", 0)),
                        }
                    }
                ]
            }]
        }

    @staticmethod
    def _group_b2b(b2b_list: List[Dict]) -> List[Dict]:
        """Group B2B invoices array by counter-party GSTIN."""
        grouped = {}
        for entry in b2b_list:
            ctin = entry["ctin"]
            if ctin not in grouped:
                grouped[ctin] = {"ctin": ctin, "inv": []}
            grouped[ctin]["inv"].extend(entry["inv"])
        return list(grouped.values())

    @staticmethod
    def _format_b2cl_inv(sale: Dict) -> Dict:
        """Format a single B2C Large invoice object."""
        return {
            "pos": sale.get("place_of_supply", "99"),
            "inv": [
                {
                    "inum": sale["invoice_number"],
                    "idt": sale.get("invoice_date", ""),
                    "val": float(sale.get("grand_total", 0)),
                    "itms": [
                        {
                            "num": 1,
                            "itm_det": {
                                "rt": float(sale.get("gst_rate", 0)),
                                "txval": float(sale.get("taxable_amount", 0)),
                                "iamt": float(sale.get("igst_amount", 0))
                            }
                        }
                    ]
                }
            ]
        }
