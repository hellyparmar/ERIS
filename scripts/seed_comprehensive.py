#!/usr/bin/env python3
"""
Comprehensive Database Seeding Script for ERIS
Populates all empty tables with realistic restaurant data
"""
import psycopg2
from datetime import datetime, timedelta
from decimal import Decimal
import random
import uuid

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'eris_admin',
    'password': 'JnCSXvJLgIY7V8KtUd2TT26QXkbgvuwv',
    'dbname': 'eris_production'
}

# Sample data
CUSTOMER_FIRST_NAMES = ['Rajesh', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Aisha', 'Arjun', 'Divya', 'Rohan', 'Neha',
                       'Sandeep', 'Pooja', 'Akshay', 'Kavya', 'Nitin', 'Riya', 'Karan', 'Anjali', 'Varun', 'Shreya']
CUSTOMER_LAST_NAMES = ['Sharma', 'Patel', 'Kumar', 'Singh', 'Gupta', 'Verma', 'Pandey', 'Iyer', 'Nair', 'Desai']

SUPPLIER_NAMES = ['Metro Wholesale', 'Fresh Foods Ltd', 'Premium Beverages', 'Spice Trading Co', 
                  'Dairy Delights', 'Bakery Supplies', 'Meat & Poultry', 'Packaging Solutions',
                  'Cleaning Supplies', 'Kitchen Equipment']

PAYMENT_METHODS = ['CASH', 'CARD', 'UPI', 'WALLET', 'CHEQUE']
PAYMENT_STATUSES = ['PENDING', 'COMPLETED', 'PARTIAL']
SALE_STATUSES = ['INITIATED', 'COMPLETED', 'CANCELLED']

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("\n" + "=" * 70)
        print("🌱 COMPREHENSIVE DATABASE SEEDING STARTED")
        print("=" * 70)
        
        # Get existing IDs
        cur.execute("SELECT id FROM organizations LIMIT 1")
        org_id = cur.fetchone()[0]
        print(f"\n✓ Using Organization ID: {org_id}")
        
        cur.execute("SELECT id FROM outlets ORDER BY id")
        outlet_ids = [row[0] for row in cur.fetchall()]
        print(f"✓ Found {len(outlet_ids)} outlets: {outlet_ids}")
        
        cur.execute("SELECT id FROM users ORDER BY id")
        user_ids = [row[0] for row in cur.fetchall()]
        print(f"✓ Found {len(user_ids)} users: {user_ids[:5]}...")
        
        cur.execute("SELECT id, name FROM products ORDER BY id")
        products = {row[0]: row[1] for row in cur.fetchall()}
        print(f"✓ Found {len(products)} products")
        
        # 1. SEED CUSTOMERS
        print("\n[1/8] Seeding Customers...")
        cur.execute("SELECT COUNT(*) FROM customers")
        if cur.fetchone()[0] == 0:
            customers = []
            for i in range(50):
                fname = random.choice(CUSTOMER_FIRST_NAMES)
                lname = random.choice(CUSTOMER_LAST_NAMES)
                cust_type = random.choice(['retail', 'wholesale', 'corporate'])
                
                cur.execute("""
                    INSERT INTO customers 
                    (organization_id, first_name, last_name, email, phone, customer_type, 
                     city, state, country, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (org_id, fname, lname, f"{fname.lower()}{i}@email.com", 
                      f"+91-{random.randint(7000000000, 9999999999)}", cust_type,
                      random.choice(['Bangalore', 'Mumbai', 'Delhi', 'Chennai']), 
                      random.choice(['KA', 'MH', 'DL', 'TN']), 'India', True))
                customers.append(cur.fetchone()[0])
            print(f"   ✓ Created {len(customers)} customers")
            conn.commit()
        else:
            cur.execute("SELECT id FROM customers")
            customers = [row[0] for row in cur.fetchall()]
            print(f"   ✓ {len(customers)} customers already exist")
        
        # 2. SEED SUPPLIERS
        print("\n[2/8] Seeding Suppliers...")
        cur.execute("SELECT COUNT(*) FROM suppliers")
        if cur.fetchone()[0] == 0:
            suppliers = []
            for name in SUPPLIER_NAMES:
                cur.execute("""
                    INSERT INTO suppliers
                    (organization_id, name, contact_person, email, phone, address, city, 
                     state, country, postal_code, payment_terms, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (org_id, name, f"Contact {name}", f"contact@{name.lower().replace(' ', '')}.com",
                      f"+91-{random.randint(7000000000, 9999999999)}", f"{name} Building, Street",
                      'Bangalore', 'KA', 'India', '560001', 'Net 30', True))
                suppliers.append(cur.fetchone()[0])
            print(f"   ✓ Created {len(suppliers)} suppliers")
            conn.commit()
        else:
            cur.execute("SELECT id FROM suppliers")
            suppliers = [row[0] for row in cur.fetchall()]
            print(f"   ✓ {len(suppliers)} suppliers already exist")
        
        # 3. SEED EMPLOYEES
        print("\n[3/8] Seeding Employees...")
        cur.execute("SELECT COUNT(*) FROM employees")
        if cur.fetchone()[0] == 0:
            emp_positions = ['Chef', 'Sous Chef', 'Waiter', 'Cashier', 'Manager', 'Cook', 'Busboy']
            employees = []
            for i in range(30):
                fname = random.choice(CUSTOMER_FIRST_NAMES)
                lname = random.choice(CUSTOMER_LAST_NAMES)
                joining_date = (datetime.now() - timedelta(days=random.randint(30, 730))).date()
                
                cur.execute("""
                    INSERT INTO employees
                    (outlet_id, first_name, last_name, email, phone, position, 
                     joining_date, base_salary, is_active, is_deleted, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (random.choice(outlet_ids), fname, lname,
                      f"emp{i}@petpooja.com", f"+91-{random.randint(7000000000, 9999999999)}",
                      random.choice(emp_positions), joining_date, random.randint(15000, 50000),
                      True, False))
                employees.append(cur.fetchone()[0])
            print(f"   ✓ Created {len(employees)} employees")
            conn.commit()
        else:
            cur.execute("SELECT id FROM employees")
            employees = [row[0] for row in cur.fetchall()]
            print(f"   ✓ {len(employees)} employees already exist")
        
        # 4. SEED SALES
        print("\n[4/8] Seeding Sales...")
        cur.execute("SELECT COUNT(*) FROM sales")
        if cur.fetchone()[0] == 0:
            sales = []
            for i in range(500):
                outlet_id = random.choice(outlet_ids)
                user_id = random.choice(user_ids)
                customer_id = random.choice(customers) if random.random() > 0.3 else None
                
                subtotal = Decimal(str(random.uniform(500, 5000)))
                tax_amount = subtotal * Decimal('0.05')
                discount = Decimal(str(random.uniform(0, 200)))
                total_amount = subtotal + tax_amount - discount
                
                sale_date = datetime.now() - timedelta(days=random.randint(1, 180))
                
                cur.execute("""
                    INSERT INTO sales
                    (outlet_id, user_id, customer_id, sale_number, subtotal, tax_amount,
                     discount_amount, total_amount, payment_method, payment_status, 
                     amount_paid, status, sale_date, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (outlet_id, user_id, customer_id, f"SAL-{i+1:06d}",
                      subtotal, tax_amount, discount, total_amount,
                      random.choice(PAYMENT_METHODS), random.choice(PAYMENT_STATUSES),
                      total_amount, random.choice(SALE_STATUSES), sale_date))
                sales.append(cur.fetchone()[0])
                
                if (i + 1) % 100 == 0:
                    print(f"   ... {i + 1} sales created")
            
            print(f"   ✓ Created {len(sales)} sales")
            conn.commit()
        else:
            cur.execute("SELECT id FROM sales")
            sales = [row[0] for row in cur.fetchall()]
            print(f"   ✓ {len(sales)} sales already exist")
        
        # 5. SEED SALE_ITEMS
        print("\n[5/8] Seeding Sale Items...")
        cur.execute("SELECT COUNT(*) FROM sale_items")
        if cur.fetchone()[0] == 0 and sales:
            sale_items = []
            for sale_id in sales:
                num_items = random.randint(1, 8)
                for _ in range(num_items):
                    product_id = random.choice(list(products.keys()))
                    quantity = random.randint(1, 5)
                    unit_price = Decimal(str(random.uniform(50, 500)))
                    discount = Decimal(str(random.uniform(0, 10)))
                    line_total = unit_price * quantity
                    
                    cur.execute("""
                        INSERT INTO sale_items
                        (sale_id, product_id, quantity, unit_price, discount_percent, line_total, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        RETURNING id
                    """, (sale_id, product_id, quantity, unit_price, discount, line_total))
                    sale_items.append(cur.fetchone()[0])
            
            print(f"   ✓ Created {len(sale_items)} sale items")
            conn.commit()
        else:
            cur.execute("SELECT COUNT(*) FROM sale_items")
            count = cur.fetchone()[0]
            print(f"   ✓ {count} sale items already exist or no sales")
        
        # 6. SEED INVOICES
        print("\n[6/8] Seeding Invoices...")
        cur.execute("SELECT COUNT(*) FROM invoices")
        if cur.fetchone()[0] == 0 and sales:
            invoices = []
            for idx, sale_id in enumerate(sales[:300]):
                invoice_date = datetime.now() - timedelta(days=random.randint(1, 180))
                due_date = invoice_date + timedelta(days=30)
                
                cur.execute("""
                    SELECT subtotal, tax_amount, total_amount FROM sales WHERE id = %s
                """, (sale_id,))
                row = cur.fetchone()
                subtotal, tax_amount, total_amount = row if row else (1000, 100, 1100)
                
                cur.execute("""
                    INSERT INTO invoices
                    (sale_id, invoice_number, invoice_date, due_date, subtotal, tax_amount,
                     total_amount, is_paid, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (sale_id, f"INV-{idx+1:06d}", invoice_date.date(), due_date.date(),
                      subtotal, tax_amount, total_amount, random.random() > 0.3))
                invoices.append(cur.fetchone()[0])
                
                if (idx + 1) % 100 == 0:
                    print(f"   ... {idx + 1} invoices created")
            
            print(f"   ✓ Created {len(invoices)} invoices")
            conn.commit()
        else:
            cur.execute("SELECT COUNT(*) FROM invoices")
            count = cur.fetchone()[0]
            print(f"   ✓ {count} invoices already exist")
        
        # 7. SEED INVENTORY_MOVEMENTS
        print("\n[7/8] Seeding Inventory Movements...")
        cur.execute("SELECT COUNT(*) FROM inventory_movements")
        if cur.fetchone()[0] == 0:
            movements = []
            for outlet_id in outlet_ids:
                for product_id in list(products.keys())[:20]:
                    for i in range(random.randint(3, 8)):
                        movement_type = random.choice(['IN', 'OUT', 'ADJUSTMENT'])
                        quantity = random.randint(10, 500)
                        movement_date = datetime.now() - timedelta(days=random.randint(1, 180))
                        
                        cur.execute("""
                            INSERT INTO inventory_movements
                            (product_id, outlet_id, movement_type, quantity, notes, movement_date, created_at)
                            VALUES (%s, %s, %s::inventorymovementtypeenum, %s, %s, %s, NOW())
                            RETURNING id
                        """, (product_id, outlet_id, movement_type, quantity,
                              f"{movement_type} movement for {products[product_id]}", movement_date))
                        movements.append(cur.fetchone()[0])
            
            print(f"   ✓ Created {len(movements)} inventory movements")
            conn.commit()
        else:
            cur.execute("SELECT COUNT(*) FROM inventory_movements")
            count = cur.fetchone()[0]
            print(f"   ✓ {count} inventory movements already exist")
        
        # 8. SEED GST_CONFIGURATION
        print("\n[8/8] Seeding Additional Data...")
        
        # Businesses (needed for customer_credit)
        cur.execute("SELECT COUNT(*) FROM businesses")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO businesses (name, gst_number, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id
            """, ('PetPooja Main Business', '27AABPB1234B1Z5'))
            business_id = cur.fetchone()[0]
            print(f"   ✓ Created business (ID: {business_id})")
            conn.commit()
        else:
            cur.execute("SELECT id FROM businesses LIMIT 1")
            business_id = cur.fetchone()[0]
            print(f"   ✓ Business exists (ID: {business_id})")
        
        # Attendance
        cur.execute("SELECT COUNT(*) FROM attendance")
        if cur.fetchone()[0] == 0 and employees:
            attendance_count = 0
            for emp_id in employees:
                for day_offset in range(1, 31):
                    status = random.choice(['PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'LEAVE'])
                    att_date = (datetime.now() - timedelta(days=day_offset)).date()
                    
                    cur.execute("""
                        INSERT INTO attendance
                        (employee_id, date, status, created_at, updated_at)
                        VALUES (%s, %s, %s::attendancestatusenum, NOW(), NOW())
                    """, (emp_id, att_date, status))
                    attendance_count += 1
            print(f"   ✓ Created {attendance_count} attendance records")
            conn.commit()
        else:
            print(f"   ✓ Attendance records already exist or no employees")
        
        # Customer Credit
        cur.execute("SELECT COUNT(*) FROM customer_credit")
        if cur.fetchone()[0] == 0 and customers:
            credit_count = 0
            
            for cust_id in customers[:30]:
                cur.execute("""
                    INSERT INTO customer_credit
                    (business_id, customer_id, credit_limit, current_balance, credit_score,
                     total_transactions, on_time_payments, late_payments, missed_payments,
                     is_active, is_blocked, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (business_id, cust_id, Decimal('50000'), Decimal(str(random.uniform(0, 50000))),
                      random.randint(600, 900), random.randint(5, 50), random.randint(0, 40),
                      random.randint(0, 5), 0, True, False))
                credit_count += 1
            print(f"   ✓ Created {credit_count} customer credit records")
            conn.commit()
        else:
            print(f"   ✓ Customer credit records already exist")
        
        # Invoice Payments
        cur.execute("SELECT COUNT(*) FROM invoice_payments")
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT id FROM invoices")
            invoices_for_payment = [row[0] for row in cur.fetchall()]
            
            if invoices_for_payment:
                payment_count = 0
                for inv_id in invoices_for_payment:
                    if random.random() > 0.5:
                        cur.execute("SELECT total_amount FROM invoices WHERE id = %s", (inv_id,))
                        inv_row = cur.fetchone()
                        if inv_row:
                            amount = inv_row[0]
                            cur.execute("""
                                INSERT INTO invoice_payments
                                (invoice_id, payment_date, amount, payment_method, created_at)
                                VALUES (%s, %s, %s, %s, NOW())
                            """, (inv_id, datetime.now().date(), amount,
                                  random.choice(PAYMENT_METHODS)))
                            payment_count += 1
                
                print(f"   ✓ Created {payment_count} invoice payment records")
                conn.commit()
        else:
            print(f"   ✓ Invoice payment records already exist")
        
        # Final verification
        print("\n" + "=" * 70)
        print("FINAL DATABASE STATUS")
        print("=" * 70)
        
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        tables = [row[0] for row in cur.fetchall()]
        
        filled = 0
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            if count > 0:
                filled += 1
                status = "✓"
            else:
                status = "✗"
            
            if count > 0 or table in ['alerts', 'customers', 'suppliers', 'sales', 'invoices', 
                                      'inventory_movements', 'employees', 'gst_configuration']:
                print(f"{status} {table:30} {count:8} rows")
        
        print("=" * 70)
        print(f"✅ SEEDING COMPLETE! {filled}/{len(tables)} tables have data")
        print("=" * 70)
        
        cur.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
