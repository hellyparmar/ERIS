#!/usr/bin/env python3
"""Direct data loader execution"""
import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(__file__))

from load_petpooja_18months_data import PetpoojaDataLoader
from pathlib import Path

data_dir = Path("/tmp/petpooja_18months_data")

print("=" * 80)
print("PETPOOJA 18-MONTH DATASET LOADER")
print("=" * 80)

try:
    loader = PetpoojaDataLoader()
    
    # Load each entity type
    print("\n1️⃣  Loading products...")
    products_count = loader.load_products(str(data_dir / "products.csv"))
    print(f"✅ Products loaded: {products_count}")
    
    print("\n2️⃣  Loading customers...")
    customers_count = loader.load_customers(str(data_dir / "customers.csv"))
    print(f"✅ Customers loaded: {customers_count}")
    
    print("\n3️⃣  Loading sales...")
    sales_count = loader.load_sales(str(data_dir / "sales.csv"))
    print(f"✅ Sales loaded: {sales_count}")
    
    print("\n4️⃣  Loading sale items...")
    sale_items_count = loader.load_sale_items(str(data_dir / "sale_items.csv"))
    print(f"✅ Sale items loaded: {sale_items_count}")
    
    print("\n5️⃣  Loading invoices...")
    invoices_count = loader.load_invoices(str(data_dir / "invoices.csv"))
    print(f"✅ Invoices loaded: {invoices_count}")
    
    print("\n6️⃣  Loading employees...")
    employees_count = loader.load_employees(str(data_dir / "employees.csv"))
    print(f"✅ Employees loaded: {employees_count}")
    
    print("\n" + "=" * 80)
    print("📊 DATA LOAD SUMMARY")
    print("=" * 80)
    print(f"Products:      {products_count}")
    print(f"Customers:     {customers_count}")
    print(f"Sales:         {sales_count}")
    print(f"Sale Items:    {sale_items_count}")
    print(f"Invoices:      {invoices_count}")
    print(f"Employees:     {employees_count}")
    print("\n✅ All data loaded successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
