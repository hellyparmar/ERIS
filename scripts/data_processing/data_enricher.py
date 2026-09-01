"""
Data Enrichment Script for R-DIOS v5.0
Adds Indian retail context to Olist Brazilian dataset:
- HSN codes (product categories)
- GST tax rates
- Cost prices
- Stock levels
- Dead stock flags
- WhatsApp numbers
- Currency conversion (BRL → INR)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

class DataEnricher:
    def __init__(self, raw_dir, processed_dir):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # HSN Code Mapping (Brazilian categories → Indian HSN codes)
        self.hsn_mapping = {
            'health_beauty': ('3304', 18),  # Cosmetics - 18% GST
            'watches_gifts': ('9102', 18),  # Watches - 18%
            'bed_bath_table': ('6302', 12),  # Bed linen - 12%
            'sports_leisure': ('9506', 18),  # Sports equipment - 18%
            'computers_accessories': ('8471', 18),  # Computers - 18%
            'furniture_decor': ('9403', 18),  # Furniture - 18%
            'housewares': ('7323', 18),  # Tableware - 18%
            'telephony': ('8517', 18),  # Telephones - 18%
            'auto': ('8708', 28),  # Auto parts - 28%
            'toys': ('9503', 12),  # Toys - 12%
            'cool_stuff': ('9505', 18),  # Festive articles - 18%
            'baby': ('9503', 12),  # Baby products - 12%
            'fashion_bags_accessories': ('4202', 18),  # Bags - 18%
            'perfumery': ('3303', 18),  # Perfumes - 18%
            'electronics': ('8517', 18),  # Electronics - 18%
            'computers': ('8471', 18),  # Computers - 18%
            'office_furniture': ('9403', 18),  # Office furniture - 18%
            'home_appliances': ('8516', 18),  # Home appliances - 18%
            'home_appliances_2': ('8509', 18),  # Appliances - 18%
            'garden_tools': ('8201', 18),  # Hand tools - 18%
            'furniture_bedroom': ('9403', 18),  # Bedroom furniture - 18%
            'furniture_living_room': ('9403', 18),  # Living room furniture - 18%
            'construction_tools_safety': ('8205', 18),  # Construction tools - 18%
            'construction_tools_lights': ('9405', 18),  # Lights - 18%
            'industry_commerce_and_business': ('8471', 18),  # Business equipment - 18%
            'food_drink': ('2106', 12),  # Food preparations - 12%
            'food': ('1905', 12),  # Food products - 12%
            'books_general_interest': ('4901', 5),  # Books - 5%
            'books_technical': ('4901', 5),  # Technical books - 5%
            'books_imported': ('4901', 5),  # Imported books - 5%
            'stationery': ('4820', 12),  # Stationery - 12%
            'fashion_male_clothing': ('6203', 12),  # Men's clothing - 12%
            'fashion_female_clothing': ('6204', 12),  # Women's clothing - 12%
            'fashion_childrens_clothes': ('6209', 12),  # Children's clothing - 12%
            'fashion_sport': ('6211', 12),  # Sports clothing - 12%
            'fashion_underwear_beach': ('6208', 12),  # Underwear - 12%
            'fashion_shoes': ('6403', 18),  # Footwear - 18%
            'pet_shop': ('2309', 18),  # Pet food - 18%
            'musical_instruments': ('9207', 18),  # Musical instruments - 18%
            'cds_dvds_musicals': ('8523', 18),  # CDs/DVDs - 18%
            'dvds_blu_ray': ('8523', 18),  # DVDs - 18%
            'consoles_games': ('9504', 28),  # Video games - 28%
            'audio': ('8518', 18),  # Audio equipment - 18%
            'cine_photo': ('9006', 18),  # Cameras - 18%
            'art': ('9701', 12),  # Art - 12%
            'christmas_supplies': ('9505', 18),  # Christmas items - 18%
            'party_supplies': ('9505', 18),  # Party supplies - 18%
            'default': ('9999', 18)  # Default - 18%
        }
        
        # BRL to INR conversion rate (approximate)
        self.brl_to_inr = 17.5
        
    def load_datasets(self):
        """Load required datasets"""
        print("📂 Loading datasets for enrichment...\n")
        
        self.products = pd.read_csv(self.raw_dir / 'olist_products_dataset.csv')
        self.customers = pd.read_csv(self.raw_dir / 'olist_customers_dataset.csv')
        self.orders = pd.read_csv(self.raw_dir / 'olist_orders_dataset.csv')
        self.order_items = pd.read_csv(self.raw_dir / 'olist_order_items_dataset.csv')
        self.payments = pd.read_csv(self.raw_dir / 'olist_order_payments_dataset.csv')
        self.sellers = pd.read_csv(self.raw_dir / 'olist_sellers_dataset.csv')
        
        print(f"✅ Loaded {len(self.products):,} products")
        print(f"✅ Loaded {len(self.customers):,} customers")
        print(f"✅ Loaded {len(self.orders):,} orders")
        print(f"✅ Loaded {len(self.order_items):,} order items")
        print(f"✅ Loaded {len(self.payments):,} payments")
        print(f"✅ Loaded {len(self.sellers):,} sellers\n")
        
    def enrich_products(self):
        """Add HSN codes, GST rates, cost prices, and stock levels"""
        print("=" * 80)
        print("🏷️  ENRICHING PRODUCTS")
        print("=" * 80 + "\n")
        
        df = self.products.copy()
        
        # 1. Map HSN codes and GST rates
        print("1️⃣  Mapping HSN codes and GST rates...")
        
        def get_hsn_and_gst(category):
            if pd.isna(category):
                return self.hsn_mapping['default']
            return self.hsn_mapping.get(category, self.hsn_mapping['default'])
        
        df[['hsn_code', 'gst_rate']] = df['product_category_name'].apply(
            lambda x: pd.Series(get_hsn_and_gst(x))
        )
        
        print(f"   ✅ Added HSN codes and GST rates to {len(df):,} products")
        
        # 2. Generate cost prices (70-80% of selling price)
        print("2️⃣  Generating cost prices...")
        
        # Merge with order_items to get prices
        items_with_price = self.order_items.groupby('product_id')['price'].mean().reset_index()
        df = df.merge(items_with_price, on='product_id', how='left')
        
        # Generate cost price (70-80% of selling price)
        df['cost_price_brl'] = df['price'] * np.random.uniform(0.70, 0.80, len(df))
        df['selling_price_brl'] = df['price']
        
        # Convert to INR
        df['cost_price_inr'] = (df['cost_price_brl'] * self.brl_to_inr).round(2)
        df['selling_price_inr'] = (df['selling_price_brl'] * self.brl_to_inr).round(2)
        
        # Drop temporary price column
        df = df.drop('price', axis=1)
        
        print(f"   ✅ Generated cost prices (70-80% of selling price)")
        
        # 3. Add stock levels
        print("3️⃣  Adding initial stock levels...")
        
        # Generate random stock levels (50-500 units)
        df['stock_quantity'] = np.random.randint(50, 501, len(df))
        df['reorder_point'] = (df['stock_quantity'] * 0.2).astype(int)  # 20% of stock
        df['max_stock_level'] = (df['stock_quantity'] * 1.5).astype(int)
        
        print(f"   ✅ Added stock levels (50-500 units per product)")
        
        # 4. Flag dead stock (no sales in last 6 months)
        print("4️⃣  Identifying dead stock...")
        
        # Get last sale date for each product
        orders_df = self.orders.copy()
        orders_df['order_purchase_timestamp'] = pd.to_datetime(orders_df['order_purchase_timestamp'])
        
        items_with_dates = self.order_items.merge(
            orders_df[['order_id', 'order_purchase_timestamp']], 
            on='order_id'
        )
        
        last_sale = items_with_dates.groupby('product_id')['order_purchase_timestamp'].max().reset_index()
        last_sale.columns = ['product_id', 'last_sale_date']
        
        df = df.merge(last_sale, on='product_id', how='left')
        
        # Calculate if dead stock (no sale in last 180 days from dataset end date)
        dataset_end_date = orders_df['order_purchase_timestamp'].max()
        df['days_since_last_sale'] = (dataset_end_date - df['last_sale_date']).dt.days
        df['is_dead_stock'] = df['days_since_last_sale'] > 180
        
        dead_stock_count = df['is_dead_stock'].sum()
        print(f"   ✅ Flagged {dead_stock_count:,} products as dead stock (no sales > 180 days)")
        
        # Save enriched products
        output_file = self.processed_dir / 'products_enriched.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Saved to: {output_file}")
        print(f"   Rows: {len(df):,}")
        print(f"   New columns: hsn_code, gst_rate, cost_price_inr, selling_price_inr, stock_quantity, is_dead_stock\n")
        
        return df
        
    def enrich_customers(self):
        """Add WhatsApp numbers and credit management fields"""
        print("=" * 80)
        print("👥 ENRICHING CUSTOMERS")
        print("=" * 80 + "\n")
        
        df = self.customers.copy()
        
        # 1. Generate WhatsApp numbers (Indian format)
        print("1️⃣  Generating WhatsApp numbers...")
        
        def generate_indian_phone():
            # Indian mobile: +91-XXXXX-XXXXX (10 digits starting with 6-9)
            first_digit = random.choice([6, 7, 8, 9])
            remaining = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            return f"+91-{first_digit}{remaining[:4]}-{remaining[4:]}"
        
        df['whatsapp_number'] = [generate_indian_phone() for _ in range(len(df))]
        df['preferred_channel'] = np.random.choice(['whatsapp', 'email', 'sms'], len(df), p=[0.7, 0.2, 0.1])
        
        print(f"   ✅ Added WhatsApp numbers for {len(df):,} customers")
        
        # 2. Credit management fields
        print("2️⃣  Adding credit management fields...")
        
        # 30% of customers are credit-allowed
        df['credit_allowed'] = np.random.choice([True, False], len(df), p=[0.3, 0.7])
        
        # Credit limits (₹5,000 to ₹50,000 for allowed customers)
        df['credit_limit_inr'] = df['credit_allowed'].apply(
            lambda x: random.randint(5000, 50000) if x else 0
        )
        
        # Current balance (0 to 50% of credit limit)
        df['current_balance_inr'] = df.apply(
            lambda row: random.randint(0, int(row['credit_limit_inr'] * 0.5)) if row['credit_allowed'] else 0,
            axis=1
        )
        
        # Loyalty points (0-1000)
        df['loyalty_points'] = np.random.randint(0, 1001, len(df))
        
        credit_customers = df['credit_allowed'].sum()
        print(f"   ✅ {credit_customers:,} customers ({credit_customers/len(df)*100:.1f}%) have credit enabled")
        
        # Save enriched customers
        output_file = self.processed_dir / 'customers_enriched.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Saved to: {output_file}")
        print(f"   Rows: {len(df):,}")
        print(f"   New columns: whatsapp_number, preferred_channel, credit_allowed, credit_limit_inr\n")
        
        return df
        
    def enrich_sales(self):
        """Add payment status and installation info, convert currency"""
        print("=" * 80)
        print("💰 ENRICHING SALES & PAYMENTS")
        print("=" * 80 + "\n")
        
        # Merge orders with payments
        df = self.orders.copy()
        payment_summary = self.payments.groupby('order_id').agg({
            'payment_installments': 'max',
            'payment_value': 'sum',
            'payment_type': 'first'
        }).reset_index()
        
        df = df.merge(payment_summary, on='order_id', how='left')
        
        # Convert to INR
        df['payment_value_inr'] = (df['payment_value'] * self.brl_to_inr).round(2)
        
        # Determine payment status
        df['payment_status'] = df['payment_installments'].apply(
            lambda x: 'partial' if x > 1 else 'paid'
        )
        
        # For installment orders, calculate paid vs due
        df['amount_paid_inr'] = df.apply(
            lambda row: row['payment_value_inr'] / row['payment_installments'] if row['payment_installments'] > 0 else row['payment_value_inr'],
            axis=1
        ).round(2)
        
        df['amount_due_inr'] = (df['payment_value_inr'] - df['amount_paid_inr']).round(2)
        
        partial_payments = (df['payment_status'] == 'partial').sum()
        print(f"📊 Payment Analysis:")
        print(f"   Total orders: {len(df):,}")
        print(f"   Paid in full: {(df['payment_status'] == 'paid').sum():,}")
        print(f"   Partial payments: {partial_payments:,} ({partial_payments/len(df)*100:.1f}%)")
        
        # Save enriched sales
        output_file = self.processed_dir / 'sales_enriched.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Saved to: {output_file}")
        print(f"   Rows: {len(df):,}")
        print(f"   New columns: payment_value_inr, payment_status, amount_paid_inr, amount_due_inr\n")
        
        return df
    
    def create_inventory_table(self, products_enriched):
        """Create inventory table from enriched products"""
        print("=" * 80)
        print("📦 CREATING INVENTORY TABLE")
        print("=" * 80 + "\n")
        
        # Select relevant columns
        inventory = products_enriched[[
            'product_id', 'stock_quantity', 'reorder_point', 'max_stock_level', 
            'cost_price_inr', 'selling_price_inr', 'is_dead_stock', 'last_sale_date'
        ]].copy()
        
        # Add last restocked date (random date in last 30 days)
        max_date = pd.to_datetime(self.orders['order_purchase_timestamp']).max()
        inventory['last_restocked'] = [
            max_date - timedelta(days=random.randint(1, 30)) for _ in range(len(inventory))
        ]
        
        # Save inventory table
        output_file = self.processed_dir / 'inventory_enriched.csv'
        inventory.to_csv(output_file, index=False)
        print(f"💾 Saved to: {output_file}")
        print(f"   Rows: {len(inventory):,}\n")
        
        return inventory
    
    def generate_summary_report(self):
        """Generate enrichment summary"""
        print("=" * 80)
        print("📋 ENRICHMENT SUMMARY")
        print("=" * 80 + "\n")
        
        print("✅ Enriched Datasets:")
        print(f"   1. products_enriched.csv")
        print(f"   2. customers_enriched.csv")
        print(f"   3. sales_enriched.csv")
        print(f"   4. inventory_enriched.csv")
        
        print("\n✅ Indian Context Added:")
        print("   • HSN codes (based on product categories)")
        print("   • GST tax rates (5%, 12%, 18%, 28%)")
        print("   • Cost prices (70-80% of selling price)")
        print("   • Stock levels (50-500 units)")
        print("   • Dead stock flags (>180 days no sales)")
        print("   • WhatsApp numbers (+91 format)")
        print("   • Credit management (30% customers enabled)")
        print("   • Currency conversion (BRL → INR at ₹17.5)")
        
        print("\n🎯 Ready for:")
        print("   1. External factors integration (weather, economy)")
        print("   2. PostgreSQL database loading")
        print("   3. Transaction Engine development")
        
        print()

def main():
    print("🏭 R-DIOS v5.0 - Data Enrichment Pipeline")
    print("=" * 80)
    print()
    
    # Paths
    script_dir = Path(__file__).parent
    raw_dir = script_dir.parent.parent / 'data' / 'raw'
    processed_dir = script_dir.parent.parent / 'data' / 'processed'
    
    # Initialize enricher
    enricher = DataEnricher(raw_dir, processed_dir)
    
    # Execute pipeline
    enricher.load_datasets()
    
    products_enriched = enricher.enrich_products()
    customers_enriched = enricher.enrich_customers()
    sales_enriched = enricher.enrich_sales()
    inventory_enriched = enricher.create_inventory_table(products_enriched)
    
    enricher.generate_summary_report()
    
    print("✅ Data enrichment complete!")
    print()

if __name__ == "__main__":
    main()
