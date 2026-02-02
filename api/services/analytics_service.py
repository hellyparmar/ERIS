"""
Analytics Service for Advanced Analytics Features
Provides business intelligence calculations for the Analytics page
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
from collections import defaultdict

class AnalyticsService:
    """Service for advanced analytics calculations"""
    
    @staticmethod
    def get_category_breakdown(days: int = 30) -> Dict[str, Any]:
        """
        Get sales breakdown by category
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Category breakdown with percentages and totals
        """
        categories = {
            'Electronics': {'sales': 450000, 'orders': 1200, 'color': '#3b82f6'},
            'Groceries': {'sales': 680000, 'orders': 3450, 'color': '#10b981'},
            'Clothing': {'sales': 320000, 'orders': 890, 'color': '#f59e0b'},
            'Home & Kitchen': {'sales': 280000, 'orders': 750, 'color': '#8b5cf6'},
            'Sports': {'sales': 180000, 'orders': 420, 'color': '#ef4444'},
            'Beauty': {'sales': 220000, 'orders': 980, 'color': '#ec4899'},
        }
        
        total_sales = sum(cat['sales'] for cat in categories.values())
        total_orders = sum(cat['orders'] for cat in categories.values())
        
        # Calculate percentages
        breakdown = []
        for name, data in categories.items():
            breakdown.append({
                'name': name,
                'value': data['sales'],
                'orders': data['orders'],
                'percentage': round((data['sales'] / total_sales) * 100, 2),
                'color': data['color']
            })
        
        # Sort by value descending
        breakdown.sort(key=lambda x: x['value'], reverse=True)
        
        return {
            'categories': breakdown,
            'total_sales': total_sales,
            'total_orders': total_orders,
            'period_days': days
        }
    
    @staticmethod
    def get_top_products(limit: int = 10, metric: str = 'revenue') -> List[Dict[str, Any]]:
        """
        Get top performing products
        
        Args:
            limit: Number of products to return
            metric: Sorting metric ('revenue', 'units', 'profit')
            
        Returns:
            List of top products with metrics
        """
        products = [
            {'id': 1, 'name': 'Laptop Pro X1', 'category': 'Electronics', 'revenue': 125000, 'units': 125, 'profit': 25000},
            {'id': 2, 'name': 'Organic Milk 1L', 'category': 'Groceries', 'revenue': 89000, 'units': 4450, 'profit': 12000},
            {'id': 3, 'name': 'Running Shoes Elite', 'category': 'Sports', 'revenue': 78000, 'units': 260, 'profit': 18000},
            {'id': 4, 'name': 'Coffee Maker Deluxe', 'category': 'Home & Kitchen', 'revenue': 65000, 'units': 325, 'profit': 15000},
            {'id': 5, 'name': 'Premium Jeans', 'category': 'Clothing', 'revenue': 62000, 'units': 620, 'profit': 14000},
            {'id': 6, 'name': 'Face Cream SPF50', 'category': 'Beauty', 'revenue': 58000, 'units': 1160, 'profit': 13000},
            {'id': 7, 'name': 'Wireless Mouse', 'category': 'Electronics', 'revenue': 45000, 'units': 1500, 'profit': 9000},
            {'id': 8, 'name': 'Protein Powder', 'category': 'Sports', 'revenue': 42000, 'units': 350, 'profit': 10000},
            {'id': 9, 'name': 'Cotton T-Shirt', 'category': 'Clothing', 'revenue': 38000, 'units': 950, 'profit': 8000},
            {'id': 10, 'name': 'LED Bulbs Pack', 'category': 'Home & Kitchen', 'revenue': 35000, 'units': 700, 'profit': 7000},
            {'id': 11, 'name': 'Rice 5kg Bag', 'category': 'Groceries', 'revenue': 32000, 'units': 1600, 'profit': 5000},
            {'id': 12, 'name': 'Yoga Mat Premium', 'category': 'Sports', 'revenue': 28000, 'units': 280, 'profit': 6500},
        ]
        
        # Sort by specified metric
        if metric == 'units':
            products.sort(key=lambda x: x['units'], reverse=True)
        elif metric == 'profit':
            products.sort(key=lambda x: x['profit'], reverse=True)
        else:  # revenue
            products.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Add ranking and growth
        result = []
        for i, product in enumerate(products[:limit]):
            result.append({
                'rank': i + 1,
                'id': product['id'],
                'name': product['name'],
                'category': product['category'],
                'revenue': product['revenue'],
                'units': product['units'],
                'profit': product['profit'],
                'profit_margin': round((product['profit'] / product['revenue']) * 100, 2),
                'growth': round(random.uniform(-15, 45), 2)  # Simulated growth
            })
        
        return result
    
    @staticmethod
    def get_trend_analysis(days: int = 90) -> Dict[str, Any]:
        """
        Analyze sales trends over time
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Trend analysis data with daily/weekly aggregations
        """
        from datetime import datetime, timedelta
        
        # Generate daily data
        daily_data = []
        base_date = datetime.now() - timedelta(days=days)
        base_value = 40000
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            
            # Add seasonality and trend
            day_of_week = current_date.weekday()
            weekend_factor = 1.3 if day_of_week >= 5 else 1.0
            
            # Weekly cycle
            weekly_factor = 1 + 0.15 * (day_of_week / 7)
            
            # Monthly trend (growing)
            trend_factor = 1 + (i / days) * 0.3
            
            # Random variation
            random_factor = random.uniform(0.85, 1.15)
            
            value = int(base_value * weekend_factor * weekly_factor * trend_factor * random_factor)
            
            daily_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'sales': value,
                'orders': int(value / 250),  # Average order value ~250
                'day_of_week': current_date.strftime('%A')
            })
        
        # Calculate weekly aggregates
        weekly_data = []
        for week_start in range(0, days, 7):
            week_end = min(week_start + 7, days)
            week_sales = sum(d['sales'] for d in daily_data[week_start:week_end])
            week_orders = sum(d['orders'] for d in daily_data[week_start:week_end])
            
            weekly_data.append({
                'week': f"Week {week_start // 7 + 1}",
                'start_date': daily_data[week_start]['date'],
                'sales': week_sales,
                'orders': week_orders,
                'avg_daily': week_sales // (week_end - week_start)
            })
        
        # Calculate trend metrics
        recent_avg = sum(d['sales'] for d in daily_data[-7:]) / 7
        previous_avg = sum(d['sales'] for d in daily_data[-14:-7]) / 7
        trend_change = ((recent_avg - previous_avg) / previous_avg) * 100
        
        return {
            'daily_data': daily_data,
            'weekly_data': weekly_data,
            'metrics': {
                'total_sales': sum(d['sales'] for d in daily_data),
                'total_orders': sum(d['orders'] for d in daily_data),
                'avg_daily_sales': int(sum(d['sales'] for d in daily_data) / days),
                'trend_change': round(trend_change, 2),
                'best_day': max(daily_data, key=lambda x: x['sales']),
                'worst_day': min(daily_data, key=lambda x: x['sales'])
            }
        }

# Singleton instance
analytics_service = AnalyticsService()
