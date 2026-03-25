"""
Enterprise Retail Intelligence System v3.0
MOCK DATA GENERATOR (Python version)

Realistic synthetic data generation for API responses.
Python port of src/lib/mockData.js
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict

def generate_demand_data(days: int = 90) -> List[Dict]:
    """Generate realistic demand data with seasonal patterns."""
    data = []
    today = datetime.now()
    baseline_daily = 50000  # ₹50,000 baseline daily sales
    
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        day_of_week = date.weekday()
        day_of_year = date.timetuple().tm_yday
        
        # Seasonal patterns
        weekend_boost = 1.3 if day_of_week >= 5 else 1.0
        monthly_trend = 1 + (np.sin(day_of_year / 30) * 0.15)
        seasonal_pattern = 1 + (np.sin(2 * np.pi * day_of_year / 365) * 0.2)
        
        # Random events (5% chance)
        has_event = np.random.random() < 0.05
        event_multiplier = (1.5 + np.random.random() * 0.5) if has_event else 1.0
        
        # Market noise
        noise = 1 + (np.random.random() - 0.5) * 0.1
        
        # Calculate final sales
        sales = round(
            baseline_daily *
            weekend_boost *
            monthly_trend *
            seasonal_pattern *
            event_multiplier *
            noise
        )
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'sales': sales,
            'orders': round(sales / 250),
            'customers': round(sales / 500),
            'hasEvent': has_event
        })
    
    return data

def generate_forecast_data(historical_data: List[Dict], forecast_days: int = 30) -> List[Dict]:
    """Generate AI-powered forecast data."""
    if not historical_data:
        return []
    
    # Calculate  trend
    recent_avg = sum(d['sales'] for d in historical_data[-7:]) / 7
    trend = (historical_data[-1]['sales'] - historical_data[0]['sales']) / len(historical_data)
    
    last_date = datetime.strptime(historical_data[-1]['date'], '%Y-%m-%d')
    
    forecast = []
    for i in range(1, forecast_days + 1):
        forecast_date = last_date + timedelta(days=i)
        day_of_week = forecast_date.weekday()
        weekend_boost = 1.3 if day_of_week >= 5 else 1.0
        
        # Predicted sales
        predicted = round((recent_avg + (trend * i)) * weekend_boost)
        
        # Confidence intervals
        uncertainty_factor = 1 + (i / forecast_days) * 0.3
        lower_bound = round(predicted * (1 - 0.1 * uncertainty_factor))
        upper_bound = round(predicted * (1 + 0.1 * uncertainty_factor))
        
        forecast.append({
            'date': forecast_date.strftime('%Y-%m-%d'),
            'predicted': predicted,
            'lowerBound': lower_bound,
            'upperBound': upper_bound,
            'confidence': round((1 - (i / forecast_days) * 0.3) * 100)
        })
    
    return forecast

def generate_inventory_data(product_count: int = 20) -> List[Dict]:
    """Generate inventory data with stockout risks."""
    categories = ['Groceries', 'Electronics', 'Clothing', 'Home & Kitchen', 'Beauty']
    inventory = []
    
    for i in range(1, product_count + 1):
        category = np.random.choice(categories)
        current_stock = np.random.randint(0, 500)
        daily_consumption = 10 + np.random.randint(0, 40)
        days_to_stockout = int(current_stock / daily_consumption) if daily_consumption > 0 else 999
        
        # Determine status
        if days_to_stockout < 7:
            status = 'critical'
            severity = 'critical'
        elif days_to_stockout < 14:
            status = 'warning'
            severity = 'warning'
        else:
            status = 'healthy'
            severity = 'success'
        
        inventory.append({
            'id': f'PROD_{i:03d}',
            'name': f'Product {i}',
            'category': category,
            'currentStock': current_stock,
            'reorderPoint': daily_consumption * 14,
            'dailyConsumption': daily_consumption,
            'daysToStockout': days_to_stockout,
            'status': status,
            'severity': severity,
            'lastRestocked': (datetime.now() - timedelta(days=np.random.randint(1, 30))).strftime('%Y-%m-%d')
        })
    
    return sorted(inventory, key=lambda x: x['daysToStockout'])

def generate_alerts(inventory_data: List[Dict], demand_data: List[Dict]) -> List[Dict]:
    """Generate actionable alerts."""
    alerts = []
    
    # Stockout alerts
    critical_items = [item for item in inventory_data if item['daysToStockout'] < 7]
    warning_items = [item for item in inventory_data if 7 <= item['daysToStockout'] < 14]
    
    for item in critical_items:
        alerts.append({
            'id': f"alert_{item['id']}_stockout",
            'type': 'stockout',
            'severity': 'critical',
            'productId': item['id'],
            'productName': item['name'],
            'message': f"Critical: {item['name']} will run out in {item['daysToStockout']} days",
            'recommendation': f"Order {item['reorderPoint'] * 2} units immediately",
            'daysToStockout': item['daysToStockout'],
            'timestamp': datetime.now().isoformat()
        })
    
    for item in warning_items:
        alerts.append({
            'id': f"alert_{item['id']}_low",
            'type': 'low_stock',
            'severity': 'warning',
            'productId': item['id'],
            'productName': item['name'],
            'message': f"Warning: {item['name']} stock running low ({item['daysToStockout']} days remaining)",
            'recommendation': f"Plan reorder of {item['reorderPoint']} units",
            'daysToStockout': item['daysToStockout'],
            'timestamp': datetime.now().isoformat()
        })
    
    # Demand spike alerts
    if demand_data and len(demand_data) >= 14:
        recent_sales = sum(d['sales'] for d in demand_data[-7:]) / 7
        previous_sales = sum(d['sales'] for d in demand_data[-14:-7]) / 7
        growth_rate = ((recent_sales - previous_sales) / previous_sales) * 100
        
        if growth_rate > 30:
            alerts.append({
                'id': 'alert_demand_spike',
                'type': 'demand_spike',
                'severity': 'info',
                'message': f"Demand spike detected: {growth_rate:.1f}% increase over last week",
                'recommendation': 'Review inventory levels and prepare for increased orders',
                'growthRate': growth_rate,
                'timestamp': datetime.now().isoformat()
            })
    
    return alerts

def calculate_metrics(demand_data: List[Dict], inventory_data: List[Dict]) -> Dict:
    """Calculate key performance metrics."""
    if not demand_data:
        return {
            'totalRevenue': 0,
            'avgDailySales': 0,
            'totalOrders': 0,
            'totalCustomers': 0,
            'inventoryValue': 0,
            'stockoutRisk': 0,
            'growthRate': 0
        }
    
    # Revenue metrics
    total_revenue = sum(d['sales'] for d in demand_data)
    avg_daily_sales = total_revenue / len(demand_data)
    total_orders = sum(d['orders'] for d in demand_data)
    total_customers = sum(d['customers'] for d in demand_data)
    
    # Growth rate
    if len(demand_data) >= 14:
        recent_revenue = sum(d['sales'] for d in demand_data[-7:])
        previous_revenue = sum(d['sales'] for d in demand_data[-14:-7])
        growth_rate = ((recent_revenue - previous_revenue) / previous_revenue) * 100 if previous_revenue > 0 else 0
    else:
        growth_rate = 0
    
    # Inventory metrics
    inventory_value = sum(item['currentStock'] * 100 for item in inventory_data) if inventory_data else 0
    critical_items = len([item for item in inventory_data if item['daysToStockout'] < 7]) if inventory_data else 0
    stockout_risk = (critical_items / len(inventory_data)) * 100 if inventory_data else 0
    
    return {
        'totalRevenue': total_revenue,
        'avgDailySales': round(avg_daily_sales),
        'totalOrders': total_orders,
        'totalCustomers': total_customers,
        'inventoryValue': inventory_value,
        'stockoutRisk': round(stockout_risk),
        'growthRate': round(growth_rate, 1)
    }
