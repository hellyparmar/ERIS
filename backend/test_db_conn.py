from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
print(f"Testing connection to: {db_url}")

try:
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✅ Connection successful!")
    print(f"Tables found: {tables}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
