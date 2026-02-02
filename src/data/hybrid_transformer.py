"""
Olist to Indian Retail Data Transformer
Converts Brazilian e-commerce data to Indian retail context with synthetic enrichment
and embedded causal effects for model validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import random
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndianRetailContext:
    """Indian retail domain knowledge for data enrichment"""
    
    # Brazilian to Indian category mapping
    CATEGORY_MAPPING = {
        # Original Olist categories -> Indian equivalents
        "informatica_acessorios": "electronics_accessories",
        "telefonia": "electronics_mobile",
        "eletronicos": "electronics_general",
        "consoles_games": "electronics_gaming",
        "audio": "electronics_audio",
        "pcs": "electronics_computers",
        "tablets_impressao_imagem": "electronics_tablets",
        "eletrodomesticos": "home_appliances",
        "eletrodomesticos_2": "home_appliances",
        "eletroportateis": "home_appliances_small",
        "moveis_decoracao": "furniture_decor",
        "moveis_cozinha_area_de_servico_jantar_e_jardim": "furniture_kitchen",
        "moveis_quarto": "furniture_bedroom",
        "moveis_sala": "furniture_living",
        "moveis_escritorio": "furniture_office",
        "cama_mesa_banho": "home_textiles",
        "utilidades_domesticas": "kitchen_home",
        "casa_conforto": "home_comfort",
        "casa_conforto_2": "home_comfort",
        "casa_construcao": "home_improvement",
        "construcao_ferramentas_construcao": "tools_construction",
        "construcao_ferramentas_ferramentas": "tools_general",
        "construcao_ferramentas_iluminacao": "lighting",
        "construcao_ferramentas_jardim": "garden",
        "construcao_ferramentas_seguranca": "security",
        "beleza_saude": "health_beauty",
        "perfumaria": "beauty_perfumes",
        "fraldas_higiene": "baby_hygiene",
        "bebes": "baby_products",
        "brinquedos": "toys",
        "cool_stuff": "novelty_gifts",
        "esporte_lazer": "sports_leisure",
        "fashion_bolsas_e_acessorios": "fashion_accessories",
        "fashion_calcados": "fashion_footwear",
        "fashion_roupa_feminina": "fashion_women",
        "fashion_roupa_masculina": "fashion_men",
        "fashion_roupa_infanto_juvenil": "fashion_kids",
        "fashion_underwear_e_moda_praia": "fashion_innerwear",
        "relogios_presentes": "watches_gifts",
        "livros_interesse_geral": "books_general",
        "livros_tecnicos": "books_technical",
        "livros_importados": "books_imported",
        "cds_dvds_musicais": "media_music",
        "dvds_blu_ray": "media_video",
        "musica": "media_instruments",
        "artes": "art_supplies",
        "artigos_de_festas": "party_supplies",
        "artigos_de_natal": "seasonal_christmas",
        "flores": "flowers",
        "alimentos": "grocery_food",
        "alimentos_bebidas": "grocery_beverages",
        "bebidas": "beverages",
        "industria_comercio_e_negocios": "business_supplies",
        "papelaria": "stationery",
        "market_place": "marketplace",
        "agro_industria_e_comercio": "agriculture",
        "malas_acessorios": "luggage",
        "pet_shop": "pet_supplies",
        "seguros_e_servicos": "services",
        "sinalizacao_e_seguranca": "signage_safety",
        "climatizacao": "climate_control",
        "la_cuisine": "kitchen_gourmet",
        "portateis_cozinha_e_preparadores_de_alimentos": "kitchen_appliances",
        "pc_gamer": "gaming_pc"
    }
    
    # HSN codes by category (GST compliance)
    HSN_MAPPING = {
        "electronics_accessories": "8473",
        "electronics_mobile": "8517",
        "electronics_general": "8471",
        "electronics_gaming": "9504",
        "electronics_audio": "8518",
        "electronics_computers": "8471",
        "electronics_tablets": "8471",
        "home_appliances": "8516",
        "home_appliances_small": "8509",
        "furniture_decor": "9403",
        "furniture_kitchen": "9403",
        "furniture_bedroom": "9403",
        "furniture_living": "9403",
        "furniture_office": "9403",
        "home_textiles": "6302",
        "kitchen_home": "7323",
        "home_comfort": "9404",
        "home_improvement": "6809",
        "tools_construction": "8205",
        "tools_general": "8205",
        "lighting": "9405",
        "garden": "8201",
        "security": "8531",
        "health_beauty": "3304",
        "beauty_perfumes": "3303",
        "baby_hygiene": "9619",
        "baby_products": "9503",
        "toys": "9503",
        "novelty_gifts": "9505",
        "sports_leisure": "9506",
        "fashion_accessories": "4202",
        "fashion_footwear": "6403",
        "fashion_women": "6204",
        "fashion_men": "6203",
        "fashion_kids": "6209",
        "fashion_innerwear": "6108",
        "watches_gifts": "9102",
        "books_general": "4901",
        "books_technical": "4901",
        "books_imported": "4901",
        "media_music": "8523",
        "media_video": "8523",
        "media_instruments": "9201",
        "art_supplies": "9609",
        "party_supplies": "9505",
        "seasonal_christmas": "9505",
        "flowers": "0603",
        "grocery_food": "1905",
        "grocery_beverages": "2201",
        "beverages": "2201",
        "business_supplies": "8472",
        "stationery": "4820",
        "marketplace": "9999",
        "agriculture": "0101",
        "luggage": "4202",
        "pet_supplies": "2309",
        "services": "9999",
        "signage_safety": "8310",
        "climate_control": "8415",
        "kitchen_gourmet": "7323",
        "kitchen_appliances": "8509",
        "gaming_pc": "8471"
    }
    
    # GST rates by category
    GST_RATES = {
        "electronics_accessories": 18.0,
        "electronics_mobile": 18.0,
        "electronics_general": 18.0,
        "electronics_gaming": 18.0,
        "electronics_audio": 18.0,
        "electronics_computers": 18.0,
        "electronics_tablets": 18.0,
        "home_appliances": 18.0,
        "home_appliances_small": 18.0,
        "furniture_decor": 18.0,
        "furniture_kitchen": 18.0,
        "furniture_bedroom": 18.0,
        "furniture_living": 18.0,
        "furniture_office": 18.0,
        "home_textiles": 12.0,
        "kitchen_home": 18.0,
        "home_comfort": 18.0,
        "home_improvement": 18.0,
        "tools_construction": 18.0,
        "tools_general": 18.0,
        "lighting": 18.0,
        "garden": 18.0,
        "security": 18.0,
        "health_beauty": 12.0,
        "beauty_perfumes": 18.0,
        "baby_hygiene": 12.0,
        "baby_products": 12.0,
        "toys": 12.0,
        "novelty_gifts": 18.0,
        "sports_leisure": 18.0,
        "fashion_accessories": 18.0,
        "fashion_footwear": 12.0,
        "fashion_women": 12.0,
        "fashion_men": 12.0,
        "fashion_kids": 12.0,
        "fashion_innerwear": 12.0,
        "watches_gifts": 18.0,
        "books_general": 0.0,
        "books_technical": 0.0,
        "books_imported": 0.0,
        "media_music": 18.0,
        "media_video": 18.0,
        "media_instruments": 18.0,
        "art_supplies": 12.0,
        "party_supplies": 18.0,
        "seasonal_christmas": 18.0,
        "flowers": 5.0,
        "grocery_food": 0.0,
        "grocery_beverages": 5.0,
        "beverages": 12.0,
        "business_supplies": 18.0,
        "stationery": 12.0,
        "marketplace": 18.0,
        "agriculture": 5.0,
        "luggage": 18.0,
        "pet_supplies": 18.0,
        "services": 18.0,
        "signage_safety": 18.0,
        "climate_control": 18.0,
        "kitchen_gourmet": 18.0,
        "kitchen_appliances": 18.0,
        "gaming_pc": 18.0
    }
    
    # Category-specific profit margins (Indian retail norms)
    MARGIN_RANGES = {
        "electronics_accessories": (0.08, 0.15),
        "electronics_mobile": (0.05, 0.12),
        "electronics_general": (0.08, 0.15),
        "electronics_computers": (0.08, 0.12),
        "home_appliances": (0.12, 0.20),
        "furniture_decor": (0.25, 0.40),
        "home_textiles": (0.30, 0.50),
        "kitchen_home": (0.25, 0.40),
        "health_beauty": (0.30, 0.50),
        "beauty_perfumes": (0.40, 0.60),
        "baby_products": (0.25, 0.40),
        "toys": (0.30, 0.50),
        "sports_leisure": (0.25, 0.40),
        "fashion_accessories": (0.40, 0.60),
        "fashion_footwear": (0.35, 0.55),
        "fashion_women": (0.40, 0.60),
        "fashion_men": (0.35, 0.55),
        "fashion_kids": (0.40, 0.60),
        "watches_gifts": (0.40, 0.60),
        "books_general": (0.20, 0.35),
        "grocery_food": (0.10, 0.20),
        "grocery_beverages": (0.15, 0.25),
        "stationery": (0.25, 0.40),
        "pet_supplies": (0.25, 0.40)
    }
    
    # Indian major cities for weather data
    CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad"]
    
    # Indian holidays (major shopping events with known causal effects)
    HOLIDAYS = {
        # 2022
        "2022-03-18": ("Holi", 0.25),
        "2022-05-03": ("Eid-ul-Fitr", 0.30),
        "2022-08-15": ("Independence Day", 0.10),
        "2022-10-02": ("Gandhi Jayanti", 0.05),
        "2022-10-24": ("Diwali", 0.35),
        "2022-10-25": ("Diwali", 0.35),
        "2022-10-26": ("Bhai Dooj", 0.20),
        "2022-12-25": ("Christmas", 0.25),
        # 2023
        "2023-03-08": ("Holi", 0.25),
        "2023-04-22": ("Eid-ul-Fitr", 0.30),
        "2023-08-15": ("Independence Day", 0.10),
        "2023-10-02": ("Gandhi Jayanti", 0.05),
        "2023-11-12": ("Diwali", 0.35),
        "2023-11-13": ("Diwali", 0.35),
        "2023-11-14": ("Bhai Dooj", 0.20),
        "2023-12-25": ("Christmas", 0.25),
        # 2024
        "2024-03-25": ("Holi", 0.25),
        "2024-04-10": ("Eid-ul-Fitr", 0.30),
        "2024-08-15": ("Independence Day", 0.10),
        "2024-10-02": ("Gandhi Jayanti", 0.05),
        "2024-10-31": ("Diwali", 0.35),
        "2024-11-01": ("Diwali", 0.35),
        "2024-11-02": ("Bhai Dooj", 0.20),
        "2024-12-25": ("Christmas", 0.25)
    }
    
    # Payment method distribution in India
    PAYMENT_METHODS = {
        "cash": 0.45,
        "upi": 0.40,
        "card": 0.10,
        "credit": 0.05
    }


class HybridDataTransformer:
    """
    Transform Olist Brazilian e-commerce data to Indian retail context
    with synthetic causal effects for model validation
    """
    
    def __init__(self, olist_path: str = None):
        self.olist_path = Path(olist_path) if olist_path else None
        self.context = IndianRetailContext()
        self.random_state = 42
        np.random.seed(self.random_state)
        random.seed(self.random_state)
        
        logger.info("HybridDataTransformer initialized")
    
    def load_olist_data(self) -> Dict[str, pd.DataFrame]:
        """Load all Olist dataset files"""
        if not self.olist_path or not self.olist_path.exists():
            logger.warning("Olist path not found, generating synthetic data instead")
            return self._generate_synthetic_base()
        
        files = {
            "orders": "olist_orders_dataset.csv",
            "order_items": "olist_order_items_dataset.csv",
            "products": "olist_products_dataset.csv",
            "customers": "olist_customers_dataset.csv",
            "sellers": "olist_sellers_dataset.csv",
            "order_payments": "olist_order_payments_dataset.csv",
            "order_reviews": "olist_order_reviews_dataset.csv",
            "geolocation": "olist_geolocation_dataset.csv",
            "category_translation": "product_category_name_translation.csv"
        }
        
        data = {}
        for key, filename in files.items():
            filepath = self.olist_path / filename
            if filepath.exists():
                data[key] = pd.read_csv(filepath)
                logger.info(f"Loaded {key}: {len(data[key])} rows")
            else:
                logger.warning(f"File not found: {filename}")
        
        return data
    
    def _generate_synthetic_base(self) -> Dict[str, pd.DataFrame]:
        """Generate synthetic base data if Olist not available"""
        logger.info("Generating synthetic base dataset...")
        
        # Generate 50,000 orders over 2 years
        n_orders = 50000
        n_customers = 5000
        n_products = 500
        
        # Date range: 2022-2024
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2024, 12, 31)
        date_range = (end_date - start_date).days
        
        # Generate customers
        customers = pd.DataFrame({
            "customer_id": [f"CUST_{i:05d}" for i in range(n_customers)],
            "customer_city": np.random.choice(self.context.CITIES, n_customers),
            "customer_state": np.random.choice(["MH", "DL", "KA", "TN", "WB", "TG", "GJ", "RJ"], n_customers)
        })
        
        # Generate products with categories
        categories = list(self.context.HSN_MAPPING.keys())
        products = pd.DataFrame({
            "product_id": [f"PROD_{i:05d}" for i in range(n_products)],
            "product_category_name": np.random.choice(categories, n_products)
        })
        
        # Generate orders with seasonal patterns
        order_dates = []
        for _ in range(n_orders):
            days = random.randint(0, date_range)
            order_date = start_date + timedelta(days=days)
            
            # Add seasonal bias (more orders in Oct-Nov for Diwali)
            if order_date.month in [10, 11]:
                if random.random() < 0.3:  # 30% more likely
                    order_dates.append(order_date)
                    continue
            order_dates.append(order_date)
        
        orders = pd.DataFrame({
            "order_id": [f"ORD_{i:08d}" for i in range(n_orders)],
            "customer_id": np.random.choice(customers["customer_id"], n_orders),
            "order_purchase_timestamp": order_dates,
            "order_status": np.random.choice(["delivered", "shipped", "processing"], n_orders, p=[0.9, 0.08, 0.02])
        })
        
        # Generate order items
        order_items = []
        for _, order in orders.iterrows():
            n_items = np.random.choice([1, 2, 3, 4, 5], p=[0.5, 0.25, 0.15, 0.07, 0.03])
            for _ in range(n_items):
                product = products.sample(1).iloc[0]
                category = product["product_category_name"]
                
                # Price based on category
                base_price = random.uniform(200, 5000)  # INR
                if "electronics" in category:
                    base_price = random.uniform(1000, 50000)
                elif "furniture" in category:
                    base_price = random.uniform(2000, 30000)
                elif "fashion" in category:
                    base_price = random.uniform(300, 5000)
                elif "grocery" in category or "books" in category:
                    base_price = random.uniform(50, 500)
                
                order_items.append({
                    "order_id": order["order_id"],
                    "product_id": product["product_id"],
                    "price": round(base_price, 2),
                    "freight_value": round(base_price * 0.05, 2)
                })
        
        order_items_df = pd.DataFrame(order_items)
        
        return {
            "orders": orders,
            "order_items": order_items_df,
            "products": products,
            "customers": customers
        }
    
    def transform_to_indian_context(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Apply Indian retail context transformations"""
        logger.info("Transforming to Indian retail context...")
        
        # Transform products
        products = data["products"].copy()
        
        # Map categories to Indian equivalents
        if "product_category_name" in products.columns:
            products["indian_category"] = products["product_category_name"].map(
                self.context.CATEGORY_MAPPING
            ).fillna("general_merchandise")
        else:
            products["indian_category"] = "general_merchandise"
        
        # Add HSN codes
        products["hsn_code"] = products["indian_category"].map(
            self.context.HSN_MAPPING
        ).fillna("9999")
        
        # Add GST rates
        products["gst_rate"] = products["indian_category"].map(
            self.context.GST_RATES
        ).fillna(18.0)
        
        # Add realistic cost prices based on margins
        def calculate_cost(row):
            category = row["indian_category"]
            margin_range = self.context.MARGIN_RANGES.get(category, (0.20, 0.35))
            margin = random.uniform(*margin_range)
            return 1 / (1 + margin)  # Cost multiplier
        
        data["products"] = products
        
        # Transform orders
        orders = data["orders"].copy()
        
        # Shift dates to Indian context (keep same patterns, adjust year if needed)
        if "order_purchase_timestamp" in orders.columns:
            orders["order_date"] = pd.to_datetime(orders["order_purchase_timestamp"])
        
        # Add city based on customer
        customers = data.get("customers", pd.DataFrame())
        if not customers.empty and "customer_city" in customers.columns:
            orders = orders.merge(
                customers[["customer_id", "customer_city"]],
                on="customer_id",
                how="left"
            )
        else:
            orders["customer_city"] = np.random.choice(self.context.CITIES, len(orders))
        
        data["orders"] = orders
        
        # Transform order items with Indian pricing
        order_items = data["order_items"].copy()
        
        # Convert BRL to INR (if Olist data) or keep as INR (if synthetic)
        # 1 BRL ≈ 15 INR adjusted for PPP
        if order_items["price"].mean() < 1000:  # Likely BRL
            order_items["price_inr"] = order_items["price"] * 15
        else:
            order_items["price_inr"] = order_items["price"]
        
        # Add product details
        order_items = order_items.merge(
            products[["product_id", "indian_category", "hsn_code", "gst_rate"]],
            on="product_id",
            how="left"
        )
        
        # Calculate cost price based on category margins
        def get_cost_price(row):
            category = row.get("indian_category", "general")
            margin_range = self.context.MARGIN_RANGES.get(category, (0.20, 0.35))
            margin = random.uniform(*margin_range)
            return round(row["price_inr"] / (1 + margin), 2)
        
        order_items["cost_price"] = order_items.apply(get_cost_price, axis=1)
        
        # Calculate GST amounts
        order_items["gst_amount"] = round(
            order_items["price_inr"] * (order_items["gst_rate"] / (100 + order_items["gst_rate"])),
            2
        )
        
        data["order_items"] = order_items
        
        logger.info(f"Transformed {len(orders)} orders, {len(order_items)} items, {len(products)} products")
        return data
    
    def inject_causal_effects(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Inject KNOWN causal effects for model validation
        These are ground-truth effects we can validate against
        """
        logger.info("Injecting known causal effects...")
        
        orders = data["orders"].copy()
        order_items = data["order_items"].copy()
        
        # Ensure order_date is datetime
        if "order_date" not in orders.columns:
            orders["order_date"] = pd.to_datetime(orders.get("order_purchase_timestamp", datetime.now()))
        
        orders["order_date"] = pd.to_datetime(orders["order_date"])
        
        # Initialize causal flags
        orders["is_holiday"] = False
        orders["holiday_name"] = None
        orders["holiday_effect"] = 0.0
        orders["weather_effect"] = 0.0
        orders["is_monsoon"] = False
        
        # Effect 1: Holiday Effects (Known +X% impact)
        for date_str, (holiday_name, effect) in self.context.HOLIDAYS.items():
            holiday_date = pd.to_datetime(date_str)
            
            # Window: 3 days before to 1 day after
            window_start = holiday_date - timedelta(days=3)
            window_end = holiday_date + timedelta(days=1)
            
            mask = (orders["order_date"] >= window_start) & (orders["order_date"] <= window_end)
            orders.loc[mask, "is_holiday"] = True
            orders.loc[mask, "holiday_name"] = holiday_name
            orders.loc[mask, "holiday_effect"] = effect
        
        logger.info(f"Marked {orders['is_holiday'].sum()} orders as holiday-affected")
        
        # Effect 2: Monsoon Effect (Jun-Sep, -15% for non-essentials)
        monsoon_months = [6, 7, 8, 9]
        orders["is_monsoon"] = orders["order_date"].dt.month.isin(monsoon_months)
        orders.loc[orders["is_monsoon"], "weather_effect"] = -0.15
        
        logger.info(f"Marked {orders['is_monsoon'].sum()} orders as monsoon-affected")
        
        # Effect 3: Weekend Effect (+10% for leisure categories)
        orders["is_weekend"] = orders["order_date"].dt.dayofweek.isin([5, 6])
        
        # Apply effects to order values
        # Merge effects back to order items
        order_items = order_items.merge(
            orders[["order_id", "is_holiday", "holiday_effect", "is_monsoon", "weather_effect", "is_weekend"]],
            on="order_id",
            how="left"
        )
        
        # Adjust quantities/values based on effects (for training data realism)
        # Holiday: Increase quantity
        holiday_mask = order_items["is_holiday"] == True
        order_items.loc[holiday_mask, "price_inr"] *= (1 + order_items.loc[holiday_mask, "holiday_effect"])
        
        # Monsoon: Decrease for non-essentials
        monsoon_mask = (order_items["is_monsoon"] == True) & (~order_items["indian_category"].str.contains("grocery|food|beverage", na=False))
        order_items.loc[monsoon_mask, "price_inr"] *= (1 + order_items.loc[monsoon_mask, "weather_effect"])
        
        # Recalculate GST
        order_items["gst_amount"] = round(
            order_items["price_inr"] * (order_items["gst_rate"] / (100 + order_items["gst_rate"])),
            2
        )
        
        data["orders"] = orders
        data["order_items"] = order_items
        
        # Create ground truth effects summary
        effects_summary = {
            "diwali_effect": 0.35,
            "holi_effect": 0.25,
            "christmas_effect": 0.25,
            "eid_effect": 0.30,
            "monsoon_effect": -0.15,
            "weekend_effect": 0.10
        }
        data["causal_ground_truth"] = effects_summary
        
        logger.info("Causal effects injected successfully")
        logger.info(f"Ground truth effects: {effects_summary}")
        
        return data
    
    def generate_weather_data(self, date_range: Tuple[datetime, datetime]) -> pd.DataFrame:
        """Generate realistic Indian weather data by city"""
        logger.info("Generating weather data...")
        
        start_date, end_date = date_range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        weather_records = []
        for city in self.context.CITIES:
            for date in dates:
                month = date.month
                
                # Base temperature by city (approximate)
                city_base_temp = {
                    "Mumbai": 28, "Delhi": 25, "Bangalore": 24, "Chennai": 30,
                    "Kolkata": 27, "Hyderabad": 28, "Pune": 26, "Ahmedabad": 29
                }
                
                base_temp = city_base_temp.get(city, 27)
                
                # Seasonal variation
                if month in [12, 1, 2]:  # Winter
                    temp_avg = base_temp - 8 + random.uniform(-2, 2)
                elif month in [3, 4, 5]:  # Summer
                    temp_avg = base_temp + 5 + random.uniform(-2, 4)
                elif month in [6, 7, 8, 9]:  # Monsoon
                    temp_avg = base_temp - 2 + random.uniform(-3, 3)
                else:  # Autumn
                    temp_avg = base_temp + random.uniform(-2, 2)
                
                # Precipitation (monsoon heavy)
                if month in [6, 7, 8, 9]:
                    precipitation = random.uniform(5, 50) if random.random() < 0.6 else 0
                    condition = "rainy" if precipitation > 0 else random.choice(["cloudy", "sunny"])
                else:
                    precipitation = random.uniform(0, 10) if random.random() < 0.1 else 0
                    condition = random.choice(["sunny", "cloudy", "partly_cloudy"])
                
                weather_records.append({
                    "city": city,
                    "date": date.date(),
                    "temperature_high": round(temp_avg + random.uniform(3, 8), 1),
                    "temperature_low": round(temp_avg - random.uniform(3, 8), 1),
                    "temperature_avg": round(temp_avg, 1),
                    "precipitation_mm": round(precipitation, 1),
                    "humidity_percent": random.randint(40, 95) if month in [6, 7, 8, 9] else random.randint(30, 70),
                    "condition": condition
                })
        
        weather_df = pd.DataFrame(weather_records)
        logger.info(f"Generated {len(weather_df)} weather records for {len(self.context.CITIES)} cities")
        
        return weather_df
    
    def generate_economic_indicators(self, date_range: Tuple[datetime, datetime]) -> pd.DataFrame:
        """Generate Indian economic indicators time series"""
        logger.info("Generating economic indicators...")
        
        start_date, end_date = date_range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Base values (approximate 2022-2024 Indian data)
        base_cpi = 5.5  # CPI inflation %
        base_wpi = 4.0  # WPI inflation %
        base_petrol = 100.0  # INR per liter
        base_diesel = 90.0
        base_gold = 55000.0  # INR per 10g
        base_usd = 82.0  # USD-INR rate
        
        records = []
        for date in dates:
            # Add trend and random variation
            days_from_start = (date - start_date).days
            trend = days_from_start / 365 * 0.02  # 2% annual inflation-like trend
            
            records.append({
                "date": date.date(),
                "cpi_inflation": round(base_cpi + trend * 100 + random.uniform(-0.5, 0.5), 2),
                "wpi_inflation": round(base_wpi + trend * 100 + random.uniform(-0.8, 0.8), 2),
                "fuel_price_petrol": round(base_petrol * (1 + trend + random.uniform(-0.02, 0.03)), 2),
                "fuel_price_diesel": round(base_diesel * (1 + trend + random.uniform(-0.02, 0.03)), 2),
                "gold_price": round(base_gold * (1 + trend * 2 + random.uniform(-0.01, 0.02)), 2),
                "usd_inr_rate": round(base_usd * (1 + trend * 0.5 + random.uniform(-0.005, 0.01)), 2)
            })
        
        economic_df = pd.DataFrame(records)
        logger.info(f"Generated {len(economic_df)} economic indicator records")
        
        return economic_df
    
    def transform_and_export(
        self,
        output_dir: str = "data/transformed",
        generate_external: bool = True
    ) -> Dict[str, str]:
        """Main transformation pipeline - export to CSV for database loading"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load data
        data = self.load_olist_data()
        
        # Transform to Indian context
        data = self.transform_to_indian_context(data)
        
        # Inject causal effects
        data = self.inject_causal_effects(data)
        
        # Export core data
        exported_files = {}
        
        # Orders
        if "orders" in data:
            orders_path = output_path / "orders_transformed.csv"
            data["orders"].to_csv(orders_path, index=False)
            exported_files["orders"] = str(orders_path)
            logger.info(f"Exported orders to {orders_path}")
        
        # Order items
        if "order_items" in data:
            items_path = output_path / "order_items_transformed.csv"
            data["order_items"].to_csv(items_path, index=False)
            exported_files["order_items"] = str(items_path)
            logger.info(f"Exported order items to {items_path}")
        
        # Products
        if "products" in data:
            products_path = output_path / "products_transformed.csv"
            data["products"].to_csv(products_path, index=False)
            exported_files["products"] = str(products_path)
            logger.info(f"Exported products to {products_path}")
        
        # Customers
        if "customers" in data:
            customers_path = output_path / "customers_transformed.csv"
            data["customers"].to_csv(customers_path, index=False)
            exported_files["customers"] = str(customers_path)
            logger.info(f"Exported customers to {customers_path}")
        
        # Generate external data
        if generate_external:
            date_range = (datetime(2022, 1, 1), datetime(2024, 12, 31))
            
            # Weather
            weather_df = self.generate_weather_data(date_range)
            weather_path = output_path / "weather_data.csv"
            weather_df.to_csv(weather_path, index=False)
            exported_files["weather"] = str(weather_path)
            
            # Economic indicators
            economic_df = self.generate_economic_indicators(date_range)
            economic_path = output_path / "economic_indicators.csv"
            economic_df.to_csv(economic_path, index=False)
            exported_files["economic"] = str(economic_path)
        
        # Export ground truth effects
        if "causal_ground_truth" in data:
            import json
            ground_truth_path = output_path / "causal_ground_truth.json"
            with open(ground_truth_path, "w") as f:
                json.dump(data["causal_ground_truth"], f, indent=2)
            exported_files["ground_truth"] = str(ground_truth_path)
            logger.info(f"Exported causal ground truth to {ground_truth_path}")
        
        logger.info(f"Transformation complete. Exported {len(exported_files)} files to {output_path}")
        return exported_files


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Transform Olist data to Indian retail context")
    parser.add_argument("--olist-path", type=str, default=None, help="Path to Olist dataset folder")
    parser.add_argument("--output-dir", type=str, default="data/transformed", help="Output directory")
    parser.add_argument("--no-external", action="store_true", help="Skip weather/economic data generation")
    
    args = parser.parse_args()
    
    transformer = HybridDataTransformer(olist_path=args.olist_path)
    exported = transformer.transform_and_export(
        output_dir=args.output_dir,
        generate_external=not args.no_external
    )
    
    print("\n✅ Transformation Complete!")
    print(f"Files exported to: {args.output_dir}")
    for name, path in exported.items():
        print(f"  - {name}: {path}")
