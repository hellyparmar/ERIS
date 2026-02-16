"""
Reorder Automation Service
AI-driven reorder suggestions based on sales velocity
Per CLAUDE.md Part 3.3
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from api.db.models import Product, Inventory, Sale, SaleItem

def calculate_sales_velocity(product_id: int, days: int, db: Session) -> float:
    """
    Calculate average daily sales for a product
    
    Args:
        product_id: Product ID
        days: Number of days to analyze
        db: Database session
    
    Returns:
        Average units sold per day
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Get total units sold in the period
    total_sold = db.query(
        func.sum(SaleItem.quantity)
    ).join(
        Sale, SaleItem.sale_id == Sale.id
    ).filter(
        and_(
            SaleItem.product_id == product_id,
            Sale.created_at >= cutoff_date
        )
    ).scalar() or 0
    
    return total_sold / days if days > 0 else 0

def calculate_reorder_quantity(
    product_id: int,
    db: Session,
    lead_time_days: int = 7,
    safety_stock_multiplier: float = 1.5
) -> Dict:
    """
    Calculate optimal reorder quantity using sales velocity
    
    Formula:
    reorder_qty = (daily_sales * lead_time) * safety_multiplier
    
    Args:
        product_id: Product ID
        db: Database session
        lead_time_days: Supplier lead time in days
        safety_stock_multiplier: Safety stock factor (default 1.5)
    
    Returns:
        {
            'suggested_quantity': int,
            'daily_sales_7d': float,
            'daily_sales_30d': float,
            'confidence_score': float,
            'reasoning': str
        }
    """
    # Get sales velocity for 7 and 30 days
    velocity_7d = calculate_sales_velocity(product_id, 7, db)
    velocity_30d = calculate_sales_velocity(product_id, 30, db)
    
    # Use 7-day velocity if available, otherwise 30-day
    daily_sales = velocity_7d if velocity_7d > 0 else velocity_30d
    
    # Calculate suggested quantity
    base_quantity = daily_sales * lead_time_days
    suggested_quantity = int(base_quantity * safety_stock_multiplier)
    
    # Calculate confidence score (0-100)
    # Higher confidence if:
    # - More recent sales (7d > 30d)
    # - Consistent velocity between periods
    # - Higher sales volume
    confidence = 0
    
    if velocity_7d > 0:
        confidence += 40  # Recent sales data
        
        # Consistency check
        if velocity_30d > 0:
            ratio = min(velocity_7d, velocity_30d) / max(velocity_7d, velocity_30d)
            confidence += int(ratio * 30)  # Up to 30 points for consistency
        
        # Volume check
        if velocity_7d >= 5:
            confidence += 30  # High volume = high confidence
        elif velocity_7d >= 1:
            confidence += 20  # Medium volume
        else:
            confidence += 10  # Low volume
    elif velocity_30d > 0:
        confidence += 20  # Only historical data
        if velocity_30d >= 1:
            confidence += 10
    
    # Generate reasoning
    reasoning = []
    if velocity_7d > 0:
        reasoning.append(f"Selling {velocity_7d:.1f} units/day (7-day avg)")
    if velocity_30d > 0:
        reasoning.append(f"{velocity_30d:.1f} units/day (30-day avg)")
    reasoning.append(f"{lead_time_days}-day lead time")
    reasoning.append(f"{safety_stock_multiplier}x safety stock")
    
    return {
        'suggested_quantity': max(suggested_quantity, 1),  # At least 1
        'daily_sales_7d': round(velocity_7d, 2),
        'daily_sales_30d': round(velocity_30d, 2),
        'confidence_score': min(confidence, 100),
        'reasoning': ' • '.join(reasoning)
    }

def get_reorder_suggestions(
    db: Session,
    min_confidence: int = 50,
    limit: int = 20
) -> List[Dict]:
    """
    Get reorder suggestions for all low-stock items
    Sorted by urgency (stock level + sales velocity)
    
    Args:
        db: Database session
        min_confidence: Minimum confidence score to include
        limit: Max number of suggestions
    
    Returns:
        List of reorder suggestions
    """
    suggestions = []
    
    # Get all inventory items at or below reorder point
    low_stock_items = db.query(Inventory, Product).join(
        Product, Inventory.product_id == Product.id
    ).filter(
        Inventory.current_stock <= Inventory.reorder_point
    ).all()
    
    for inv, product in low_stock_items:
        # Calculate reorder quantity
        reorder_calc = calculate_reorder_quantity(product.id, db)
        
        # Skip if confidence too low
        if reorder_calc['confidence_score'] < min_confidence:
            continue
        
        # Calculate urgency score (0-100)
        # Higher urgency = lower stock + higher sales velocity
        stock_ratio = inv.current_stock / max(inv.reorder_point, 1)
        velocity_factor = min(reorder_calc['daily_sales_7d'] / 10, 1)  # Normalize to 0-1
        urgency = int((1 - stock_ratio) * 50 + velocity_factor * 50)
        
        suggestions.append({
            'product_id': product.id,
            'product_name': product.name,
            'category': product.category,
            'current_stock': inv.current_stock,
            'reorder_point': inv.reorder_point,
            'suggested_quantity': reorder_calc['suggested_quantity'],
            'daily_sales_7d': reorder_calc['daily_sales_7d'],
            'daily_sales_30d': reorder_calc['daily_sales_30d'],
            'confidence_score': reorder_calc['confidence_score'],
            'reasoning': reorder_calc['reasoning'],
            'urgency_score': urgency,
            'estimated_cost': float(product.unit_price) * reorder_calc['suggested_quantity']
        })
    
    # Sort by urgency (highest first)
    suggestions.sort(key=lambda x: x['urgency_score'], reverse=True)
    
    return suggestions[:limit]
