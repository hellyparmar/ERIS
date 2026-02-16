"""
Inventory Control Router
Barcode scanning, stock alerts, reorder suggestions, stock adjustments
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from api.db import get_db
from api.services.barcode_scanner import lookup_barcode, update_product_barcode

router = APIRouter(prefix="/inventory", tags=["Inventory Control"])

class BarcodeUpdateRequest(BaseModel):
    product_id: int
    barcode: str

@router.get("/scan/{barcode}")
async def scan_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    Lookup product by barcode
    Supports EAN-13, UPC-A, Code128, EAN-8
    """
    result = lookup_barcode(barcode, db)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'data': {
            'product': result['product'],
            'inventory': result['inventory'],
            'barcode_type': result['barcode_type']
        }
    }

@router.post("/barcode/update")
async def update_barcode(request: BarcodeUpdateRequest, db: Session = Depends(get_db)):
    """
    Update product barcode
    """
    result = update_product_barcode(request.product_id, request.barcode, db)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return {'success': True, 'message': 'Barcode updated successfully'}
