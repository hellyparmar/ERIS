"""Static reference data for the demo organization, a neighbourhood supermarket chain: outlets, suppliers and its
product catalogue (packaged groceries, fresh produce, dairy, and household & personal care - all retail SKUs)."""

ORGANIZATION = {
    "name": "Urban Harvest Supermarkets Pvt. Ltd.",
    "industry": "Grocery Retail (Supermarkets)",
    "currency": "INR",
    "currency_symbol": "₹",
    "timezone": "Asia/Kolkata",
    "email": "hello@urbanharvest.example",
    "phone": "+91 22 4000 1234",
    "address": "4th Floor, Lotus Corporate Park, Goregaon East, Mumbai 400063",
    "state": "Maharashtra",
    "state_code": "27",
    # tax_id: a synthetic, checksum-valid GSTIN is generated from the seed (see services/gst.py) and marked demo.
}

# The demo company runs five outlets by default (SEED_OUTLETS, up to 7) - each with a different demand profile.
# code, name, city, state, state code, address, manager, size, growth/yr, opened N days before data end (None = long open)
OUTLETS = [
    ("MUM-AND", "Andheri West", "Mumbai", "Maharashtra", "27", "Lokhandwala Complex, Andheri West, Mumbai",
     "Priya Sharma", 1.30, 0.12, None),   # flagship, steady growth, monsoon city
    ("PUN-KOR", "Koregaon Park", "Pune", "Maharashtra", "27", "North Main Road, Koregaon Park, Pune",
     "Sneha Kulkarni", 0.95, 0.16, None),  # fastest-growing established outlet
    ("BLR-IND", "Indiranagar", "Bengaluru", "Karnataka", "29", "100 Feet Road, Indiranagar, Bengaluru",
     "Arjun Rao", 1.10, 0.10, None),       # mild climate, high delivery share
    ("AMD-SGH", "SG Highway", "Ahmedabad", "Gujarat", "24", "Sindhu Bhavan Road, SG Highway, Ahmedabad",
     "Kavya Patel", 0.85, -0.08, None),    # losing ground to a new competitor
    ("BLR-WHF", "Whitefield", "Bengaluru", "Karnataka", "29", "ITPL Main Road, Whitefield, Bengaluru",
     "Vikram Nair", 0.90, 0.10, 240),      # new outlet ramping up
    ("MUM-BAN", "Bandra", "Mumbai", "Maharashtra", "27", "Hill Road, Bandra West, Mumbai",
     "Rahul Mehta", 1.15, 0.09, None),     # optional 6th outlet
    ("HYD-JUB", "Jubilee Hills", "Hyderabad", "Telangana", "36", "Road No. 36, Jubilee Hills, Hyderabad",
     "Farah Khan", 0.95, 0.12, 420),       # optional 7th outlet
]

# Monthly climatology per city: (mean max temperature C by month Jan..Dec, rain probability by month, mean rain mm on
# a rainy day by month). Approximate public climate normals - used to synthesise daily weather.
CLIMATE = {
    "Mumbai": ([30, 31, 32, 33, 34, 32, 30, 29, 30, 32, 33, 32],
               [0.01, 0.01, 0.01, 0.02, 0.08, 0.6, 0.9, 0.85, 0.6, 0.2, 0.05, 0.01],
               [2, 2, 2, 3, 10, 28, 35, 25, 18, 10, 5, 2]),
    "Pune": ([30, 32, 35, 37, 37, 32, 28, 28, 29, 31, 30, 29],
             [0.01, 0.01, 0.02, 0.05, 0.12, 0.55, 0.8, 0.7, 0.5, 0.25, 0.05, 0.02],
             [2, 2, 3, 4, 8, 12, 14, 10, 12, 10, 6, 2]),
    "Bengaluru": ([28, 31, 33, 34, 33, 29, 28, 28, 29, 28, 27, 27],
                  [0.02, 0.02, 0.05, 0.15, 0.35, 0.4, 0.45, 0.5, 0.55, 0.5, 0.25, 0.08],
                  [3, 3, 5, 8, 12, 8, 8, 10, 14, 14, 10, 5]),
    "Ahmedabad": ([29, 31, 36, 40, 42, 38, 33, 32, 34, 36, 33, 30],
                  [0.0, 0.0, 0.01, 0.01, 0.03, 0.25, 0.65, 0.55, 0.3, 0.05, 0.02, 0.0],
                  [1, 1, 2, 2, 5, 15, 25, 20, 15, 6, 3, 1]),
    "Hyderabad": ([29, 32, 36, 38, 39, 34, 31, 30, 31, 31, 29, 28],
                  [0.01, 0.01, 0.03, 0.06, 0.1, 0.45, 0.6, 0.6, 0.55, 0.3, 0.08, 0.02],
                  [2, 2, 4, 5, 8, 10, 12, 12, 14, 10, 6, 2]),
}

# HSN codes (first 4 digits of the Harmonised System chapter heading) used on demo GST invoices.
HSN = {
    "STA-001": "1006", "STA-002": "1006", "STA-003": "1101", "STA-004": "0713", "STA-005": "0713", "STA-006": "1512",
    "STA-007": "2501", "STA-008": "1701", "STA-009": "1904",
    "DAI-001": "0401", "DAI-002": "0403", "DAI-003": "0406", "DAI-004": "0405", "DAI-005": "0406", "DAI-006": "0407",
    "DAI-007": "0403",
    "FRV-001": "0803", "FRV-002": "0808", "FRV-003": "0702", "FRV-004": "0703", "FRV-005": "0805", "FRV-006": "0804",
    "FRV-007": "0709", "FRV-008": "0701",
    "BEV-001": "2201", "BEV-002": "2202", "BEV-003": "2009", "BEV-004": "2202", "BEV-005": "2202", "BEV-006": "2201",
    "BEV-007": "2202", "BEV-008": "2009",
    "TEA-001": "0902", "TEA-002": "0902", "TEA-003": "0901", "TEA-004": "2101", "TEA-005": "2101",
    "BRK-001": "1905", "BRK-002": "1905", "BRK-003": "1104", "BRK-004": "1904", "BRK-005": "2008", "BRK-006": "2007",
    "BRK-007": "0409",
    "SNK-001": "2005", "SNK-002": "1904", "SNK-003": "2106", "SNK-004": "1905", "SNK-005": "1905", "SNK-006": "1806",
    "SNK-007": "0802", "SNK-008": "2106",
    "FRZ-001": "0710", "FRZ-002": "2105", "FRZ-003": "2004", "FRZ-004": "0710",
    "HPC-001": "3402", "HPC-002": "3402", "HPC-003": "3402", "HPC-004": "3402", "HPC-005": "3401", "HPC-006": "3305",
    "HPC-007": "3306", "HPC-008": "3401",
    "GFT-001": "0801", "GFT-002": "0813", "GFT-003": "1806", "GFT-004": "1905",
}

# name, contact, phone, email, city, lead time days, payment terms
SUPPLIERS = [
    ("Gokul Dairy Co-operative", "Suresh Patil", "+91 98200 11223", "orders@gokuldairy.example", "Kolhapur", 1, "Weekly"),
    ("Morning Fresh Breads & Cereals", "Anita D'Souza", "+91 98201 33445", "sales@morningfresh.example", "Mumbai", 1, "Weekly"),
    ("Coastal Beverages Distributors", "Imran Shaikh", "+91 98673 55667", "dispatch@coastalbev.example", "Mumbai", 3, "Net 15"),
    ("Nilgiri Tea & Coffee Traders", "Lakshmi Iyer", "+91 94430 77889", "trade@nilgiritc.example", "Coimbatore", 5, "Net 30"),
    ("AgroFresh Farms", "Mahesh Jadhav", "+91 97300 99001", "fresh@agrofresh.example", "Nashik", 1, "Cash on delivery"),
    ("Bharat Staples Wholesale", "Rakesh Agarwal", "+91 98250 12121", "orders@bharatstaples.example", "Ahmedabad", 4, "Net 30"),
    ("SnackWorld Distributors", "Neha Kapoor", "+91 99100 34343", "sales@snackworld.example", "Delhi", 5, "Net 30"),
    ("Polar Frozen Foods", "Joseph Mathew", "+91 98450 56565", "orders@polarfrozen.example", "Bengaluru", 3, "Net 15"),
    ("CleanHome Distributors", "Pradeep Menon", "+91 98860 78787", "orders@cleanhome.example", "Bengaluru", 4, "Net 30"),
]

# sku, name, category, unit, cost, price (tax incl.), tax %, popularity weight, seasonal profile, supplier index.
# Every item is a retail SKU a supermarket shelf would carry: packaged groceries, fresh produce sold by weight,
# dairy, and household & personal care. Prices are typical Indian MRPs (2026).
PRODUCTS = [
    # Staples & Grains
    ("STA-001", "Basmati Rice 5kg", "Staples & Grains", "bag", 520, 699, 5, 1.4, "staple", 5),
    ("STA-002", "Sona Masoori Rice 5kg", "Staples & Grains", "bag", 340, 430, 5, 1.6, "staple", 5),
    ("STA-003", "Whole Wheat Atta 5kg", "Staples & Grains", "bag", 215, 285, 5, 1.9, "staple", 5),
    ("STA-004", "Toor Dal 1kg", "Staples & Grains", "pack", 135, 175, 5, 2.4, "staple", 5),
    ("STA-005", "Moong Dal 1kg", "Staples & Grains", "pack", 118, 155, 5, 1.5, "staple", 5),
    ("STA-006", "Sunflower Oil 1L", "Staples & Grains", "pouch", 118, 150, 5, 2.8, "festive", 5),
    ("STA-007", "Iodised Salt 1kg", "Staples & Grains", "pack", 20, 28, 0, 2.2, "staple", 5),
    ("STA-008", "Refined Sugar 1kg", "Staples & Grains", "pack", 42, 52, 5, 3.0, "festive", 5),
    ("STA-009", "Thick Poha 500g", "Staples & Grains", "pack", 32, 45, 5, 1.4, "flat", 5),
    # Dairy & Eggs
    ("DAI-001", "Toned Milk 1L", "Dairy & Eggs", "pack", 58, 68, 0, 12.0, "flat", 0),
    ("DAI-002", "Fresh Curd 400g", "Dairy & Eggs", "cup", 32, 45, 5, 5.5, "summer", 0),
    ("DAI-003", "Malai Paneer 200g", "Dairy & Eggs", "pack", 72, 95, 5, 4.2, "festive", 0),
    ("DAI-004", "Salted Butter 100g", "Dairy & Eggs", "pack", 48, 62, 12, 3.4, "winter", 0),
    ("DAI-005", "Cheese Slices 200g", "Dairy & Eggs", "pack", 105, 145, 12, 2.3, "flat", 0),
    ("DAI-006", "Farm Eggs (12)", "Dairy & Eggs", "tray", 72, 96, 0, 5.0, "winter", 0),
    ("DAI-007", "Greek Yogurt 100g", "Dairy & Eggs", "cup", 32, 50, 5, 2.0, "summer", 0),
    # Fruits & Vegetables
    ("FRV-001", "Robusta Bananas (dozen)", "Fruits & Vegetables", "dozen", 42, 60, 0, 5.5, "flat", 4),
    ("FRV-002", "Shimla Apples 1kg", "Fruits & Vegetables", "kg", 140, 199, 0, 2.6, "winter", 4),
    ("FRV-003", "Tomatoes 1kg", "Fruits & Vegetables", "kg", 30, 45, 0, 5.2, "flat", 4),
    ("FRV-004", "Red Onions 1kg", "Fruits & Vegetables", "kg", 32, 45, 0, 5.0, "flat", 4),
    ("FRV-005", "Nagpur Oranges 1kg", "Fruits & Vegetables", "kg", 70, 99, 0, 1.8, "winter", 4),
    ("FRV-006", "Alphonso Mangoes 1kg", "Fruits & Vegetables", "kg", 320, 480, 0, 2.5, "mango", 4),
    ("FRV-007", "Baby Spinach 200g", "Fruits & Vegetables", "pack", 30, 49, 0, 2.2, "winter", 4),
    ("FRV-008", "Potatoes 1kg", "Fruits & Vegetables", "kg", 26, 38, 0, 4.4, "flat", 4),
    # Beverages
    ("BEV-001", "Packaged Drinking Water 1L", "Beverages", "bottle", 12, 20, 18, 9.0, "summer", 2),
    ("BEV-002", "Tender Coconut Water 200ml", "Beverages", "pack", 28, 45, 12, 3.5, "summer", 2),
    ("BEV-003", "Mango Juice 1L", "Beverages", "pack", 78, 120, 12, 2.6, "summer", 2),
    ("BEV-004", "Cold Coffee 200ml", "Beverages", "bottle", 28, 45, 12, 2.2, "summer", 2),
    ("BEV-005", "Lemon Iced Tea 500ml", "Beverages", "bottle", 38, 60, 12, 2.4, "summer", 2),
    ("BEV-006", "Sparkling Water 300ml", "Beverages", "can", 42, 70, 18, 1.6, "party", 2),
    ("BEV-007", "Cola 750ml", "Beverages", "bottle", 30, 45, 28, 3.2, "party", 2),
    ("BEV-008", "Orange Juice 1L", "Beverages", "pack", 85, 130, 12, 1.4, "flat", 2),
    # Tea & Coffee
    ("TEA-001", "Assam CTC Tea 500g", "Tea & Coffee", "pack", 190, 275, 5, 1.8, "winter", 3),
    ("TEA-002", "Darjeeling Green Tea 25 bags", "Tea & Coffee", "box", 140, 220, 5, 1.1, "flat", 3),
    ("TEA-003", "Filter Coffee Powder 250g", "Tea & Coffee", "pack", 165, 245, 5, 1.3, "winter", 3),
    ("TEA-004", "Instant Coffee 100g", "Tea & Coffee", "jar", 260, 380, 18, 1.0, "winter", 3),
    ("TEA-005", "Masala Chai Premix 10 sachets", "Tea & Coffee", "box", 95, 150, 18, 1.0, "monsoon", 3),
    # Bread & Breakfast
    ("BRK-001", "Whole Wheat Bread 400g", "Bread & Breakfast", "loaf", 34, 50, 0, 6.5, "flat", 1),
    ("BRK-002", "Multigrain Bread 400g", "Bread & Breakfast", "loaf", 42, 65, 0, 3.0, "weekend", 1),
    ("BRK-003", "Rolled Oats 1kg", "Bread & Breakfast", "pack", 150, 215, 5, 1.4, "winter", 1),
    ("BRK-004", "Corn Flakes 475g", "Bread & Breakfast", "box", 130, 195, 18, 1.6, "flat", 1),
    ("BRK-005", "Peanut Butter 340g", "Bread & Breakfast", "jar", 140, 210, 12, 1.2, "flat", 1),
    ("BRK-006", "Mixed Fruit Jam 500g", "Bread & Breakfast", "jar", 110, 165, 12, 1.1, "weekend", 1),
    ("BRK-007", "Natural Honey 250g", "Bread & Breakfast", "jar", 120, 180, 5, 0.9, "winter", 1),
    # Snacks & Biscuits
    ("SNK-001", "Classic Salted Chips 90g", "Snacks & Biscuits", "pack", 30, 50, 12, 5.0, "party", 6),
    ("SNK-002", "Peri Peri Nachos 150g", "Snacks & Biscuits", "pack", 58, 99, 12, 2.2, "party", 6),
    ("SNK-003", "Bhujia Namkeen 400g", "Snacks & Biscuits", "pack", 75, 110, 12, 2.6, "festive", 6),
    ("SNK-004", "Digestive Biscuits 250g", "Snacks & Biscuits", "pack", 38, 55, 18, 3.6, "flat", 6),
    ("SNK-005", "Butter Cookies 300g", "Snacks & Biscuits", "box", 120, 199, 18, 1.4, "festive", 6),
    ("SNK-006", "Dark Chocolate 70% 100g", "Snacks & Biscuits", "bar", 110, 175, 18, 2.0, "festive", 6),
    ("SNK-007", "California Almonds 200g", "Snacks & Biscuits", "pack", 210, 299, 12, 1.6, "festive", 6),
    ("SNK-008", "Protein Bar 60g", "Snacks & Biscuits", "bar", 55, 90, 18, 1.8, "flat", 6),
    # Frozen Foods
    ("FRZ-001", "Frozen Green Peas 500g", "Frozen Foods", "pack", 75, 110, 5, 1.6, "flat", 7),
    ("FRZ-002", "Chocolate Ice Cream 500ml", "Frozen Foods", "tub", 165, 260, 18, 2.2, "summer", 7),
    ("FRZ-003", "Frozen French Fries 750g", "Frozen Foods", "pack", 110, 170, 12, 1.5, "party", 7),
    ("FRZ-004", "Frozen Sweet Corn 500g", "Frozen Foods", "pack", 70, 105, 5, 1.0, "monsoon", 7),
    # Household & Personal Care
    ("HPC-001", "Detergent Powder 1kg", "Household & Personal Care", "pack", 90, 135, 18, 2.4, "staple", 8),
    ("HPC-002", "Dishwash Liquid 750ml", "Household & Personal Care", "bottle", 102, 155, 18, 2.0, "staple", 8),
    ("HPC-003", "Floor Cleaner 1L", "Household & Personal Care", "bottle", 130, 199, 18, 1.4, "festive", 8),
    ("HPC-004", "Toilet Cleaner 500ml", "Household & Personal Care", "bottle", 67, 99, 18, 1.2, "staple", 8),
    ("HPC-005", "Bath Soap (pack of 4)", "Household & Personal Care", "pack", 112, 170, 18, 1.8, "staple", 8),
    ("HPC-006", "Anti-dandruff Shampoo 340ml", "Household & Personal Care", "bottle", 245, 375, 18, 1.0, "flat", 8),
    ("HPC-007", "Toothpaste 150g", "Household & Personal Care", "tube", 67, 105, 18, 2.2, "staple", 8),
    ("HPC-008", "Hand Wash Refill 750ml", "Household & Personal Care", "pouch", 88, 140, 18, 1.2, "monsoon", 8),
    # Festive & Gifting
    ("GFT-001", "Premium Cashews 500g", "Festive & Gifting", "pack", 420, 599, 5, 1.1, "festive", 6),
    ("GFT-002", "Dry Fruit Gift Box", "Festive & Gifting", "box", 780, 1199, 12, 0.3, "diwali", 6),
    ("GFT-003", "Assorted Chocolate Gift Pack", "Festive & Gifting", "box", 330, 499, 18, 0.7, "festive", 6),
    ("GFT-004", "Christmas Plum Cake 500g", "Festive & Gifting", "pack", 210, 350, 18, 0.25, "christmas", 1),
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Akash", "Ananya", "Arjun", "Bhavna", "Chetan", "Deepa", "Dev", "Divya", "Farhan", "Gauri",
    "Harsh", "Isha", "Jay", "Kabir", "Kiran", "Lavanya", "Manish", "Meera", "Mohit", "Nandini", "Neel", "Nikita",
    "Om", "Pooja", "Pranav", "Radhika", "Rahul", "Riya", "Rohan", "Saanvi", "Sahil", "Sanjana", "Shreya", "Siddharth",
    "Simran", "Tanvi", "Tarun", "Uday", "Varun", "Vidya", "Yash", "Zara", "Aisha", "Kunal", "Maya", "Nisha", "Parth",
    "Rina", "Sameer", "Tara", "Vivek", "Anjali", "Gaurav", "Irfan", "Joseph", "Leela", "Naveen", "Sunita",
]
LAST_NAMES = [
    "Sharma", "Patel", "Iyer", "Reddy", "Nair", "Mehta", "Kulkarni", "Shah", "Rao", "Gupta", "Desai", "Joshi",
    "Menon", "Pillai", "Kapoor", "Singh", "Verma", "D'Souza", "Fernandes", "Khan", "Bhat", "Chopra", "Banerjee",
    "Das", "Hegde", "Shetty", "Agarwal", "Malhotra", "Jain", "Kamath",
]
BUSINESS_NAMES = [
    "Cafe Brewster", "The Daily Grind Cafe", "Spice Route Kitchen", "Green Bowl Salads", "Corner Bistro",
    "Sunrise Caterers", "Little Italy Pizzeria", "Chai Sutta Point", "Bombay Brunch Co.", "Hearth & Oven Bakery",
    "Saffron Tiffin Services", "Urban Eats Cloud Kitchen",
]

# Items that are often bought together: (anchor sku, companion sku, probability the companion is added)
COMPANIONS = [
    ("BRK-001", "DAI-004", 0.28), ("BRK-001", "DAI-006", 0.22), ("BRK-002", "DAI-005", 0.20),
    ("BRK-004", "DAI-001", 0.35), ("BRK-003", "DAI-001", 0.30), ("BRK-005", "BRK-001", 0.25),
    ("BRK-006", "BRK-001", 0.25), ("SNK-001", "BEV-007", 0.35), ("SNK-002", "BEV-007", 0.30),
    ("SNK-002", "BEV-006", 0.18), ("FRZ-003", "BEV-007", 0.20), ("TEA-001", "DAI-001", 0.40),
    ("TEA-001", "STA-008", 0.30), ("TEA-003", "DAI-001", 0.40), ("TEA-005", "SNK-004", 0.25),
    ("DAI-003", "FRV-003", 0.30), ("DAI-003", "FRV-004", 0.25), ("STA-001", "STA-004", 0.30),
    ("STA-002", "STA-005", 0.25), ("STA-003", "STA-006", 0.22), ("HPC-001", "HPC-002", 0.25),
    ("HPC-005", "HPC-007", 0.20), ("GFT-001", "GFT-002", 0.20), ("FRV-004", "FRV-003", 0.30),
    ("DAI-007", "FRV-001", 0.18),
]
