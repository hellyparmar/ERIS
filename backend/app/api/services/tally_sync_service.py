"""
Tally Synchronization Service
Handles bi-directional sync between R-DIOS and Tally
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

from app.api.integrations.tally_connector import TallyXMLConnector
from app.api.db.models import Product, Customer
from app.api.db.multitenant_models import Organization

logger = logging.getLogger(__name__)


class TallySyncService:
    """
    Service for syncing data between R-DIOS and Tally
    """
    
    def __init__(self, tally_host: str = "localhost", tally_port: int = 9000):
        """Initialize Tally sync service"""
        self.connector = TallyXMLConnector(host=tally_host, port=tally_port)
    
    def test_connection(self) -> Dict:
        """Test Tally connection and get status"""
        is_connected = self.connector.test_connection()
        
        result = {
            'connected': is_connected,
            'host': self.connector.host,
            'port': self.connector.port,
            'timestamp': datetime.now().isoformat()
        }
        
        if is_connected:
            company_info = self.connector.get_company_info()
            if company_info:
                result['company'] = company_info
        
        return result
    
    def import_stock_items_to_rdios(self, db: Session, organization_id: str) -> Dict:
        """
        Import stock items from Tally to R-DIOS
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Import statistics
        """
        try:
            # Get stock items from Tally
            tally_items = self.connector.import_stock_items()
            
            if not tally_items:
                return {
                    'success': False,
                    'message': 'No stock items found in Tally',
                    'total': 0
                }
            
            imported = 0
            updated = 0
            skipped = 0
            errors = []
            
            for tally_item in tally_items:
                try:
                    # Check if product already exists
                    existing_product = db.query(Product).filter(
                        Product.organization_id == organization_id,
                        Product.name == tally_item['name']
                    ).first()
                    
                    if existing_product:
                        # Update existing product
                        existing_product.hsn_code = tally_item.get('hsn_code', '')
                        existing_product.unit = tally_item.get('unit', 'PCS')
                        
                        # Update GST rate
                        if tally_item.get('gst_applicable'):
                            gst_rate = tally_item.get('gst_rate', 0)
                            existing_product.cgst_rate = Decimal(str(gst_rate / 2))
                            existing_product.sgst_rate = Decimal(str(gst_rate / 2))
                            existing_product.igst_rate = Decimal(str(gst_rate))
                        
                        updated += 1
                    else:
                        # Create new product
                        new_product = Product(
                            organization_id=organization_id,
                            name=tally_item['name'],
                            sku=f"TALLY-{tally_item.get('guid', '')[:8]}",
                            hsn_code=tally_item.get('hsn_code', ''),
                            unit=tally_item.get('unit', 'PCS'),
                            category=tally_item.get('category', 'Imported from Tally'),
                            is_taxable=tally_item.get('gst_applicable', False)
                        )
                        
                        # Set GST rates
                        if tally_item.get('gst_applicable'):
                            gst_rate = tally_item.get('gst_rate', 0)
                            new_product.cgst_rate = Decimal(str(gst_rate / 2))
                            new_product.sgst_rate = Decimal(str(gst_rate / 2))
                            new_product.igst_rate = Decimal(str(gst_rate))
                        
                        db.add(new_product)
                        imported += 1
                    
                except Exception as e:
                    logger.error(f"Error importing item {tally_item.get('name')}: {e}")
                    errors.append(str(e))
                    skipped += 1
            
            # Commit changes
            db.commit()
            
            return {
                'success': True,
                'total': len(tally_items),
                'imported': imported,
                'updated': updated,
                'skipped': skipped,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Stock items import failed: {e}")
            db.rollback()
            return {
                'success': False,
                'message': str(e),
                'total': 0
            }
    
    def import_ledgers_to_rdios(self, db: Session, organization_id: str) -> Dict:
        """
        Import ledgers from Tally as customers
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Import statistics
        """
        try:
            # Get ledgers from Tally
            tally_ledgers = self.connector.import_ledgers()
            
            if not tally_ledgers:
                return {
                    'success': False,
                    'message': 'No ledgers found in Tally',
                    'total': 0
                }
            
            imported = 0
            updated = 0
            skipped = 0
            
            # Filter ledgers that are sundry debtors (customers)
            customer_groups = ['Sundry Debtors', 'Debtors']
            
            for ledger in tally_ledgers:
                try:
                    # Check if it's a customer ledger
                    if ledger.get('group') not in customer_groups:
                        skipped += 1
                        continue
                    
                    # Check if customer already exists
                    existing_customer = db.query(Customer).filter(
                        Customer.organization_id == organization_id,
                        Customer.name == ledger['name']
                    ).first()
                    
                    if existing_customer:
                        # Update existing customer
                        if ledger.get('gstin'):
                            existing_customer.gstin = ledger['gstin']
                        updated += 1
                    else:
                        # Create new customer
                        new_customer = Customer(
                            organization_id=organization_id,
                            name=ledger['name'],
                            gstin=ledger.get('gstin', ''),
                            phone='',  # Not available in Tally ledger
                            email='',   # Not available in Tally ledger
                            address={'line1': '', 'city': '', 'state': '', 'pincode': ''}
                        )
                        
                        db.add(new_customer)
                        imported += 1
                    
                except Exception as e:
                    logger.error(f"Error importing ledger {ledger.get('name')}: {e}")
                    skipped += 1
            
            # Commit changes
            db.commit()
            
            return {
                'success': True,
                'total': len([l for l in tally_ledgers if l.get('group') in customer_groups]),
                'imported': imported,
                'updated': updated,
                'skipped': skipped
            }
            
        except Exception as e:
            logger.error(f"Ledgers import failed: {e}")
            db.rollback()
            return {
                'success': False,
                'message': str(e),
                'total': 0
            }
    
    def export_sales_invoice_to_tally(self, invoice_data: Dict) -> Dict:
        """
        Export R-DIOS sales invoice to Tally
        
        Args:
            invoice_data: Invoice data from R-DIOS
            
        Returns:
            Export result
        """
        try:
            # Prepare voucher data
            voucher_data = {
                'date': datetime.fromisoformat(invoice_data['invoice_date']).date(),
                'invoice_number': invoice_data['invoice_number'],
                'customer_name': invoice_data['customer_name'],
                'taxable_amount': invoice_data['taxable_amount'],
                'cgst_amount': invoice_data.get('cgst_amount', 0),
                'sgst_amount': invoice_data.get('sgst_amount', 0),
                'igst_amount': invoice_data.get('igst_amount', 0),
                'grand_total': invoice_data['grand_total']
            }
            
            # Export to Tally
            success = self.connector.export_sales_voucher(voucher_data)
            
            if success:
                return {
                    'success': True,
                    'invoice_number': invoice_data['invoice_number'],
                    'message': f"Invoice {invoice_data['invoice_number']} exported to Tally"
                }
            else:
                return {
                    'success': False,
                    'invoice_number': invoice_data['invoice_number'],
                    'message': 'Failed to export invoice to Tally'
                }
                
        except Exception as e:
            logger.error(f"Invoice export failed: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def sync_all(self, db: Session, organization_id: str) -> Dict:
        """
        Perform full sync (import stock items and ledgers)
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Sync summary
        """
        result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'stock_items': {},
            'ledgers': {}
        }
        
        # Test connection first
        if not self.connector.test_connection():
            result['message'] = 'Cannot connect to Tally. Is Tally running?'
            return result
        
        # Import stock items
        stock_result = self.import_stock_items_to_rdios(db, organization_id)
        result['stock_items'] = stock_result
        
        # Import ledgers
        ledgers_result = self.import_ledgers_to_rdios(db, organization_id)
        result['ledgers'] = ledgers_result
        
        # Overall success
        result['success'] = stock_result.get('success', False) or ledgers_result.get('success', False)
        
        return result


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create DB session
    engine = create_engine('postgresql://user:pass@localhost/rdios')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Initialize service
    tally_sync = TallySyncService(tally_host="localhost", tally_port=9000)
    
    # Test connection
    status = tally_sync.test_connection()
    print(f"Tally Connection: {status}")
    
    # Full sync
    org_id = "00000000-0000-0000-0000-000000000001"
    result = tally_sync.sync_all(db, org_id)
    
    print("\nSync Results:")
    print(f"Stock Items: {result['stock_items']}")
    print(f"Ledgers: {result['ledgers']}")
