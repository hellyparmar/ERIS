"""
Minimal seed script for R-DIOS restaurant management system
Run from project root: python3 scripts/seed_minimal.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from passlib.context import CryptContext
from datetime import datetime, date, timedelta
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="eris_admin",
    password="JnCSXvJLgIY7V8KtUd2TT26QXkbgvuwv",
    dbname="eris_production"
)
cur = conn.cursor()

print("Starting database seeding...")

# Check table structure first
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position;")
user_cols = [r[0] for r in cur.fetchall()]
print(f"Users table columns: {user_cols}")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='organizations' ORDER BY ordinal_position;")
org_cols = [r[0] for r in cur.fetchall()]
print(f"Organizations table columns: {org_cols}")

conn.commit()
cur.close()
conn.close()
print("Schema inspection complete. Ready to seed.")
