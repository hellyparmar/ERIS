"""
Simple Forecasting Service: 30-Day Moving Average
Replaces complex Prophet + XGBoost + SHAP implementation
with dead-simple moving average that actually works
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.db.models import Sale
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SimpleForecastingService:
    """
    Simple forecasting using 30-day moving average
    
    Benefits:
    - No ML dependencies (no Prophet, XGBoost, SHAP)
    - Fast: Single SQL query
    - Understandable: Just averaging
    - Reliable: No model training failures
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def forecast_daily_sales(
        self, 
        store_id: int,
        product_id: Optional[int] = None,
        days_to_forecast: int = 30
    ) -> Dict[str, Any]:
        """
        Simple forecast: Average daily sales from last 30 days
        
        Args:
            store_id: Store ID
            product_id: Specific product or None for all
            days_to_forecast: Days to forecast (default 30)
            
        Returns:
            {
                'forecast': [
                    {'date': '2026-03-04', 'predicted_sales': 15000},
                    ...
                ],
                'daily_average': 14500,
                'confidence_lower': 10000,
                'confidence_upper': 19000,
                'data_points': 30,
                'method': 'simple_moving_average'
            }
        """
        try:
            # Get last 30 days of sales
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            query = self.db.query(
                func.date(Sale.created_at).label('date'),
                func.sum(Sale.total_amount).label('daily_total')
            ).filter(
                Sale.store_id == store_id,
                Sale.created_at >= thirty_days_ago
            )
            
            if product_id:
                # Filter by product via sale items
                from app.api.db.models import SaleItem
                query = query.join(SaleItem).filter(SaleItem.product_id == product_id)
            
            query = query.group_by(func.date(Sale.created_at))
            
            daily_sales = query.all()
            
            if not daily_sales:
                # No data, return zero forecast
                return {
                    'forecast': [
                        {
                            'date': (datetime.utcnow() + timedelta(days=i)).strftime('%Y-%m-%d'),
                            'predicted_sales': 0
                        }
                        for i in range(1, days_to_forecast + 1)
                    ],
                    'daily_average': 0,
                    'confidence_lower': 0,
                    'confidence_upper': 0,
                    'data_points': 0,
                    'method': 'simple_moving_average',
                    'warning': 'No historical data available'
                }
            
            # Calculate average
            sales_values = [float(sale.daily_total or 0) for sale in daily_sales]
            daily_average = sum(sales_values) / len(sales_values)
            
            # Simple confidence interval: ±30% of average
            std_dev = self._calculate_std_dev(sales_values, daily_average)
            confidence_lower = max(0, daily_average - (std_dev * 1.96))
            confidence_upper = daily_average + (std_dev * 1.96)
            
            # Generate forecast
            today = datetime.utcnow().date()
            forecast = []
            for i in range(1, days_to_forecast + 1):
                forecast_date = today + timedelta(days=i)
                forecast.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'predicted_sales': round(daily_average, 2)
                })
            
            return {
                'forecast': forecast,
                'daily_average': round(daily_average, 2),
                'confidence_lower': round(confidence_lower, 2),
                'confidence_upper': round(confidence_upper, 2),
                'data_points': len(daily_sales),
                'method': 'simple_moving_average',
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Forecast error for store {store_id}: {e}")
            return {
                'error': str(e),
                'method': 'simple_moving_average',
                'forecast': []
            }
    
    def forecast_by_product(
        self,
        store_id: int,
        days_to_forecast: int = 30,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Forecast for top N products
        
        Returns:
            {
                'store_id': 1,
                'products': [
                    {
                        'product_id': 5,
                        'product_name': 'Widget A',
                        'daily_average': 150,
                        'forecast': [...]
                    },
                    ...
                ]
            }
        """
        try:
            # Get top products by sales volume
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            from app.api.db.models import Product, SaleItem
            
            top_products = self.db.query(
                Product.id,
                Product.name,
                func.sum(SaleItem.quantity).label('total_qty'),
                func.sum(SaleItem.unit_price * SaleItem.quantity).label('total_sales')
            ).join(
                SaleItem
            ).join(
                Sale
            ).filter(
                Sale.store_id == store_id,
                Sale.created_at >= thirty_days_ago
            ).group_by(
                Product.id, Product.name
            ).order_by(
                func.sum(SaleItem.unit_price * SaleItem.quantity).desc()
            ).limit(top_n).all()
            
            products_forecast = []
            for product in top_products:
                forecast = self.forecast_daily_sales(
                    store_id=store_id,
                    product_id=product.id,
                    days_to_forecast=days_to_forecast
                )
                
                products_forecast.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'daily_average': forecast.get('daily_average', 0),
                    'confidence_lower': forecast.get('confidence_lower', 0),
                    'confidence_upper': forecast.get('confidence_upper', 0),
                    'data_points': forecast.get('data_points', 0)
                })
            
            return {
                'store_id': store_id,
                'forecast_days': days_to_forecast,
                'products': products_forecast,
                'method': 'simple_moving_average',
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Product forecast error: {e}")
            return {'error': str(e), 'products': []}
    
    @staticmethod
    def _calculate_std_dev(values: List[float], mean: float) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return mean * 0.3  # Default 30% variation
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
