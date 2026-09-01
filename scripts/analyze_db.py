
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from api.db.database import engine

def check_data():
    with engine.connect() as conn:
        print("--- DISITINCT CATEGORIES ---")
        cats = conn.execute(text("SELECT category, count(*) FROM products GROUP BY category")).fetchall()
        for c in cats:
            print(f"{c[0]}: {c[1]}")
            
        print("\n--- SALES DATE RANGE ---")
        dates = conn.execute(text("SELECT min(transaction_date), max(transaction_date), count(*) FROM sales")).fetchone()
        print(f"Min Date: {dates[0]}")
        print(f"Max Date: {dates[1]}")
        print(f"Total Sales: {dates[2]}")
        
        print("\n--- SALES LAST 30 DAYS (Simulation) ---")
        # Assuming current date is relevant, checking distribution
        # If data is 2024-2025, and app defaults to 'now', we need to align.
        
if __name__ == "__main__":
    check_data()
