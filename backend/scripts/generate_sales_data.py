#!/usr/bin/env python3
"""
18-Month Sales Data Generator for ERIS Retail Intelligence System

Generates realistic sales transactions for 18 months to support forecasting model training and testing.
Creates sales data with seasonal patterns, holidays, and realistic business variations.
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Dict, Any
from dotenv import load_dotenv

# SQLAlchemy imports
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.sql import select, insert

# Load environment variables
load_dotenv()

# Constants (same as main generator)
FESTIVALS = [
    {"name": "Diwali", "month": 10, "day": 20, "duration": 5, "categories": ["Snacks", "Personal Care", "Cleaning"]},
    {"name": "Holi", "month": 3, "day": 10, "duration": 2, "categories": ["Beverages", "Snacks"]},
    {"name": "Eid", "month": 4, "day": 15, "duration": 3, "categories": ["Snacks", "Staples"]},
    {"name": "Christmas", "month": 12, "day": 25, "duration": 2, "categories": ["Bakery", "Beverages"]},
    {"name": "New Year", "month": 1, "day": 1, "duration": 1, "categories": ["Beverages", "Snacks"]},
    {"name": "Republic Day", "month": 1, "day": 26, "duration": 1, "categories": ["Snacks"]},
    {"name": "Independence Day", "month": 8, "day": 15, "duration": 1, "categories": ["Beverages", "Snacks"]},
    {"name": "Ganesh Chaturthi", "month": 9, "day": 10, "duration": 10, "categories": ["Snacks", "Beverages"]},
    {"name": "Durga Puja", "month": 10, "day": 5, "duration": 5, "categories": ["Snacks", "Personal Care"]}
]

PAYMENT_METHODS = ["CASH", "CARD", "UPI", "CHEQUE", "BANK_TRANSFER", "WALLET"]
PAYMENT_STATUSES = ["PENDING", "COMPLETED", "FAILED", "REFUNDED", "PARTIAL"]
SALE_STATUSES = ["INITIATED", "COMPLETED", "CANCELLED", "RETURNED"]
PRODUCT_CATEGORIES = {
    "Beverages": ["Coca Cola 500ml", "Pepsi 500ml", "Sprite 500ml", "Fanta Orange 500ml", "Thums Up 500ml"],
    "Snacks": ["Lay's Classic Salted", "Lay's Cream & Onion", "Lay's Magic Masala", "Doritos Nacho Cheese", "Cheetos Puffs"],
    "Dairy": ["Amul Milk 500ml", "Amul Cheese 200g", "Amul Butter 100g", "Mother Dairy Yogurt 400g", "Nestle Yogurt 100g"],
    "Bakery": ["Britannia Bread White", "Britannia Bread Brown", "Britannia Cake Pineapple", "Britannia Marie Gold", "Britannia Good Day"],
    "Personal Care": ["Colgate Toothpaste", "Pepsodent Toothpaste", "Close Up Toothpaste", "Himalaya Neem Face Wash", "Fair & Lovely Cream"],
    "Cleaning": ["Surf Excel Detergent", "Ariel Detergent", "Tide Detergent", "Vim Dishwash", "Pril Dishwash"],
    "Frozen Foods": ["McCain French Fries", "McCain Smiles", "Gits Frozen Peas", "Mother Dairy Ice Cream", "Amul Ice Cream"],
    "Staples": ["India Gate Basmati Rice", "Tata Salt", "Fortune Sunflower Oil", "MDH Garam Masala", "Everest Turmeric"]
}


class SalesDataGenerator:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)

        # Get existing data
        self.products = self.get_products()
        self.outlets = self.get_outlets()
        self.users = self.get_users()

    def get_products(self):
        """Get all products from database"""
        with self.engine.connect() as conn:
            result = conn.execute(select(self.metadata.tables['products']))
            return [dict(row._mapping) for row in result]

    def get_outlets(self):
        """Get all outlets from database"""
        with self.engine.connect() as conn:
            result = conn.execute(select(self.metadata.tables['outlets']))
            return [dict(row._mapping) for row in result]

    def get_users(self):
        """Get all users from database"""
        with self.engine.connect() as conn:
            result = conn.execute(select(self.metadata.tables['users']))
            return [dict(row._mapping) for row in result]

    def get_sales_multiplier(self, sale_date: date, category: str) -> float:
        """Calculate sales multiplier based on date and category"""
        multiplier = 1.0

        # Weekend multiplier
        if sale_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            multiplier *= 1.3

        # Holiday/festival multiplier
        for festival in FESTIVALS:
            festival_date = date(sale_date.year, festival['month'], festival['day'])
            if abs((sale_date - festival_date).days) <= festival['duration'] // 2:
                if category in festival['categories']:
                    multiplier *= random.uniform(1.5, 1.8)
                break

        # Seasonal effects
        month = sale_date.month
        if month in [12, 1, 2]:  # Winter
            if category == "Beverages":
                multiplier *= 1.2  # Hot drinks
        elif month in [3, 4, 5]:  # Summer
            if category == "Beverages":
                multiplier *= 1.4  # Cold drinks boost
        elif month in [6, 7, 8, 9]:  # Monsoon
            multiplier *= 0.8  # Reduced footfall

        # Economic factors (slight random variation)
        economic_factor = random.uniform(0.9, 1.1)
        multiplier *= economic_factor

        return multiplier

    def generate_sales_for_date(self, sale_date: date) -> List[Dict]:
        """Generate sales transactions for a specific date"""
        sales_data = []
        sale_id = 1

        for outlet in self.outlets:
            outlet_id = outlet['id']

            # Base transactions per day per outlet: 50-200 (scaled for realistic retail)
            base_transactions = random.randint(50, 200)

            # Adjust for day of week and season
            day_multiplier = 1.0
            if sale_date.weekday() >= 5:  # Weekend
                day_multiplier = 1.4
            elif sale_date.weekday() == 0:  # Monday (post-weekend recovery)
                day_multiplier = 0.9

            transactions = int(base_transactions * day_multiplier)
            sale_sequence = 1

            for _ in range(transactions):
                # Select random product
                product = random.choice(self.products)
                category_name = None

                # Find category name (this is simplified - in real implementation would join with categories table)
                for cat_name, products in PRODUCT_CATEGORIES.items():
                    if product['name'] in products:
                        category_name = cat_name
                        break

                if not category_name:
                    category_name = "General"

                # Get sales multiplier
                multiplier = self.get_sales_multiplier(sale_date, category_name)

                # Adjust quantity based on multiplier
                base_quantity = random.randint(1, 5)
                quantity = max(1, int(base_quantity * multiplier))

                # Calculate amounts
                unit_price = float(product['selling_price'])
                subtotal = quantity * unit_price
                tax_amount = subtotal * 0.18  # 18% GST
                discount_amount = random.uniform(0, subtotal * 0.1)  # Up to 10% discount
                total_amount = subtotal + tax_amount - discount_amount

                # Select random user for this outlet
                outlet_users = [u for u in self.users if u.get('outlet_id') == outlet_id]
                if outlet_users:
                    user_id = random.choice(outlet_users)['id']
                else:
                    user_id = None

                # Generate sale number with a deterministic sequence to ensure uniqueness
                sale_number = f"SAL-{sale_date.strftime('%Y%m%d')}-{outlet_id:03d}-{sale_sequence:04d}"
                sale_sequence += 1

                sales_data.append({
                    'outlet_id': outlet_id,
                    'user_id': user_id,
                    'customer_id': None,  # Anonymous sales
                    'sale_number': sale_number,
                    'subtotal': Decimal(str(round(subtotal, 2))),
                    'tax_amount': Decimal(str(round(tax_amount, 2))),
                    'discount_amount': Decimal(str(round(discount_amount, 2))),
                    'total_amount': Decimal(str(round(total_amount, 2))),
                    'payment_method': random.choice(PAYMENT_METHODS),
                    'payment_status': 'COMPLETED',
                    'amount_paid': Decimal(str(round(total_amount, 2))),
                    'status': 'COMPLETED',
                    'notes': None,
                    'sale_date': datetime.combine(sale_date, datetime.min.time()) + timedelta(
                        hours=random.randint(9, 21),  # Business hours
                        minutes=random.randint(0, 59)
                    ),
                    'created_at': datetime.combine(sale_date, datetime.min.time()) + timedelta(
                        hours=random.randint(9, 21),
                        minutes=random.randint(0, 59)
                    ),
                    'updated_at': datetime.combine(sale_date, datetime.min.time()) + timedelta(
                        hours=random.randint(9, 21),
                        minutes=random.randint(0, 59)
                    )
                })

        return sales_data

    def generate_18_months_sales(self):
        """Generate sales data for 18 months"""
        print("💰 Generating 18 months of sales data...")

        # Calculate exact date range: 18 months = 540 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=539)  # inclusive range gives exactly 540 days

        all_sales_data = []
        current_date = start_date

        while current_date <= end_date:
            daily_sales = self.generate_sales_for_date(current_date)
            all_sales_data.extend(daily_sales)

            # Progress indicator
            days_processed = (current_date - start_date).days + 1
            total_days = (end_date - start_date).days + 1
            if days_processed % 30 == 0 or days_processed == total_days:
                print(f"📅 Processed {days_processed}/{total_days} days ({len(all_sales_data)} transactions so far)")

            current_date += timedelta(days=1)

        # Insert in batches to avoid memory issues
        batch_size = 1000
        with self.engine.connect() as conn:
            for i in range(0, len(all_sales_data), batch_size):
                batch = all_sales_data[i:i+batch_size]
                conn.execute(insert(self.metadata.tables['sales']), batch)
                print(f"💰 Inserted sales batch {i//batch_size + 1}/{(len(all_sales_data)-1)//batch_size + 1}")
            conn.commit()

        print(f"✅ Generated {len(all_sales_data)} sales transactions over 18 months")
        return all_sales_data


def main():
    parser = argparse.ArgumentParser(description='Generate 18 months of sales data for ERIS forecasting')
    args = parser.parse_args()

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not found")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)

    try:
        generator = SalesDataGenerator(database_url)
        sales_data = generator.generate_18_months_sales()

        print("\n🎉 Sales data generation complete!")
        print(f"📊 Total transactions: {len(sales_data)}")
        print(f"📅 Date range: 18 months back from {datetime.now().date()}")

    except Exception as e:
        print(f"❌ Error during sales data generation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()