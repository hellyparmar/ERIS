"""
ERP Integration Service
Integration with Tally, SAP, and other ERP systems for Indian retail
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import logging
import hashlib
import base64
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ERPConfig:
    """ERP connection configuration"""
    erp_type: str  # 'tally', 'sap', 'zoho', 'busy'
    host: str
    port: int
    company_name: str
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 30


@dataclass
class SyncResult:
    """Result of ERP sync operation"""
    success: bool
    records_synced: int
    records_failed: int
    sync_type: str
    timestamp: str
    errors: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ERPConnector(ABC):
    """Abstract base class for ERP connectors"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to ERP"""
        pass
    
    @abstractmethod
    def sync_products(self, products: List[Dict]) -> SyncResult:
        """Sync products to ERP"""
        pass
    
    @abstractmethod
    def sync_invoices(self, invoices: List[Dict]) -> SyncResult:
        """Sync invoices to ERP"""
        pass
    
    @abstractmethod
    def fetch_stock_levels(self) -> List[Dict]:
        """Fetch current stock levels from ERP"""
        pass
    
    @abstractmethod
    def fetch_ledgers(self) -> List[Dict]:
        """Fetch customer/vendor ledgers"""
        pass


class TallyConnector(ERPConnector):
    """
    Tally ERP Prime/ERP 9 Integration
    Uses Tally XML format for data exchange
    """
    
    def __init__(self, config: ERPConfig):
        self.config = config
        self.base_url = f"http://{config.host}:{config.port}"
        self.connected = False
        self.session = requests.Session()
    
    def _build_tally_xml(self, request_type: str, data: Dict = None) -> str:
        """Build Tally XML request"""
        envelope = ET.Element('ENVELOPE')
        
        header = ET.SubElement(envelope, 'HEADER')
        ET.SubElement(header, 'TALLYREQUEST').text = request_type
        
        body = ET.SubElement(envelope, 'BODY')
        
        if data:
            desc = ET.SubElement(body, 'DESC')
            for key, value in data.items():
                ET.SubElement(desc, key.upper()).text = str(value)
        
        return ET.tostring(envelope, encoding='unicode')
    
    def _send_request(self, xml_data: str) -> Optional[ET.Element]:
        """Send XML request to Tally"""
        try:
            response = self.session.post(
                self.base_url,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return ET.fromstring(response.text)
        except requests.exceptions.RequestException as e:
            logger.error(f"Tally request failed: {e}")
            return None
        except ET.ParseError as e:
            logger.error(f"Failed to parse Tally response: {e}")
            return None
    
    def connect(self) -> bool:
        """Test connection to Tally"""
        xml = self._build_tally_xml('Export', {
            'CompanyName': self.config.company_name
        })
        
        response = self._send_request(xml)
        if response is not None:
            self.connected = True
            logger.info(f"Connected to Tally at {self.base_url}")
            return True
        
        logger.error("Failed to connect to Tally")
        return False
    
    def sync_products(self, products: List[Dict]) -> SyncResult:
        """Sync products to Tally as Stock Items"""
        synced = 0
        failed = 0
        errors = []
        
        for product in products:
            try:
                xml = self._build_stock_item_xml(product)
                response = self._send_request(xml)
                
                if response is not None:
                    synced += 1
                else:
                    failed += 1
                    errors.append(f"Failed to sync product: {product.get('name')}")
            except Exception as e:
                failed += 1
                errors.append(str(e))
        
        return SyncResult(
            success=failed == 0,
            records_synced=synced,
            records_failed=failed,
            sync_type='products',
            timestamp=datetime.now().isoformat(),
            errors=errors
        )
    
    def _build_stock_item_xml(self, product: Dict) -> str:
        """Build Tally stock item XML"""
        envelope = ET.Element('ENVELOPE')
        header = ET.SubElement(envelope, 'HEADER')
        ET.SubElement(header, 'TALLYREQUEST').text = 'Import Data'
        
        body = ET.SubElement(envelope, 'BODY')
        importdata = ET.SubElement(body, 'IMPORTDATA')
        requestdesc = ET.SubElement(importdata, 'REQUESTDESC')
        ET.SubElement(requestdesc, 'REPORTNAME').text = 'All Masters'
        
        requestdata = ET.SubElement(importdata, 'REQUESTDATA')
        tallymessage = ET.SubElement(requestdata, 'TALLYMESSAGE', {'xmlns:UDF': 'TallyUDF'})
        
        stockitem = ET.SubElement(tallymessage, 'STOCKITEM', {'NAME': product['name']})
        ET.SubElement(stockitem, 'NAME.LIST', {'TYPE': 'String'}).text = product['name']
        ET.SubElement(stockitem, 'PARENT').text = product.get('category', 'Primary')
        ET.SubElement(stockitem, 'BASEUNITS').text = product.get('unit', 'Nos')
        ET.SubElement(stockitem, 'OPENINGBALANCE').text = str(product.get('stock', 0))
        ET.SubElement(stockitem, 'OPENINGVALUE').text = str(product.get('cost', 0))
        ET.SubElement(stockitem, 'GSTAPPLICABLE').text = 'Yes'
        ET.SubElement(stockitem, 'GSTRATE').text = str(product.get('gst_rate', 18))
        ET.SubElement(stockitem, 'HSNCODE').text = product.get('hsn_code', '')
        
        return ET.tostring(envelope, encoding='unicode')
    
    def sync_invoices(self, invoices: List[Dict]) -> SyncResult:
        """Sync invoices to Tally as Sales Vouchers"""
        synced = 0
        failed = 0
        errors = []
        
        for invoice in invoices:
            try:
                xml = self._build_sales_voucher_xml(invoice)
                response = self._send_request(xml)
                
                if response is not None:
                    synced += 1
                else:
                    failed += 1
                    errors.append(f"Failed to sync invoice: {invoice.get('invoice_number')}")
            except Exception as e:
                failed += 1
                errors.append(str(e))
        
        return SyncResult(
            success=failed == 0,
            records_synced=synced,
            records_failed=failed,
            sync_type='invoices',
            timestamp=datetime.now().isoformat(),
            errors=errors
        )
    
    def _build_sales_voucher_xml(self, invoice: Dict) -> str:
        """Build Tally sales voucher XML"""
        envelope = ET.Element('ENVELOPE')
        header = ET.SubElement(envelope, 'HEADER')
        ET.SubElement(header, 'TALLYREQUEST').text = 'Import Data'
        
        body = ET.SubElement(envelope, 'BODY')
        importdata = ET.SubElement(body, 'IMPORTDATA')
        requestdesc = ET.SubElement(importdata, 'REQUESTDESC')
        ET.SubElement(requestdesc, 'REPORTNAME').text = 'Vouchers'
        
        requestdata = ET.SubElement(importdata, 'REQUESTDATA')
        tallymessage = ET.SubElement(requestdata, 'TALLYMESSAGE', {'xmlns:UDF': 'TallyUDF'})
        
        voucher = ET.SubElement(tallymessage, 'VOUCHER', {
            'VCHTYPE': 'Sales',
            'ACTION': 'Create'
        })
        
        ET.SubElement(voucher, 'DATE').text = invoice.get('date', datetime.now().strftime('%Y%m%d'))
        ET.SubElement(voucher, 'VOUCHERNUMBER').text = invoice.get('invoice_number', '')
        ET.SubElement(voucher, 'PARTYNAME').text = invoice.get('customer_name', 'Cash')
        ET.SubElement(voucher, 'NARRATION').text = f"Invoice {invoice.get('invoice_number')}"
        
        # GST details
        ET.SubElement(voucher, 'GSTREGISTRATIONTYPE').text = 'Regular'
        ET.SubElement(voucher, 'GSTIN').text = invoice.get('gstin', '')
        ET.SubElement(voucher, 'PLACEOFSUPPLY').text = invoice.get('state', 'Maharashtra')
        
        # Line items
        for item in invoice.get('items', []):
            ledger = ET.SubElement(voucher, 'ALLINVENTORYENTRIES.LIST')
            ET.SubElement(ledger, 'STOCKITEMNAME').text = item.get('product_name', '')
            ET.SubElement(ledger, 'ACTUALQTY').text = str(item.get('quantity', 1))
            ET.SubElement(ledger, 'RATE').text = str(item.get('price', 0))
            ET.SubElement(ledger, 'AMOUNT').text = str(item.get('total', 0))
        
        return ET.tostring(envelope, encoding='unicode')
    
    def fetch_stock_levels(self) -> List[Dict]:
        """Fetch current stock from Tally"""
        xml = '''
        <ENVELOPE>
            <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
            <BODY>
                <EXPORTDATA>
                    <REQUESTDESC>
                        <STATICVARIABLES>
                            <SVCURRENTCOMPANY>{}</SVCURRENTCOMPANY>
                        </STATICVARIABLES>
                        <TDL>
                            <TDLMESSAGE>
                                <REPORT NAME="StockList">
                                    <FORMS>StockForm</FORMS>
                                </REPORT>
                                <FORM NAME="StockForm">
                                    <PARTS>StockPart</PARTS>
                                </FORM>
                                <PART NAME="StockPart">
                                    <LINES>StockLine</LINES>
                                    <REPEAT>StockLine:STOCKITEM</REPEAT>
                                </PART>
                                <LINE NAME="StockLine">
                                    <FIELDS>Name,ClosingBalance</FIELDS>
                                </LINE>
                            </TDLMESSAGE>
                        </TDL>
                    </REQUESTDESC>
                </EXPORTDATA>
            </BODY>
        </ENVELOPE>
        '''.format(self.config.company_name)
        
        response = self._send_request(xml)
        
        if response is None:
            return []
        
        # Parse stock items
        stocks = []
        for item in response.findall('.//STOCKITEM'):
            name = item.find('NAME')
            balance = item.find('CLOSINGBALANCE')
            
            if name is not None:
                stocks.append({
                    'name': name.text,
                    'quantity': float(balance.text) if balance is not None else 0
                })
        
        return stocks
    
    def fetch_ledgers(self) -> List[Dict]:
        """Fetch customer/supplier ledgers from Tally"""
        xml = '''
        <ENVELOPE>
            <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
            <BODY>
                <EXPORTDATA>
                    <REQUESTDESC>
                        <REPORTNAME>List of Ledgers</REPORTNAME>
                    </REQUESTDESC>
                </EXPORTDATA>
            </BODY>
        </ENVELOPE>
        '''
        
        response = self._send_request(xml)
        
        if response is None:
            return []
        
        ledgers = []
        for ledger in response.findall('.//LEDGER'):
            name = ledger.find('NAME')
            parent = ledger.find('PARENT')
            
            if name is not None:
                ledgers.append({
                    'name': name.text,
                    'type': parent.text if parent is not None else 'Unknown'
                })
        
        return ledgers


class ZohoConnector(ERPConnector):
    """
    Zoho Books / Zoho Inventory Integration
    Uses REST API
    """
    
    def __init__(self, config: ERPConfig):
        self.config = config
        self.base_url = "https://books.zoho.in/api/v3"
        self.org_id = config.company_name
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Zoho-oauthtoken {config.api_key}',
            'Content-Type': 'application/json'
        })
    
    def connect(self) -> bool:
        """Test Zoho connection"""
        try:
            response = self.session.get(
                f"{self.base_url}/organization",
                params={'organization_id': self.org_id},
                timeout=self.config.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def sync_products(self, products: List[Dict]) -> SyncResult:
        """Sync products to Zoho Inventory"""
        synced = 0
        failed = 0
        errors = []
        
        for product in products:
            try:
                zoho_item = {
                    'name': product['name'],
                    'sku': product.get('sku', ''),
                    'rate': product.get('price', 0),
                    'purchase_rate': product.get('cost', 0),
                    'initial_stock': product.get('stock', 0),
                    'hsn_or_sac': product.get('hsn_code', ''),
                    'tax_id': self._get_tax_id(product.get('gst_rate', 18))
                }
                
                response = self.session.post(
                    f"{self.base_url}/items",
                    params={'organization_id': self.org_id},
                    json={'item': zoho_item}
                )
                
                if response.status_code in [200, 201]:
                    synced += 1
                else:
                    failed += 1
                    errors.append(f"Zoho error: {response.text}")
                    
            except Exception as e:
                failed += 1
                errors.append(str(e))
        
        return SyncResult(
            success=failed == 0,
            records_synced=synced,
            records_failed=failed,
            sync_type='products',
            timestamp=datetime.now().isoformat(),
            errors=errors
        )
    
    def _get_tax_id(self, gst_rate: float) -> str:
        """Map GST rate to Zoho tax ID"""
        tax_map = {5: 'gst_5', 12: 'gst_12', 18: 'gst_18', 28: 'gst_28'}
        return tax_map.get(int(gst_rate), 'gst_18')
    
    def sync_invoices(self, invoices: List[Dict]) -> SyncResult:
        """Sync invoices to Zoho Books"""
        synced = 0
        failed = 0
        errors = []
        
        for invoice in invoices:
            try:
                zoho_invoice = {
                    'customer_name': invoice.get('customer_name'),
                    'invoice_number': invoice.get('invoice_number'),
                    'date': invoice.get('date'),
                    'line_items': [
                        {
                            'item_id': item.get('product_id'),
                            'name': item.get('product_name'),
                            'quantity': item.get('quantity'),
                            'rate': item.get('price')
                        }
                        for item in invoice.get('items', [])
                    ]
                }
                
                response = self.session.post(
                    f"{self.base_url}/invoices",
                    params={'organization_id': self.org_id},
                    json={'invoice': zoho_invoice}
                )
                
                if response.status_code in [200, 201]:
                    synced += 1
                else:
                    failed += 1
                    errors.append(response.text)
                    
            except Exception as e:
                failed += 1
                errors.append(str(e))
        
        return SyncResult(
            success=failed == 0,
            records_synced=synced,
            records_failed=failed,
            sync_type='invoices',
            timestamp=datetime.now().isoformat(),
            errors=errors
        )
    
    def fetch_stock_levels(self) -> List[Dict]:
        """Fetch stock from Zoho Inventory"""
        try:
            response = self.session.get(
                f"{self.base_url}/items",
                params={'organization_id': self.org_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    {'name': item['name'], 'quantity': item.get('stock_on_hand', 0)}
                    for item in data.get('items', [])
                ]
        except Exception as e:
            logger.error(f"Zoho stock fetch error: {e}")
        
        return []
    
    def fetch_ledgers(self) -> List[Dict]:
        """Fetch contacts from Zoho"""
        try:
            response = self.session.get(
                f"{self.base_url}/contacts",
                params={'organization_id': self.org_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    {'name': c['contact_name'], 'type': c.get('contact_type', 'customer')}
                    for c in data.get('contacts', [])
                ]
        except Exception as e:
            logger.error(f"Zoho contacts fetch error: {e}")
        
        return []


class ERPIntegrationService:
    """
    High-level ERP integration service
    Manages multiple ERP connections and sync operations
    """
    
    def __init__(self):
        self.connectors: Dict[str, ERPConnector] = {}
        self.sync_history: List[SyncResult] = []
    
    def register_connector(self, name: str, config: ERPConfig):
        """Register an ERP connector"""
        if config.erp_type == 'tally':
            self.connectors[name] = TallyConnector(config)
        elif config.erp_type == 'zoho':
            self.connectors[name] = ZohoConnector(config)
        else:
            raise ValueError(f"Unsupported ERP type: {config.erp_type}")
        
        logger.info(f"Registered {config.erp_type} connector: {name}")
    
    def test_connection(self, connector_name: str) -> bool:
        """Test ERP connection"""
        if connector_name not in self.connectors:
            return False
        return self.connectors[connector_name].connect()
    
    def sync_all_products(self, products: List[Dict]) -> Dict[str, SyncResult]:
        """Sync products to all registered ERPs"""
        results = {}
        
        for name, connector in self.connectors.items():
            result = connector.sync_products(products)
            results[name] = result
            self.sync_history.append(result)
        
        return results
    
    def sync_all_invoices(self, invoices: List[Dict]) -> Dict[str, SyncResult]:
        """Sync invoices to all registered ERPs"""
        results = {}
        
        for name, connector in self.connectors.items():
            result = connector.sync_invoices(invoices)
            results[name] = result
            self.sync_history.append(result)
        
        return results
    
    def get_consolidated_stock(self) -> Dict[str, Dict]:
        """Get stock levels from all ERPs"""
        all_stock = {}
        
        for name, connector in self.connectors.items():
            stocks = connector.fetch_stock_levels()
            all_stock[name] = {item['name']: item['quantity'] for item in stocks}
        
        return all_stock
    
    def get_sync_history(self, limit: int = 50) -> List[Dict]:
        """Get recent sync history"""
        return [r.to_dict() for r in self.sync_history[-limit:]]


# FastAPI Router for ERP Integration
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/erp", tags=["ERP Integration"])


class ERPConnectionRequest(BaseModel):
    name: str
    erp_type: str
    host: str
    port: int
    company_name: str
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None


# Global service instance
_erp_service: Optional[ERPIntegrationService] = None

def get_erp_service() -> ERPIntegrationService:
    global _erp_service
    if _erp_service is None:
        _erp_service = ERPIntegrationService()
    return _erp_service


@router.post("/connect")
async def connect_erp(request: ERPConnectionRequest):
    """Register and connect to an ERP system"""
    service = get_erp_service()
    
    config = ERPConfig(
        erp_type=request.erp_type,
        host=request.host,
        port=request.port,
        company_name=request.company_name,
        username=request.username,
        password=request.password,
        api_key=request.api_key
    )
    
    try:
        service.register_connector(request.name, config)
        connected = service.test_connection(request.name)
        
        return {
            "status": "connected" if connected else "connection_failed",
            "connector": request.name,
            "erp_type": request.erp_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/products")
async def sync_products_to_erp(products: List[Dict]):
    """Sync products to all connected ERPs"""
    service = get_erp_service()
    
    if not service.connectors:
        return {"status": "no_connectors", "message": "No ERP connectors registered"}
    
    results = service.sync_all_products(products)
    
    return {
        "status": "completed",
        "results": {name: r.to_dict() for name, r in results.items()}
    }


@router.post("/sync/invoices")
async def sync_invoices_to_erp(invoices: List[Dict]):
    """Sync invoices to all connected ERPs"""
    service = get_erp_service()
    
    if not service.connectors:
        return {"status": "no_connectors", "message": "No ERP connectors registered"}
    
    results = service.sync_all_invoices(invoices)
    
    return {
        "status": "completed",
        "results": {name: r.to_dict() for name, r in results.items()}
    }


@router.get("/stock")
async def get_erp_stock():
    """Get consolidated stock from all ERPs"""
    service = get_erp_service()
    return service.get_consolidated_stock()


@router.get("/history")
async def get_sync_history(limit: int = 50):
    """Get ERP sync history"""
    service = get_erp_service()
    return {"history": service.get_sync_history(limit)}


@router.get("/connectors")
async def list_connectors():
    """List registered ERP connectors"""
    service = get_erp_service()
    return {
        "connectors": [
            {"name": name, "type": type(conn).__name__}
            for name, conn in service.connectors.items()
        ]
    }
