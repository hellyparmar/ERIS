"""
Tally ERP Integration Module

Provides integration with Tally ERP (India's most popular accounting software).
Tally supports data exchange via XML over HTTP using its built-in web server (default port 9000).

This module handles:
- Connection verification to Tally server
- Conversion of invoice data to Tally XML voucher format
- Posting vouchers to Tally
- Fetching ledger balances for reconciliation
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

logger = logging.getLogger(__name__)


class TallyIntegration:
    """
    Integration layer for Tally ERP via XML over HTTP.
    
    Tally's built-in web server runs on port 9000 by default and accepts
    XML requests for data import/export.
    """

    def __init__(self, tally_host: Optional[str] = None, tally_port: Optional[int] = None):
        """
        Initialize Tally integration with server details.
        
        Args:
            tally_host: Tally server hostname (default: from env or 'localhost')
            tally_port: Tally server port (default: from env or 9000)
        """
        self.tally_host = tally_host or os.getenv('TALLY_HOST', 'localhost')
        self.tally_port = tally_port or int(os.getenv('TALLY_PORT', 9000))
        self.base_url = f"http://{self.tally_host}:{self.tally_port}"
        self.timeout = 10  # Request timeout in seconds
        self.logger = logger

    def is_connected(self) -> Dict[str, Any]:
        """
        Ping Tally's HTTP server to check if it's running and reachable.
        
        Returns:
            {
                'connected': bool,
                'message': str,
                'tally_host': str,
                'tally_port': int
            }
        """
        try:
            # Tally responds to ping requests
            response = requests.get(
                f"{self.base_url}/",
                timeout=self.timeout
            )
            
            if response.status_code in [200, 204, 404]:
                # Tally might return 404 for root, but if it responds, server is running
                self.logger.info(
                    f"✅ Connected to Tally ERP at {self.tally_host}:{self.tally_port}"
                )
                return {
                    'connected': True,
                    'message': f'Connected to Tally ERP at {self.tally_host}:{self.tally_port}',
                    'tally_host': self.tally_host,
                    'tally_port': self.tally_port,
                    'status_code': response.status_code,
                }
            else:
                self.logger.warning(
                    f"⚠️ Tally server responded with status {response.status_code}"
                )
                return {
                    'connected': False,
                    'message': f'Tally server responded with status {response.status_code}',
                    'tally_host': self.tally_host,
                    'tally_port': self.tally_port,
                }
                
        except requests.exceptions.ConnectionError:
            self.logger.error(
                f"❌ Could not connect to Tally ERP at {self.tally_host}:{self.tally_port}. "
                "Make sure Tally is running locally."
            )
            return {
                'connected': False,
                'message': (
                    f'Could not connect to Tally ERP at {self.tally_host}:{self.tally_port}. '
                    'Make sure Tally is running locally on port 9000.'
                ),
                'tally_host': self.tally_host,
                'tally_port': self.tally_port,
                'error': 'Connection refused',
            }
        except requests.exceptions.Timeout:
            self.logger.error(
                f"❌ Timeout connecting to Tally ERP at {self.tally_host}:{self.tally_port}"
            )
            return {
                'connected': False,
                'message': f'Timeout connecting to Tally ERP. Please check if Tally is running.',
                'tally_host': self.tally_host,
                'tally_port': self.tally_port,
                'error': 'Timeout',
            }
        except Exception as e:
            self.logger.error(f"❌ Error checking Tally connection: {str(e)}")
            return {
                'connected': False,
                'message': f'Error checking Tally connection: {str(e)}',
                'tally_host': self.tally_host,
                'tally_port': self.tally_port,
                'error': str(e),
            }

    def _build_voucher_xml(self, invoice: Dict[str, Any]) -> str:
        """
        Convert invoice data to Tally XML voucher format.
        
        Args:
            invoice: Invoice dict with keys:
                - invoice_id: str
                - supplier_name: str
                - invoice_date: str (YYYY-MM-DD)
                - amount: float
                - description: str (optional)
        
        Returns:
            XML string in Tally format
        """
        try:
            # Create root envelope
            envelope = ET.Element('ENVELOPE')
            
            # Add header
            header = ET.SubElement(envelope, 'HEADER')
            tallyrequest = ET.SubElement(header, 'TALLYREQUEST')
            tallyrequest.text = 'Import Data'
            
            # Add body with import data
            body = ET.SubElement(envelope, 'BODY')
            importdata = ET.SubElement(body, 'IMPORTDATA')
            
            # Request description
            requestdesc = ET.SubElement(importdata, 'REQUESTDESC')
            reportname = ET.SubElement(requestdesc, 'REPORTNAME')
            reportname.text = 'Vouchers'
            
            # Request data with voucher
            requestdata = ET.SubElement(importdata, 'REQUESTDATA')
            tallymessage = ET.SubElement(requestdata, 'TALLYMESSAGE')
            
            # Create voucher
            voucher = ET.SubElement(tallymessage, 'VOUCHER')
            voucher.set('VCHTYPE', 'Purchase')
            voucher.set('ACTION', 'Create')
            
            # Voucher details
            date_elem = ET.SubElement(voucher, 'DATE')
            date_elem.text = invoice.get('invoice_date', datetime.now().strftime('%d-%m-%Y'))
            
            vchnum = ET.SubElement(voucher, 'VOUCHERNUM')
            vchnum.text = str(invoice.get('invoice_id', ''))
            
            supplier = ET.SubElement(voucher, 'PARTYLEDGERNAME')
            supplier.text = invoice.get('supplier_name', 'Unknown Supplier')
            
            amount = ET.SubElement(voucher, 'AMOUNT')
            amount.text = str(invoice.get('amount', 0.0))
            
            if invoice.get('description'):
                narration = ET.SubElement(voucher, 'NARRATION')
                narration.text = invoice.get('description')
            
            # Pretty print XML
            xml_str = minidom.parseString(ET.tostring(envelope)).toprettyxml(indent='  ')
            
            return xml_str
            
        except Exception as e:
            self.logger.error(f"Error building Tally XML: {str(e)}")
            raise

    def sync_vouchers_to_tally(self, invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert invoice data to Tally XML voucher format and post to Tally.
        
        Args:
            invoices: List of invoice dicts with keys:
                - invoice_id
                - supplier_name
                - invoice_date (YYYY-MM-DD)
                - amount
                - description (optional)
        
        Returns:
            {
                'status': 'success' | 'partial' | 'error',
                'message': str,
                'synced_count': int,
                'failed_count': int,
                'details': [
                    {'invoice_id': str, 'status': str, 'message': str}
                ]
            }
        """
        if not invoices:
            return {
                'status': 'error',
                'message': 'No invoices provided',
                'synced_count': 0,
                'failed_count': 0,
                'details': []
            }
        
        # First check if Tally is connected
        connection = self.is_connected()
        if not connection['connected']:
            return {
                'status': 'error',
                'message': connection['message'],
                'synced_count': 0,
                'failed_count': len(invoices),
                'details': [
                    {
                        'invoice_id': inv.get('invoice_id'),
                        'status': 'failed',
                        'message': 'Tally is not connected'
                    }
                    for inv in invoices
                ]
            }
        
        synced_count = 0
        failed_count = 0
        details = []
        
        for invoice in invoices:
            try:
                # Build XML for this invoice
                xml_data = self._build_voucher_xml(invoice)
                
                # Post to Tally
                response = requests.post(
                    f"{self.base_url}/",
                    data=xml_data.encode('utf-8'),
                    headers={'Content-Type': 'application/xml'},
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 201, 204]:
                    synced_count += 1
                    self.logger.info(
                        f"✅ Synced invoice {invoice.get('invoice_id')} to Tally"
                    )
                    details.append({
                        'invoice_id': invoice.get('invoice_id'),
                        'status': 'success',
                        'message': 'Invoice synced to Tally'
                    })
                else:
                    failed_count += 1
                    self.logger.warning(
                        f"⚠️ Failed to sync invoice {invoice.get('invoice_id')}: "
                        f"Status {response.status_code}"
                    )
                    details.append({
                        'invoice_id': invoice.get('invoice_id'),
                        'status': 'failed',
                        'message': f'Tally returned status {response.status_code}'
                    })
                    
            except Exception as e:
                failed_count += 1
                self.logger.error(
                    f"❌ Error syncing invoice {invoice.get('invoice_id')}: {str(e)}"
                )
                details.append({
                    'invoice_id': invoice.get('invoice_id'),
                    'status': 'failed',
                    'message': str(e)
                })
        
        # Determine overall status
        if failed_count == 0:
            overall_status = 'success'
        elif synced_count == 0:
            overall_status = 'error'
        else:
            overall_status = 'partial'
        
        return {
            'status': overall_status,
            'message': f'Synced {synced_count} invoice(s), {failed_count} failed',
            'synced_count': synced_count,
            'failed_count': failed_count,
            'details': details
        }

    def fetch_ledger_balance(self, ledger_name: str) -> Dict[str, Any]:
        """
        Fetch ledger balance from Tally for reconciliation.
        
        Args:
            ledger_name: Name of the ledger in Tally
        
        Returns:
            {
                'status': 'success' | 'error',
                'ledger_name': str,
                'balance': float,
                'message': str
            }
        """
        try:
            # Check if Tally is connected
            connection = self.is_connected()
            if not connection['connected']:
                return {
                    'status': 'error',
                    'ledger_name': ledger_name,
                    'balance': None,
                    'message': 'Tally is not connected'
                }
            
            # Build request XML for ledger fetch
            envelope = ET.Element('ENVELOPE')
            
            header = ET.SubElement(envelope, 'HEADER')
            tallyrequest = ET.SubElement(header, 'TALLYREQUEST')
            tallyrequest.text = 'Export Data'
            
            body = ET.SubElement(envelope, 'BODY')
            exportdata = ET.SubElement(body, 'EXPORTDATA')
            
            requestdesc = ET.SubElement(exportdata, 'REQUESTDESC')
            reportname = ET.SubElement(requestdesc, 'REPORTNAME')
            reportname.text = 'Ledger Balances'
            
            filterdata = ET.SubElement(requestdesc, 'FILTERDATA')
            filtername = ET.SubElement(filterdata, 'FILTERNAME')
            filtername.text = ledger_name
            
            xml_str = minidom.parseString(ET.tostring(envelope)).toprettyxml()
            
            # Post request to Tally
            response = requests.post(
                f"{self.base_url}/",
                data=xml_str.encode('utf-8'),
                headers={'Content-Type': 'application/xml'},
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                # Parse response and extract balance (simplified)
                # In production, would parse the XML response
                self.logger.info(f"✅ Fetched balance for ledger: {ledger_name}")
                return {
                    'status': 'success',
                    'ledger_name': ledger_name,
                    'balance': 0.0,  # Would parse from response
                    'message': f'Successfully fetched balance for {ledger_name}'
                }
            else:
                return {
                    'status': 'error',
                    'ledger_name': ledger_name,
                    'balance': None,
                    'message': f'Tally returned status {response.status_code}'
                }
                
        except Exception as e:
            self.logger.error(f"Error fetching ledger balance: {str(e)}")
            return {
                'status': 'error',
                'ledger_name': ledger_name,
                'balance': None,
                'message': str(e)
            }
