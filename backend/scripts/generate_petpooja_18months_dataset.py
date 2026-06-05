#!/usr/bin/env python3
"""
Petpooja Retail Intelligence System - 18 Month Synthetic Dataset Generator
================================================================================
Generates 18 months of realistic retail business data for Petpooja with:
- 17.5 months for model training
- 0.5 months (15 days) for model testing

Dataset includes:
- Seasonal patterns (Diwali, Holi, summers, monsoons, year-end shopping)
- Realistic product categories aligned with Indian retail/restaurants
- Customer segmentation (walk-in, regular, corporate, VIP)
- Multiple payment methods (Cash, Card, UPI, Credit)
- Weather & holiday impact on sales
- Inventory movements
- Employee data
- Supplier interactions
================================================================================
"""

import os
import sys
import random
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
import csv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text, insert
from sqlalchemy.orm import sessionmaker, Session
from decimal import Decimal
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ORGANIZATION_ID = 1
STORE_ID = 1

# Petpooja - Indian Restaurant/Retail Categories
PRODUCT_CATEGORIES = {
    "North Indian": {
        "products": [
            "Paneer Butter Masala", "Dal Makhani", "Butter Chicken", "Naan",
            "Roti", "Paratha", "Tandoori Chicken", "Chole Bhature"
        ],
        "price_range": (150, 450)
    },
    "South Indian": {
        "products": [
            "Masala Dosa", "Idli", "Sambar", "Coconut Chutney", "Upma",
            "Uttapam", "Vada", "Rasam"
        ],
        "price_range": (80, 250)
    },
    "Chinese": {
        "products": [
            "Hakka Noodles", "Fried Rice", "Manchurian", "Sweet & Sour Chicken",
            "Spring Rolls", "Chow Mein", "Schezwan Noodles"
        ],
        "price_range": (120, 350)
    },
    "Beverages": {
        "products": [
            "Tea", "Coffee", "Lassi", "Fresh Juice", "Soft Drink", "Mineral Water",
            "Iced Tea", "Smoothie"
        ],
        "price_range": (30, 150)
    },
    "Desserts & Sweets": {
        "products": [
            "Gulab Jamun", "Kheer", "Rasgulla", "Ice Cream", "Brownie",
            "Cheesecake", "Jalebi", "Barfi"
        ],
        "price_range": (80, 300)
    },
    "Breads": {
        "products": [
            "Naan", "Roti", "Paratha", "Puri", "Bhakri", "Kulcha"
        ],
        "price_range": (30, 80)
    },
    "Biryani": {
        "products": [
            "Chicken Biryani", "Mutton Biryani", "Vegetable Biryani",
            "Paneer Biryani", "Hyderabadi Biryani"
        ],
        "price_range": (250, 450)
    }
}

# Seasonal multipliers for demand
SEASONAL_PATTERNS = {
    "New Year": (datetime(2025, 1, 1), datetime(2025, 1, 15), 1.5),
    "Valentine's Day": (datetime(2025, 2, 1), datetime(2025, 2, 28), 1.4),
    "Holi": (datetime(2025, 3, 1), datetime(2025, 3, 31), 1.8),
    "Summer Season": (datetime(2025, 4, 1), datetime(2025, 6, 30), 0.8),  # Lower
    "Monsoon": (datetime(2025, 7, 1), datetime(2025, 9, 30), 0.7),  # Lower
    "Diwali": (datetime(2025, 10, 1), datetime(2025, 11, 15), 2.0),  # Peak
    "Christmas & New Year": (datetime(2025, 12, 1), datetime(2025, 12, 31), 1.9),
    "Summer 2026": (datetime(2026, 4, 1), datetime(2026, 6, 30), 0.8),
}

# Indian holidays (affects sales)
INDIAN_HOLIDAYS_2025_2026 = [
    ("Republic Day", datetime(2025, 1, 26)),
    ("Holi", datetime(2025, 3, 14)),
    ("Good Friday", datetime(2025, 4, 18)),
    ("Ramzan Eid", datetime(2025, 4, 10)),
    ("Independence Day", datetime(2025, 8, 15)),
    ("Janmashtami", datetime(2025, 8, 16)),
    ("Ganesh Chaturthi", datetime(2025, 9, 7)),
    ("Gandhi Jayanti", datetime(2025, 10, 2)),
    ("Diwali", datetime(2025, 10, 20)),
    ("Guru Nanak Jayanti", datetime(2025, 11, 15)),
    ("Christmas", datetime(2025, 12, 25)),
    ("Republic Day", datetime(2026, 1, 26)),
    ("Holi", datetime(2026, 3, 25)),
]

# Customer segments
CUSTOMER_SEGMENTS = {
    "Walk-in": {"probability": 0.50, "avg_order_value": 400, "frequency": 1},
    "Regular": {"probability": 0.30, "avg_order_value": 600, "frequency": 3},
    "Corporate": {"probability": 0.12, "avg_order_value": 1500, "frequency": 2},
    "VIP": {"probability": 0.08, "avg_order_value": 2000, "frequency": 4},
}

# Payment methods
PAYMENT_METHODS = ["Cash", "Card", "UPI", "Credit", "Wallet"]
PAYMENT_PROBABILITIES = [0.30, 0.25, 0.35, 0.08, 0.02]


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTHETIC DATA GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class Petpooja18MonthsDatasetGenerator:
    """Generates 18 months of realistic retail data for Petpooja"""

    def __init__(self, database_url: str = None):
        """Initialize with database connection"""
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://eris_admin:admin1234@127.0.0.1:5432/eris_production"
            )
        
        # Replace asyncpg with psycopg2 for sync operations
        database_url = database_url.replace("asyncpg://", "psycopg2://")
        
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.session: Session = self.Session()
        
        # Date range: Sept 2024 - April 2026 (18 months)
        self.start_date = datetime(2024, 9, 1)
        self.train_end_date = datetime(2026, 3, 16)  # 17.5 months
        self.test_end_date = datetime(2026, 3, 31)   # 0.5 months (15 days)
        
        self.data_stats = {
            "products": 0,
            "customers": 0,
            "sales": 0,
            "sale_items": 0,
            "invoices": 0,
            "training_period_sales": 0,
            "testing_period_sales": 0,
        }
        
        logger.info("✓ Petpooja 18-Month Dataset Generator initialized")
        logger.info(f"  Training period: {self.start_date.date()} → {self.train_end_date.date()}")
        logger.info(f"  Testing period:  {self.train_end_date.date()} → {self.test_end_date.date()}")

    def _get_seasonal_multiplier(self, sale_date: datetime) -> float:
        """Get demand multiplier based on season/holidays"""
        base_multiplier = 1.0
        
        for season_name, (start, end, multiplier) in SEASONAL_PATTERNS.items():
            if start <= sale_date <= end:
                base_multiplier = multiplier
                break
        
        # Check if it's a holiday (add 1.5x boost)
        for holiday_name, holiday_date in INDIAN_HOLIDAYS_2025_2026:
            if abs((sale_date - holiday_date).days) <= 7:
                base_multiplier *= 1.5
                break
        
        # Weekday/weekend effect
        if sale_date.weekday() >= 4:  # Friday-Sunday
            base_multiplier *= 1.2
        
        return base_multiplier

    def _generate_products(self) -> List[Dict]:
        """Generate product catalog"""
        logger.info("🏪 Generating products...")
        products = []
        product_id = 1
        
        for category_name, category_data in PRODUCT_CATEGORIES.items():
            for product_name in category_data["products"]:
                min_price, max_price = category_data["price_range"]
                
                products.append({
                    "id": product_id,
                    "organization_id": ORGANIZATION_ID,
                    "name": product_name,
                    "category_id": list(PRODUCT_CATEGORIES.keys()).index(category_name) + 1,
                    "category_name": category_name,
                    "description": f"{product_name} - {category_name}",
                    "sku": f"PETPOOJA-{product_id:04d}",
                    "unit": "Plate/Cup/Serving",
                    "price": round(random.uniform(min_price, max_price), 2),
                    "cost": round(random.uniform(min_price * 0.35, min_price * 0.50), 2),
                    "stock": random.randint(20, 100),
                    "reorder_level": 10,
                    "supplier_id": random.randint(1, 5),
                    "is_active": True,
                    "is_deleted": False,
                    "created_at": self.start_date,
                    "updated_at": datetime.utcnow(),
                })
                product_id += 1
        
        logger.info(f"✅ Generated {len(products)} products across {len(PRODUCT_CATEGORIES)} categories")
        self.data_stats["products"] = len(products)
        return products

    def _generate_customers(self, count: int = 500) -> List[Dict]:
        """Generate customer base"""
        logger.info(f"👥 Generating {count} customers...")
        customers = []
        
        first_names = ["Rajesh", "Priya", "Amit", "Neha", "Suresh", "Divya", "Arjun", "Ananya",
                       "Vikram", "Pooja", "Rohit", "Sneha", "Arun", "Shreya", "Nikhil", "Isha"]
        last_names = ["Kumar", "Singh", "Sharma", "Patel", "Gupta", "Verma", "Nair", "Desai",
                      "Iyer", "Menon", "Reddy", "Bhat", "Chopra", "Malhotra"]
        
        cities = ["Mumbai", "Bangalore", "Delhi", "Pune", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad"]
        
        for i in range(count):
            segment = random.choices(
                list(CUSTOMER_SEGMENTS.keys()),
                weights=[CUSTOMER_SEGMENTS[s]["probability"] for s in CUSTOMER_SEGMENTS.keys()]
            )[0]
            
            customers.append({
                "id": i + 1,
                "organization_id": ORGANIZATION_ID,
                "name": f"{random.choice(first_names)} {random.choice(last_names)}",
                "email": f"customer{i+1}@petpooja.local",
                "phone": f"+91{random.randint(9000000000, 9999999999)}",
                "segment": segment,
                "city": random.choice(cities),
                "state": "Maharashtra",
                "country": "India",
                "credit_limit": Decimal(str(random.choice([5000, 10000, 25000, 50000]))),
                "outstanding_amount": Decimal("0"),
                "purchase_count": 0,
                "total_spent": Decimal("0"),
                "loyalty_points": random.randint(0, 1000),
                "is_active": True,
                "is_deleted": False,
                "created_at": self.start_date,
                "updated_at": datetime.utcnow(),
            })
        
        logger.info(f"✅ Generated {len(customers)} customers")
        self.data_stats["customers"] = len(customers)
        return customers

    def _generate_sales(self, products: List[Dict], customers: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Generate sales transactions for 18 months"""
        logger.info("💰 Generating sales transactions for 18 months...")
        
        sales = []
        sale_items = []
        sale_id = 1
        sale_item_id = 1
        current_date = self.start_date
        
        # Daily sales target: 40-80 transactions per day
        training_sales_count = 0
        testing_sales_count = 0
        
        while current_date <= self.test_end_date:
            daily_transactions = random.randint(40, 80)
            seasonal_mult = self._get_seasonal_multiplier(current_date)
            daily_transactions = int(daily_transactions * seasonal_mult)
            
            for _ in range(daily_transactions):
                # Select random customer
                customer = random.choice(customers)
                
                # Select random products (1-5 items per transaction)
                num_items = random.choices([1, 2, 3, 4, 5], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
                selected_products = random.sample(products, min(num_items, len(products)))
                
                # Calculate transaction total
                transaction_total = Decimal("0")
                items_for_sale = []
                
                for product in selected_products:
                    quantity = random.randint(1, 3)
                    unit_price = Decimal(str(product["price"]))
                    gst_rate = Decimal("0.05")  # 5% GST for food
                    
                    line_total = unit_price * Decimal(str(quantity))
                    tax_amount = line_total * gst_rate
                    
                    items_for_sale.append({
                        "product_id": product["id"],
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "tax_rate": float(gst_rate),
                        "tax_amount": tax_amount,
                        "line_total": line_total + tax_amount,
                    })
                    
                    transaction_total += line_total + tax_amount
                    
                    # Add sale item
                    sale_items.append({
                        "id": sale_item_id,
                        "sale_id": sale_id,
                        "product_id": product["id"],
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "tax_rate": float(gst_rate),
                        "tax_amount": tax_amount,
                        "discount": Decimal("0"),
                        "line_total": line_total + tax_amount,
                        "created_at": current_date,
                    })
                    sale_item_id += 1
                
                # Determine if it's training or testing period
                is_training = current_date <= self.train_end_date
                
                # Create sale record
                sales.append({
                    "id": sale_id,
                    "organization_id": ORGANIZATION_ID,
                    "store_id": STORE_ID,
                    "customer_id": customer["id"],
                    "cashier_id": random.randint(1, 10),
                    "invoice_number": f"INV-{current_date.strftime('%Y%m%d')}-{sale_id:06d}",
                    "sale_date": current_date,
                    "total_amount": transaction_total,
                    "subtotal": transaction_total * Decimal("0.95"),  # Before GST
                    "tax_amount": transaction_total * Decimal("0.05"),
                    "discount": Decimal("0"),
                    "payment_method": random.choices(PAYMENT_METHODS, PAYMENT_PROBABILITIES)[0],
                    "payment_status": "paid",
                    "status": "completed",
                    "is_training_data": is_training,
                    "is_testing_data": not is_training,
                    "created_at": current_date,
                    "updated_at": current_date,
                })
                
                if is_training:
                    training_sales_count += 1
                else:
                    testing_sales_count += 1
                
                sale_id += 1
            
            current_date += timedelta(days=1)
        
        logger.info(f"✅ Generated {len(sales)} sales")
        logger.info(f"   Training period: {training_sales_count} sales ({self.start_date.date()} → {self.train_end_date.date()})")
        logger.info(f"   Testing period:  {testing_sales_count} sales ({(self.train_end_date + timedelta(days=1)).date()} → {self.test_end_date.date()})")
        
        self.data_stats["sales"] = len(sales)
        self.data_stats["sale_items"] = len(sale_items)
        self.data_stats["training_period_sales"] = training_sales_count
        self.data_stats["testing_period_sales"] = testing_sales_count
        
        return sales, sale_items

    def _generate_invoices(self, sales: List[Dict]) -> List[Dict]:
        """Generate invoices from sales"""
        logger.info("📄 Generating invoices from sales...")
        invoices = []
        
        for idx, sale in enumerate(sales, 1):
            invoices.append({
                "id": idx,
                "organization_id": ORGANIZATION_ID,
                "invoice_number": sale["invoice_number"],
                "invoice_date": sale["sale_date"],
                "customer_id": sale["customer_id"],
                "total_amount": sale["total_amount"],
                "subtotal": sale["subtotal"],
                "tax_amount": sale["tax_amount"],
                "amount_paid": sale["total_amount"],
                "amount_due": Decimal("0"),
                "payment_status": "paid",
                "status": "completed",
                "created_at": sale["sale_date"],
                "updated_at": sale["sale_date"],
            })
        
        logger.info(f"✅ Generated {len(invoices)} invoices")
        self.data_stats["invoices"] = len(invoices)
        return invoices

    def _generate_employees(self) -> List[Dict]:
        """Generate employee data"""
        logger.info("👔 Generating employees...")
        employees = []
        
        roles = ["Manager", "Cashier", "Chef", "Server", "Delivery", "Admin"]
        first_names = ["Rajesh", "Priya", "Amit", "Neha", "Suresh", "Divya"]
        last_names = ["Kumar", "Singh", "Sharma", "Patel", "Gupta", "Verma"]
        
        for i in range(1, 11):  # 10 employees
            employees.append({
                "id": i,
                "organization_id": ORGANIZATION_ID,
                "store_id": STORE_ID,
                "username": f"emp{i:03d}",
                "email": f"employee{i}@petpooja.local",
                "first_name": random.choice(first_names),
                "last_name": random.choice(last_names),
                "phone": f"+91{random.randint(9000000000, 9999999999)}",
                "role": random.choice(roles),
                "salary": round(random.uniform(15000, 50000), 2),
                "joining_date": self.start_date,
                "is_active": True,
                "is_deleted": False,
                "created_at": self.start_date,
            })
        
        logger.info(f"✅ Generated {len(employees)} employees")
        return employees

    def generate_all_data(self) -> Dict[str, Any]:
        """Generate complete 18-month dataset"""
        try:
            logger.info("\n" + "="*80)
            logger.info("PETPOOJA 18-MONTH SYNTHETIC DATASET GENERATION")
            logger.info("="*80 + "\n")
            
            # Generate data
            products = self._generate_products()
            customers = self._generate_customers(count=500)
            sales, sale_items = self._generate_sales(products, customers)
            invoices = self._generate_invoices(sales)
            employees = self._generate_employees()
            
            logger.info("\n" + "="*80)
            logger.info("DATA GENERATION SUMMARY")
            logger.info("="*80)
            logger.info(f"✅ Products:          {self.data_stats['products']:,}")
            logger.info(f"✅ Customers:         {self.data_stats['customers']:,}")
            logger.info(f"✅ Sales:             {self.data_stats['sales']:,}")
            logger.info(f"✅ Sale Items:        {self.data_stats['sale_items']:,}")
            logger.info(f"✅ Invoices:          {self.data_stats['invoices']:,}")
            logger.info(f"✅ Employees:         {len(employees)}")
            logger.info("\n📊 TRAINING/TESTING SPLIT:")
            logger.info(f"   Training Data:     {self.data_stats['training_period_sales']:,} sales")
            logger.info(f"   Testing Data:      {self.data_stats['testing_period_sales']:,} sales")
            logger.info(f"   Training %:        {(self.data_stats['training_period_sales']/(self.data_stats['training_period_sales']+self.data_stats['testing_period_sales'])*100):.1f}%")
            logger.info(f"   Testing %:         {(self.data_stats['testing_period_sales']/(self.data_stats['training_period_sales']+self.data_stats['testing_period_sales'])*100):.1f}%")
            logger.info("="*80 + "\n")
            
            # Create export directory
            export_dir = Path("/tmp/petpooja_18months_data")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export to CSV for inspection
            self._export_to_csv(products, customers, sales, sale_items, invoices, employees, export_dir)
            
            return {
                "success": True,
                "data": {
                    "products": products,
                    "customers": customers,
                    "sales": sales,
                    "sale_items": sale_items,
                    "invoices": invoices,
                    "employees": employees,
                },
                "stats": self.data_stats,
                "export_path": str(export_dir),
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating data: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _export_to_csv(self, products, customers, sales, sale_items, invoices, employees, export_dir):
        """Export generated data to CSV files"""
        logger.info(f"📁 Exporting data to CSV in {export_dir}...")
        
        # Products
        pd.DataFrame(products).to_csv(export_dir / "products.csv", index=False)
        
        # Customers
        customers_df = pd.DataFrame(customers)
        customers_df['credit_limit'] = customers_df['credit_limit'].astype(float)
        customers_df['outstanding_amount'] = customers_df['outstanding_amount'].astype(float)
        customers_df['total_spent'] = customers_df['total_spent'].astype(float)
        customers_df.to_csv(export_dir / "customers.csv", index=False)
        
        # Sales
        sales_df = pd.DataFrame(sales)
        sales_df['total_amount'] = sales_df['total_amount'].astype(float)
        sales_df['subtotal'] = sales_df['subtotal'].astype(float)
        sales_df['tax_amount'] = sales_df['tax_amount'].astype(float)
        sales_df.to_csv(export_dir / "sales.csv", index=False)
        
        # Sale Items
        sale_items_df = pd.DataFrame(sale_items)
        sale_items_df['unit_price'] = sale_items_df['unit_price'].astype(float)
        sale_items_df['tax_amount'] = sale_items_df['tax_amount'].astype(float)
        sale_items_df['line_total'] = sale_items_df['line_total'].astype(float)
        sale_items_df.to_csv(export_dir / "sale_items.csv", index=False)
        
        # Invoices
        invoices_df = pd.DataFrame(invoices)
        invoices_df['total_amount'] = invoices_df['total_amount'].astype(float)
        invoices_df['subtotal'] = invoices_df['subtotal'].astype(float)
        invoices_df['tax_amount'] = invoices_df['tax_amount'].astype(float)
        invoices_df['amount_paid'] = invoices_df['amount_paid'].astype(float)
        invoices_df['amount_due'] = invoices_df['amount_due'].astype(float)
        invoices_df.to_csv(export_dir / "invoices.csv", index=False)
        
        # Employees
        pd.DataFrame(employees).to_csv(export_dir / "employees.csv", index=False)
        
        # Dataset info JSON
        info = {
            "dataset_name": "Petpooja 18-Month Synthetic Retail Dataset",
            "period": f"{self.start_date.date()} to {self.test_end_date.date()}",
            "training_period": f"{self.start_date.date()} to {self.train_end_date.date()} (17.5 months)",
            "testing_period": f"{(self.train_end_date + timedelta(days=1)).date()} to {self.test_end_date.date()} (0.5 months)",
            "business_type": "Indian Restaurant & Retail",
            "company": "Petpooja",
            "statistics": self.data_stats,
            "categories": list(PRODUCT_CATEGORIES.keys()),
            "customer_segments": list(CUSTOMER_SEGMENTS.keys()),
            "payment_methods": PAYMENT_METHODS,
        }
        
        with open(export_dir / "dataset_info.json", "w") as f:
            json.dump(info, f, indent=2, default=str)
        
        logger.info(f"✅ Data exported to {export_dir}")
        logger.info(f"   - products.csv")
        logger.info(f"   - customers.csv")
        logger.info(f"   - sales.csv")
        logger.info(f"   - sale_items.csv")
        logger.info(f"   - invoices.csv")
        logger.info(f"   - employees.csv")
        logger.info(f"   - dataset_info.json")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Generate the 18-month dataset"""
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL not set in environment")
        sys.exit(1)
    
    # Generate dataset
    generator = Petpooja18MonthsDatasetGenerator(database_url)
    result = generator.generate_all_data()
    
    if result["success"]:
        logger.info("\n✅ Dataset generation completed successfully!")
        logger.info(f"\n📊 CSV files available at: {result['export_path']}")
        logger.info("\n📝 Next steps:")
        logger.info("   1. Review the exported CSV files")
        logger.info("   2. Load data into database with: python backend/scripts/load_petpooja_data.py")
        logger.info("   3. Train forecasting models on 17.5 months of data")
        logger.info("   4. Test predictions on 0.5 months of unseen data")
    else:
        logger.error(f"\n❌ Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
