#!/usr/bin/env python3
"""
Synthetic Data Generator for ERIS Retail Intelligence System

Generates realistic synthetic data for all major tables in the ERIS system.
Uses SQLAlchemy Core for high-performance bulk inserts.

Usage:
    python scripts/generate_synthetic_data.py [--reset]

Options:
    --reset    Drop and recreate all tables before inserting
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Dict, Any
import bcrypt
from dotenv import load_dotenv

# SQLAlchemy imports
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, Date, Text, JSON, Numeric, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import select, insert

# Load environment variables
load_dotenv()

# Constants
OUTLETS = [
    {"name": "ERIS Mumbai Central", "city": "Mumbai", "address": "123 MG Road, Bandra West, Mumbai 400050", "manager_name": "Rajesh Kumar"},
    {"name": "ERIS Delhi Plaza", "city": "Delhi", "address": "456 Connaught Place, New Delhi 110001", "manager_name": "Priya Sharma"},
    {"name": "ERIS Bangalore Tech Park", "city": "Bangalore", "address": "789 Brigade Road, Bangalore 560001", "manager_name": "Arun Patel"},
    {"name": "ERIS Ahmedabad Market", "city": "Ahmedabad", "address": "321 Relief Road, Ahmedabad 380001", "manager_name": "Meera Singh"},
    {"name": "ERIS Chennai Marina", "city": "Chennai", "address": "654 Anna Salai, Chennai 600002", "manager_name": "Venkat Raman"}
]

PRODUCT_CATEGORIES = {
    "Beverages": [
        "Coca Cola 500ml", "Pepsi 500ml", "Sprite 500ml", "Fanta Orange 500ml", "Thums Up 500ml",
        "Kinley Water 1L", "Bisleri Water 1L", "Aquafina Water 1L", "Maaza Mango 250ml", "Slice Mango 250ml",
        "Red Bull 250ml", "Monster Energy 500ml", "Tropicana Orange Juice 1L", "Real Fruit Juice 1L", "Paper Boat Aamras 200ml"
    ],
    "Snacks": [
        "Lay's Classic Salted", "Lay's Cream & Onion", "Lay's Magic Masala", "Doritos Nacho Cheese", "Cheetos Puffs",
        "Kurkure Masala Munch", "Kurkure Puffcorn", "Bingo Mad Angles", "Bingo Tedhe Medhe", "Haldiram's Bhujia",
        "Uncle Chipps", "Pringles Original", "Oreo Original", "Hide & Seek", "Parle-G Biscuits"
    ],
    "Dairy": [
        "Amul Milk 500ml", "Amul Cheese 200g", "Amul Butter 100g", "Mother Dairy Yogurt 400g", "Nestle Yogurt 100g",
        "Britannia Cheese Slices", "Go Cheese", "Amul Paneer 200g", "Mother Dairy Paneer 200g", "Gowardhan Paneer 200g"
    ],
    "Bakery": [
        "Britannia Bread White", "Britannia Bread Brown", "Britannia Cake Pineapple", "Britannia Marie Gold", "Britannia Good Day",
        "Sunfeast Yippee Noodles", "Maggi 2-Minute Noodles", "Top Ramen", "Wai Wai Noodles", "Ching's Secret Noodles"
    ],
    "Personal Care": [
        "Colgate Toothpaste", "Pepsodent Toothpaste", "Close Up Toothpaste", "Himalaya Neem Face Wash", "Fair & Lovely Cream",
        "Ponds Powder", "Lakme Lipstick", "Garnier Shampoo", "Head & Shoulders Shampoo", "Clinic Plus Shampoo"
    ],
    "Cleaning": [
        "Surf Excel Detergent", "Ariel Detergent", "Tide Detergent", "Vim Dishwash", "Pril Dishwash",
        "Harpic Toilet Cleaner", "Lizol Floor Cleaner", "Domex Toilet Cleaner", "Colin Glass Cleaner", "Mr. Muscle Cleaner"
    ],
    "Frozen Foods": [
        "McCain French Fries", "McCain Smiles", "Gits Frozen Peas", "Mother Dairy Ice Cream", "Amul Ice Cream",
        "Kwality Walls Kulfi", "Cream Bell Ice Cream", "Vadilal Ice Cream", "Frozen Chicken 500g", "Frozen Fish 500g"
    ],
    "Staples": [
        "India Gate Basmati Rice", "Tata Salt", "Fortune Sunflower Oil", "MDH Garam Masala", "Everest Turmeric",
        "Aashirvaad Atta", "Saffola Oats", "Quaker Oats", "Nestle Milo", "Horlicks Health Drink"
    ]
}

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

PAYMENT_METHODS = ["cash", "card", "upi"]
EMPLOYEE_ROLES = ["cashier", "sales_associate", "stock_clerk", "cleaner", "security"]
SHIFTS = ["morning", "evening", "night"]

class SyntheticDataGenerator:
    def __init__(self, database_url: str, reset: bool = False):
        self.database_url = database_url
        self.reset = reset
        self.sync_database_url = self.database_url.replace(
            'postgresql+asyncpg://', 'postgresql://'
        ) if self.database_url.startswith('postgresql+asyncpg://') else self.database_url
        self.engine = create_engine(self.sync_database_url)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)  # Reflect existing schema

        if reset:
            self.reset_tables()

    def reset_tables(self):
        """Delete existing data from tables"""
        print("🔄 Deleting existing data...")

        # Tables to clear in reverse dependency order
        tables_to_clear = [
            'attendance', 'forecast_results', 'forecast_models', 'audit_logs', 'refresh_tokens',
            'alerts', 'invoices', 'sale_items', 'sales', 'inventory_movements', 'stock_levels',
            'products', 'categories', 'employees', 'suppliers', 'customers', 'user_outlets',
            'outlets', 'users', 'organizations', 'role_permissions', 'roles', 'permissions'
        ]

        with self.engine.connect() as conn:
            for table_name in tables_to_clear:
                if table_name in self.metadata.tables:
                    try:
                        conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
                        print(f"✅ Cleared {table_name}")
                    except Exception as e:
                        print(f"⚠️  Could not clear {table_name}: {e}")
                        conn.rollback()
            conn.commit()

        print("✅ Data deletion complete")





    def generate_organizations(self):
        """Generate organization data first (required for other tables)"""
        print("🏢 Generating organizations...")
        organizations_data = [{
            'id': 1,
            'name': 'ERIS Retail Intelligence System',
            'description': 'Enterprise Retail Intelligence System for comprehensive retail management',
            'is_active': True,
            'is_deleted': False,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }]

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['organizations']), organizations_data)
            conn.commit()

        print("✅ Inserted 1 organization")
        return organizations_data

    def generate_outlets(self):
        """Generate outlet data"""
        print("🏪 Generating outlets...")
        outlets_data = []

        for i, outlet in enumerate(OUTLETS, 1):
            outlets_data.append({
                'id': i,
                'organization_id': 1,  # Reference the organization we just created
                'name': outlet['name'],
                'code': f'OUT{i:03d}',
                'address': outlet['address'],
                'city': outlet['city'],
                'state': 'Maharashtra',  # Assuming Maharashtra for Indian cities
                'country': 'India',
                'postal_code': f'4000{random.randint(10, 99)}',
                'phone': f'+91{random.randint(7000000000, 9999999999)}',
                'email': f'contact.{outlet["city"].lower()}@erisretail.com',
                'opening_time': '09:00:00',
                'closing_time': '21:00:00',
                'is_active': True,
                'is_deleted': False,
                'created_at': datetime.utcnow() - timedelta(days=random.randint(365, 730)),
                'updated_at': datetime.utcnow()
            })

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['outlets']), outlets_data)
            conn.commit()

        print(f"✅ Inserted {len(outlets_data)} outlets")
        return outlets_data

    def generate_roles_and_permissions(self):
        """Generate roles and permissions required for users"""
        print("🔐 Generating roles and permissions...")

        # Basic permissions
        permissions_data = [
            {'id': 1, 'name': 'view_dashboard', 'description': 'View dashboard', 'resource': 'dashboard', 'action': 'view'},
            {'id': 2, 'name': 'manage_users', 'description': 'Manage users', 'resource': 'users', 'action': 'manage'},
            {'id': 3, 'name': 'manage_products', 'description': 'Manage products', 'resource': 'products', 'action': 'manage'},
            {'id': 4, 'name': 'manage_sales', 'description': 'Manage sales', 'resource': 'sales', 'action': 'manage'},
            {'id': 5, 'name': 'view_reports', 'description': 'View reports', 'resource': 'reports', 'action': 'view'},
        ]

        # Roles
        roles_data = [
            {'id': 1, 'name': 'superadmin', 'description': 'Super Administrator', 'is_system_role': True, 'is_active': True, 'is_deleted': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
            {'id': 2, 'name': 'manager', 'description': 'Outlet Manager', 'is_system_role': False, 'is_active': True, 'is_deleted': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
            {'id': 3, 'name': 'staff', 'description': 'Staff Member', 'is_system_role': False, 'is_active': True, 'is_deleted': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        ]

        # Role permissions
        role_permissions_data = [
            {'role_id': 1, 'permission_id': 1},  # superadmin can view dashboard
            {'role_id': 1, 'permission_id': 2},  # superadmin can manage users
            {'role_id': 1, 'permission_id': 3},  # superadmin can manage products
            {'role_id': 1, 'permission_id': 4},  # superadmin can manage sales
            {'role_id': 1, 'permission_id': 5},  # superadmin can view reports
            {'role_id': 2, 'permission_id': 1},  # manager can view dashboard
            {'role_id': 2, 'permission_id': 3},  # manager can manage products
            {'role_id': 2, 'permission_id': 4},  # manager can manage sales
            {'role_id': 2, 'permission_id': 5},  # manager can view reports
            {'role_id': 3, 'permission_id': 1},  # staff can view dashboard
            {'role_id': 3, 'permission_id': 4},  # staff can manage sales
        ]

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['permissions']), permissions_data)
            conn.execute(insert(self.metadata.tables['roles']), roles_data)
            conn.execute(insert(self.metadata.tables['role_permissions']), role_permissions_data)
            conn.commit()

        print("✅ Inserted roles and permissions")
        return roles_data, permissions_data

    def generate_users(self):
        """Generate user data with bcrypt-hashed passwords"""
        print("👥 Generating users...")
        users_data = []
        password_hash = bcrypt.hashpw("Test@1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Superadmin
        users_data.append({
            'id': 1,
            'username': 'superadmin',
            'email': 'admin@erisretail.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'phone': '+919876543210',
            'password_hash': password_hash,
            'role_id': 1,  # superadmin
            'organization_id': 1,
            'is_active': True,
            'is_deleted': False,
            'email_verified': True,
            'last_login': None,
            'created_at': datetime.utcnow() - timedelta(days=730),
            'updated_at': datetime.utcnow(),
            'full_name': 'Super Admin',
            'avatar_url': None,
            'is_superadmin': True,
            'last_login_at': None,
            'failed_logins': 0,
            'locked_until': None,
            'deleted_at': None
        })

        # Outlet managers
        for i, outlet in enumerate(OUTLETS, 1):
            first_name, last_name = outlet['manager_name'].split(' ', 1)
            users_data.append({
                'id': i + 1,
                'username': f'manager_{outlet["city"].lower()}',
                'email': f'manager.{outlet["city"].lower()}@erisretail.com',
                'first_name': first_name,
                'last_name': last_name,
                'phone': f'+91{random.randint(7000000000, 9999999999)}',
                'password_hash': password_hash,
                'role_id': 2,  # manager
                'organization_id': 1,
                'is_active': True,
                'is_deleted': False,
                'email_verified': True,
                'last_login': None,
                'created_at': datetime.utcnow() - timedelta(days=random.randint(180, 365)),
                'updated_at': datetime.utcnow(),
                'full_name': outlet['manager_name'],
                'avatar_url': None,
                'is_superadmin': False,
                'last_login_at': None,
                'failed_logins': 0,
                'locked_until': None,
                'deleted_at': None
            })

        # Staff users
        for i in range(9):
            outlet_id = (i % 5) + 1
            users_data.append({
                'id': i + 7,
                'username': f'staff_{i+1:02d}',
                'email': f'staff{i+1:02d}@erisretail.com',
                'first_name': f'Staff{i+1}',
                'last_name': f'Member{i+1}',
                'phone': f'+91{random.randint(7000000000, 9999999999)}',
                'password_hash': password_hash,
                'role_id': 3,  # staff
                'organization_id': 1,
                'is_active': True,
                'is_deleted': False,
                'email_verified': True,
                'last_login': None,
                'created_at': datetime.utcnow() - timedelta(days=random.randint(30, 180)),
                'updated_at': datetime.utcnow(),
                'full_name': f'Staff{i+1} Member{i+1}',
                'avatar_url': None,
                'is_superadmin': False,
                'last_login_at': None,
                'failed_logins': 0,
                'locked_until': None,
                'deleted_at': None
            })

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['users']), users_data)
            conn.commit()

        print(f"✅ Inserted {len(users_data)} users")
        return users_data

    def generate_products(self):
        """Generate product data"""
        print("📦 Generating products...")
        products_data = []

        for category, product_list in PRODUCT_CATEGORIES.items():
            for product_name in product_list:
                # Generate realistic pricing
                base_price = random.uniform(10, 500)
                cost_price = base_price * random.uniform(0.6, 0.8)
                unit_price = base_price * random.uniform(1.1, 1.3)

                products_data.append({
                    'id': len(products_data) + 1,
                    'organization_id': 1,
                    'category_id': None,  # Will be set after categories are created
                    'sku': f'ERIS-{category[:3].upper()}-{len(products_data)+1:04d}',
                    'name': product_name,
                    'description': f'High-quality {category.lower()} product',
                    'cost_price': Decimal(str(round(cost_price, 2))),
                    'selling_price': Decimal(str(round(unit_price, 2))),
                    'mrp': Decimal(str(round(unit_price * 1.1, 2))),
                    'current_stock': random.randint(50, 200),
                    'reorder_level': random.randint(10, 30),
                    'reorder_quantity': random.randint(20, 50),
                    'unit': 'pieces',
                    'is_perishable': category in ['Dairy', 'Bakery', 'Frozen Foods'],
                    'is_active': True,
                    'is_deleted': False,
                    'created_at': datetime.utcnow() - timedelta(days=random.randint(180, 365)),
                    'updated_at': datetime.utcnow()
                })

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['products']), products_data)
            conn.commit()

        print(f"✅ Inserted {len(products_data)} products")
        return products_data

    def generate_inventory(self, products_data):
        """Generate inventory snapshots for past 180 days"""
        print("📊 Generating inventory data...")
        inventory_data = []
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=180)

        for outlet_id in range(1, 6):  # 5 outlets
            for product in products_data:
                current_quantity = random.randint(product['reorder_level'], 200)

                # Generate daily snapshots
                current_date = start_date
                while current_date <= end_date:
                    # Simulate inventory changes
                    change = random.randint(-10, 15)
                    current_quantity = max(0, current_quantity + change)

                    inventory_data.append({
                        'outlet_id': outlet_id,
                        'product_id': product['product_id'],
                        'quantity': current_quantity,
                        'min_stock_level': product['reorder_level'],
                        'max_stock_level': product['reorder_level'] * 10,
                        'last_updated': datetime.combine(current_date, datetime.min.time())
                    })

                    current_date += timedelta(days=1)

        # Insert in batches
        batch_size = 1000
        with self.engine.connect() as conn:
            for i in range(0, len(inventory_data), batch_size):
                batch = inventory_data[i:i+batch_size]
                conn.execute(insert(self.metadata.tables['stock_levels']), batch)
                print(f"📊 Inserted inventory batch {i//batch_size + 1}/{(len(inventory_data)-1)//batch_size + 1}")
            conn.commit()

        print(f"✅ Inserted {len(inventory_data)} inventory records")
        return inventory_data

    def generate_sales_factors(self):
        """Generate sales factors for past 365 days"""
        print("📈 Generating sales factors...")
        factors_data = []
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=365)

        current_date = start_date
        while current_date <= end_date:
            # Determine if weekend or holiday
            is_weekend = current_date.weekday() >= 5
            is_holiday = False
            festival_name = None
            local_event = None

            # Check for festivals
            for festival in FESTIVALS:
                festival_date = date(current_date.year, festival['month'], festival['day'])
                if abs((current_date - festival_date).days) <= festival['duration'] // 2:
                    is_holiday = True
                    festival_name = festival['name']
                    break

            # Generate weather data (simplified seasonal patterns)
            month = current_date.month
            if month in [12, 1, 2]:  # Winter
                temperature = random.uniform(15, 25)
                rainfall = random.uniform(0, 5)
            elif month in [3, 4, 5]:  # Summer
                temperature = random.uniform(30, 45)
                rainfall = random.uniform(0, 10)
            elif month in [6, 7, 8, 9]:  # Monsoon
                temperature = random.uniform(25, 35)
                rainfall = random.uniform(5, 50)
            else:  # Autumn
                temperature = random.uniform(20, 30)
                rainfall = random.uniform(0, 15)

            # Economic index (market conditions)
            economic_index = random.uniform(0.8, 1.2)

            factors_data.append({
                'date': current_date,
                'is_holiday': is_holiday,
                'is_weekend': is_weekend,
                'temperature_celsius': round(temperature, 1),
                'rainfall_mm': round(rainfall, 1),
                'festival_name': festival_name,
                'local_event': local_event,
                'economic_index': round(economic_index, 2)
            })

            current_date += timedelta(days=1)

        # with self.engine.connect() as conn:
        #     conn.execute(insert(self.metadata.tables['sales_factors']), factors_data)
        #     conn.commit()

        print(f"ℹ️  Skipped sales_factors (table not in schema)")
        return factors_data

    def get_sales_multiplier(self, sale_date: date, category: str, factors_data: List[Dict]) -> float:
        """Calculate sales multiplier based on date and category"""
        multiplier = 1.0

        # Find factors for this date
        factors = next((f for f in factors_data if f['date'] == sale_date), None)
        if not factors:
            return multiplier

        # Weekend multiplier
        if factors['is_weekend']:
            multiplier *= 1.3

        # Holiday/festival multiplier
        if factors['festival_name']:
            festival = next((f for f in FESTIVALS if f['name'] == factors['festival_name']), None)
            if festival and category in festival['categories']:
                multiplier *= random.uniform(1.5, 1.8)

        # Weather effects
        if factors['rainfall_mm'] > 20:  # Heavy rain
            multiplier *= 0.8  # 20% reduction

        # Summer beverage boost
        if sale_date.month in [3, 4, 5] and category == "Beverages":
            multiplier *= 1.4

        # Economic conditions
        multiplier *= factors['economic_index']

        return multiplier

    def generate_sales(self, products_data, factors_data):
        """Generate sales transactions for past 18 months"""
        print("💰 Generating sales transactions...")
        sales_data = []
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=540)  # 18 months

        current_date = start_date
        sale_id = 1

        while current_date <= end_date:
            for outlet_id in range(1, 6):  # 5 outlets
                # Base transactions per day per outlet: 30-120
                base_transactions = random.randint(30, 120)

                for _ in range(base_transactions):
                    # Select random product
                    product = random.choice(products_data)
                    category = product['category']

                    # Get sales multiplier
                    multiplier = self.get_sales_multiplier(current_date, category, factors_data)

                    # Adjust quantity based on multiplier
                    base_quantity = random.randint(1, 5)
                    quantity = max(1, int(base_quantity * multiplier))

                    unit_price = float(product['unit_price'])
                    total_amount = round(quantity * unit_price, 2)

                    sales_data.append({
                        'sale_id': sale_id,
                        'outlet_id': outlet_id,
                        'product_id': product['product_id'],
                        'quantity': quantity,
                        'unit_price': Decimal(str(unit_price)),
                        'total_amount': Decimal(str(total_amount)),
                        'sale_date': datetime.combine(current_date, datetime.min.time()) + timedelta(
                            hours=random.randint(9, 21),  # Business hours
                            minutes=random.randint(0, 59)
                        ),
                        'payment_method': random.choice(PAYMENT_METHODS)
                    })

                    sale_id += 1

            print(f"💰 Generated sales for {current_date}")
            current_date += timedelta(days=1)

        # Insert in batches
        batch_size = 1000
        with self.engine.connect() as conn:
            for i in range(0, len(sales_data), batch_size):
                batch = sales_data[i:i+batch_size]
                conn.execute(insert(self.metadata.tables['sales']), batch)
                print(f"💰 Inserted sales batch {i//batch_size + 1}/{(len(sales_data)-1)//batch_size + 1}")
            conn.commit()

        print(f"✅ Inserted {len(sales_data)} sales transactions")
        return sales_data

    def generate_alerts(self, products_data):
        """Generate sample alerts"""
        print("🚨 Generating alerts...")
        alerts_data = []
        alert_types = ['low_stock', 'overstock', 'expiry_warning']

        for i in range(50):
            outlet_id = random.randint(1, 5)
            product = random.choice(products_data)
            alert_type = random.choice(alert_types)

            if alert_type == 'low_stock':
                threshold = product['reorder_level']
                current = random.randint(0, threshold - 1)
                severity = 'high'
                message = f"Low stock alert: {product['name']} has only {current} units remaining"
            elif alert_type == 'overstock':
                threshold = product['reorder_level'] * 8
                current = random.randint(threshold + 10, threshold + 50)
                severity = 'medium'
                message = f"Overstock alert: {product['name']} has {current} units (threshold: {threshold})"
            else:  # expiry_warning
                threshold = 30  # days
                current = random.randint(1, threshold - 1)
                severity = 'medium'
                message = f"Expiry warning: {product['name']} expires in {current} days"

            alerts_data.append({
                'alert_id': i + 1,
                'outlet_id': outlet_id,
                'product_id': product['product_id'],
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'threshold_value': threshold,
                'current_value': current,
                'is_acknowledged': random.choice([True, False]),
                'created_at': datetime.utcnow() - timedelta(days=random.randint(1, 30))
            })

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['alerts']), alerts_data)
            conn.commit()

        print(f"✅ Inserted {len(alerts_data)} alerts")
        return alerts_data

    def generate_business_contacts(self):
        """Generate supplier/vendor contacts"""
        print("🤝 Generating business contacts...")
        contacts_data = []
        contact_types = ['supplier', 'distributor', 'logistics']

        company_names = [
            "Global Foods Ltd", "Metro Distributors", "Fresh Supply Co", "Prime Logistics", "City Vendors",
            "National Traders", "Regional Supplies", "Bulk Buyers Inc", "Quality Foods", "Express Delivery",
            "Wholesale Mart", "Local Suppliers", "Chain Stores Ltd", "Food Corporation", "Supply Chain Pro",
            "Mega Distributors", "Retail Partners", "Fast Track Logistics", "Premium Vendors", "Market Leaders",
            "Trade Solutions", "Distribution Hub", "Supply Masters", "Vendor Network", "Commerce Connect",
            "Bulk Supplies", "Retail Giants", "Food Chain", "Supply Partners", "Market Distributors"
        ]

        for i in range(30):
            contact_type = random.choice(contact_types)
            categories = random.sample(list(PRODUCT_CATEGORIES.keys()), random.randint(1, 4))

            contacts_data.append({
                'contact_id': i + 1,
                'company_name': company_names[i],
                'contact_person': f"Contact Person {i+1}",
                'phone': f"+91{random.randint(7000000000, 9999999999)}",
                'email': f"contact{i+1}@{company_names[i].lower().replace(' ', '')}.com",
                'gst_number': f"22AAAAA0000A{random.randint(100, 999)}Z{random.randint(1, 9)}",
                'address': f"{random.randint(100, 999)} Business Street, {random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Ahmedabad'])} {random.randint(100000, 999999)}",
                'contact_type': contact_type,
                'product_categories': categories,
                'created_at': datetime.utcnow() - timedelta(days=random.randint(90, 365))
            })

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['suppliers']), contacts_data)
            conn.commit()

        print(f"✅ Inserted {len(contacts_data)} business contacts")
        return contacts_data

    def generate_invoices(self, contacts_data):
        """Generate purchase invoices"""
        print("📄 Generating invoices...")
        invoices_data = []
        statuses = ['paid', 'pending', 'overdue']

        for i in range(200):
            supplier = random.choice([c for c in contacts_data if c['contact_type'] == 'supplier'])
            invoice_date = datetime.utcnow().date() - timedelta(days=random.randint(1, 365))
            due_date = invoice_date + timedelta(days=random.randint(15, 60))

            # Generate invoice items
            num_items = random.randint(3, 12)
            items = []
            total_amount = 0

            for _ in range(num_items):
                quantity = random.randint(10, 100)
                unit_price = random.uniform(50, 1000)
                item_total = quantity * unit_price
                total_amount += item_total

                items.append({
                    'product_name': f'Product {random.randint(1, 120)}',
                    'quantity': quantity,
                    'unit_price': round(unit_price, 2),
                    'total': round(item_total, 2)
                })

            status = random.choice(statuses)
            if status == 'overdue' and due_date < datetime.utcnow().date():
                status = 'overdue'
            elif due_date < datetime.utcnow().date():
                status = random.choice(['paid', 'pending'])

            invoices_data.append({
                'invoice_id': i + 1,
                'supplier_id': supplier['contact_id'],
                'total_amount': Decimal(str(round(total_amount, 2))),
                'items': json.dumps(items),
                'status': status,
                'invoice_date': invoice_date,
                'due_date': due_date,
                'created_at': datetime.combine(invoice_date, datetime.min.time())
            })

        with self.engine.connect() as conn:
            conn.execute(insert(self.invoices_table), invoices_data)
            conn.commit()

        print(f"✅ Inserted {len(invoices_data)} invoices")
        return invoices_data

    def generate_employees(self):
        """Generate employee data"""
        print("👷 Generating employees...")
        employees_data = []

        for i in range(40):
            outlet_id = (i % 5) + 1  # Distribute across 5 outlets
            role = random.choice(EMPLOYEE_ROLES)
            shift = random.choice(SHIFTS)

            # Salary based on role
            if role == 'cashier':
                salary = random.uniform(15000, 25000)
            elif role == 'sales_associate':
                salary = random.uniform(18000, 30000)
            elif role == 'stock_clerk':
                salary = random.uniform(16000, 22000)
            elif role == 'cleaner':
                salary = random.uniform(12000, 18000)
            else:  # security
                salary = random.uniform(14000, 20000)

            joining_date = datetime.utcnow().date() - timedelta(days=random.randint(30, 730))

            employees_data.append({
                'employee_id': i + 1,
                'outlet_id': outlet_id,
                'name': f"Employee {i+1}",
                'role': role,
                'salary': Decimal(str(round(salary, 2))),
                'joining_date': joining_date,
                'shift': shift,
                'is_active': random.choice([True, True, True, False])  # 75% active
            })

        with self.engine.connect() as conn:
            conn.execute(insert(self.employees_table), employees_data)
            conn.commit()

        print(f"✅ Inserted {len(employees_data)} employees")
        return employees_data

    def generate_categories(self):
        """Generate product categories"""
        print("📂 Generating categories...")
        categories_data = []

        for i, category_name in enumerate(PRODUCT_CATEGORIES.keys(), 1):
            categories_data.append({
                'id': i,
                'organization_id': 1,
                'name': category_name,
                'description': f'{category_name} products category',
                'parent_category_id': None,
                'is_active': True,
                'is_deleted': False,
                'created_at': datetime.utcnow() - timedelta(days=365),
                'updated_at': datetime.utcnow()
            })

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['categories']), categories_data)
            conn.commit()

        print(f"✅ Inserted {len(categories_data)} categories")
        return categories_data

    def generate_stock_levels(self, products_data):
        """Generate stock levels for all products across outlets"""
        print("📊 Generating stock levels...")
        stock_data = []

        for outlet_id in range(1, 6):  # 5 outlets
            for product in products_data:
                stock_data.append({
                    'product_id': product['id'],
                    'outlet_id': outlet_id,
                    'quantity': random.randint(20, 150),
                    'reserved_quantity': 0,
                    'available_quantity': random.randint(20, 150),
                    'minimum_level': product['reorder_level'],
                    'maximum_level': product['reorder_level'] * 5,
                    'is_low_stock': False,
                    'last_restocked': datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    'created_at': datetime.utcnow() - timedelta(days=random.randint(30, 180)),
                    'updated_at': datetime.utcnow()
                })

        with self.engine.connect() as conn:
            conn.execute(insert(self.metadata.tables['stock_levels']), stock_data)
            conn.commit()

        print(f"✅ Inserted {len(stock_data)} stock levels")
        return stock_data

    def generate_all_data(self):
        """Generate all synthetic data"""
        print("🚀 Starting synthetic data generation...")

        # Generate data in dependency order
        orgs = self.generate_organizations()
        roles, perms = self.generate_roles_and_permissions()
        outlets = self.generate_outlets()
        users = self.generate_users()
        categories = self.generate_categories()
        products = self.generate_products()
        stock_levels = self.generate_stock_levels(products)
        # Note: Sales generation will be added separately for 18 months

        print("🎉 Synthetic data generation complete!")
        print(f"""
📊 Summary:
- Organizations: {len(orgs)}
- Roles: {len(roles)}
- Permissions: {len(perms)}
- Outlets: {len(outlets)}
- Users: {len(users)}
- Categories: {len(categories)}
- Products: {len(products)}
- Stock Levels: {len(stock_levels)}
        """)


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic data for ERIS Retail System')
    parser.add_argument('--reset', action='store_true', help='Drop and recreate all tables before inserting')
    args = parser.parse_args()

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not found")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)

    try:
        generator = SyntheticDataGenerator(database_url, args.reset)
        generator.generate_all_data()
    except Exception as e:
        print(f"❌ Error during data generation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
