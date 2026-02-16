"""
Stock Adjustment Service
Track manual stock changes with audit log
Per CLAUDE.md Part 3.4
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from api.db import engine
from sqlalchemy import text

# Adjustment types
ADJUSTMENT_ADD = 'add'
ADJUSTMENT_REMOVE = 'remove'
ADJUSTMENT_SET = 'set'

# Adjustment reasons
REASONS = [
    'damage',
    'theft',
    'expiry',
    'recount',
    'supplier_return',
    'customer_return',
    'transfer_in',
    'transfer_out',
    'other'
]

def record_adjustment(
    product_id: int,
    adjustment_type: str,
    quantity: int,
    reason: str,
    notes: Optional[str],
    user_id: int,
    db: Session
) -> Dict:
    """
    Record a stock adjustment with audit trail
    
    Args:
        product_id: Product ID
        adjustment_type: 'add', 'remove', or 'set'
        quantity: Quantity to add/remove or new stock level (for 'set')
        reason: Reason for adjustment
        notes: Optional notes
        user_id: User making the adjustment
        db: Database session
    
    Returns:
        {
            'success': bool,
            'adjustment_id': int or None,
            'new_stock_level': int or None,
            'error': str or None
        }
    """
    # Validate adjustment type
    if adjustment_type not in [ADJUSTMENT_ADD, ADJUSTMENT_REMOVE, ADJUSTMENT_SET]:
        return {
            'success': False,
            'adjustment_id': None,
            'new_stock_level': None,
            'error': f'Invalid adjustment type: {adjustment_type}'
        }
    
    # Validate reason
    if reason not in REASONS:
        return {
            'success': False,
            'adjustment_id': None,
            'new_stock_level': None,
            'error': f'Invalid reason: {reason}. Must be one of: {", ".join(REASONS)}'
        }
    
    # Get current inventory using raw SQL
    with engine.connect() as conn:
        result = conn.execute(
            text('SELECT current_stock FROM inventory WHERE product_id = :product_id'),
            {'product_id': product_id}
        )
        row = result.fetchone()
        
        if not row:
            return {
                'success': False,
                'adjustment_id': None,
                'new_stock_level': None,
                'error': f'Inventory record not found for product {product_id}'
            }
        
        quantity_before = row[0]
    
    # Calculate new stock level
    if adjustment_type == ADJUSTMENT_ADD:
        quantity_after = quantity_before + quantity
        quantity_change = quantity
    elif adjustment_type == ADJUSTMENT_REMOVE:
        quantity_after = max(0, quantity_before - quantity)
        quantity_change = -(quantity_before - quantity_after)
    else:  # ADJUSTMENT_SET
        quantity_after = quantity
        quantity_change = quantity - quantity_before
    
    # Validate new stock level
    if quantity_after < 0:
        return {
            'success': False,
            'adjustment_id': None,
            'new_stock_level': None,
            'error': f'Cannot reduce stock below 0 (current: {quantity_before}, requested: {quantity})'
        }
    
    # Record adjustment using raw SQL
    with engine.connect() as conn:
        result = conn.execute(
            text('''
                INSERT INTO stock_adjustments 
                (product_id, adjustment_type, quantity_before, quantity_after, quantity_change, reason, notes, user_id, created_at)
                VALUES (:product_id, :adjustment_type, :quantity_before, :quantity_after, :quantity_change, :reason, :notes, :user_id, NOW())
                RETURNING id
            '''),
            {
                'product_id': product_id,
                'adjustment_type': adjustment_type,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after,
                'quantity_change': quantity_change,
                'reason': reason,
                'notes': notes,
                'user_id': user_id
            }
        )
        adjustment_id = result.fetchone()[0]
        conn.commit()
        
        # Update inventory
        conn.execute(
            text('UPDATE inventory SET current_stock = :new_stock WHERE product_id = :product_id'),
            {'new_stock': quantity_after, 'product_id': product_id}
        )
        conn.commit()
    
    return {
        'success': True,
        'adjustment_id': adjustment_id,
        'new_stock_level': quantity_after,
        'error': None
    }

def get_adjustment_history(
    product_id: Optional[int] = None,
    user_id: Optional[int] = None,
    adjustment_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict:
    """
    Get stock adjustment history with filtering
    
    Args:
        product_id: Filter by product
        user_id: Filter by user
        adjustment_type: Filter by type
        limit: Results per page
        offset: Pagination offset
    
    Returns:
        {
            'adjustments': [...],
            'total': int
        }
    """
    # Build query
    where_clauses = []
    params = {}
    
    if product_id:
        where_clauses.append('sa.product_id = :product_id')
        params['product_id'] = product_id
    
    if user_id:
        where_clauses.append('sa.user_id = :user_id')
        params['user_id'] = user_id
    
    if adjustment_type:
        where_clauses.append('sa.adjustment_type = :adjustment_type')
        params['adjustment_type'] = adjustment_type
    
    where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''
    
    # Get total count
    with engine.connect() as conn:
        count_result = conn.execute(
            text(f'SELECT COUNT(*) FROM stock_adjustments sa {where_sql}'),
            params
        )
        total = count_result.scalar()
        
        # Get adjustments with product names
        params['limit'] = limit
        params['offset'] = offset
        
        results = conn.execute(
            text(f'''
                SELECT 
                    sa.id, sa.product_id, p.name as product_name, p.category,
                    sa.adjustment_type, sa.quantity_before, sa.quantity_after, sa.quantity_change,
                    sa.reason, sa.notes, sa.user_id, sa.created_at
                FROM stock_adjustments sa
                JOIN products p ON sa.product_id = p.id
                {where_sql}
                ORDER BY sa.created_at DESC
                LIMIT :limit OFFSET :offset
            '''),
            params
        )
        
        adjustments = []
        for row in results:
            adjustments.append({
                'id': row[0],
                'product_id': row[1],
                'product_name': row[2],
                'category': row[3],
                'adjustment_type': row[4],
                'quantity_before': row[5],
                'quantity_after': row[6],
                'quantity_change': row[7],
                'reason': row[8],
                'notes': row[9],
                'user_id': row[10],
                'created_at': row[11].isoformat() if row[11] else None
            })
    
    return {
        'adjustments': adjustments,
        'total': total
    }
