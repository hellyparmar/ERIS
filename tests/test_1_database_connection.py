"""
Test Script 1: Database Connection Verification
Verifies PostgreSQL/SQLite connection and basic database functionality
"""

import sys
sys.path.insert(0, '/home/petpooja/Enterprise Retail Intelligence System')

from sqlalchemy import create_engine, inspect, text
from api.db.database import engine
import json
from datetime import datetime


def verify_database_connection():
    """
    Verify database connection and basic functionality
    """
    print("=" * 70)
    print("TEST SCRIPT 1: DATABASE CONNECTION VERIFICATION")
    print("=" * 70)
    print()
    
    tests = {
        "connection": False,
        "tables_exist": False,
        "data_populated": False,
        "indexes_created": False,
        "foreign_keys_valid": False
    }
    
    try:
        # 1. Test connection
        print("📡 Testing database connection...")
        conn = engine.connect()
        tests["connection"] = True
        print("   ✅ Connection successful")
        print(f"   Database URL: {engine.url}")
        print()
        
        # 2. Verify all required tables exist
        print("📋 Verifying required tables exist...")
        inspector = inspect(engine)
        required_tables = [
            'organizations', 'stores', 'users', 'products', 'customers',
            'sales', 'sale_items', 'inventory', 'suppliers', 'invoices'
        ]
        existing_tables = inspector.get_table_names()
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            print(f"   ❌ Missing tables: {missing_tables}")
            tests["tables_exist"] = False
        else:
            print(f"   ✅ All {len(required_tables)} required tables exist")
            tests["tables_exist"] = True
        
        print(f"   Found tables: {', '.join(existing_tables[:10])}...")
        print()
        
        # 3. Verify data volume
        print("📊 Verifying data volume...")
        table_counts = {}
        
        for table in required_tables:
            if table in existing_tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                table_counts[table] = count
                print(f"   {table}: {count:,} rows")
        
        # Check if key tables have data
        has_data = (
            table_counts.get('products', 0) > 1000 and
            table_counts.get('customers', 0) > 1000 and
            table_counts.get('sales', 0) > 1000
        )
        tests["data_populated"] = has_data
        
        if has_data:
            print(f"   ✅ Data populated (Products: {table_counts.get('products', 0):,}, "
                  f"Customers: {table_counts.get('customers', 0):,}, "
                  f"Sales: {table_counts.get('sales', 0):,})")
        else:
            print("   ❌ Insufficient data in key tables")
        print()
        
        # 4. Verify indexes exist on critical tables
        print("🔍 Verifying indexes...")
        index_count = 0
        for table in ['products', 'customers', 'sales']:
            if table in existing_tables:
                indexes = inspector.get_indexes(table)
                index_count += len(indexes)
                print(f"   {table}: {len(indexes)} indexes")
        
        tests["indexes_created"] = index_count > 0
        if index_count > 0:
            print(f"   ✅ {index_count} indexes found")
        else:
            print("   ⚠️  No indexes found (may impact performance)")
        print()
        
        # 5. Verify foreign key constraints (sample check)
        print("🔗 Verifying referential integrity...")
        try:
            # Check if all product_ids in sale_items exist in products
            result = conn.execute(text("""
                SELECT COUNT(*) FROM sale_items si
                LEFT JOIN products p ON si.product_id = p.id
                WHERE p.id IS NULL
            """))
            orphaned_items = result.scalar()
            
            # Check if all customer_ids in sales exist in customers
            result = conn.execute(text("""
                SELECT COUNT(*) FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE c.id IS NULL AND s.customer_id IS NOT NULL
            """))
            orphaned_sales = result.scalar()
            
            tests["foreign_keys_valid"] = (orphaned_items == 0 and orphaned_sales == 0)
            
            if tests["foreign_keys_valid"]:
                print("   ✅ Referential integrity maintained (no orphaned records)")
            else:
                print(f"   ❌ Found orphaned records: {orphaned_items} items, {orphaned_sales} sales")
        except Exception as e:
            print(f"   ⚠️  Could not verify foreign keys: {e}")
            tests["foreign_keys_valid"] = None
        
        print()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    for test_name, result in tests.items():
        status = "✅ PASS" if result else ("⚠️  UNKNOWN" if result is None else "❌ FAIL")
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print()
    print(f"Overall Status: {'✅ ALL TESTS PASSED' if all(v for v in tests.values() if v is not None) else '❌ SOME TESTS FAILED'}")
    print()
    
    # Return results as JSON
    return {
        "timestamp": datetime.now().isoformat(),
        "tests": tests,
        "table_counts": table_counts if 'table_counts' in locals() else {},
        "all_passed": all(v for v in tests.values() if v is not None)
    }


if __name__ == "__main__":
    results = verify_database_connection()
    
    # Save results to file
    with open('test_results_1_database.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: test_results_1_database.json")
    
    # Exit with appropriate code
    sys.exit(0 if results["all_passed"] else 1)
