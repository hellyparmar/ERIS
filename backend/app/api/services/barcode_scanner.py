"""
Barcode Scanner Service
Product lookup by barcode (EAN-13, UPC-A, Code128)
Per CLAUDE.md Part 3.1
"""
import re
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.db.models import Product, Inventory

# Barcode format validators
BARCODE_PATTERNS = {
    'EAN-13': re.compile(r'^\d{13}$'),
    'UPC-A': re.compile(r'^\d{12}$'),
    'Code128': re.compile(r'^[\x00-\x7F]{1,48}$'),
    'EAN-8': re.compile(r'^\d{8}$')
}

def validate_barcode(barcode: str) -> Optional[str]:
    """
    Validate barcode format
    Returns barcode type if valid, None otherwise
    """
    for barcode_type, pattern in BARCODE_PATTERNS.items():
        if pattern.match(barcode):
            return barcode_type
    return None

def lookup_barcode(barcode: str, db: Session) -> Dict:
    """
    Lookup product by barcode
    
    Args:
        barcode: Barcode string (EAN-13, UPC-A, Code128, etc.)
        db: Database session
    
    Returns:
        {
            'success': bool,
            'product': {...} or None,
            'inventory': {...} or None,
            'barcode_type': str or None,
            'error': str or None
        }
    """
    # Validate barcode format
    barcode_type = validate_barcode(barcode)
    if not barcode_type:
        return {
            'success': False,
            'product': None,
            'inventory': None,
            'barcode_type': None,
            'error': f'Invalid barcode format: {barcode}'
        }
    
    # Lookup product by barcode or SKU (fallback)
    product = db.query(Product).filter(
        or_(
            Product.barcode == barcode,
            Product.sku == barcode
        )
    ).first()
    
    if not product:
        return {
            'success': False,
            'product': None,
            'inventory': None,
            'barcode_type': barcode_type,
            'error': f'Product not found for barcode: {barcode}'
        }
    
    # Get inventory data
    inventory = db.query(Inventory).filter(
        Inventory.product_id == product.id
    ).first()
    
    return {
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'barcode': product.barcode,
            'category': product.category,
            'unit_price': float(product.unit_price),
            'gst_rate': product.gst_rate
        },
        'inventory': {
            'current_stock': inventory.current_stock if inventory else 0,
            'reorder_point': inventory.reorder_point if inventory else 0,
            'stock_status': inventory.stock_status if inventory else 'unknown'
        } if inventory else None,
        'barcode_type': barcode_type,
        'error': None
    }

def update_product_barcode(product_id: int, barcode: str, db: Session) -> Dict:
    """
    Update product barcode
    
    Args:
        product_id: Product ID
        barcode: New barcode value
        db: Database session
    
    Returns:
        {'success': bool, 'error': str or None}
    """
    # Validate barcode
    barcode_type = validate_barcode(barcode)
    if not barcode_type:
        return {
            'success': False,
            'error': f'Invalid barcode format: {barcode}'
        }
    
    # Check if barcode already exists
    existing = db.query(Product).filter(
        Product.barcode == barcode,
        Product.id != product_id
    ).first()
    
    if existing:
        return {
            'success': False,
            'error': f'Barcode {barcode} already assigned to product: {existing.name}'
        }
    
    # Update product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {
            'success': False,
            'error': f'Product {product_id} not found'
        }
    
    product.barcode = barcode
    db.commit()
    
    return {
        'success': True,
        'error': None
    }
