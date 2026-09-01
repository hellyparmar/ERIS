"""
PetPooja-Style Synthetic Dataset Generator for R-DIOS
Enterprise Retail Intelligence System

Generates 232,744+ rows of realistic Indian retail data:
- 33,000+ products with HSN codes and GST rates
- 99,000+ customers with regional distribution
- 100,000+ sales transactions with seasonality
- Realistic Indian retail patterns (Diwali, Monsoon, etc.)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple
import json
from pathlib import Path

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)

class PetPoojaSyntheticDataGenerator:
    """Generate comprehensive synthetic Indian retail dataset"""
    
    def __init__(self):
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2025, 12, 31)
        
        # Indian Restaurant Menu Categories (PetPooja Context)
        self.product_categories = {
            "North Indian Main Course": {
                "hsn": "2106", "gst_rate": 5,
                "subcategories": ["Paneer Dishes", "Vegetable Curries", "Chicken Curries", "Mutton Delicacies", "Dal & Lentils"],
                "price_range": (240, 650)
            },
            "Indian Breads": {
                "hsn": "1905", "gst_rate": 5,
                "subcategories": ["Roti & Naan", "Parathas", "Kulchas", "Bread Basket"],
                "price_range": (40, 150)
            },
            "Rice & Biryani": {
                "hsn": "1904", "gst_rate": 5,
                "subcategories": ["Biryani", "Pulao", "Fried Rice", "Basmati Specials"],
                "price_range": (200, 550)
            },
            "South Indian": {
                "hsn": "2106", "gst_rate": 5,
                "subcategories": ["Dosa & Idli", "Vada & Snacks", "Thali", "Rice Specials"],
                "price_range": (120, 350)
            },
            "Chinese & Oriental": {
                "hsn": "2106", "gst_rate": 5,
                "subcategories": ["Starters", "Noodles & Rice", "Manchurian & Gravies", "Soups"],
                "price_range": (220, 480)
            },
            "Starters & Appetizers": {
                "hsn": "2106", "gst_rate": 5,
                "subcategories": ["Tandoori Starters", "Kababs", "Crispy Snacks", "Platters"],
                "price_range": (250, 550)
            },
            "Beverages": {
                "hsn": "2202", "gst_rate": 18,
                "subcategories": ["Mocktails", "Soft Drinks", "Lassi & Shakes", "Hot Beverages"],
                "price_range": (80, 250)
            },
            "Desserts": {
                "hsn": "2105", "gst_rate": 18,
                "subcategories": ["Ice Cream", "Indian Sweets", "Cakes & Pastries"],
                "price_range": (150, 350)
            }
        }
        
        # Indian regions with cities (unchanged, but context is now restaurant locations)
        self.regions = {
            "North": {
                "weight": 0.40, # Higher density for North Indian cuisine
                "cities": ["Delhi", "Noida", "Gurgaon", "Chandigarh", "Jaipur", "Lucknow", "Amritsar"]
            },
            "South": {
                "weight": 0.25,
                "cities": ["Bangalore", "Chennai", "Hyderabad", "Kochi", "Coimbatore", "Mysore"]
            },
            "West": {
                "weight": 0.25,
                "cities": ["Mumbai", "Pune", "Ahmedabad", "Surat", "Goa"]
            },
            "East": {
                "weight": 0.10,
                "cities": ["Kolkata", "Bhubaneswar", "Guwahati"]
            }
        }
        
        # Indian festivals and holidays (2024-2025)
        self.festivals = [
            {"name": "Makar Sankranti", "date": "2024-01-15", "boost": 1.25},
            {"name": "Republic Day", "date": "2024-01-26", "boost": 1.15},
            {"name": "Holi", "date": "2024-03-25", "boost": 1.35},
            {"name": "Eid ul-Fitr", "date": "2024-04-11", "boost": 1.30},
            {"name": "Independence Day", "date": "2024-08-15", "boost": 1.20},
            {"name": "Raksha Bandhan", "date": "2024-08-19", "boost": 1.25},
            {"name": "Ganesh Chaturthi", "date": "2024-09-07", "boost": 1.30},
            {"name": "Dussehra", "date": "2024-10-12", "boost": 1.40},
            {"name": "Diwali", "date": "2024-11-01", "boost": 1.60},
            {"name": "Christmas", "date": "2024-12-25", "boost": 1.25},
            # 2025
            {"name": "Makar Sankranti", "date": "2025-01-14", "boost": 1.25},
            {"name": "Republic Day", "date": "2025-01-26", "boost": 1.15},
            {"name": "Holi", "date": "2025-03-14", "boost": 1.35},
            {"name": "Eid ul-Fitr", "date": "2025-03-31", "boost": 1.30},
            {"name": "Independence Day", "date": "2025-08-15", "boost": 1.20},
            {"name": "Raksha Bandhan", "date": "2025-08-09", "boost": 1.25},
            {"name": "Ganesh Chaturthi", "date": "2025-08-27", "boost": 1.30},
            {"name": "Dussehra", "date": "2025-10-02", "boost": 1.40},
            {"name": "Diwali", "date": "2025-10-20", "boost": 1.60},
            {"name": "Christmas", "date": "2025-12-25", "boost": 1.25},
        ]
        
        # Indian names
        self.first_names = [
            "Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rahul", "Pooja",
            "Arjun", "Kavita", "Sanjay", "Neha", "Karthik", "Divya", "Rohit", "Swati",
            "Manoj", "Ritu", "Anil", "Meera", "Suresh", "Lakshmi", "Ramesh", "Sunita",
            "Deepak", "Anita", "Ashok", "Rekha", "Vijay", "Geeta", "Mahesh", "Shanti",
            "Ravi", "Usha", "Prakash", "Savita", "Ajay", "Nisha", "Sunil", "Radha",
            "Mohan", "Parvati", "Dinesh", "Kamala", "Gopal", "Sita", "Hari", "Ganga"
        ]
        
        self.last_names = [
            "Kumar", "Sharma", "Patel", "Gupta", "Singh", "Reddy", "Verma", "Desai",
            "Nair", "Joshi", "Mehta", "Kapoor", "Iyer", "Menon", "Agarwal", "Kulkarni",
            "Rao", "Malhotra", "Chopra", "Pillai", "Sinha", "Banerjee", "Das", "Roy",
            "Mishra", "Pandey", "Tiwari", "Yadav", "Chauhan", "Thakur"
        ]
        
        # Payment methods with realistic distribution
        self.payment_methods = [
            ("credit", 0.51),  # Khata/Credit
            ("cash", 0.30),
            ("upi", 0.15),
            ("card", 0.04)
        ]
        
        # Communication preferences
        self.comm_preferences = [
            ("whatsapp", 0.70),
            ("sms", 0.20),
            ("email", 0.10)
        ]
        
    def get_seasonal_multiplier(self, date: datetime) -> float:
        """Get sales multiplier based on season and festivals"""
        # Base seasonal patterns
        month = date.month
        
        # Monsoon effect (June-September): -10 to -20%
        if 6 <= month <= 9:
            base_multiplier = 0.85
        # Wedding season (November-February): +15 to +25%
        elif month in [11, 12, 1, 2]:
            base_multiplier = 1.20
        # Summer (March-May): Normal
        else:
            base_multiplier = 1.0
        
        # Check for festivals (±7 days window)
        for festival in self.festivals:
            festival_date = datetime.strptime(festival["date"], "%Y-%m-%d")
            days_diff = abs((date - festival_date).days)
            
            if days_diff <= 7:
                # Gradual increase leading to festival, peak on day, gradual decrease after
                if days_diff == 0:
                    return base_multiplier * festival["boost"]
                elif days_diff <= 3:
                    return base_multiplier * (1 + (festival["boost"] - 1) * 0.7)
                else:
                    return base_multiplier * (1 + (festival["boost"] - 1) * 0.4)
        
        # Weekend boost: +20%
        if date.weekday() >= 5:  # Saturday or Sunday
            base_multiplier *= 1.20
        
        return base_multiplier
    
    def get_time_multiplier(self, hour: int) -> float:
        """Get sales multiplier based on time of day"""
        # Peak hours: 10 AM - 2 PM, 6 PM - 9 PM
        if 10 <= hour < 14:
            return 2.0
        elif 18 <= hour < 21:
            return 2.5
        elif 8 <= hour < 10 or 14 <= hour < 18:
            return 1.0
        else:
            return 0.3
    
    def generate_products(self, num_products: int = 33000) -> pd.DataFrame:
        """Generate product catalog with HSN codes and GST rates"""
        print(f"📦 Generating {num_products:,} products...")
        
        products = []
        product_id = 1
        
        # Distribute products across categories
        for category, details in self.product_categories.items():
            # Number of products per category (proportional)
            category_products = int(num_products * 0.1)  # 10% per category
            
            for _ in range(category_products):
                subcategory = random.choice(details["subcategories"])
                
                # Generate Menu Item Names
                prefixes = ["Special", "Classic", "Spicy", "Butter", "Masala", "Crispy", "Tandoori", "Hyderabadi", "Amritsari"]
                
                if category == "North Indian Main Course":
                    suffixes = ["Butter Masala", "Tikka Masala", "Korma", "Makhani", "Do Pyaza", "Roganjosh", "Saag", "Lababdar"]
                    base = subcategory.split(" ")[0] # e.g., "Paneer"
                    name = f"{random.choice(prefixes)} {base} {random.choice(suffixes)}"
                elif category == "Indian Breads":
                    varieties = ["Butter", "Garlic", "Cheese", "Stuffed", "Plain", "Methi"]
                    name = f"{random.choice(varieties)} {subcategory}"
                elif category == "Rice & Biryani":
                    styles = ["Dum", "Hyderabadi", "Lucknowi", "Veg", "Chicken", "Mutton", "Jeera"]
                    name = f"{random.choice(styles)} {subcategory}"
                elif category == "Chinese & Oriental":
                    styles = ["Schezwan", "Hakka", "Manchurian", "Chilly", "Garlic", "Singapuri"]
                    name = f"{random.choice(styles)} {subcategory}"
                elif category == "Beverages":
                    flavors = ["Masala", "Sweet", "Salted", "Chocolate", "Strawberry", "Mango", "Cold", "Hot", "Fresh"]
                    name = f"{random.choice(flavors)} {subcategory}"
                else:
                    # Generic fallback for other categories
                    name = f"{random.choice(prefixes)} {subcategory}"
                
                # Generate SKU
                sku = f"{category[:3].upper()}-{subcategory[:3].upper()}-{product_id:05d}"
                
                # Generate price
                min_price, max_price = details["price_range"]
                selling_price = round(random.uniform(min_price, max_price), 2)
                cost_price = round(selling_price * random.uniform(0.70, 0.80), 2)
                
                products.append({
                    "product_id": product_id,
                    "name": name,
                    "sku": sku,
                    "category": category,
                    "subcategory": subcategory,
                    "hsn_code": details["hsn"],
                    "gst_rate": details["gst_rate"],
                    "cost_price": cost_price,
                    "selling_price": selling_price,
                    "margin_percent": round(((selling_price - cost_price) / selling_price) * 100, 2),
                    "created_at": (self.start_date - timedelta(days=random.randint(30, 730))).isoformat()
                })
                
                product_id += 1
        
        df = pd.DataFrame(products)
        print(f"✅ Generated {len(df):,} products across {len(self.product_categories)} categories")
        return df
    
    def generate_customers(self, num_customers: int = 99000) -> pd.DataFrame:
        """Generate customer profiles with regional distribution"""
        print(f"👥 Generating {num_customers:,} customers...")
        
        customers = []
        
        for i in range(num_customers):
            # Select region based on weights
            region = random.choices(
                list(self.regions.keys()),
                weights=[r["weight"] for r in self.regions.values()]
            )[0]
            
            city = random.choice(self.regions[region]["cities"])
            
            # Generate name
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            name = f"{first_name} {last_name}"
            
            # Generate contact details
            phone = f"+91{random.randint(7000000000, 9999999999)}"
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            
            # Address
            street_num = random.randint(1, 999)
            streets = ["MG Road", "Main Street", "Park Avenue", "Gandhi Nagar", "Nehru Road", "Station Road"]
            address = f"{street_num} {random.choice(streets)}, {city}"
            
            # Credit facility (29.8% have credit enabled)
            credit_enabled = random.random() < 0.298
            credit_limit = round(random.uniform(5000, 50000), 2) if credit_enabled else 0
            current_balance = round(random.uniform(0, credit_limit * 0.3), 2) if credit_enabled else 0
            
            # Communication preference
            comm_pref = random.choices(
                [p[0] for p in self.comm_preferences],
                weights=[p[1] for p in self.comm_preferences]
            )[0]
            
            # R-DIOS AI Features: Churn & Segmentation
            # Simulate realistic segments based on credit and history
            churn_risk_score = round(random.uniform(0.01, 0.99), 2)
            
            # Weighted segment assignment
            if i < num_customers * 0.05:
                segment = "Whale" # Top 5% spenders
                churn_risk_score = round(random.uniform(0.0, 0.2), 2) # Loyal
            elif i < num_customers * 0.25:
                segment = "Loyal"
                churn_risk_score = round(random.uniform(0.1, 0.4), 2)
            elif churn_risk_score > 0.7:
                segment = "At Risk"
            elif churn_risk_score > 0.9:
                segment = "Churned"
            else:
                segment = "Regular"

            customers.append({
                "customer_id": i + 1,
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "city": city,
                "region": region,
                "credit_enabled": credit_enabled,
                "credit_limit": credit_limit,
                "current_balance": current_balance,
                "loyalty_points": random.randint(0, 5000) if segment in ["Whale", "Loyal"] else random.randint(0, 500),
                "preferred_channel": comm_pref,
                "created_at": (self.start_date - timedelta(days=random.randint(1, 730))).isoformat(),
                "churn_risk_score": churn_risk_score,
                "customer_segment": segment
            })
        
        df = pd.DataFrame(customers)
        print(f"✅ Generated {len(df):,} customers")
        print(f"   - Credit enabled: {df['credit_enabled'].sum():,} ({df['credit_enabled'].mean()*100:.1f}%)")
        print(f"   - WhatsApp preference: {(df['preferred_channel'] == 'whatsapp').sum():,} ({(df['preferred_channel'] == 'whatsapp').mean()*100:.1f}%)")
        return df
    
    def generate_sales(self, products_df: pd.DataFrame, customers_df: pd.DataFrame, 
                      num_sales: int = 100000) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate sales transactions with seasonality"""
        print(f"💰 Generating {num_sales:,} sales transactions...")
        
        sales = []
        sale_items = []
        sale_id = 1
        item_id = 1
        
        # Generate sales across date range with seasonal weighting
        total_days = (self.end_date - self.start_date).days
        
        # Pre-calculate seasonal weights for each day
        print("   Calculating seasonal weights...")
        date_weights = []
        all_dates = []
        for day_offset in range(total_days + 1):
            date = self.start_date + timedelta(days=day_offset)
            weight = self.get_seasonal_multiplier(date)
            date_weights.append(weight)
            all_dates.append(date)
        
        # Normalize weights
        total_weight = sum(date_weights)
        date_probabilities = [w / total_weight for w in date_weights]
        
        print(f"   Generating {num_sales:,} sales with seasonal distribution...")
        
        for _ in range(num_sales):
            # Select date based on seasonal weights
            sale_date = random.choices(all_dates, weights=date_probabilities)[0]
            
            # Random time with peak hour distribution
            hour = random.choices(
                range(8, 23),
                weights=[self.get_time_multiplier(h) for h in range(8, 23)]
            )[0]
            
            sale_datetime = sale_date.replace(hour=hour, minute=random.randint(0, 59))
            
            # Select customer
            customer = customers_df.sample(1).iloc[0]
            
            # Payment method
            payment_method = random.choices(
                [p[0] for p in self.payment_methods],
                weights=[p[1] for p in self.payment_methods]
            )[0]
            
            # Number of items (1-5, higher during festivals)
            seasonal_mult = self.get_seasonal_multiplier(sale_date)
            max_items = min(5, int(3 * seasonal_mult))
            num_items = random.randint(1, max(1, max_items))
            
            # Generate sale items
            subtotal = 0
            gst_amount = 0
            
            selected_products = products_df.sample(num_items)
            
            for _, product in selected_products.iterrows():
                quantity = random.randint(1, 3)
                unit_price = product["selling_price"]
                item_total = unit_price * quantity
                item_gst = item_total * (product["gst_rate"] / 100)
                
                sale_items.append({
                    "item_id": item_id,
                    "sale_id": sale_id,
                    "product_id": product["product_id"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "subtotal": round(item_total, 2),
                    "gst_rate": product["gst_rate"],
                    "gst_amount": round(item_gst, 2),
                    "total": round(item_total + item_gst, 2)
                })
                
                subtotal += item_total
                gst_amount += item_gst
                item_id += 1
            
            total_amount = subtotal + gst_amount
            
            # Payment status (51% use credit/partial payment)
            if payment_method == "credit":
                payment_status = random.choice(["paid", "partial"])
                if payment_status == "partial":
                    amount_paid = round(total_amount * random.uniform(0.3, 0.7), 2)
                    amount_due = round(total_amount - amount_paid, 2)
                else:
                    amount_paid = total_amount
                    amount_due = 0
            else:
                payment_status = "paid"
                amount_paid = total_amount
                amount_due = 0
            
            sales.append({
                "sale_id": sale_id,
                "customer_id": customer["customer_id"],
                "sale_date": sale_datetime.isoformat(),
                "subtotal": round(subtotal, 2),
                "gst_amount": round(gst_amount, 2),
                "total_amount": round(total_amount, 2),
                "payment_method": payment_method,
                "payment_status": payment_status,
                "amount_paid": round(amount_paid, 2),
                "amount_due": round(amount_due, 2),
                "region": customer["region"],
                "city": customer["city"]
            })
            
            sale_id += 1
        
        sales_df = pd.DataFrame(sales)
        items_df = pd.DataFrame(sale_items)
        
        print(f"✅ Generated {len(sales_df):,} sales with {len(items_df):,} line items")
        print(f"   - Credit/Partial: {(sales_df['payment_method'] == 'credit').sum():,} ({(sales_df['payment_method'] == 'credit').mean()*100:.1f}%)")
        print(f"   - Total Revenue: ₹{sales_df['total_amount'].sum():,.2f}")
        
        return sales_df, items_df


def main():
    """Generate complete PetPooja-style synthetic dataset"""
    print("=" * 70)
    print("🚀 PetPooja-Style Synthetic Dataset Generator")
    print("=" * 70)
    print()
    
    generator = PetPoojaSyntheticDataGenerator()
    
    # Create output directory
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate datasets
    products_df = generator.generate_products(33000)
    customers_df = generator.generate_customers(99000)
    sales_df, sale_items_df = generator.generate_sales(products_df, customers_df, 100000)
    
    # Save to CSV
    print("\n💾 Saving datasets...")
    products_df.to_csv(output_dir / "products.csv", index=False)
    customers_df.to_csv(output_dir / "customers.csv", index=False)
    sales_df.to_csv(output_dir / "sales.csv", index=False)
    sale_items_df.to_csv(output_dir / "sale_items.csv", index=False)
    
    # Generate summary
    total_rows = len(products_df) + len(customers_df) + len(sales_df) + len(sale_items_df)
    
    summary = f"""# PetPooja Synthetic Dataset Summary

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Dataset Statistics

- **Total Rows**: {total_rows:,}
- **Products**: {len(products_df):,}
- **Customers**: {len(customers_df):,}
- **Sales Transactions**: {len(sales_df):,}
- **Sale Line Items**: {len(sale_items_df):,}

## Financial Metrics

- **Total Revenue**: ₹{sales_df['total_amount'].sum():,.2f}
- **Total GST Collected**: ₹{sales_df['gst_amount'].sum():,.2f}
- **Average Order Value**: ₹{sales_df['total_amount'].mean():,.2f}

## Customer Insights

- **Credit Enabled**: {customers_df['credit_enabled'].sum():,} ({customers_df['credit_enabled'].mean()*100:.1f}%)
- **WhatsApp Preference**: {(customers_df['preferred_channel'] == 'whatsapp').sum():,} ({(customers_df['preferred_channel'] == 'whatsapp').mean()*100:.1f}%)
- **Total Credit Extended**: ₹{customers_df['credit_limit'].sum():,.2f}
- **Outstanding Balance**: ₹{customers_df['current_balance'].sum():,.2f}

## Regional Distribution

{customers_df.groupby('region').size().to_string()}

## Payment Methods

{sales_df.groupby('payment_method').size().to_string()}

## Product Categories

{products_df.groupby('category').size().to_string()}
"""
    
    with open(output_dir / "DATASET_SUMMARY.md", "w") as f:
        f.write(summary)
    
    print(f"✅ Saved all datasets to {output_dir}/")
    print()
    print("=" * 70)
    print("🎉 Dataset Generation Complete!")
    print("=" * 70)
    print(f"\n📊 Total Rows Generated: {total_rows:,}")
    print(f"💰 Total Revenue: ₹{sales_df['total_amount'].sum():,.2f}")
    print()


if __name__ == "__main__":
    main()
