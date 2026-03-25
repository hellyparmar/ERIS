"""
Tally Integration Endpoints
Generates Tally-compatible XML exports for daily sales transactions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date
from typing import Optional
from fastapi.responses import Response

from app.api.db import get_db

router = APIRouter(prefix="/api/v1/integrations/tally", tags=["Tally Integration"])

@router.get("/export")
async def export_tally_xml(
    target_date: Optional[date] = None,
    store_id: int = Query(1, description="Store ID for the export"),
    db: Session = Depends(get_db)
):
    """
    Export day's invoices into Tally-compatible XML format.
    Requires sales, products, and customer data.
    """
    if not target_date:
        target_date = datetime.now().date()
        
    start_time = f"{target_date} 00:00:00"
    end_time = f"{target_date} 23:59:59"

    # Fetch daily sales
    try:
        sales = db.execute(text("""
            SELECT s.id, s.transaction_id, s.transaction_date, s.total_amount, 
                   s.tax, s.payment_method, c.name as customer_name
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE s.store_id = :store_id 
              AND s.transaction_date >= :start_time 
              AND s.transaction_date <= :end_time
              AND s.payment_status = 'PAID'
        """), {"store_id": str(store_id), "start_time": start_time, "end_time": end_time}).fetchall()

        if not sales:
            # Return an empty Tally XML envelope if no sales
            empty_xml = f'''<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDATA>
                <!-- No transactions found for {target_date} -->
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>'''
            return Response(content=empty_xml, media_type="application/xml")

        # Build Tally XML Envelope
        xml_parts = []
        xml_parts.append("<ENVELOPE>")
        xml_parts.append("    <HEADER>")
        xml_parts.append("        <TALLYREQUEST>Import Data</TALLYREQUEST>")
        xml_parts.append("    </HEADER>")
        xml_parts.append("    <BODY>")
        xml_parts.append("        <IMPORTDATA>")
        xml_parts.append("            <REQUESTDESC>")
        xml_parts.append("                <REPORTNAME>Vouchers</REPORTNAME>")
        xml_parts.append("            </REQUESTDESC>")
        xml_parts.append("            <REQUESTDATA>")

        for sale in sales:
            txn_date_formatted = sale[2].strftime("%Y%m%d") if isinstance(sale[2], datetime) else sale[2]
            txn_id = sale[1]
            total_amount = float(sale[3])
            tax = float(sale[4])
            party_name = sale[6] or "Cash Customer"

            xml_parts.append("                <TALLYMESSAGE xmlns:UDF=\"TallyUDF\">")
            xml_parts.append(f"                    <VOUCHER VCHTYPE=\"Sales\" ACTION=\"Create\">")
            xml_parts.append(f"                        <DATE>{txn_date_formatted}</DATE>")
            xml_parts.append(f"                        <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>")
            xml_parts.append(f"                        <VOUCHERNUMBER>{txn_id}</VOUCHERNUMBER>")
            xml_parts.append(f"                        <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>")
            xml_parts.append(f"                        <NARRATION>R-DIOS POS Sale #{txn_id}</NARRATION>")
            
            # Sales Ledger Entry (Credit) - Negative amount in Tally XML for Credit
            taxable_amount = total_amount - tax
            xml_parts.append("                        <ALLLEDGERENTRIES.LIST>")
            xml_parts.append("                            <LEDGERNAME>Sales A/c</LEDGERNAME>")
            xml_parts.append("                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>")
            xml_parts.append(f"                            <AMOUNT>{-taxable_amount:.2f}</AMOUNT>")
            xml_parts.append("                        </ALLLEDGERENTRIES.LIST>")
            
            # GST Ledger Entries (Credit) - Split into CGST and SGST
            if tax > 0:
                half_tax = tax / 2.0
                xml_parts.append("                        <ALLLEDGERENTRIES.LIST>")
                xml_parts.append("                            <LEDGERNAME>Output CGST</LEDGERNAME>")
                xml_parts.append("                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>")
                xml_parts.append(f"                            <AMOUNT>{-half_tax:.2f}</AMOUNT>")
                xml_parts.append("                        </ALLLEDGERENTRIES.LIST>")
                
                xml_parts.append("                        <ALLLEDGERENTRIES.LIST>")
                xml_parts.append("                            <LEDGERNAME>Output SGST</LEDGERNAME>")
                xml_parts.append("                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>")
                xml_parts.append(f"                            <AMOUNT>{-half_tax:.2f}</AMOUNT>")
                xml_parts.append("                        </ALLLEDGERENTRIES.LIST>")
                
            # Cash/Bank Ledger Entry (Debit) - Positive amount for Debit
            ledger_name = "Cash" if sale[5].lower() == "cash" else "Bank A/c"
            xml_parts.append("                        <ALLLEDGERENTRIES.LIST>")
            xml_parts.append(f"                            <LEDGERNAME>{ledger_name}</LEDGERNAME>")
            xml_parts.append("                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>")
            xml_parts.append(f"                            <AMOUNT>{total_amount:.2f}</AMOUNT>")
            xml_parts.append("                        </ALLLEDGERENTRIES.LIST>")

            xml_parts.append("                    </VOUCHER>")
            xml_parts.append("                </TALLYMESSAGE>")

        xml_parts.append("            </REQUESTDATA>")
        xml_parts.append("        </IMPORTDATA>")
        xml_parts.append("    </BODY>")
        xml_parts.append("</ENVELOPE>")

        xml_str = "\\n".join(xml_parts)
        return Response(content=xml_str, media_type="application/xml")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
