
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

class TallyConnector:
    """
    Bridge between R-DIOS and Tally Prime via XML Interface.
    Target: Tally running on localhost:9000
    """
    
    TALLY_URL = "http://localhost:9000"
    
    @staticmethod
    def _create_voucher_xml(invoice_data):
        """
        Constructs the Tally XML for a Sales Voucher.
        """
        # Formating date for Tally (YYYYMMDD)
        tally_date = invoice_data['date'].strftime('%Y%m%d')
        
        # Root Envelope
        envelope = ET.Element('ENVELOPE')
        
        # Header
        header = ET.SubElement(envelope, 'HEADER')
        ET.SubElement(header, 'TALLYREQUEST').text = 'Import Data'
        
        # Body
        body = ET.SubElement(envelope, 'BODY')
        import_data = ET.SubElement(body, 'IMPORTDATA')
        
        # Request Desc
        req_desc = ET.SubElement(import_data, 'REQUESTDESC')
        ET.SubElement(req_desc, 'REPORTNAME').text = 'Vouchers'
        
        # Request Data
        req_data = ET.SubElement(import_data, 'REQUESTDATA')
        tally_msg = ET.SubElement(req_data, 'TALLYMESSAGE', {'xmlns:UDF': 'TallyUDF'})
        
        # Voucher
        voucher = ET.SubElement(tally_msg, 'VOUCHER', {
            'VCHTYPE': 'Sales',
            'ACTION': 'Create',
            'OBJVIEW': 'Invoice Voucher View'
        })
        
        # Basic Voucher Fields
        ET.SubElement(voucher, 'DATE').text = tally_date
        ET.SubElement(voucher, 'VOUCHERTYPENAME').text = 'Sales'
        ET.SubElement(voucher, 'VOUCHERNUMBER').text = invoice_data['invoice_number']
        ET.SubElement(voucher, 'PARTYLEDGERNAME').text = invoice_data['customer_ledger_name']
        ET.SubElement(voucher, 'PERSISTEDVIEW').text = 'Invoice Voucher View'
        ET.SubElement(voucher, 'NARRATION').text = f"Synced from R-DIOS: {invoice_data['invoice_number']}"
        
        # Effect Date
        ET.SubElement(voucher, 'EFFECTIVEDATE').text = tally_date
        
        # Ledger Entries (Party - Debtor)
        ledger_entry = ET.SubElement(voucher, 'LEDGERENTRIES.LIST')
        ET.SubElement(ledger_entry, 'LEDGERNAME').text = invoice_data['customer_ledger_name']
        ET.SubElement(ledger_entry, 'ISDEEMEDPOSITIVE').text = 'Yes' # Debit the party
        ET.SubElement(ledger_entry, 'AMOUNT').text = f"-{invoice_data['total_amount']}" # Negative logic for Debit in some Tally versions or strictly sign based
        
        # Inventory Entries
        for item in invoice_data['items']:
            inv_entry = ET.SubElement(voucher, 'ALLINVENTORYENTRIES.LIST')
            ET.SubElement(inv_entry, 'STOCKITEMNAME').text = item['product_name']
            ET.SubElement(inv_entry, 'ISDEEMEDPOSITIVE').text = 'No' # Credit sales
            ET.SubElement(inv_entry, 'RATE').text = f"{item['unit_price']}/No"
            ET.SubElement(inv_entry, 'AMOUNT').text = str(item['total']) # Positive for Credit
            
            # Sales Ledger for Item
            acct_list = ET.SubElement(inv_entry, 'ACCOUNTINGALLOCATIONS.LIST')
            ET.SubElement(acct_list, 'LEDGERNAME').text = "Sales" # Common Sales Ledger
            ET.SubElement(acct_list, 'ISDEEMEDPOSITIVE').text = 'No'
            ET.SubElement(acct_list, 'AMOUNT').text = str(item['total'])

        return ET.tostring(envelope, encoding='unicode')

    @staticmethod
    def push_voucher(invoice_data):
        """
        Sends the XML to Tally.
        Returns: (success: bool, response_message: str)
        """
        xml_payload = TallyConnector._create_voucher_xml(invoice_data)
        
        try:
            response = requests.post(
                TallyConnector.TALLY_URL, 
                data=xml_payload, 
                headers={'Content-Type': 'application/xml'},
                timeout=5
            )
            
            if response.status_code == 200:
                # Tally returns 200 even on some logic errors, need to check response body
                resp_text = response.text
                if "<CREATED>1</CREATED>" in resp_text:
                    return True, "Successfully created in Tally"
                elif "<ERRORS>" in resp_text:
                    return False, f"Tally Logic Error: {resp_text}"
                else:
                    return True, "Request Accepted (Check Tally Import Log)"
            else:
                return False, f"HTTP Error: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Tally is not running or port 9000 is blocked."
        except Exception as e:
            return False, str(e)
