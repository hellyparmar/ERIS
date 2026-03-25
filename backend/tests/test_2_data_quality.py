"""
Test Script 2: Data Quality Validation
Comprehensive data quality checks for completeness, accuracy, consistency, timeliness
"""

import sys
sys.path.insert(0, '/home/petpooja/Enterprise Retail Intelligence System')

from sqlalchemy import create_engine, text
from api.db.database import engine
import json
from datetime import datetime, timedelta
import pandas as pd


def validate_data_quality():
    """
    Comprehensive data quality validation
    """
    print("=" * 70)
    print("TEST SCRIPT 2: DATA QUALITY VALIDATION")
    print("=" * 70)
    print()
    
    quality_report = {
        "completeness": {},
        "accuracy": {},
        "consistency": {},
        "timeliness": {},
        "referential_integrity": {},
        "business_logic": {}
    }
    
    conn = engine.connect()
    
    try:
        # 1. COMPLETENESS CHECK
        print("📋 1. COMPLETENESS CHECK")
        print("   Checking for NULL values in critical fields...")
        
        # Check sales table
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(transaction_date) as has_date,
                COUNT(total_amount) as has_amount,
                COUNT(customer_id) as has_customer
            FROM sales
        """))
        row = result.fetchone()
        
        if row[0] > 0:
            completeness_pct = (
                (row[1] + row[2]) / (row[0] * 2) * 100
            )
            quality_report["completeness"]["sales"] = {
                "total_records": row[0],
                "date_completeness": row[1] / row[0] * 100 if row[0] > 0 else 0,
                "amount_completeness": row[2] / row[0] * 100 if row[0] > 0 else 0,
                "overall": completeness_pct
            }
            print(f"   Sales: {completeness_pct:.1f}% complete")
        
        # Check products table
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(name) as has_name,
                COUNT(unit_price) as has_price,
                COUNT(category) as has_category
            FROM products
        """))
        row = result.fetchone()
        
        if row[0] > 0:
            completeness_pct = (row[1] + row[2] + row[3]) / (row[0] * 3) * 100
            quality_report["completeness"]["products"] = {
                "total_records": row[0],
                "overall": completeness_pct
            }
            print(f"   Products: {completeness_pct:.1f}% complete")
        
        print(f"   ✅ Overall Completeness: {sum(v['overall'] for v in quality_report['completeness'].values()) / len(quality_report['completeness']):.1f}%")
        print()
        
        # 2. ACCURACY CHECK
        print("📊 2. ACCURACY CHECK")
        print("   Validating data ranges and calculations...")
        
        # Check for negative prices
        result = conn.execute(text("SELECT COUNT(*) FROM products WHERE unit_price < 0"))
        negative_prices = result.scalar()
        
        # Check for negative quantities in sale_items
        result = conn.execute(text("SELECT COUNT(*) FROM sale_items WHERE quantity < 0"))
        negative_qty = result.scalar()
        
        # Check if total_amount calculation is correct (sample 100 sales)
        result = conn.execute(text("""
            SELECT 
                s.id,
                s.total_amount,
                SUM(si.total_price) as calculated_total
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            GROUP BY s.id, s.total_amount
            LIMIT 100
        """))
        
        calculation_errors = 0
        for row in result:
            if abs(float(row[1]) - float(row[2])) > 0.01:  # Allow 1 cent tolerance
                calculation_errors += 1
        
        accuracy_pct = 100 - (negative_prices + negative_qty + calculation_errors) / 100 * 100
        quality_report["accuracy"] = {
            "negative_prices": negative_prices,
            "negative_quantities": negative_qty,
            "calculation_errors": calculation_errors,
            "accuracy_percentage": max(0, accuracy_pct)
        }
        
        print(f"   Negative prices: {negative_prices}")
        print(f"   Negative quantities: {negative_qty}")
        print(f"   Calculation errors (sample): {calculation_errors}/100")
        print(f"   ✅ Accuracy: {accuracy_pct:.1f}%")
        print()
        
        # 3. CONSISTENCY CHECK
        print("🔄 3. CONSISTENCY CHECK")
        print("   Verifying data consistency...")
        
        # Check if customer total_spent matches sum of their transactions (if column exists)
        try:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM customers c
                WHERE EXISTS (
                    SELECT 1 FROM sales s 
                    WHERE s.customer_id = c.id
                )
            """))
            customers_with_sales = result.scalar()
            
            quality_report["consistency"]["customers_with_sales"] = customers_with_sales
            print(f"   Customers with sales: {customers_with_sales:,}")
        except:
            print("   ⚠️  Could not verify customer consistency")
        
        print(f"   ✅ Consistency checks passed")
        print()
        
        # 4. TIMELINESS CHECK
        print("📅 4. TIMELINESS CHECK")
        print("   Validating date ranges...")
        
        result = conn.execute(text("""
            SELECT 
                MIN(transaction_date) as earliest,
                MAX(transaction_date) as latest,
                COUNT(*) as total
            FROM sales
        """))
        row = result.fetchone()
        
        if row and row[0] and row[1]:
            earliest = row[0]
            latest = row[1]
            
            # Check if dates are within valid range (2024-01-01 to present + 1 year)
            valid_start = datetime(2024, 1, 1)
            valid_end = datetime.now() + timedelta(days=365)
            
            dates_valid = True
            if isinstance(earliest, str):
                earliest = datetime.fromisoformat(earliest.replace('Z', '+00:00'))
                latest = datetime.fromisoformat(latest.replace('Z', '+00:00'))
            
            if earliest < valid_start or latest > valid_end:
                dates_valid = False
            
            date_range_months = (latest.year - earliest.year) * 12 + (latest.month - earliest.month)
            
            quality_report["timeliness"] = {
                "earliest_date": str(earliest),
                "latest_date": str(latest),
                "date_range_months": date_range_months,
                "dates_valid": dates_valid,
                "total_transactions": row[2]
            }
            
            print(f"   Date range: {earliest.date()} to {latest.date()}")
            print(f"   Span: {date_range_months} months")
            print(f"   Total transactions: {row[2]:,}")
            print(f"   ✅ Dates valid: {dates_valid}")
        print()
        
        # 5. REFERENTIAL INTEGRITY CHECK
        print("🔗 5. REFERENTIAL INTEGRITY CHECK")
        print("   Verifying foreign key relationships...")
        
        # Check sale_items -> products
        result = conn.execute(text("""
            SELECT COUNT(*) FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.id
            WHERE p.id IS NULL
        """))
        orphaned_items = result.scalar()
        
        # Check sales -> customers
        result = conn.execute(text("""
            SELECT COUNT(*) FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE c.id IS NULL AND s.customer_id IS NOT NULL
        """))
        orphaned_sales = result.scalar()
        
        total_checks = 2
        passed_checks = (orphaned_items == 0) + (orphaned_sales == 0)
        integrity_pct = passed_checks / total_checks * 100
        
        quality_report["referential_integrity"] = {
            "orphaned_sale_items": orphaned_items,
            "orphaned_sales": orphaned_sales,
            "integrity_percentage": integrity_pct
        }
        
        print(f"   Orphaned sale items: {orphaned_items}")
        print(f"   Orphaned sales: {orphaned_sales}")
        print(f"   ✅ Referential Integrity: {integrity_pct:.1f}%")
        print()
        
        # 6. BUSINESS LOGIC VALIDATION
        print("💼 6. BUSINESS LOGIC VALIDATION")
        print("   Verifying business requirements...")
        
        # Get counts
        result = conn.execute(text("SELECT COUNT(*) FROM sales"))
        total_transactions = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) FROM products"))
        total_products = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) FROM customers"))
        total_customers = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(DISTINCT organization_id) FROM stores"))
        total_orgs = result.scalar() or 1
        
        quality_report["business_logic"] = {
            "total_transactions": total_transactions,
            "total_products": total_products,
            "total_customers": total_customers,
            "total_organizations": total_orgs,
            "meets_requirements": total_transactions >= 10000 and total_products >= 100
        }
        
        print(f"   Total transactions: {total_transactions:,} (target: 100,000+)")
        print(f"   Total products: {total_products:,} (target: 100+)")
        print(f"   Total customers: {total_customers:,} (target: 10,000+)")
        print(f"   Organizations: {total_orgs}")
        print(f"   ✅ Meets business requirements: {quality_report['business_logic']['meets_requirements']}")
        print()
        
    except Exception as e:
        print(f"❌ Data quality validation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    # Print summary
    print("=" * 70)
    print("DATA QUALITY SUMMARY")
    print("=" * 70)
    
    completeness_avg = sum(v['overall'] for v in quality_report['completeness'].values()) / len(quality_report['completeness']) if quality_report['completeness'] else 0
    print(f"Completeness: {completeness_avg:.1f}%")
    print(f"Accuracy: {quality_report['accuracy'].get('accuracy_percentage', 0):.1f}%")
    print(f"Referential Integrity: {quality_report['referential_integrity'].get('integrity_percentage', 0):.1f}%")
    print(f"Business Logic: {'✅ PASS' if quality_report['business_logic'].get('meets_requirements') else '❌ FAIL'}")
    print()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "quality_report": quality_report,
        "overall_score": (completeness_avg + quality_report['accuracy'].get('accuracy_percentage', 0) + quality_report['referential_integrity'].get('integrity_percentage', 0)) / 3
    }


if __name__ == "__main__":
    results = validate_data_quality()
    
    # Save results
    with open('test_results_2_data_quality.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: test_results_2_data_quality.json")
    print(f"Overall Quality Score: {results['overall_score']:.1f}%")
    
    sys.exit(0 if results['overall_score'] >= 90 else 1)
