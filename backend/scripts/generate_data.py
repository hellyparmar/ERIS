"""
R-DIOS Synthetic Data Generator
Generates realistic Indian retail data with external causal factors.
Run: cd backend && python scripts/generate_data.py
"""
import random
import hashlib
from datetime import date, timedelta
from passlib.context import CryptContext
import os

random.seed(42)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Outlets with geo-coordinates ──────────────────────────────
OUTLETS = [
    (1,"Mumbai Central","Mumbai","Maharashtra","flagship","400001",19.0760,72.8777),
    (2,"Mumbai Andheri","Mumbai","Maharashtra","standard","400058",19.1136,72.8697),
    (3,"Delhi Connaught","Delhi","Delhi","flagship","110001",28.6315,77.2167),
    (4,"Delhi Lajpat","Delhi","Delhi","standard","110024",28.5672,77.2434),
    (5,"Bangalore Koramangala","Bangalore","Karnataka","flagship","560034",12.9352,77.6245),
    (6,"Chennai Anna Nagar","Chennai","Tamil Nadu","standard","600040",13.0827,80.2707),
    (7,"Hyderabad Banjara","Hyderabad","Telangana","standard","500034",17.4126,78.4071),
    (8,"Pune Koregaon","Pune","Maharashtra","express","411001",18.5204,73.8567),
    (9,"Ahmedabad CG Road","Ahmedabad","Gujarat","standard","380009",23.0225,72.5714),
    (10,"Jaipur MI Road","Jaipur","Rajasthan","express","302001",26.9124,75.7873),
]

# ── Products with HSN codes ────────────────────────────────────
PRODUCTS = [
    (1,"Coca Cola 300ml","Beverages","SKU0001","22021010",20,28,12,"ml","Coca Cola"),
    (2,"Pepsi 300ml","Beverages","SKU0002","22021010",20,27,12,"ml","PepsiCo"),
    (3,"Sprite 300ml","Beverages","SKU0003","22021010",19,26,12,"ml","Coca Cola"),
    (4,"Thums Up 600ml","Beverages","SKU0004","22021010",32,45,12,"ml","Coca Cola"),
    (5,"Amul Butter 100g","Dairy","SKU0005","04051000",55,65,5,"g","Amul"),
    (6,"Mother Dairy Paneer 200g","Dairy","SKU0006","04061000",70,85,5,"g","Mother Dairy"),
    (7,"Amul Dahi 400g","Dairy","SKU0007","04031000",48,58,5,"g","Amul"),
    (8,"Lays Classic 26g","Snacks","SKU0008","19042000",10,22,12,"g","PepsiCo"),
    (9,"Kurkure Masala 70g","Snacks","SKU0009","19042000",15,26,12,"g","PepsiCo"),
    (10,"Haldiram Bhujia 200g","Snacks","SKU0010","19042000",85,130,12,"g","Haldiram"),
    (11,"Parle G 100g","Snacks","SKU0011","19053100",8,13,5,"g","Parle"),
    (12,"Dove Soap 100g","Personal Care","SKU0012","34011190",38,65,18,"g","Unilever"),
    (13,"Head Shoulders 340ml","Personal Care","SKU0013","33051000",210,290,18,"ml","P&G"),
    (14,"Colgate MaxFresh 150g","Personal Care","SKU0014","33061000",78,115,18,"g","Colgate"),
    (15,"Aashirvaad Atta 5kg","Staples","SKU0015","11010000",225,265,5,"kg","ITC"),
    (16,"Fortune Sunflower Oil 1L","Staples","SKU0016","15121100",135,165,5,"L","Adani Wilmar"),
    (17,"Tata Salt 1kg","Staples","SKU0017","25010000",19,26,5,"kg","Tata"),
    (18,"Maggi 2min Noodles 70g","Packaged Food","SKU0018","19023010",12,20,12,"g","Nestle"),
    (19,"MTR Ready to Eat","Packaged Food","SKU0019","21069099",58,85,12,"piece","MTR"),
    (20,"Britannia NutriChoice","Packaged Food","SKU0020","19053100",38,58,12,"g","Britannia"),
]

VENDORS = [
    (1,"Raj Traders","Raj Traders Pvt Ltd","Beverages","Mumbai","Maharashtra","raj@rajtraders.com","+91 98765 43001","27AABCR1234F1Z5","AABCR1234F",30,500000,45000),
    (2,"Fresh Dairy Co","Fresh Dairy Co Ltd","Dairy","Pune","Maharashtra","info@freshdairy.com","+91 98765 43002","27AABCF2345G1Z6","AABCF2345G",15,300000,0),
    (3,"Snacks World","Snacks World Distribution","Snacks","Delhi","Delhi","orders@snacksworld.in","+91 98765 43003","07AABCS3456H1Z7","AABCS3456H",45,400000,12500),
    (4,"Staples Direct","Staples Direct Pvt Ltd","Staples","Ahmedabad","Gujarat","staples@direct.co.in","+91 98765 43004","24AABCS4567I1Z8","AABCS4567I",30,600000,0),
    (5,"Personal Plus","Personal Plus Agencies","Personal Care","Bangalore","Karnataka","contact@personalplus.com","+91 98765 43005","29AABCP5678J1Z9","AABCP5678J",30,250000,8900),
    (6,"Metro Packaged","Metro Packaged Foods","Packaged Food","Hyderabad","Telangana","metro@packaged.in","+91 98765 43006","36AABCM6789K1Z0","AABCM6789K",60,350000,22000),
]

# ── Indian Holidays & Festivals (sales multipliers) ───────────
EVENTS = {
    "2024-01-14": 1.3, "2024-01-26": 1.5, "2024-03-25": 1.7,
    "2024-04-14": 1.4, "2024-04-17": 1.3, "2024-05-23": 1.2,
    "2024-08-15": 1.6, "2024-08-19": 1.4, "2024-10-02": 1.2,
    "2024-10-12": 1.5, "2024-10-13": 2.0, "2024-10-14": 1.9,
    "2024-10-31": 1.8, "2024-11-01": 1.7, "2024-11-15": 1.5,
    "2024-12-24": 1.4, "2024-12-25": 1.5, "2024-12-31": 1.6,
    "2025-01-01": 1.5, "2025-01-14": 1.3, "2025-01-26": 1.5,
    "2025-03-14": 1.7, "2025-04-14": 1.4, "2025-04-18": 1.3,
    "2025-08-15": 1.6, "2025-10-02": 1.2,
}

# Monthly seasonality (captures Diwali Oct, summer June, new year boost)
MONTH_MULT = {1:0.90,2:0.86,3:0.91,4:0.96,5:1.00,6:1.06,7:0.93,8:0.96,9:0.99,10:1.40,11:1.30,12:1.15}
# Day-of-week (0=Mon)
DOW_MULT = {0:0.76,1:0.79,2:0.81,3:0.83,4:0.91,5:1.28,6:1.18}
# Outlet type base revenue
TYPE_BASE = {"flagship":48000,"standard":30000,"express":19000}
# Season/weather multiplier by month (monsoon dip, winter boost)
WEATHER_MULT = {1:1.02,2:1.00,3:1.01,4:0.98,5:0.97,6:0.95,7:0.93,8:0.94,9:0.96,10:1.05,11:1.04,12:1.03}

def gen_daily_sales():
    rows = []
    sale_id = 1
    d = date(2024,1,1)
    end = date(2025,6,30)
    while d <= end:
        ds = str(d)
        holiday_mult = EVENTS.get(ds, 1.0)
        for oid,oname,ocity,ostate,otype,*_ in OUTLETS:
            base = TYPE_BASE[otype]
            daily = (base
                     * DOW_MULT[d.weekday()]
                     * MONTH_MULT[d.month]
                     * WEATHER_MULT[d.month]
                     * holiday_mult
                     * random.gauss(1.0, 0.07))
            n_tx = max(1, int(daily / random.randint(180, 360)))
            for _ in range(min(n_tx, 18)):
                pid,pname,pcat,psku,phsn,bp,sp,gst,unit,brand = random.choice(PRODUCTS)
                qty = random.randint(1,5)
                total = round(sp * qty, 2)
                gst_amt = round(total * gst/100, 2)
                pmode = random.choices(
                    ["cash","upi","card","credit"],
                    weights=[25,45,20,10])[0]
                rows.append((sale_id,oid,pid,ds,qty,sp,total,gst,gst_amt,pmode))
                sale_id += 1
        d += timedelta(days=1)
    return rows, sale_id

print("Generating sales data (this may take 2-3 minutes)...")
sales, total_sales = gen_daily_sales()
print(f"Generated {total_sales-1} sales records.")

# ── Inventory ──────────────────────────────────────────────────
inv_rows = []
for oid,*_ in OUTLETS:
    for pid,*_ in PRODUCTS:
        rl = random.randint(8, 25)
        cs = random.randint(0, 90)
        ms = rl * random.randint(4, 7)
        lr = str(date.today() - timedelta(days=random.randint(1,35)))
        inv_rows.append((oid, pid, cs, rl, ms, lr))

# ── Write SQL ──────────────────────────────────────────────────
os.makedirs("backend/scripts", exist_ok=True)
outfile = "backend/scripts/seed_data.sql"

with open(outfile, "w") as f:
    f.write("-- R-DIOS Synthetic Seed Data\n")
    f.write("-- 18 months, 10 outlets, 20 products, external causal factors\n\n")

    # Outlets
    f.write("INSERT INTO outlets (id,name,city,state,outlet_type,pincode,latitude,longitude,is_active) VALUES\n")
    f.write(",\n".join([f"({oid},'{name}','{city}','{state}','{otype}','{pin}',{lat},{lng},true)"
                        for oid,name,city,state,otype,pin,lat,lng in OUTLETS]) + ";\n\n")

    # Products
    f.write("INSERT INTO products (id,name,category,sku,hsn_code,base_price,selling_price,gst_rate,unit,brand,is_active) VALUES\n")
    f.write(",\n".join([f"({pid},'{name}','{cat}','{sku}','{hsn}',{bp},{sp},{gst},'{unit}','{brand}',true)"
                        for pid,name,cat,sku,hsn,bp,sp,gst,unit,brand in PRODUCTS]) + ";\n\n")

    # Users with bcrypt hashed passwords
    f.write("INSERT INTO users (name,email,hashed_password,role,outlet_id,is_active) VALUES\n")
    users = [
        ("System Admin","admin@rdios.com",pwd_context.hash("admin123"),"admin",None),
        ("Store Manager","manager@rdios.com",pwd_context.hash("manager123"),"manager",1),
        ("Data Analyst","analyst@rdios.com",pwd_context.hash("analyst123"),"analyst",None),
    ]
    f.write(",\n".join([f"('{n}','{e}','{h}','{r}',{str(o) if o else 'NULL'},true)"
                        for n,e,h,r,o in users]) + ";\n\n")

    # Vendors
    f.write("INSERT INTO vendors (id,name,company,category,city,state,email,phone,gstin,pan,payment_terms,credit_limit,outstanding_amount,is_active) VALUES\n")
    f.write(",\n".join([f"({i},'{n}','{co}','{cat}','{ci}','{st}','{em}','{ph}','{gs}','{pan}',{pt},{cl},{oa},true)"
                        for i,n,co,cat,ci,st,em,ph,gs,pan,pt,cl,oa in VENDORS]) + ";\n\n")

    # Inventory
    f.write("INSERT INTO inventory (outlet_id,product_id,current_stock,reorder_level,max_stock,last_restocked) VALUES\n")
    f.write(",\n".join([f"({oid},{pid},{cs},{rl},{ms},'{lr}')" for oid,pid,cs,rl,ms,lr in inv_rows]) + ";\n\n")

    # Sales in 1000-row chunks
    for i in range(0, len(sales), 1000):
        chunk = sales[i:i+1000]
        f.write("INSERT INTO sales (id,outlet_id,product_id,sale_date,quantity,unit_price,total_amount,gst_rate,gst_amount,payment_mode) VALUES\n")
        f.write(",\n".join([f"({sid},{oid},{pid},'{sd}',{qty},{up},{ta},{grt},{ga},'{pm}')"
                            for sid,oid,pid,sd,qty,up,ta,grt,ga,pm in chunk]) + ";\n\n")

    # Sample invoices
    f.write("INSERT INTO invoices (invoice_number,outlet_id,customer_name,invoice_date,subtotal,total_gst,total_amount,status,payment_mode,tally_synced,invoice_type) VALUES\n")
    inv_samples = [
        ("INV-2026-00001",1,"ABC Corporation",str(date.today()-timedelta(days=10)),13500.0,2430.0,15930.0,"paid","upi",True,"sale"),
        ("INV-2026-00002",1,"XYZ Retailers",str(date.today()-timedelta(days=5)),20000.0,3600.0,23600.0,"pending","credit",False,"sale"),
        ("INV-2026-00003",2,"Demo Store",str(date.today()-timedelta(days=3)),7500.0,1350.0,8850.0,"paid","cash",False,"sale"),
        ("INV-2026-00004",3,"Ramesh Traders",str(date.today()-timedelta(days=1)),32000.0,5760.0,37760.0,"overdue","credit",False,"sale"),
        ("INV-2026-00005",5,"Sunita Enterprises",str(date.today()),15000.0,2700.0,17700.0,"pending","card",False,"sale"),
    ]
    f.write(",\n".join([f"('{n}',{oi},'{cn}','{id}',{st},{tg},{ta},'{s}','{pm}',{ts},'{it}')"
                        for n,oi,cn,id,st,tg,ta,s,pm,ts,it in inv_samples]) + ";\n\n")

    # Sample community listings
    f.write("INSERT INTO community_listings (outlet_id,product_id,listing_type,available_qty,price_per_unit,description,is_active) VALUES\n")
    cl_samples = [
        (2,1,"sell",50,26.0,"Excess stock of Coca Cola 300ml. Near expiry within 3 months.",True),
        (4,15,"sell",20,250.0,"Surplus Aashirvaad Atta from last bulk purchase.",True),
        (6,18,"buy",100,18.0,"Looking to buy Maggi Noodles at bulk rate.",True),
        (8,12,"sell",30,60.0,"Slow moving Dove Soap — open to negotiation.",True),
        (3,8,"sell",200,20.0,"Lays chips overstock — selling at cost.",True),
    ]
    f.write(",\n".join([f"({oi},{pi},'{lt}',{aq},{pp},'{desc}',{ia})"
                        for oi,pi,lt,aq,pp,desc,ia in cl_samples]) + ";\n\n")

print(f"Seed file written: {outfile}")
print("Now run:")
print("  createdb rdios  (if database does not exist)")
print("  psql -U postgres -d rdios -f backend/scripts/seed_data.sql")
