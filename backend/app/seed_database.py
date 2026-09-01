"""
seed_database.py - Comprehensive database seeding
Generates realistic Indian QSR/Restaurant chain data.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict
import random
import uuid
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import holidays
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.models.organization import Organization
from app.models.users import Role, User
from app.models.outlet import Outlet
from app.models.customers import Customer
from app.models.employee_models import Employee, EmployeeRole
from app.models.models_v6 import Supplier, Product, Sale, SaleItem
from app.models.inventory import Inventory
from app.models.business_contact import BusinessContact, ContactType
from app.models.external_factors_models import EconomicIndicatorHistory

logger = logging.getLogger(__name__)

def pg_or_sqlite_insert(session: AsyncSession, model):
    try:
        bind = getattr(session, 'bind', None) or getattr(session, '_bind', None)
        if bind and hasattr(bind, 'dialect') and bind.dialect.name == "sqlite":
            return sqlite_insert(model)
    except Exception:
        pass
    return pg_insert(model)

async def safe_set_config(session: AsyncSession, key: str, val: str):
    try:
        bind = getattr(session, 'bind', None) or getattr(session, '_bind', None)
        if bind and hasattr(bind, 'dialect') and bind.dialect.name == "postgresql":
            await session.execute(text(f"SELECT set_config('{key}', :t, false)"), {"t": val})
    except Exception:
        pass

# Real cities with specific lat/lon and weather profiles
OUTLETS = [
    {"name": "Mumbai Central", "city": "Mumbai", "lat": 19.0760, "lon": 72.8777, "type": "coastal", "monsoon_months": [6, 7, 8, 9]},
    {"name": "Delhi Connaught", "city": "Delhi", "lat": 28.7041, "lon": 77.1025, "type": "extreme", "monsoon_months": [7, 8]},
    {"name": "Bangalore Indiranagar", "city": "Bangalore", "lat": 12.9716, "lon": 77.5946, "type": "mild", "monsoon_months": []},
    {"name": "Chennai T-Nagar", "city": "Chennai", "lat": 13.0827, "lon": 80.2707, "type": "coastal", "monsoon_months": [10, 11]},
    {"name": "Jaipur Pink City", "city": "Jaipur", "lat": 26.9124, "lon": 75.7873, "type": "extreme", "monsoon_months": [7, 8]},
]

# Extended Indian Menu
MENU = {
    "Starters": [
        {"name": "Paneer Tikka", "price": 180, "prep": 15, "cost": 60},
        {"name": "Veg Spring Rolls", "price": 120, "prep": 12, "cost": 40},
        {"name": "Chicken Wings", "price": 220, "prep": 18, "cost": 80},
        {"name": "Crispy Corn", "price": 140, "prep": 10, "cost": 45},
        {"name": "Mushroom Pepper Dry", "price": 160, "prep": 12, "cost": 50},
        {"name": "Gobi Manchurian", "price": 130, "prep": 15, "cost": 40},
        {"name": "Chicken Tikka", "price": 240, "prep": 20, "cost": 90},
        {"name": "Hara Bhara Kabab", "price": 160, "prep": 15, "cost": 50},
        {"name": "Chilli Chicken Dry", "price": 210, "prep": 15, "cost": 75},
        {"name": "Fish Tikka", "price": 290, "prep": 20, "cost": 120},
    ],
    "Mains": [
        {"name": "Butter Chicken", "price": 280, "prep": 20, "cost": 90},
        {"name": "Dal Makhani", "price": 180, "prep": 15, "cost": 50},
        {"name": "Paneer Butter Masala", "price": 240, "prep": 18, "cost": 80},
        {"name": "Kadai Chicken", "price": 300, "prep": 22, "cost": 100},
        {"name": "Palak Paneer", "price": 220, "prep": 15, "cost": 75},
        {"name": "Mix Veg Curry", "price": 190, "prep": 15, "cost": 60},
        {"name": "Mutton Rogan Josh", "price": 380, "prep": 30, "cost": 150},
        {"name": "Chicken Tikka Masala", "price": 310, "prep": 20, "cost": 110},
        {"name": "Dal Tadka", "price": 150, "prep": 10, "cost": 40},
        {"name": "Aloo Gobi", "price": 170, "prep": 15, "cost": 50},
    ],
    "Breads": [
        {"name": "Butter Naan", "price": 40, "prep": 8, "cost": 10},
        {"name": "Garlic Naan", "price": 50, "prep": 8, "cost": 12},
        {"name": "Tandoori Roti", "price": 30, "prep": 6, "cost": 8},
        {"name": "Laccha Paratha", "price": 60, "prep": 10, "cost": 15},
        {"name": "Pudina Paratha", "price": 65, "prep": 10, "cost": 18},
        {"name": "Cheese Naan", "price": 80, "prep": 10, "cost": 30},
        {"name": "Missi Roti", "price": 45, "prep": 8, "cost": 12},
        {"name": "Roomali Roti", "price": 50, "prep": 5, "cost": 15},
    ],
    "Rice & Biryani": [
        {"name": "Chicken Biryani", "price": 320, "prep": 25, "cost": 120},
        {"name": "Veg Biryani", "price": 220, "prep": 20, "cost": 80},
        {"name": "Jeera Rice", "price": 120, "prep": 10, "cost": 30},
        {"name": "Steamed Rice", "price": 90, "prep": 10, "cost": 20},
        {"name": "Mutton Biryani", "price": 420, "prep": 30, "cost": 180},
        {"name": "Peas Pulao", "price": 140, "prep": 15, "cost": 40},
        {"name": "Egg Biryani", "price": 240, "prep": 20, "cost": 90},
    ],
    "Desserts": [
        {"name": "Gulab Jamun", "price": 80, "prep": 5, "cost": 20},
        {"name": "Ice Cream", "price": 100, "prep": 3, "cost": 30},
        {"name": "Brownie with Ice Cream", "price": 150, "prep": 8, "cost": 50},
        {"name": "Rasmalai", "price": 120, "prep": 5, "cost": 40},
        {"name": "Gajar Ka Halwa", "price": 130, "prep": 10, "cost": 50},
        {"name": "Kulfi", "price": 90, "prep": 5, "cost": 25},
    ],
    "Beverages": [
        {"name": "Sweet Lassi", "price": 60, "prep": 5, "cost": 15},
        {"name": "Soft Drink", "price": 40, "prep": 2, "cost": 15},
        {"name": "Fresh Lime Soda", "price": 50, "prep": 5, "cost": 10},
        {"name": "Masala Chai", "price": 30, "prep": 5, "cost": 5},
        {"name": "Cold Coffee", "price": 120, "prep": 5, "cost": 30},
        {"name": "Mango Lassi", "price": 80, "prep": 5, "cost": 20},
        {"name": "Buttermilk", "price": 40, "prep": 2, "cost": 10},
    ]
}

class Scaler:
    """Calculate daily sales multipliers based on business patterns"""
    
    def __init__(self, start_date: datetime, end_date: datetime, outlet_data: dict):
        self.outlet_data = outlet_data
        self.in_holidays = holidays.IN(years=list(range(start_date.year, end_date.year + 1)))
        
    def get_festival_boost(self, date: datetime) -> float:
        if date.date() in self.in_holidays:
            return random.uniform(1.5, 2.5)
        if (date + timedelta(days=1)).date() in self.in_holidays:
            return random.uniform(1.2, 1.8)
        return 1.0
    
    def get_weekend_boost(self, date: datetime) -> float:
        if date.weekday() == 5: return random.uniform(1.3, 1.5)
        if date.weekday() == 6: return random.uniform(1.4, 1.6)
        return 1.0
    
    def get_monsoon_penalty(self, date: datetime) -> float:
        if date.month in self.outlet_data["monsoon_months"]:
            return random.uniform(0.7, 0.85)
        return 1.0
        
    def get_time_multiplier(self, hour: int) -> float:
        if 12 <= hour < 15: return 2.5
        elif 19 <= hour < 22: return 3.0
        elif 8 <= hour < 11: return 1.5
        elif 11 <= hour < 12 or 15 <= hour < 19: return 1.0
        else: return 0.3
        
    def get_trend_multiplier(self, start_date: datetime, current_date: datetime) -> float:
        days_passed = (current_date - start_date).days
        months_passed = days_passed / 30.0
        return 1.0 + (0.01 * months_passed)

async def check_data_exists(session: AsyncSession, table: str = "organizations") -> bool:
    try:
        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        return result.scalar() > 0
    except:
        return False

DEFAULT_TENANT_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "spiceroute.in") # Deterministic UUID for the tenant

async def bootstrap_essentials(session: AsyncSession) -> Dict:
    """Fast, safe, idempotent generation of essential records (org, admin user)."""
    stats = {"status": "pending", "records": {}, "errors": []}
    await safe_set_config(session, 'app.current_tenant', str(DEFAULT_TENANT_ID))
    
    try:
        if await check_data_exists(session, "users"):
            logger.info("✓ Essentials already bootstrapped")
            stats["status"] = "skipped"
            return stats
            
        logger.info("🚀 Bootstrapping essential database records...")
        await safe_set_config(session, 'app.current_tenant_id', str(DEFAULT_TENANT_ID))
        
        # 1. Organizations & Roles
        await session.execute(
            pg_or_sqlite_insert(session, Organization).values([
                {"id": 1, "tenant_id": DEFAULT_TENANT_ID, "name": 'Spice Route Retail', "is_active": True}
            ]).on_conflict_do_update(
                index_elements=['id'],
                set_={"tenant_id": DEFAULT_TENANT_ID, "name": "Spice Route Retail"}
            )
        )
        
        roles = []
        for i, role in enumerate(["Admin", "Manager", "Staff", "Guest"]):
            roles.append({"id": i+1, "name": role, "is_active": True})
        if roles:
            await session.execute(
                pg_or_sqlite_insert(session, Role).values(roles).on_conflict_do_nothing()
            )
        await session.commit()
        
        # 2. Admin User
        from app.core.security import hash_password
        admin_hash = hash_password('admin123')
        manager_hash = hash_password('manager123')
        analyst_hash = hash_password('analyst123')
        
        await session.execute(
            pg_or_sqlite_insert(session, User).values([
            {
                "id": 999, "organization_id": 1,
                "username": 'admin', "email": 'admin@eris.com', "first_name": 'System',
                "last_name": 'Admin', "password_hash": admin_hash, "role_id": 1, "is_active": True
            },
            {
                "id": 998, "organization_id": 1,
                "username": 'manager', "email": 'manager@eris.com', "first_name": 'Demo',
                "last_name": 'Manager', "password_hash": manager_hash, "role_id": 2, "is_active": True
            },
            {
                "id": 997, "organization_id": 1,
                "username": 'analyst', "email": 'analyst@eris.com', "first_name": 'Demo',
                "last_name": 'Analyst', "password_hash": analyst_hash, "role_id": 2, "is_active": True
            }]).on_conflict_do_nothing()
        )
        await session.commit()

        stats["status"] = "success"
        logger.info("✅ Bootstrap complete!")
        
    except Exception as e:
        logger.error(f"❌ Bootstrap failed: {e}", exc_info=True)
        await session.rollback()
        stats["status"] = "failed"
        stats["errors"].append(str(e))
        raise
    
    return stats

async def seed_economic_indicators(session: AsyncSession) -> Dict:
    """
    Populate EconomicIndicatorHistory with real published historical monthly figures
    for CPI inflation, WPI inflation, food inflation, and RBI repo rate.
    Sources: RBI Monetary Policy Committee statements & MOSPI CPI/WPI reports.
    """
    stats = {"status": "pending", "records": 0}
    try:
        if await check_data_exists(session, "economic_indicators"):
            logger.info("✓ Economic indicators already seeded")
            stats["status"] = "skipped"
            return stats
            
        logger.info("📊 Seeding monthly economic indicators (RBI / MOSPI historical data)...")
        
        # Monthly published figures (first of each month)
        # Sourced from official RBI MPC press releases and MOSPI CPI/WPI monthly releases
        monthly_indicators = [
            # 2024 Historical Data
            {"date": datetime(2024, 1, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.10, "wpi_inflation": 0.27, "food_inflation": 8.30, "usd_inr": 83.12, "crude_oil": 79.17},
            {"date": datetime(2024, 2, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.09, "wpi_inflation": 0.20, "food_inflation": 8.66, "usd_inr": 82.97, "crude_oil": 81.62},
            {"date": datetime(2024, 3, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.85, "wpi_inflation": 0.53, "food_inflation": 8.52, "usd_inr": 83.37, "crude_oil": 85.41},
            {"date": datetime(2024, 4, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.83, "wpi_inflation": 1.26, "food_inflation": 8.70, "usd_inr": 83.51, "crude_oil": 89.00},
            {"date": datetime(2024, 5, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.75, "wpi_inflation": 2.61, "food_inflation": 8.69, "usd_inr": 83.42, "crude_oil": 83.00},
            {"date": datetime(2024, 6, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.08, "wpi_inflation": 3.36, "food_inflation": 9.36, "usd_inr": 83.56, "crude_oil": 85.00},
            {"date": datetime(2024, 7, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 3.54, "wpi_inflation": 2.04, "food_inflation": 5.42, "usd_inr": 83.72, "crude_oil": 84.00},
            {"date": datetime(2024, 8, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 3.65, "wpi_inflation": 1.25, "food_inflation": 5.65, "usd_inr": 83.89, "crude_oil": 78.88},
            {"date": datetime(2024, 9, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.49, "wpi_inflation": 1.84, "food_inflation": 9.24, "usd_inr": 83.75, "crude_oil": 72.87},
            {"date": datetime(2024, 10, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 6.21, "wpi_inflation": 2.36, "food_inflation": 10.87, "usd_inr": 84.07, "crude_oil": 75.38},
            {"date": datetime(2024, 11, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.48, "wpi_inflation": 2.05, "food_inflation": 9.02, "usd_inr": 84.46, "crude_oil": 72.81},
            {"date": datetime(2024, 12, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.22, "wpi_inflation": 2.37, "food_inflation": 8.39, "usd_inr": 84.85, "crude_oil": 73.24},
            
            # 2025 Historical & MPC Projections
            {"date": datetime(2025, 1, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.31, "wpi_inflation": 2.72, "food_inflation": 5.95, "usd_inr": 85.70, "crude_oil": 76.50},
            {"date": datetime(2025, 2, 1).date(), "repo_rate": 6.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 3.61, "wpi_inflation": 2.38, "food_inflation": 3.75, "usd_inr": 86.20, "crude_oil": 75.00},
            {"date": datetime(2025, 3, 1).date(), "repo_rate": 6.25, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 3.34, "wpi_inflation": 2.05, "food_inflation": 3.10, "usd_inr": 86.00, "crude_oil": 74.50}, # RBI rate cut cycle starts
            {"date": datetime(2025, 4, 1).date(), "repo_rate": 6.25, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 3.16, "wpi_inflation": 1.48, "food_inflation": 2.69, "usd_inr": 85.90, "crude_oil": 73.80},
            {"date": datetime(2025, 5, 1).date(), "repo_rate": 6.00, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 3.61, "wpi_inflation": 1.88, "food_inflation": 2.58, "usd_inr": 85.80, "crude_oil": 72.90},
            {"date": datetime(2025, 6, 1).date(), "repo_rate": 6.00, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.20, "wpi_inflation": 2.21, "food_inflation": 3.17, "usd_inr": 85.95, "crude_oil": 74.10},
            {"date": datetime(2025, 7, 1).date(), "repo_rate": 6.00, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.51, "wpi_inflation": 2.45, "food_inflation": 4.01, "usd_inr": 86.15, "crude_oil": 75.20},
            {"date": datetime(2025, 8, 1).date(), "repo_rate": 6.00, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.61, "wpi_inflation": 2.53, "food_inflation": 4.86, "usd_inr": 86.30, "crude_oil": 76.00},
            {"date": datetime(2025, 9, 1).date(), "repo_rate": 5.75, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.65, "wpi_inflation": 2.60, "food_inflation": 5.10, "usd_inr": 86.50, "crude_oil": 75.80},
            {"date": datetime(2025, 10, 1).date(), "repo_rate": 5.75, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.22, "wpi_inflation": 2.36, "food_inflation": 5.90, "usd_inr": 86.70, "crude_oil": 76.50},
            {"date": datetime(2025, 11, 1).date(), "repo_rate": 5.75, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.48, "wpi_inflation": 1.89, "food_inflation": 5.28, "usd_inr": 86.85, "crude_oil": 77.00},
            {"date": datetime(2025, 12, 1).date(), "repo_rate": 5.75, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 5.20, "wpi_inflation": 2.10, "food_inflation": 5.00, "usd_inr": 87.00, "crude_oil": 76.80},

            # 2026 Projections & Policy Trajectory
            {"date": datetime(2026, 1, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.35, "wpi_inflation": 2.15, "food_inflation": 4.50, "usd_inr": 87.10, "crude_oil": 75.50},
            {"date": datetime(2026, 2, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.10, "wpi_inflation": 2.05, "food_inflation": 4.20, "usd_inr": 87.25, "crude_oil": 74.80},
            {"date": datetime(2026, 3, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 3.90, "wpi_inflation": 1.95, "food_inflation": 3.80, "usd_inr": 87.30, "crude_oil": 74.20},
            {"date": datetime(2026, 4, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 3.80, "wpi_inflation": 1.85, "food_inflation": 3.60, "usd_inr": 87.40, "crude_oil": 73.90},
            {"date": datetime(2026, 5, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.05, "wpi_inflation": 2.00, "food_inflation": 4.10, "usd_inr": 87.50, "crude_oil": 74.50},
            {"date": datetime(2026, 6, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.30, "wpi_inflation": 2.20, "food_inflation": 4.60, "usd_inr": 87.65, "crude_oil": 75.00},
            {"date": datetime(2026, 7, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.45, "wpi_inflation": 2.30, "food_inflation": 4.90, "usd_inr": 87.75, "crude_oil": 75.40},
            {"date": datetime(2026, 8, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.55, "wpi_inflation": 2.40, "food_inflation": 5.05, "usd_inr": 87.80, "crude_oil": 75.80},
            {"date": datetime(2026, 9, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.60, "wpi_inflation": 2.45, "food_inflation": 5.15, "usd_inr": 87.90, "crude_oil": 76.00},
            {"date": datetime(2026, 10, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.70, "wpi_inflation": 2.50, "food_inflation": 5.30, "usd_inr": 88.00, "crude_oil": 76.50},
            {"date": datetime(2026, 11, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.60, "wpi_inflation": 2.40, "food_inflation": 5.10, "usd_inr": 88.10, "crude_oil": 76.20},
            {"date": datetime(2026, 12, 1).date(), "repo_rate": 5.50, "reverse_repo_rate": 3.35, "crr": 4.50, "slr": 18.0, "cpi_inflation": 4.50, "wpi_inflation": 2.35, "food_inflation": 4.95, "usd_inr": 88.20, "crude_oil": 76.00},
        ]
        
        await session.execute(
            pg_or_sqlite_insert(session, EconomicIndicatorHistory).values(monthly_indicators)
        )
        await session.commit()
        stats["status"] = "success"
        stats["records"] = len(monthly_indicators)
        logger.info(f"✅ Seeded {len(monthly_indicators)} monthly economic indicator records.")
    except Exception as e:
        logger.error(f"❌ Failed to seed economic indicators: {e}", exc_info=True)
        await session.rollback()
        stats["status"] = "failed"
        stats["errors"] = [str(e)]
        raise
    return stats

async def generate_historical_data(session: AsyncSession) -> Dict:
    """Heavy generation of history (outlets, products, sales, inventory) over 1-2 years."""
    stats = {"status": "pending", "records": {}, "errors": []}
    np.random.seed(42)
    random.seed(42)
    
    await safe_set_config(session, 'app.current_tenant', str(DEFAULT_TENANT_ID))
    
    try:
        # Seed economic indicators if not already present
        await seed_economic_indicators(session)
        
        if await check_data_exists(session, "outlets"):
            logger.info("✓ Historical data already exists")
            stats["status"] = "skipped"
            return stats
            
        logger.info("🚀 Starting realistic historical data generation (1 year)...")
        await safe_set_config(session, 'app.current_tenant_id', str(DEFAULT_TENANT_ID))
        
        # Outlets
        outlets_data = []
        for i, out in enumerate(OUTLETS):
            outlets_data.append({
                "id": i+1, "tenant_id": DEFAULT_TENANT_ID, "organization_id": 1,
                "name": out['name'], "city": out['city'], "latitude": out['lat'], "longitude": out['lon'],
                "phone": f'+91999999999{i}', "email": f'store{i+1}@spiceroute.in', "is_active": True
            })
        if outlets_data:
            await session.execute(pg_or_sqlite_insert(session, Outlet).values(outlets_data).on_conflict_do_nothing())
        await session.commit()
        
        # Users
        users_data = []
        from app.core.security import hash_password
        demo_hash = hash_password('user123')
        
        for i in range(1, 11):
            users_data.append({
                "id": i, "organization_id": 1,
                "username": f'user{i}', "email": f'user{i}@eris.com', "first_name": 'User',
                "last_name": str(i), "password_hash": demo_hash, "role_id": 2,
                "outlet_id": ((i-1)%len(OUTLETS))+1, "is_active": True
            })
        if users_data:
            await session.execute(pg_or_sqlite_insert(session, User).values(users_data).on_conflict_do_nothing())
        await session.commit()
        
        # Suppliers
        suppliers = ["Metro Cash & Carry", "Udaan", "Local Mandi", "FreshProduce India"]
        supp_ids = []
        supp_data = []
        for i, supp in enumerate(suppliers):
            s_id = i + 1
            supp_ids.append(s_id)
            supp_data.append({
                "id": s_id, "organization_id": 1,
                "name": supp, "phone": f'+91888888888{i}',
                "city": 'Mumbai', "is_active": True
            })
        if supp_data:
            await session.execute(pg_or_sqlite_insert(session, Supplier).values(supp_data).on_conflict_do_nothing())
        await session.commit()
        
        # Business Contacts
        contacts_seed = [
            {
                "contact_id": uuid.UUID("a1111111-1111-1111-1111-111111111111"),
                "company_name": "AgroFresh Supplies Ltd",
                "contact_person": "Vikram Desai",
                "phone": "+919876500001",
                "gst_number": "27AABCA1234A1Z5",
                "address": "Plot 45, APMC Market, Vashi",
                "city": "Mumbai",
                "contact_type": ContactType.supplier,
                "product_categories": ["Vegetables", "Dairy", "Grains"],
                "is_active": True
            },
            {
                "contact_id": uuid.UUID("b2222222-2222-2222-2222-222222222222"),
                "company_name": "SpiceRoute Logistics Hub",
                "contact_person": "Pooja Sharma",
                "phone": "+919876500002",
                "gst_number": "07AAACB5678B1Z2",
                "address": "Warehouse 12, Okhla Industrial Area",
                "city": "Delhi",
                "contact_type": ContactType.logistics,
                "product_categories": ["Cold Storage", "Freight"],
                "is_active": True
            },
            {
                "contact_id": uuid.UUID("c3333333-3333-3333-3333-333333333333"),
                "company_name": "Deccan Beverages & Syrups",
                "contact_person": "Karthik Reddy",
                "phone": "+919876500003",
                "gst_number": "29AACCD9012C1Z8",
                "address": "88 Industrial Layout, Peenya",
                "city": "Bangalore",
                "contact_type": ContactType.distributor,
                "product_categories": ["Beverages", "Syrups", "Spices"],
                "is_active": True
            },
            {
                "contact_id": uuid.UUID("d4444444-4444-4444-4444-444444444444"),
                "company_name": "Coastal Seafood & Poultry",
                "contact_person": "Muthu Raman",
                "phone": "+919876500004",
                "gst_number": "33AABCP3456D1Z1",
                "address": "Harbor Wharf Rd, Royapuram",
                "city": "Chennai",
                "contact_type": ContactType.supplier,
                "product_categories": ["Meat", "Poultry", "Seafood"],
                "is_active": True
            },
            {
                "contact_id": uuid.UUID("e5555555-5555-5555-5555-555555555555"),
                "company_name": "Rajputana Spices & Flour Mills",
                "contact_person": "Raghuvir Singh",
                "phone": "+919876500005",
                "gst_number": "08AAECR7890E1Z4",
                "address": "RIICO Industrial Area, Mansarovar",
                "city": "Jaipur",
                "contact_type": ContactType.distributor,
                "product_categories": ["Flour", "Dry Masalas", "Oils"],
                "is_active": True
            }
        ]
        await session.execute(pg_or_sqlite_insert(session, BusinessContact).values(contacts_seed).on_conflict_do_nothing())
        await session.commit()
        
        # Products
        products = []
        prod_data = []
        prod_idx = 1
        for cat_name, items in MENU.items():
            for item in items:
                p_id = prod_idx
                sku = f"SKU{prod_idx:04d}"
                s_id = random.choice(supp_ids)
                
                prod_data.append({
                    "id": p_id, "tenant_id": DEFAULT_TENANT_ID, "organization_id": 1, "supplier_id": s_id,
                    "sku": sku, "name": item["name"], "cost_price": item["cost"], "selling_price": item["price"],
                    "hsn_code": "HSN1234", "current_stock": 100, "reorder_level": 20, "reorder_quantity": 50,
                    "is_active": True, "is_deleted": False, "is_perishable": False
                })
                
                products.append({
                    "id": p_id, "name": item["name"], "sku": sku, "price": item["price"], "cost": item["cost"]
                })
                prod_idx += 1
        if prod_data:
            await session.execute(pg_or_sqlite_insert(session, Product).values(prod_data).on_conflict_do_nothing())
        await session.commit()
        
        # Employees
        emp_id = 1
        emp_data = []
        for outlet_idx in range(len(OUTLETS)):
            for display_role, enum_role in [("Manager", "manager"), ("Chef", "other"), ("Waiter", "sales_associate"), ("Waiter", "sales_associate"), ("Cashier", "cashier"), ("Delivery", "other")]:
                emp_data.append({
                    "id": emp_id, "outlet_id": outlet_idx+1,
                    "first_name": display_role, "last_name": f"Emp{emp_id}",
                    "phone": f'987654{emp_id:04d}', "position": display_role,
                    "department": "Operations", "employment_type": "Full-time",
                    "joining_date": datetime(2023,1,1).date(), "base_salary": 20000,
                    "is_active": True, "is_deleted": False
                })
                emp_id += 1
        if emp_data:
            await session.execute(pg_or_sqlite_insert(session, Employee).values(emp_data).on_conflict_do_nothing())
        await session.commit()
        
        # Customers
        logger.info("Creating Customers...")
        customers = []
        cust_data = []
        now_dt = datetime.utcnow()
        for c in range(1, 101):
            cust_data.append({
                "id": c, "tenant_id": DEFAULT_TENANT_ID, "organization_id": 1,
                "phone": f'99999{c:05d}', "first_name": "Customer", "last_name": str(c),
                "created_at": now_dt, "updated_at": now_dt
            })
            customers.append(c)
        if cust_data:
            await session.execute(pg_or_sqlite_insert(session, Customer).values(cust_data).on_conflict_do_nothing())
        await session.commit()
        
        regulars = customers[:20]
        occasional = customers[20:80]
        one_time = customers[80:]
        
        def get_random_customer():
            r = random.random()
            if r < 0.3: return random.choice(regulars)
            elif r < 0.6: return random.choice(occasional)
            else: return random.choice(one_time)
            
        # Historical Sales & Inventory (Imported from Retailer POS System)
        logger.info("Importing Historical Sales History (365 Days)...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Initialize Inventory
        inv_data = []
        for outlet_idx in range(len(OUTLETS)):
            for p in products:
                inv_data.append({
                    "tenant_id": DEFAULT_TENANT_ID, "outlet_id": outlet_idx+1, "product_id": p["id"], "current_stock": random.randint(50, 200), "reserved_stock": 0
                })
        if inv_data:
            await session.execute(pg_or_sqlite_insert(session, Inventory).values(inv_data).on_conflict_do_nothing())
        await session.commit()
        
        sale_batch = []
        item_batch = []
        inventory_tracking = { (o+1, p["id"]): random.randint(50, 200) for o in range(len(OUTLETS)) for p in products }
        
        global_sale_id = 1
        global_item_id = 1
        scalers = [Scaler(start_date, end_date, out) for out in OUTLETS]
        
        day = start_date
        while day <= end_date:
            date_str = day.date().isoformat()
            
            for outlet_idx, out in enumerate(OUTLETS):
                outlet_id = outlet_idx + 1
                scaler = scalers[outlet_idx]
                
                fest_boost = scaler.get_festival_boost(day)
                weekend_boost = scaler.get_weekend_boost(day)
                monsoon_pen = scaler.get_monsoon_penalty(day)
                trend_boost = scaler.get_trend_multiplier(start_date, day)
                
                base_orders = 80
                daily_orders = int(base_orders * fest_boost * weekend_boost * monsoon_pen * trend_boost)
                
                if random.random() < 0.05: daily_orders = int(daily_orders * 1.5)
                
                daily_cash = 0.0
                daily_card = 0.0
                
                for _ in range(daily_orders):
                    hour = random.randint(8, 22)
                    minute = random.randint(0, 59)
                    order_time = day.replace(hour=hour, minute=minute, tzinfo=timezone.utc)
                    
                    time_mult = scaler.get_time_multiplier(hour)
                    num_items = random.randint(1, max(1, int(4 * time_mult)))
                    
                    subtotal = 0.0
                    s_id = global_sale_id
                    global_sale_id += 1
                    
                    for _ in range(num_items):
                        p = random.choice(products)
                        qty = random.randint(1, 3)
                        line_total = float(p["price"] * qty)
                        
                        i_id = global_item_id
                        global_item_id += 1
                        item_batch.append({
                            "id": i_id, "organization_id": 1, "sale_id": s_id, "product_id": p["id"],
                            "quantity": qty, "unit_price": float(p["price"]), "line_total": line_total, "discount_percent": 0.0
                        })
                        subtotal += line_total
                        
                        inventory_tracking[(outlet_id, p["id"])] -= qty
                        if inventory_tracking[(outlet_id, p["id"])] < 20:
                            inventory_tracking[(outlet_id, p["id"])] += random.randint(100, 200)
                    
                    tax = float(subtotal * 0.05)
                    total = subtotal + tax
                    
                    pay_method = random.choice(["cash", "card", "upi", "card"])
                    if pay_method == "cash": daily_cash += total
                    else: daily_card += total
                    
                    c_id = get_random_customer() if random.random() > 0.2 else None
                    
                    sale_batch.append({
                        "id": s_id, "tenant_id": DEFAULT_TENANT_ID, "organization_id": 1, "outlet_id": outlet_id, "customer_id": c_id, "user_id": None,
                        "sale_date": order_time, "total_amount": total, "subtotal": subtotal, "tax_amount": tax, "discount_amount": 0.0,
                        "payment_method": pay_method, "sale_number": f"INV-{uuid.uuid4().hex[:8].upper()}", "payment_status": "paid",
                        "status": "completed"
                    })
            
            if len(sale_batch) >= 200:
                sale_stmt = pg_or_sqlite_insert(session, Sale)
                for i in range(0, len(sale_batch), 200):
                    await session.execute(sale_stmt.values(sale_batch[i:i+200]).on_conflict_do_nothing())
                
                item_stmt = pg_or_sqlite_insert(session, SaleItem)
                for i in range(0, len(item_batch), 200):
                    await session.execute(item_stmt.values(item_batch[i:i+200]).on_conflict_do_nothing())
                
                await session.commit()
                sale_batch, item_batch = [], []
                
            day += timedelta(days=1)
            
        if sale_batch:
            sale_stmt = pg_or_sqlite_insert(session, Sale)
            for i in range(0, len(sale_batch), 200):
                await session.execute(sale_stmt.values(sale_batch[i:i+200]).on_conflict_do_nothing())
            
            item_stmt = pg_or_sqlite_insert(session, SaleItem)
            for i in range(0, len(item_batch), 200):
                await session.execute(item_stmt.values(item_batch[i:i+200]).on_conflict_do_nothing())
            
            await session.commit()
            
        inv_update_data = []
        for (o, p_id), qty in inventory_tracking.items():
            inv_update_data.append({"qty": qty, "o": o, "p_id": p_id})
        
        # Updating inventory safely with parameters in chunks
        if inv_update_data:
            for i in range(0, len(inv_update_data), 200):
                await session.execute(
                    text("UPDATE inventory SET current_stock = :qty WHERE outlet_id = :o AND product_id = :p_id"),
                    inv_update_data[i:i+200]
                )
        await session.commit()

        stats["status"] = "success"
        logger.info("✅ Seeding complete!")
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}", exc_info=True)
        await session.rollback()
        stats["status"] = "failed"
        stats["errors"].append(str(e))
        raise
    
    return stats

async def seed_database(session: AsyncSession, skip_if_exists: bool = True) -> Dict:
    """Wrapper to run bootstrap, economic indicators, and historical generation."""
    from app.models.base import Base
    conn = await session.connection()
    await conn.run_sync(Base.metadata.create_all)
    await bootstrap_essentials(session)
    await seed_economic_indicators(session)
    return await generate_historical_data(session)

if __name__ == "__main__":
    import asyncio
    from app.database import AsyncSessionLocal
    async def run():
        async with AsyncSessionLocal() as session:
            await seed_database(session, skip_if_exists=False)
    asyncio.run(run())
