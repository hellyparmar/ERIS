import csv
import os
import logging
from datetime import date
from typing import List, Dict, Any
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class TallyExportService:
    def __init__(self, export_dir: str = "/tmp/tally_exports"):
        self.export_dir = export_dir
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def export_sales_to_csv(self, sales_data: List[Dict[str, Any]], filename: str = "sales_export.csv") -> str:
        """Export sales to CSV file and return the path"""
        file_path = os.path.join(self.export_dir, filename)
        
        if not sales_data:
            logger.warning("No sales data provided for export")
            return ""

        keys = sales_data[0].keys()
        try:
            with open(file_path, 'w', newline='') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(sales_data)
            return file_path
        except Exception as e:
            logger.error(f"Failed to export Tally CSV: {str(e)}")
            return ""

    def export_sales_to_xml(self, sales_data: List[Dict[str, Any]]) -> str:
        """Export sales to Tally XML format (returns XML string)"""
        # Simple Tally-like XML structure
        envelope = ET.Element("ENVELOPE")
        header = ET.SubElement(envelope, "HEADER")
        ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
        
        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        
        for sale in sales_data:
            tally_message = ET.SubElement(request_data, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})
            voucher = ET.SubElement(tally_message, "VOUCHER", {"VCHTYPE": "Sales", "ACTION": "Create"})
            ET.SubElement(voucher, "DATE").text = str(sale.get('date', date.today())).replace("-", "")
            ET.SubElement(voucher, "VOUCHERNUMBER").text = str(sale.get('id', ''))
            ET.SubElement(voucher, "PARTYLEDGERNAME").text = str(sale.get('customer', 'Cash'))
            ET.SubElement(voucher, "AMOUNT").text = str(sale.get('total_amount', 0))
            
            # Simplified item entry
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(ledger_entry, "LEDGERNAME").text = "Sales Account"
            ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE").text = "No"
            ET.SubElement(ledger_entry, "AMOUNT").text = str(sale.get('total_amount', 0))

        return ET.tostring(envelope, encoding='unicode', method='xml')

# Singleton Instance
tally_export_service = TallyExportService()
