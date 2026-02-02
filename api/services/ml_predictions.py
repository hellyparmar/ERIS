"""
ML Predictions Service - Predictive Analytics
Demand forecasting, churn prediction, and insights generation
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from api.db.models import Sale, Product, Customer, Invoice

logger = logging.getLogger(__name__)

# Try importing ML libraries
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed. ML predictions will use fallback methods.")


class MLPredictionService:
    """Service for ML-powered predictions and insights"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
    
    # ==================== DEMAND FORECASTING ====================
    
    def predict_demand(
        self, 
        product_id: int, 
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Predict future demand for a product
        
        Args:
            product_id: Product ID
            days_ahead: Number of days to forecast
            
        Returns:
            Dictionary with predictions and confidence intervals
        """
        # Get historical sales data
        sales = self.db.query(Sale).filter(
            Sale.product_id == product_id
        ).order_by(Sale.sale_date.desc()).limit(90).all()
        
        if len(sales) < 7:
            return {
                "product_id": product_id,
                "predictions": [],
                "message": "Insufficient historical data"
            }
        
        # Convert to time series
        df = pd.DataFrame([
            {
                "date": sale.sale_date,
                "quantity": sale.quantity or 0
            }
            for sale in reversed(sales)
        ])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').resample('D').sum().fillna(0)
        
        if SKLEARN_AVAILABLE:
            # Use ML model for prediction
            predictions = self._ml_forecast(df['quantity'].values, days_ahead)
        else:
            # Use moving average as fallback
            predictions = self._moving_average_forecast(df['quantity'].values, days_ahead)
        
        # Generate future dates
        last_date = df.index[-1]
        future_dates = [
            (last_date + timedelta(days=i+1)).strftime("%Y-%m-%d")
            for i in range(days_ahead)
        ]
        
        return {
            "product_id": product_id,
            "predictions": [
                {
                    "date": date,
                    "predicted_quantity": max(0, int(pred)),
                    "confidence": "medium"
                }
                for date, pred in zip(future_dates, predictions)
            ],
            "average_daily_demand": float(df['quantity'].mean()),
            "trend": "increasing" if predictions[-1] > predictions[0] else "decreasing"
        }
    
    def _ml_forecast(self, data: np.ndarray, steps: int) -> List[float]:
        """ML-based forecasting using Random Forest"""
        # Create features (lag features)
        X, y = [], []
        window = 7
        
        for i in range(window, len(data)):
            X.append(data[i-window:i])
            y.append(data[i])
        
        if len(X) < 10:
            return self._moving_average_forecast(data, steps)
        
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        # Predict future
        predictions = []
        current_window = data[-window:].tolist()
        
        for _ in range(steps):
            pred = model.predict([current_window])[0]
            predictions.append(pred)
            current_window = current_window[1:] + [pred]
        
        return predictions
    
    def _moving_average_forecast(self, data: np.ndarray, steps: int) -> List[float]:
        """Simple moving average forecast"""
        window = min(7, len(data))
        avg = np.mean(data[-window:])
        return [avg] * steps
    
    # ==================== CHURN PREDICTION ====================
    
    def predict_churn(self, customer_id: int) -> Dict[str, Any]:
        """
        Predict customer churn probability
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Churn probability and risk level
        """
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            return {"error": "Customer not found"}
        
        # Get customer activity
        recent_purchases = self.db.query(Sale).filter(
            Sale.customer_id == customer_id,
            Sale.sale_date >= datetime.now() - timedelta(days=90)
        ).count()
        
        total_purchases = self.db.query(Sale).filter(
            Sale.customer_id == customer_id
        ).count()
        
        # Get last purchase date
        last_purchase = self.db.query(Sale).filter(
            Sale.customer_id == customer_id
        ).order_by(Sale.sale_date.desc()).first()
        
        days_since_purchase = 0
        if last_purchase and last_purchase.sale_date:
            days_since_purchase = (datetime.now() - last_purchase.sale_date).days
        
        # Simple rule-based churn prediction
        churn_score = 0
        
        if days_since_purchase > 60:
            churn_score += 0.4
        elif days_since_purchase > 30:
            churn_score += 0.2
        
        if recent_purchases == 0:
            churn_score += 0.3
        elif recent_purchases < 2:
            churn_score += 0.1
        
        if total_purchases < 5:
            churn_score += 0.2
        
        churn_probability = min(churn_score, 1.0)
        
        # Determine risk level
        if churn_probability >= 0.7:
            risk_level = "high"
        elif churn_probability >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "customer_id": customer_id,
            "churn_probability": round(churn_probability, 2),
            "risk_level": risk_level,
            "days_since_purchase": days_since_purchase,
            "recent_purchases": recent_purchases,
            "total_purchases": total_purchases,
            "recommendation": self._get_retention_recommendation(risk_level)
        }
    
    def _get_retention_recommendation(self, risk_level: str) -> str:
        """Get retention strategy recommendation"""
        recommendations = {
            "high": "Immediate action required: Send personalized offer or loyalty reward",
            "medium": "Monitor closely: Consider sending engagement email or discount",
            "low": "Maintain engagement: Continue regular communication"
        }
        return recommendations.get(risk_level, "Monitor customer activity")
    
    # ==================== REORDER RECOMMENDATIONS ====================
    
    def recommend_reorder(self, threshold_days: int = 7) -> List[Dict[str, Any]]:
        """
        Recommend products to reorder based on predicted stockouts
        
        Args:
            threshold_days: Days ahead to check for stockouts
            
        Returns:
            List of products needing reorder
        """
        products = self.db.query(Product).filter(
            Product.stock_level > 0
        ).all()
        
        recommendations = []
        
        for product in products:
            # Get demand prediction
            demand_forecast = self.predict_demand(product.id, threshold_days)
            
            if not demand_forecast.get('predictions'):
                continue
            
            # Calculate total predicted demand
            total_demand = sum(
                pred['predicted_quantity'] 
                for pred in demand_forecast['predictions']
            )
            
            current_stock = product.stock_level or 0
            
            # Check if stockout is predicted
            if total_demand > current_stock:
                days_until_stockout = 0
                cumulative_demand = 0
                
                for i, pred in enumerate(demand_forecast['predictions']):
                    cumulative_demand += pred['predicted_quantity']
                    if cumulative_demand > current_stock:
                        days_until_stockout = i + 1
                        break
                
                recommendations.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "current_stock": current_stock,
                    "predicted_demand": int(total_demand),
                    "shortage": int(total_demand - current_stock),
                    "days_until_stockout": days_until_stockout,
                    "recommended_order_quantity": int(total_demand - current_stock + product.reorder_point),
                    "urgency": "high" if days_until_stockout <= 3 else "medium"
                })
        
        # Sort by urgency
        recommendations.sort(key=lambda x: x['days_until_stockout'])
        
        return recommendations
    
    # ==================== INSIGHTS GENERATION ====================
    
    def generate_insights(self) -> Dict[str, Any]:
        """
        Generate AI-powered business insights
        
        Returns:
            Dictionary with various insights and recommendations
        """
        insights = {
            "timestamp": datetime.now().isoformat(),
            "insights": []
        }
        
        # Sales trend insight
        recent_sales = self.db.query(func.sum(Sale.total_amount)).filter(
            Sale.sale_date >= datetime.now() - timedelta(days=7)
        ).scalar() or 0
        
        previous_sales = self.db.query(func.sum(Sale.total_amount)).filter(
            Sale.sale_date >= datetime.now() - timedelta(days=14),
            Sale.sale_date < datetime.now() - timedelta(days=7)
        ).scalar() or 0
        
        if previous_sales > 0:
            growth = ((recent_sales - previous_sales) / previous_sales) * 100
            insights["insights"].append({
                "type": "sales_trend",
                "title": "Weekly Sales Trend",
                "description": f"Sales {'increased' if growth > 0 else 'decreased'} by {abs(growth):.1f}% compared to previous week",
                "impact": "high" if abs(growth) > 10 else "medium",
                "action": "Investigate factors" if growth < -10 else "Maintain momentum" if growth > 10 else "Monitor closely"
            })
        
        # Inventory insights
        low_stock_count = self.db.query(Product).filter(
            Product.stock_level <= Product.reorder_point
        ).count()
        
        if low_stock_count > 0:
            insights["insights"].append({
                "type": "inventory_alert",
                "title": "Low Stock Alert",
                "description": f"{low_stock_count} products are at or below reorder point",
                "impact": "high",
                "action": "Review reorder recommendations immediately"
            })
        
        # Customer insights
        at_risk_customers = []
        top_customers = self.db.query(Customer).limit(20).all()
        
        for customer in top_customers:
            churn_pred = self.predict_churn(customer.id)
            if churn_pred.get('risk_level') == 'high':
                at_risk_customers.append(customer.name)
        
        if at_risk_customers:
            insights["insights"].append({
                "type": "customer_retention",
                "title": "Customer Retention Alert",
                "description": f"{len(at_risk_customers)} high-value customers at risk of churning",
                "impact": "high",
                "action": "Launch retention campaign with personalized offers"
            })
        
        return insights
