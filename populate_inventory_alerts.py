#!/usr/bin/env python3
"""
Populate inventory, alerts, and invoices from sales data
Part of PHASE 0 data migration
"""

import psycopg2
import random
from datetime import datetime, timedelta
from decimal import Decimal

def run():
    conn = psycopg2.connect(
        host="localhost", port=5433, database="enterprise_retail",
        user="postgres", password="EnterpriseRetail@2026"
    )
    cur = conn.cursor()
    
    print("=== POPULATING MISSING TABLES ===\n")
    
    # Step 1: Get all products
    cur.execute("SELECT id FROM products")
    product_ids = [row[0] for row in cur.fetchall()]
    print(f"✓ Found {len(product_ids)} products")
    
    # Step 2: Get store_id from stores table
    cur.execute("SELECT id FROM stores LIMIT 1")
    store_id = cur.fetchone()[0]
    print(f"✓ Store ID: {store_id}")
    
    # Step 3: Populate inventory (realistic stock levels based on sales)
    print("\nPopulating INVENTORY...")
    cur.execute("DELETE FROM inventory")
    
    for product_id in product_ids:
        # Calculate average daily sales
        cur.execute("""
            SELECT COALESCE(SUM(quantity), 0) FROM sale_items 
            WHERE product_id = %s
        """, (product_id,))
        total_sold = cur.fetchone()[0]
        avg_daily_sales = max(1, total_sold // 90)  # 90 days of data
        
        current_stock = random.randint(int(avg_daily_sales * 3), int(avg_daily_sales * 7))
        reserved_stock = random.randint(0, avg_daily_sales)
        reorder_point = avg_daily_sales * 3
        reorder_qty = avg_daily_sales * 5
        
        cur.execute("""
            INSERT INTO inventory 
            (product_id, current_stock, reserved_stock, available_stock,
             reorder_point, reorder_quantity, max_stock_level, 
             warehouse_location, last_stocked_date, last_restocked, 
             updated_at, store_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            product_id,
            current_stock,
            reserved_stock,
            current_stock - reserved_stock,
            reorder_point,
            reorder_qty,
            reorder_point * 2,
            f"Shelf_{product_id % 10}",
            datetime.now() - timedelta(days=random.randint(1, 30)),
            datetime.now() - timedelta(days=random.randint(1, 7)),
            datetime.now(),
            store_id
        ))
    
    conn.commit()
    print(f"✓ {len(product_ids)} inventory records created")
    
    # Step 4: Create ALERTS (reorder, excess, slow-moving)
    print("\nPopulating ALERTS...")
    cur.execute("DELETE FROM alerts")
    
    alert_count = 0
    for product_id in product_ids:
        cur.execute("""
            SELECT p.name, i.current_stock, i.reorder_point FROM products p
            JOIN inventory i ON p.id = i.product_id
            WHERE p.id = %s
        """, (product_id,))
        
        result = cur.fetchone()
        if result:
            name, stock, reorder_point = result
            
            # Reorder alert for 20% of products
            if random.random() < 0.2 or stock < reorder_point:
                severity_val = 'CRITICAL' if stock == 0 else 'WARNING'
                cur.execute("""
                    INSERT INTO alerts 
                    (severity, title, message, category, related_product_id,
                     is_acknowledged, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    severity_val,
                    f"Reorder {name}",
                    f"Stock {stock} units — below reorder point of {reorder_point}",
                    'inventory',
                    product_id,
                    False,
                    datetime.now(),
                    datetime.now() + timedelta(days=7)
                ))
                alert_count += 1
            
            # Excess stock alert for 10% of products
            if random.random() < 0.1:
                cur.execute("""
                    INSERT INTO alerts 
                    (severity, title, message, category, related_product_id,
                     is_acknowledged, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    'INFO',
                    f"Excess stock: {name}",
                    f"Stock {stock} units — consider discount",
                    'inventory',
                    product_id,
                    False,
                    datetime.now(),
                    datetime.now() + timedelta(days=14)
                ))
                alert_count += 1
    
    conn.commit()
    print(f"✓ {alert_count} alerts created")
    
    # Step 5: Create sample INVOICES (one per 50 sales)
    print("\nPopulating INVOICES...")
    cur.execute("DELETE FROM invoice_payments")
    cur.execute("DELETE FROM invoices")
    
    cur.execute("""
        SELECT id, customer_id, total_amount, created_at FROM sales 
        ORDER BY created_at LIMIT 100
    """)
    sales = cur.fetchall()
    
    invoice_count = 0
    for idx, (sale_id, customer_id, total, created_at) in enumerate(sales):
        if idx % 10 == 0:  # Create invoice for every 10th sale
            tax_rate = random.choice([5, 12, 18])  # GST rates
            total_float = float(total) if total else 0
            taxable_amount = total_float / (1 + tax_rate/100)
            tax_amount = total_float - taxable_amount
            
            cur.execute("""
                INSERT INTO invoices 
                (invoice_number, customer_id, hsn_code, tax_rate, 
                 taxable_amount, tax_amount, total_amount, payment_status,
                 amount_paid, amount_due, tally_sync_status,
                 receipt_sent_via, invoice_date, due_date, created_at,
                 store_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"INV-{created_at.strftime('%Y%m%d')}-{invoice_count:04d}",
                customer_id,
                '491122',  # Generic GST HSN
                tax_rate,
                round(taxable_amount, 2),
                round(tax_amount, 2),
                round(total_float, 2),
                'PAID',
                round(total_float, 2),
                0,
                'PENDING',
                'email',
                created_at.date(),
                created_at.date() + timedelta(days=30),
                created_at,
                store_id
            ))
            invoice_count += 1
    
    conn.commit()
    print(f"✓ {invoice_count} invoices created")
    
    # Step 6: Verify
    print("\n=== VERIFICATION ===")
    for t in ['inventory', 'alerts', 'invoices']:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        n = cur.fetchone()[0]
        print(f"  {t:15s}: {n:>6,} rows")
    
    cur.close()
    conn.close()
    print("\n✓ Phase 0 Step 2: All tables populated")

if __name__ == "__main__":
    run()
