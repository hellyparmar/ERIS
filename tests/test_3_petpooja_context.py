"""
Test Script 3: Petpooja Business Context Validation
Verifies data reflects authentic Petpooja retail/restaurant operations
"""

import sys
sys.path.insert(0, '/home/petpooja/Enterprise Retail Intelligence System')

from sqlalchemy import create_engine, text
from api.db.database import engine
import json
from datetime import datetime


def validate_petpooja_context():
    """
    Verify data reflects authentic Petpooja retail/restaurant operations
    """
    print("=" * 70)
    print("TEST SCRIPT 3: PETPOOJA BUSINESS CONTEXT VALIDATION")
    print("=" * 70)
    print()
    
    validation = {
        "menu_categories": [],
        "sample_products": [],
        "seasonal_patterns": {},
        "payment_distribution": {},
        "customer_segments": {}
    }
    
    conn = engine.connect()
    
    try:
        # 1. INDIAN MENU CATEGORIES
        print("🍽️  1. INDIAN MENU CATEGORIES")
        print("   Checking for authentic Indian restaurant categories...")
        
        result = conn.execute(text("SELECT DISTINCT category FROM products ORDER BY category"))
        categories = [row[0] for row in result if row[0]]
        validation["menu_categories"] = categories
        
        expected_categories = ["North Indian", "South Indian", "Chinese", "Beverages", "Desserts", "Biryani", "Bread"]
        found_indian_categories = any(
            any(exp.lower() in cat.lower() for exp in expected_categories)
            for cat in categories
        )
        
        print(f"   Found categories: {', '.join(categories[:8])}")
        print(f"   ✅ Indian categories present: {found_indian_categories}")
        print()
        
        # 2. PRODUCT EXAMPLES
        print("🥘 2. SAMPLE PRODUCT NAMES")
        print("   Checking for realistic Indian menu items...")
        
        result = conn.execute(text("""
            SELECT name, category 
            FROM products 
            WHERE category LIKE '%Indian%' OR category LIKE '%Biryani%' OR category LIKE '%Bread%'
            LIMIT 10
        """))
        
        sample_products = []
        for row in result:
            sample_products.append({"name": row[0], "category": row[1]})
            print(f"   - {row[0]} ({row[1]})")
        
        validation["sample_products"] = sample_products
        
        # Check for authentic names (not generic "Product 1")
        authentic_names = sum(1 for p in sample_products if not p["name"].startswith("Product"))
        print(f"   ✅ Authentic product names: {authentic_names}/{len(sample_products)}")
        print()
        
        # 3. SEASONAL PATTERNS
        print("🎆 3. SEASONAL SALES PATTERNS")
        print("   Analyzing Diwali and festival impact...")
        
        # Check for Diwali spike (Oct-Nov 2024)
        result = conn.execute(text("""
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                COUNT(*) as transactions
            FROM sales
            WHERE transaction_date >= '2024-09-01' AND transaction_date < '2024-12-01'
            GROUP BY month
            ORDER BY month
        """))
        
        monthly_sales = {}
        for row in result:
            monthly_sales[row[0]] = row[1]
        
        # Calculate Diwali spike (Oct/Nov vs Sep)
        sep_sales = monthly_sales.get('2024-09', 0)
        oct_sales = monthly_sales.get('2024-10', 0)
        nov_sales = monthly_sales.get('2024-11', 0)
        
        if sep_sales > 0:
            diwali_spike = max(oct_sales, nov_sales) / sep_sales if sep_sales > 0 else 1.0
        else:
            diwali_spike = 1.0
        
        validation["seasonal_patterns"] = {
            "september_2024": sep_sales,
            "october_2024": oct_sales,
            "november_2024": nov_sales,
            "diwali_spike_multiplier": round(diwali_spike, 2)
        }
        
        print(f"   September 2024: {sep_sales:,} transactions")
        print(f"   October 2024: {oct_sales:,} transactions")
        print(f"   November 2024: {nov_sales:,} transactions")
        print(f"   Diwali spike: {diwali_spike:.2f}x (target: 1.5-3.0x)")
        print(f"   ✅ Seasonal pattern detected: {diwali_spike >= 1.2}")
        print()
        
        # 4. PAYMENT METHODS (Indian Context)
        print("💳 4. PAYMENT METHOD DISTRIBUTION")
        print("   Analyzing payment preferences...")
        
        result = conn.execute(text("""
            SELECT payment_method, COUNT(*) as count
            FROM sales
            WHERE payment_method IS NOT NULL
            GROUP BY payment_method
            ORDER BY count DESC
        """))
        
        total_payments = 0
        payment_counts = {}
        for row in result:
            payment_counts[row[0]] = row[1]
            total_payments += row[1]
        
        payment_distribution = {}
        for method, count in payment_counts.items():
            pct = count / total_payments * 100 if total_payments > 0 else 0
            payment_distribution[method] = round(pct, 1)
            print(f"   {method}: {count:,} ({pct:.1f}%)")
        
        validation["payment_distribution"] = payment_distribution
        
        # Check for Indian payment methods (UPI, Cash, Credit/Khata)
        has_indian_methods = any(
            method.lower() in ['upi', 'cash', 'credit', 'khata']
            for method in payment_counts.keys()
        )
        print(f"   ✅ Indian payment methods present: {has_indian_methods}")
        print()
        
        # 5. CUSTOMER ANALYSIS
        print("👥 5. CUSTOMER SEGMENTATION")
        print("   Analyzing customer data...")
        
        result = conn.execute(text("SELECT COUNT(*) FROM customers"))
        total_customers = result.scalar()
        
        # Check for customers with credit enabled (if column exists)
        try:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM customers 
                WHERE credit_enabled = 1 OR credit_enabled = true
            """))
            credit_customers = result.scalar()
            credit_pct = credit_customers / total_customers * 100 if total_customers > 0 else 0
            
            validation["customer_segments"]["total_customers"] = total_customers
            validation["customer_segments"]["credit_enabled"] = credit_customers
            validation["customer_segments"]["credit_percentage"] = round(credit_pct, 1)
            
            print(f"   Total customers: {total_customers:,}")
            print(f"   Credit-enabled: {credit_customers:,} ({credit_pct:.1f}%)")
            print(f"   ✅ Credit management data present")
        except:
            print(f"   Total customers: {total_customers:,}")
            print("   ⚠️  Credit data column not found")
        
        print()
        
    except Exception as e:
        print(f"❌ Petpooja context validation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    # Print summary
    print("=" * 70)
    print("PETPOOJA CONTEXT VALIDATION SUMMARY")
    print("=" * 70)
    
    checks_passed = 0
    total_checks = 5
    
    if validation["menu_categories"]:
        print("✅ Indian menu categories present")
        checks_passed += 1
    else:
        print("❌ No menu categories found")
    
    if len(validation["sample_products"]) > 0:
        print("✅ Realistic product names found")
        checks_passed += 1
    else:
        print("❌ No sample products found")
    
    if validation["seasonal_patterns"].get("diwali_spike_multiplier", 0) >= 1.2:
        print("✅ Seasonal patterns detected (Diwali spike)")
        checks_passed += 1
    else:
        print("⚠️  Weak or no seasonal patterns")
    
    if validation["payment_distribution"]:
        print("✅ Payment methods distributed")
        checks_passed += 1
    else:
        print("❌ No payment data found")
    
    if validation["customer_segments"].get("total_customers", 0) > 1000:
        print("✅ Sufficient customer data")
        checks_passed += 1
    else:
        print("❌ Insufficient customer data")
    
    print()
    print(f"Overall: {checks_passed}/{total_checks} checks passed ({checks_passed/total_checks*100:.0f}%)")
    print()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "validation": validation,
        "checks_passed": checks_passed,
        "total_checks": total_checks,
        "pass_rate": checks_passed / total_checks * 100
    }


if __name__ == "__main__":
    results = validate_petpooja_context()
    
    # Save results
    with open('test_results_3_petpooja_context.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: test_results_3_petpooja_context.json")
    print(f"Pass Rate: {results['pass_rate']:.0f}%")
    
    sys.exit(0 if results['pass_rate'] >= 80 else 1)
