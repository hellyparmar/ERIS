"""
Database Seeding Script for ERIS Synthetic Data

This script loads synthetic data from CSV files into the PostgreSQL database.
It respects foreign key constraints by loading tables in the correct order.

Usage: python scripts/seed_database.py

Requirements:
- DATABASE_URL environment variable must be set
- CSV files in scripts/synthetic_data/
- SQLAlchemy and pandas installed

Note: ExternalRegressor model does not exist yet. The following model is needed:

class ExternalRegressor(Base):
    __tablename__ = "external_regressors"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    temperature_max_celsius = Column(Float)
    cpi_index = Column(Float)
    fuel_price_inr_per_litre = Column(Float)
    is_holiday = Column(Boolean)
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Outlet, Vendor, Product, Inventory, Sale  # ExternalRegressor not available yet

# Note: ExternalRegressor model is missing from app.models
# For now, external_regressors table will be skipped

def main():
    # Database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)

    data_dir = "scripts/synthetic_data"

    # Table loading order (respecting foreign keys)
    tables_config = [
        ("outlets", Outlet, None),
        ("suppliers", Vendor, None),  # Using Vendor as Supplier
        ("products", Product, None),
        ("inventory", Inventory, None),
        ("sales_transactions", Sale, None),  # Using Sale as SalesTransaction
        # ("external_regressors", ExternalRegressor, None),  # Model not available
    ]

    print("🚀 Starting ERIS Database Seeding")
    print("=" * 50)

    for table_name, model, date_columns in tables_config:
        try:
            csv_path = f"{data_dir}/{table_name}.csv"
            if not os.path.exists(csv_path):
                print(f"⚠️  CSV file not found: {csv_path}")
                continue

            # Check if table already has data
            with engine.connect() as conn:
                count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                existing_count = conn.execute(count_query).scalar()

            if existing_count > 0:
                print(f"⏭️  Skipping {table_name}: already has {existing_count} records")
                continue

            # Read CSV
            df = pd.read_csv(csv_path)

            # Handle date columns
            if date_columns:
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col]).dt.date

            # Special handling for sales_transactions
            if table_name == "sales_transactions":
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['sale_date'] = df['timestamp'].dt.date
                    df['created_at'] = df['timestamp']
                # Map CSV columns to model columns
                df = df.rename(columns={
                    'id': 'id',
                    'outlet_id': 'outlet_id',
                    'product_id': 'product_id',
                    'quantity': 'quantity',
                    'unit_price': 'unit_price',
                    'total_amount': 'total_amount',
                    'gst_amount': 'gst_amount',
                    'payment_method': 'payment_mode',
                    'cashier_id': 'cashier_id'  # Assuming Sale model has cashier_id or ignore
                })

            # Special handling for inventory
            elif table_name == "inventory":
                if 'last_restocked_at' in df.columns:
                    df['last_restocked'] = pd.to_datetime(df['last_restocked_at']).dt.date
                df = df.rename(columns={
                    'current_stock': 'current_stock',
                    'reorder_point': 'reorder_level',
                    'max_stock': 'max_stock'
                })

            # Special handling for suppliers (vendors)
            elif table_name == "suppliers":
                df = df.rename(columns={
                    'id': 'id',
                    'name': 'name',
                    'contact_person': 'company',  # Map to company
                    'phone': 'phone',
                    'email': 'email',
                    'gstin': 'gstin',
                    'city': 'city',
                    'average_lead_time_days': 'payment_terms',  # Approximate mapping
                    'rating': 'notes'  # Store rating in notes
                })

            # Bulk insert in batches
            batch_size = 1000
            total_records = len(df)
            session = Session()

            try:
                for i in range(0, total_records, batch_size):
                    batch_df = df.iloc[i:i+batch_size]
                    records = batch_df.to_dict('records')

                    # Clean records (remove NaN, handle None)
                    for record in records:
                        for key, value in record.items():
                            if pd.isna(value):
                                record[key] = None

                    session.bulk_insert_mappings(model, records)
                    session.commit()

                    progress = min(i + batch_size, total_records)
                    print(f"📊 {table_name}: {progress}/{total_records} records inserted")

                print(f"✅ {table_name}: {total_records} records loaded successfully")

            except Exception as e:
                session.rollback()
                print(f"❌ Error inserting into {table_name}: {e}")
                continue
            finally:
                session.close()

        except Exception as e:
            print(f"❌ Error processing {table_name}: {e}")
            continue

    # Verification summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)

    verification_tables = ["outlets", "vendors", "products", "inventory", "sales", "external_regressors"]

    for table_name in verification_tables:
        try:
            with engine.connect() as conn:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                print(f"{table_name}: {count} records")
        except Exception as e:
            print(f"{table_name}: Error - {e}")

    print("\n🎉 Database seeding completed!")
    print("Note: external_regressors table was skipped due to missing model.")

if __name__ == "__main__":
    main()</content>
<parameter name="filePath">/home/petpooja/Enterprise Retail Intelligence System/backend/scripts/seed_database.py