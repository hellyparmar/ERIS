"""
Tally ERP XML-RPC Connector
Connects to Tally Prime / Tally ERP 9 via XML-RPC

Tally uses a proprietary XML format for data exchange.
This connector handles the XML generation and parsing.

Supported Operations:
- Stock Items Import
- Ledgers Import
- Voucher Export (Sales, Purchase, Payment, Receipt)
- Company Info Retrieval
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class TallyXMLConnector:
    """
    Tally XML-RPC Connector
    
    Communicates with Tally using XML over HTTP
    """
    
    def __init__(self, host: str = "localhost", port: int = 9000):
        """
        Initialize Tally connector
        
        Args:
            host: Tally server hostname/IP
            port: Tally ODBC port (default: 9000)
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.company_name = None
    
    def test_connection(self) -> bool:
        """Test connection to Tally"""
        try:
            # Simple request to check if Tally is running
            xml_request = self._build_request_xml("EXPORT", {
                "STATICVARIABLES": {
                    "SVEXPORTFORMAT": "$$SysName:XML"
                }
            })
            
            response = self._send_request(xml_request)
            return response is not None
            
        except Exception as e:
            logger.error(f"Tally connection test failed: {e}")
            return False
    
    def get_company_info(self) -> Optional[Dict]:
        """Get Tally company information"""
        try:
            xml_request = """
            <ENVELOPE>
                <HEADER>
                    <VERSION>1</VERSION>
                    <TALLYREQUEST>Export</TALLYREQUEST>
                    <TYPE>Data</TYPE>
                    <ID>CompanyInfo</ID>
                </HEADER>
                <BODY>
                    <DESC>
                        <STATICVARIABLES>
                            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                        </STATICVARIABLES>
                    </DESC>
                </BODY>
            </ENVELOPE>
            """
            
            response = self._send_request(xml_request)
            
            if response:
                # Parse company info from response
                root = ET.fromstring(response)
                company = root.find('.//COMPANY')
                
                if company:
                    return {
                        'name': company.findtext('NAME', ''),
                        'guid': company.findtext('GUID', ''),
                        'address': company.findtext('ADDRESS', ''),
                        'currency': company.findtext('CURRENCY', 'INR'),
                        'financial_year': company.findtext('FINANCIALYEAR', '')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get company info: {e}")
            return None
    
    def import_stock_items(self, filter_date: Optional[date] = None) -> List[Dict]:
        """
        Import stock items from Tally
        
        Args:
            filter_date: Optional date to filter items modified after
            
        Returns:
            List of stock items
        """
        try:
            # Build XML request for stock items
            xml_request = """
            <ENVELOPE>
                <HEADER>
                    <VERSION>1</VERSION>
                    <TALLYREQUEST>Export</TALLYREQUEST>
                    <TYPE>Data</TYPE>
                    <ID>StockItems</ID>
                </HEADER>
                <BODY>
                    <DESC>
                        <STATICVARIABLES>
                            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                        </STATICVARIABLES>
                        <TDL>
                            <TDLMESSAGE>
                                <COLLECTION NAME="StockItemsCollection">
                                    <TYPE>Stock Item</TYPE>
                                    <FETCH>NAME, GUID, PARENT, BASEUNITS, GSTAPPLICABLE, HSNCODE, GSTRATE</FETCH>
                                </COLLECTION>
                            </TDLMESSAGE>
                        </TDL>
                    </DESC>
                </BODY>
            </ENVELOPE>
            """
            
            response = self._send_request(xml_request)
            
            if not response:
                return []
            
            # Parse stock items
            stock_items = []
            root = ET.fromstring(response)
            
            for item in root.findall('.//STOCKITEM'):
                stock_item = {
                    'name': item.findtext('NAME', ''),
                    'guid': item.findtext('GUID', ''),
                    'category': item.findtext('PARENT', ''),
                    'unit': item.findtext('BASEUNITS', 'PCS'),
                    'hsn_code': item.findtext('HSNCODE', ''),
                    'gst_applicable': item.findtext('GSTAPPLICABLE', 'No') == 'Yes',
                    'gst_rate': float(item.findtext('GSTRATE', '0') or 0)
                }
                stock_items.append(stock_item)
            
            logger.info(f"Imported {len(stock_items)} stock items from Tally")
            return stock_items
            
        except Exception as e:
            logger.error(f"Failed to import stock items: {e}")
            return []
    
    def import_ledgers(self) -> List[Dict]:
        """
        Import ledgers (accounts) from Tally
        
        Returns:
            List of ledgers
        """
        try:
            xml_request = """
            <ENVELOPE>
                <HEADER>
                    <VERSION>1</VERSION>
                    <TALLYREQUEST>Export</TALLYREQUEST>
                    <TYPE>Data</TYPE>
                    <ID>Ledgers</ID>
                </HEADER>
                <BODY>
                    <DESC>
                        <STATICVARIABLES>
                            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                        </STATICVARIABLES>
                        <TDL>
                            <TDLMESSAGE>
                                <COLLECTION NAME="LedgersCollection">
                                    <TYPE>Ledger</TYPE>
                                    <FETCH>NAME, GUID, PARENT, GSTREGISTRATIONTYPE, PARTYGSTIN, OPENINGBALANCE</FETCH>
                                </COLLECTION>
                            </TDLMESSAGE>
                        </TDL>
                    </DESC>
                </BODY>
            </ENVELOPE>
            """
            
            response = self._send_request(xml_request)
            
            if not response:
                return []
            
            # Parse ledgers
            ledgers = []
            root = ET.fromstring(response)
            
            for ledger in root.findall('.//LEDGER'):
                ledger_data = {
                    'name': ledger.findtext('NAME', ''),
                    'guid': ledger.findtext('GUID', ''),
                    'group': ledger.findtext('PARENT', ''),
                    'gstin': ledger.findtext('PARTYGSTIN', ''),
                    'gst_registration_type': ledger.findtext('GSTREGISTRATIONTYPE', ''),
                    'opening_balance': float(ledger.findtext('OPENINGBALANCE', '0') or 0)
                }
                ledgers.append(ledger_data)
            
            logger.info(f"Imported {len(ledgers)} ledgers from Tally")
            return ledgers
            
        except Exception as e:
            logger.error(f"Failed to import ledgers: {e}")
            return []
    
    def export_sales_voucher(self, voucher_data: Dict) -> bool:
        """
        Export sales voucher to Tally
        
        Args:
            voucher_data: Sales voucher data with items and amounts
            
        Returns:
            True if successful
        """
        try:
            # Build sales voucher XML
            xml_voucher = self._build_sales_voucher_xml(voucher_data)
            
            # Send to Tally
            response = self._send_request(xml_voucher)
            
            if response:
                # Check if voucher was created successfully
                root = ET.fromstring(response)
                
                # Tally returns success/error in response
                created = root.findtext('.//CREATED') == 'Yes'
                
                if created:
                    logger.info(f"Sales voucher {voucher_data['invoice_number']} exported to Tally")
                    return True
                else:
                    error = root.findtext('.//ERROR', 'Unknown error')
                    logger.error(f"Tally voucher export failed: {error}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to export sales voucher: {e}")
            return False
    
    def _build_sales_voucher_xml(self, voucher_data: Dict) -> str:
        """Build XML for sales voucher"""
        # Create envelope
        envelope = ET.Element('ENVELOPE')
        
        # Header
        header = ET.SubElement(envelope, 'HEADER')
        ET.SubElement(header, 'VERSION').text = '1'
        ET.SubElement(header, 'TALLYREQUEST').text = 'Import'
        ET.SubElement(header, 'TYPE').text = 'Data'
        ET.SubElement(header, 'ID').text = 'Vouchers'
        
        # Body
        body = ET.SubElement(envelope, 'BODY')
        desc = ET.SubElement(body, 'DESC')
        
        # Static variables
        static_vars = ET.SubElement(desc, 'STATICVARIABLES')
        ET.SubElement(static_vars, 'SVCURRENTCOMPANY').text = self.company_name or 'Default'
        
        # Voucher
        voucher = ET.SubElement(desc, 'VOUCHER')
        ET.SubElement(voucher, 'DATE').text = voucher_data['date'].strftime('%Y%m%d')
        ET.SubElement(voucher, 'VOUCHERTYPENAME').text = 'Sales'
        ET.SubElement(voucher, 'VOUCHERNUMBER').text = voucher_data['invoice_number']
        ET.SubElement(voucher, 'PARTYLEDGERNAME').text = voucher_data['customer_name']
        
        # Line items
        all_ledger_entries = ET.SubElement(voucher, 'ALLLEDGERENTRIES.LIST')
        
        # Customer ledger (debit)
        ledger_entry = ET.SubElement(all_ledger_entries, 'LEDGERENTRIES')
        ET.SubElement(ledger_entry, 'LEDGERNAME').text = voucher_data['customer_name']
        ET.SubElement(ledger_entry, 'ISDEEMEDPOSITIVE').text = 'Yes'
        ET.SubElement(ledger_entry, 'AMOUNT').text = str(voucher_data['grand_total'])
        
        # Sales ledger (credit)
        sales_entry = ET.SubElement(all_ledger_entries, 'LEDGERENTRIES')
        ET.SubElement(sales_entry, 'LEDGERNAME').text = 'Sales'
        ET.SubElement(sales_entry, 'ISDEEMEDPOSITIVE').text = 'No'
        ET.SubElement(sales_entry, 'AMOUNT').text = f"-{voucher_data['taxable_amount']}"
        
        # Tax ledgers
        if voucher_data.get('cgst_amount', 0) > 0:
            cgst_entry = ET.SubElement(all_ledger_entries, 'LEDGERENTRIES')
            ET.SubElement(cgst_entry, 'LEDGERNAME').text = 'CGST'
            ET.SubElement(cgst_entry, 'ISDEEMEDPOSITIVE').text = 'No'
            ET.SubElement(cgst_entry, 'AMOUNT').text = f"-{voucher_data['cgst_amount']}"
        
        if voucher_data.get('sgst_amount', 0) > 0:
            sgst_entry = ET.SubElement(all_ledger_entries, 'LEDGERENTRIES')
            ET.SubElement(sgst_entry, 'LEDGERNAME').text = 'SGST'
            ET.SubElement(sgst_entry, 'ISDEEMEDPOSITIVE').text = 'No'
            ET.SubElement(sgst_entry, 'AMOUNT').text = f"-{voucher_data['sgst_amount']}"
        
        if voucher_data.get('igst_amount', 0) > 0:
            igst_entry = ET.SubElement(all_ledger_entries, 'LEDGERENTRIES')
            ET.SubElement(igst_entry, 'LEDGERNAME').text = 'IGST'
            ET.SubElement(igst_entry, 'ISDEEMEDPOSITIVE').text = 'No'
            ET.SubElement(igst_entry, 'AMOUNT').text = f"-{voucher_data['igst_amount']}"
        
        # Convert to string
        xml_string = ET.tostring(envelope, encoding='unicode')
        return xml_string
    
    def _send_request(self, xml_request: str) -> Optional[str]:
        """
        Send XML request to Tally
        
        Args:
            xml_request: XML string
            
        Returns:
            Response XML string or None
        """
        try:
            response = requests.post(
                self.base_url,
                data=xml_request.encode('utf-8'),
                headers={'Content-Type': 'text/xml; charset=utf-8'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Tally request failed with status {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Tally at {self.base_url}. Is Tally running?")
            return None
        except requests.exceptions.Timeout:
            logger.error("Tally request timed out")
            return None
        except Exception as e:
            logger.error(f"Tally request error: {e}")
            return None
    
    def _build_request_xml(self, request_type: str, params: Dict) -> str:
        """Build generic XML request"""
        envelope = ET.Element('ENVELOPE')
        
        header = ET.SubElement(envelope, 'HEADER')
        ET.SubElement(header, 'VERSION').text = '1'
        ET.SubElement(header, 'TALLYREQUEST').text = request_type
        ET.SubElement(header, 'TYPE').text = 'Data'
        
        body = ET.SubElement(envelope, 'BODY')
        desc = ET.SubElement(body, 'DESC')
        
        # Add parameters
        for key, value in params.items():
            if isinstance(value, dict):
                sub_elem = ET.SubElement(desc, key)
                for sub_key, sub_value in value.items():
                    ET.SubElement(sub_elem, sub_key).text = str(sub_value)
            else:
                ET.SubElement(desc, key).text = str(value)
        
        return ET.tostring(envelope, encoding='unicode')


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Initialize connector
    tally = TallyXMLConnector(host="localhost", port=9000)
    
    # Test connection
    if tally.test_connection():
        print("✓ Connected to Tally!")
        
        # Get company info
        company = tally.get_company_info()
        if company:
            print(f"  Company: {company['name']}")
            print(f"  Currency: {company['currency']}")
        
        # Import stock items
        stock_items = tally.import_stock_items()
        print(f"  Stock Items: {len(stock_items)}")
        
        # Import ledgers
        ledgers = tally.import_ledgers()
        print(f"  Ledgers: {len(ledgers)}")
        
        # Export sales voucher (example)
        voucher_data = {
            'date': datetime.now().date(),
            'invoice_number': 'INV-2024-001',
            'customer_name': 'Test Customer',
            'taxable_amount': 90000,
            'cgst_amount': 8100,
            'sgst_amount': 8100,
            'igst_amount': 0,
            'grand_total': 106200
        }
        
        success = tally.export_sales_voucher(voucher_data)
        if success:
            print("✓ Sales voucher exported to Tally!")
        
    else:
        print("✗ Cannot connect to Tally")
        print("  Make sure:")
        print("  1. Tally is running")
        print("  2. ODBC Server is enabled (F12 → Advanced Config → ODBC → Yes)")
        print("  3. Port 9000 is accessible")
