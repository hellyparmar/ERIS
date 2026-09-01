"""
Enterprise Retail Intelligence System v3.0
PETPOOJA RESTAURANT DATA GENERATOR

Generates realistic restaurant/QSR data for Petpooja-style POS system:
- Menu items (Indian cuisine categories)
- Table orders (Dine-in, Takeaway, Delivery)
- Kitchen Order Tickets (KOT)
- Time-based order patterns (lunch/dinner rush)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

class PetpoojaRestaurantDataGenerator:
    """Generate realistic restaurant data for Petpooja POS"""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Indian Restaurant Menu Categories
        self.menu = {
            "Starters": [
                {"name": "Paneer Tikka", "price": 180, "prep_time": 15},
                {"name": "Veg Spring Rolls", "price": 120, "prep_time": 12},
                {"name": "Chicken Wings", "price": 220, "prep_time": 18},
                {"name": "Crispy Corn", "price": 140, "prep_time": 10},
                {"name": "Mushroom Pepper Dry", "price": 160, "prep_time": 12},
            ],
            "Mains": [
                {"name": "Butter Chicken", "price": 280, "prep_time": 20},
                {"name": "Dal Makhani", "price": 180, "prep_time": 15},
                {"name": "Chicken Biryani", "price": 320, "prep_time": 25},
                {"name": "Paneer Butter Masala", "price": 240, "prep_time": 18},
                {"name": "Kadai Chicken", "price": 300, "prep_time": 22},
                {"name": "Veg Biryani", "price": 220, "prep_time": 20},
            ],
            "Breads": [
                {"name": "Butter Naan", "price": 40, "prep_time": 8},
                {"name": "Garlic Naan", "price": 50, "prep_time": 8},
                {"name": "Tandoori Roti", "price": 30, "prep_time": 6},
                {"name": "Laccha Paratha", "price": 60, "prep_time": 10},
            ],
            "Desserts": [
                {"name": "Gulab Jamun", "price": 80, "prep_time": 5},
                {"name": "Ice Cream", "price": 100, "prep_time": 3},
                {"name": "Brownie with Ice Cream", "price": 150, "prep_time": 8},
            ],
            "Beverages": [
                {"name": "Sweet Lassi", "price": 60, "prep_time": 5},
                {"name": "Soft Drink", "price": 40, "prep_time": 2},
                {"name": "Fresh Lime Soda", "price": 50, "prep_time": 5},
                {"name": "Masala Chai", "price": 30, "prep_time": 5},
            ]
        }
        
        # Order types
        self.order_types = ["Dine-in", "Takeaway", "Delivery"]
        
        # Payment methods
        self.payment_methods = ["Cash", "Card", "UPI", "Credit"]
    
    def get_time_multiplier(self, hour: int) -> float:
        """Get order volume multiplier based on time of day"""
        # Lunch rush: 12-2 PM
        if 12 <= hour < 14:
            return 2.5
        # Dinner rush: 7-10 PM
        elif 19 <= hour < 22:
            return 3.0
        # Breakfast: 8-10 AM
        elif 8 <= hour < 10:
            return 1.5
        # Off-peak
        elif 10 <= hour < 12 or 14 <= hour < 19:
            return 1.0
        # Very slow
        else:
            return 0.3
    
    def generate_order(self, order_id: int, timestamp: datetime, status: str = "Completed") -> Dict[str, Any]:
        """Generate a single restaurant order"""
        hour = timestamp.hour
        order_type = random.choice(self.order_types)
        
        # Number of items (more items during rush hours)
        multiplier = self.get_time_multiplier(hour)
        num_items = random.randint(1, int(4 * multiplier))
        
        # Select items from menu
        items = []
        total_amount = 0
        total_prep_time = 0
        
        for _ in range(num_items):
            category = random.choice(list(self.menu.keys()))
            item = random.choice(self.menu[category])
            quantity = random.randint(1, 2)
            
            items.append({
                "category": category,
                "name": item["name"],
                "quantity": quantity,
                "unit_price": item["price"],
                "amount": item["price"] * quantity
            })
            
            total_amount += item["price"] * quantity
            total_prep_time = max(total_prep_time, item["prep_time"])
        
        # Calculate GST (5% for food)
        gst_amount = total_amount * 0.05
        final_amount = total_amount + gst_amount
        
        # Payment method
        payment_method = random.choice(self.payment_methods)
        
        # Table number (for dine-in)
        table_number = random.randint(1, 20) if order_type == "Dine-in" else None
        
        return {
            "order_id": f"ORD{order_id:06d}",
            "timestamp": timestamp.isoformat(),
            "order_type": order_type,
            "table_number": table_number,
            "items": items,
            "subtotal": total_amount,
            "gst_amount": round(gst_amount, 2),
            "total_amount": round(final_amount, 2),
            "payment_method": payment_method,
            "estimated_prep_time": total_prep_time,
            "estimated_prep_time": total_prep_time,
            "status": status
        }
    
    def generate_kot(self, order: Dict[str, Any]) -> str:
        """Generate Kitchen Order Ticket (KOT) format"""
        kot = f"""
╔══════════════════════════════════════╗
║         KITCHEN ORDER TICKET         ║
╠══════════════════════════════════════╣
║ Order: {order['order_id']}                    ║
║ Type: {order['order_type']:<15}            ║
"""
        if order['table_number']:
            kot += f"║ Table: {order['table_number']:<2}                           ║\n"
        
        kot += f"║ Time: {datetime.fromisoformat(order['timestamp']).strftime('%I:%M %p')}                        ║\n"
        kot += "╠══════════════════════════════════════╣\n"
        
        for item in order['items']:
            kot += f"║ {item['quantity']}x {item['name']:<30} ║\n"
        
        kot += f"╠══════════════════════════════════════╣\n"
        kot += f"║ Prep Time: ~{order['estimated_prep_time']} mins              ║\n"
        kot += "╚══════════════════════════════════════╝\n"
        
        return kot
    
    def generate_daily_orders(self, date: datetime, num_orders: int = None) -> List[Dict[str, Any]]:
        """Generate orders for a full day"""
        if num_orders is None:
            # Base orders per day: 80-120
            num_orders = random.randint(80, 120)
        
        orders = []
        
        for i in range(num_orders):
            # Generate random time during operating hours (8 AM - 11 PM)
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            
            timestamp = date.replace(hour=hour, minute=minute, second=0)
            
            order = self.generate_order(i + 1, timestamp)
            orders.append(order)
        
        return sorted(orders, key=lambda x: x['timestamp'])
    
    def generate_invoice(self, order: Dict[str, Any]) -> str:
        """Generate invoice format"""
        invoice = f"""
═══════════════════════════════════════════
        PETPOOJA RESTAURANT
        123 MG Road, Bangalore
        GSTIN: 29ABCDE1234F1Z5
═══════════════════════════════════════════
Invoice: INV/{datetime.now().year}/{order['order_id']}
Date: {datetime.fromisoformat(order['timestamp']).strftime('%d-%b-%Y %I:%M %p')}
Order: {order['order_id']}
Type: {order['order_type']}
"""
        if order['table_number']:
            invoice += f"Table: {order['table_number']}\n"
        
        invoice += "═══════════════════════════════════════════\n"
        invoice += f"{'Item':<25} {'Qty':>3} {'Rate':>8} {'Amount':>8}\n"
        invoice += "───────────────────────────────────────────\n"
        
        for item in order['items']:
            invoice += f"{item['name']:<25} {item['quantity']:>3} {item['unit_price']:>8.2f} {item['amount']:>8.2f}\n"
        
        invoice += "───────────────────────────────────────────\n"
        invoice += f"{'Subtotal:':<37} ₹{order['subtotal']:>8.2f}\n"
        invoice += f"{'GST @ 5%:':<37} ₹{order['gst_amount']:>8.2f}\n"
        invoice += "═══════════════════════════════════════════\n"
        invoice += f"{'TOTAL:':<37} ₹{order['total_amount']:>8.2f}\n"
        invoice += "═══════════════════════════════════════════\n"
        invoice += f"Payment: {order['payment_method']}\n"
        invoice += "\n     Thank you! Visit again!\n"
        invoice += "═══════════════════════════════════════════\n"
        
        return invoice


def main():
    """Demo: Generate sample restaurant data"""
    generator = PetpoojaRestaurantDataGenerator()
    
    # Generate orders for today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    orders = generator.generate_daily_orders(today, num_orders=10)
    
    print(f"Generated {len(orders)} orders for {today.strftime('%d-%b-%Y')}\n")
    
    # Show sample order
    sample_order = orders[0]
    print("Sample Order:")
    print(f"Order ID: {sample_order['order_id']}")
    print(f"Type: {sample_order['order_type']}")
    print(f"Total: ₹{sample_order['total_amount']}")
    print(f"\nItems:")
    for item in sample_order['items']:
        print(f"  - {item['quantity']}x {item['name']} @ ₹{item['unit_price']}")
    
    print("\n" + "="*50)
    print("KOT Format:")
    print(generator.generate_kot(sample_order))
    
    print("="*50)
    print("Invoice Format:")
    print(generator.generate_invoice(sample_order))


if __name__ == "__main__":
    main()
