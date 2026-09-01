"""
Odoo ERP Connector
Handles XML-RPC communication with Odoo instance.
Supports: Authentication, Product Sync, Customer Sync, Invoice Export
"""

import xmlrpc.client
import ssl
from typing import List, Dict, Any, Optional

class OdooClient:
    def __init__(self, url: str, db: str, username: str, api_key: str, mock_mode: bool = False):
        """
        Initialize Odoo Client
        :param url: Odoo Server URL (e.g., https://my-company.odoo.com)
        :param db: Database name
        :param username: User email/login
        :param api_key: API Key or Password
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.api_key = api_key
        self.uid = None
        self.mock_mode = mock_mode
        
        # SSL Context for secure connections (ignore self-signed certs if needed for local dev)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def connect(self) -> bool:
        """Authenticate and get User ID (UID)"""
        if self.mock_mode:
            self.uid = 9999
            return True
            
        try:
            common = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/common', 
                context=self.ssl_context
            )
            self.uid = common.authenticate(
                self.db, 
                self.username, 
                self.api_key, 
                {}
            )
            return bool(self.uid)
        except Exception as e:
            print(f"❌ Odoo Connection Error: {e}")
            return False

    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute a method on an Odoo model"""
        if not self.uid:
            if not self.connect():
                raise ConnectionError("Could not authenticate with Odoo")

        models = xmlrpc.client.ServerProxy(
            f'{self.url}/xmlrpc/2/object', 
            context=self.ssl_context
        )
        return models.execute_kw(
            self.db, 
            self.uid, 
            self.api_key, 
            model, 
            method, 
            args, 
            kwargs
        )

    def get_products(self, limit: int = 100) -> List[Dict]:
        """Fetch products from Odoo"""
        if self.mock_mode:
            return [{"id": 1, "name": "Mock Product A", "list_price": 10.0, "qty_available": 50}]
            
        try:
            # 1. Search for products (e.g., active and saleable)
            domain = [['sale_ok', '=', True], ['active', '=', True]]
            fields = ['name', 'default_code', 'list_price', 'standard_price', 'qty_available', 'uom_id']
            
            product_ids = self._execute(
                'product.product', 
                'search', 
                domain, 
                {'limit': limit}
            )
            
            # 2. Read product usage details
            products = self._execute(
                'product.product', 
                'read', 
                product_ids, 
                {'fields': fields}
            )
            return products
        except Exception as e:
            print(f"❌ Error fetching products: {e}")
            return []

    def get_customers(self, limit: int = 100) -> List[Dict]:
        """Fetch customers (partners) from Odoo"""
        if self.mock_mode:
            return [{"id": 1, "name": "Mock Customer", "email": "mock@example.com"}]
            
        try:
            domain = [['customer_rank', '>', 0], ['type', '=', 'contact']]
            fields = ['name', 'email', 'phone', 'street', 'city', 'zip', 'vat'] # vat is GSTIN often
            
            partner_ids = self._execute(
                'res.partner', 
                'search', 
                domain, 
                {'limit': limit}
            )
            
            partners = self._execute(
                'res.partner', 
                'read', 
                partner_ids, 
                {'fields': fields}
            )
            return partners
        except Exception as e:
            print(f"❌ Error fetching customers: {e}")
            return []

    def create_invoice(self, invoice_data: Dict) -> Optional[int]:
        """
        Push invoice to Odoo
        Note: Simple implementation creates a generic move (invoice)
        """
        if self.mock_mode:
            return 8888
            
        try:
            # Simplified mapping - in prod needs complex line item mapping
            invoice_id = self._execute('account.move', 'create', [invoice_data])
            return invoice_id
        except Exception as e:
            print(f"❌ Error creating invoice: {e}")
            return None

    def test_connection(self) -> Dict:
        """Test the connection and return version info"""
        if self.mock_mode:
            return {"success": True, "version": "16.0 (Mock)", "protocol": 2, "uid": 9999}
            
        try:
            common = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/common', 
                context=self.ssl_context
            )
            version = common.version()
            auth = self.connect()
            return {
                "success": auth,
                "version": version.get('server_version'),
                "protocol": version.get('protocol_version'),
                "uid": self.uid
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
