"""Static reference data for the demo organization: outlets, suppliers and product catalog."""

ORGANIZATION = {
    "name": "Urban Harvest Foods Pvt. Ltd.",
    "industry": "Food & Beverage Retail",
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
    "BEV-001": "2201", "BEV-002": "2202", "BEV-003": "2009", "BEV-004": "2101", "BEV-005": "2202", "BEV-006": "2201",
    "BEV-007": "2202", "BEV-008": "2202", "TEA-001": "0902", "TEA-002": "0902", "TEA-003": "0901", "TEA-004": "2101",
    "TEA-005": "2101", "DAI-001": "0401", "DAI-002": "0403", "DAI-003": "0406", "DAI-004": "0405", "DAI-005": "0406",
    "DAI-006": "0407", "DAI-007": "0403", "BAK-001": "1905", "BAK-002": "1905", "BAK-003": "1905", "BAK-004": "1905",
    "BAK-005": "1905", "BAK-006": "1905", "BAK-007": "1905", "SNK-001": "2005", "SNK-002": "1904", "SNK-003": "0802",
    "SNK-004": "1806", "SNK-005": "0813", "SNK-006": "2106", "SNK-007": "2106", "SNK-008": "1106", "STA-001": "1006",
    "STA-002": "1101", "STA-003": "0713", "STA-004": "1509", "STA-005": "1512", "STA-006": "1701", "STA-007": "1008",
    "STA-008": "1104", "FRV-001": "0803", "FRV-002": "0808", "FRV-003": "0702", "FRV-004": "0703", "FRV-005": "0804",
    "FRV-006": "0804", "FRV-007": "0709", "FRV-008": "0701", "FRZ-001": "0710", "FRZ-002": "2105", "FRZ-003": "1905",
    "FRZ-004": "1902", "FRZ-005": "2106", "FRZ-006": "2105", "SWT-001": "1704", "SWT-002": "2106", "SWT-003": "0813",
    "SWT-004": "2106",
}

# name, contact, phone, email, city, lead time days, payment terms
SUPPLIERS = [
    ("Gokul Dairy Co-operative", "Suresh Patil", "+91 98200 11223", "orders@gokuldairy.example", "Kolhapur", 1, "Weekly"),
    ("Bake House Supplies", "Anita D'Souza", "+91 98201 33445", "sales@bakehouse.example", "Mumbai", 1, "Weekly"),
    ("Coastal Beverages Distributors", "Imran Shaikh", "+91 98673 55667", "dispatch@coastalbev.example", "Mumbai", 3, "Net 15"),
    ("Nilgiri Tea & Coffee Traders", "Lakshmi Iyer", "+91 94430 77889", "trade@nilgiritc.example", "Coimbatore", 5, "Net 30"),
    ("AgroFresh Farms", "Mahesh Jadhav", "+91 97300 99001", "fresh@agrofresh.example", "Nashik", 1, "Cash on delivery"),
    ("Bharat Staples Wholesale", "Rakesh Agarwal", "+91 98250 12121", "orders@bharatstaples.example", "Ahmedabad", 4, "Net 30"),
    ("SnackWorld Distributors", "Neha Kapoor", "+91 99100 34343", "sales@snackworld.example", "Delhi", 5, "Net 30"),
    ("Polar Frozen Foods", "Joseph Mathew", "+91 98450 56565", "orders@polarfrozen.example", "Bengaluru", 3, "Net 15"),
]

# sku, name, category, unit, cost, price (tax incl.), tax %, popularity weight, seasonal profile, supplier index
PRODUCTS = [
    # Beverages
    ("BEV-001", "Packaged Drinking Water 1L", "Beverages", "bottle", 12, 20, 18, 9.0, "summer", 2),
    ("BEV-002", "Tender Coconut Water 200ml", "Beverages", "pack", 28, 45, 12, 3.5, "summer", 2),
    ("BEV-003", "Alphonso Mango Juice 1L", "Beverages", "pack", 78, 120, 12, 2.6, "summer", 2),
    ("BEV-004", "Cold Brew Coffee 250ml", "Beverages", "bottle", 85, 140, 12, 2.2, "summer", 2),
    ("BEV-005", "Lemon Iced Tea 500ml", "Beverages", "bottle", 38, 60, 12, 2.4, "summer", 2),
    ("BEV-006", "Sparkling Water 300ml", "Beverages", "can", 42, 70, 18, 1.6, "party", 2),
    ("BEV-007", "Cola 750ml", "Beverages", "bottle", 30, 45, 28, 3.2, "party", 2),
    ("BEV-008", "Kombucha Ginger 330ml", "Beverages", "bottle", 110, 180, 12, 0.9, "flat", 2),
    # Tea & Coffee
    ("TEA-001", "Assam CTC Tea 500g", "Tea & Coffee", "pack", 190, 275, 5, 1.6, "winter", 3),
    ("TEA-002", "Darjeeling Green Tea 25 bags", "Tea & Coffee", "box", 140, 220, 5, 1.1, "flat", 3),
    ("TEA-003", "Filter Coffee Powder 250g", "Tea & Coffee", "pack", 165, 245, 5, 1.3, "winter", 3),
    ("TEA-004", "Instant Coffee 100g", "Tea & Coffee", "jar", 260, 380, 18, 1.0, "winter", 3),
    ("TEA-005", "Masala Chai Premix 10 sachets", "Tea & Coffee", "box", 95, 150, 18, 1.2, "monsoon", 3),
    # Dairy & Eggs
    ("DAI-001", "Toned Milk 1L", "Dairy & Eggs", "pack", 58, 68, 0, 12.0, "flat", 0),
    ("DAI-002", "Fresh Curd 400g", "Dairy & Eggs", "cup", 32, 45, 5, 5.5, "summer", 0),
    ("DAI-003", "Malai Paneer 200g", "Dairy & Eggs", "pack", 72, 95, 5, 4.2, "festive", 0),
    ("DAI-004", "Salted Butter 100g", "Dairy & Eggs", "pack", 48, 62, 12, 3.4, "winter", 0),
    ("DAI-005", "Cheese Slices 200g", "Dairy & Eggs", "pack", 105, 145, 12, 2.3, "flat", 0),
    ("DAI-006", "Farm Eggs (12)", "Dairy & Eggs", "tray", 72, 96, 0, 5.0, "winter", 0),
    ("DAI-007", "Greek Yogurt 100g", "Dairy & Eggs", "cup", 32, 50, 5, 2.0, "summer", 0),
    # Bakery
    ("BAK-001", "Sourdough Loaf", "Bakery", "loaf", 95, 160, 5, 2.4, "weekend", 1),
    ("BAK-002", "Whole Wheat Bread 400g", "Bakery", "loaf", 34, 50, 0, 6.5, "flat", 1),
    ("BAK-003", "Butter Croissant", "Bakery", "pcs", 38, 75, 18, 3.6, "weekend", 1),
    ("BAK-004", "Multigrain Bread 400g", "Bakery", "loaf", 42, 65, 0, 3.0, "flat", 1),
    ("BAK-005", "Chocolate Muffin", "Bakery", "pcs", 30, 60, 18, 2.8, "weekend", 1),
    ("BAK-006", "Butter Cookies 300g", "Bakery", "box", 120, 199, 18, 1.4, "festive", 1),
    ("BAK-007", "Plum Cake 500g", "Bakery", "pcs", 210, 350, 18, 0.25, "christmas", 1),
    # Snacks & Confectionery
    ("SNK-001", "Classic Salted Chips 90g", "Snacks & Confectionery", "pack", 30, 50, 12, 5.0, "party", 6),
    ("SNK-002", "Peri Peri Nachos 150g", "Snacks & Confectionery", "pack", 58, 99, 12, 2.2, "party", 6),
    ("SNK-003", "California Almonds 200g", "Snacks & Confectionery", "pack", 210, 299, 12, 1.6, "festive", 6),
    ("SNK-004", "Dark Chocolate 70% 100g", "Snacks & Confectionery", "bar", 110, 175, 18, 2.0, "festive", 6),
    ("SNK-005", "Roasted Trail Mix 150g", "Snacks & Confectionery", "pack", 120, 185, 12, 1.2, "flat", 6),
    ("SNK-006", "Bhujia Namkeen 400g", "Snacks & Confectionery", "pack", 75, 110, 12, 2.6, "festive", 6),
    ("SNK-007", "Protein Bar 60g", "Snacks & Confectionery", "bar", 55, 90, 18, 1.8, "flat", 6),
    ("SNK-008", "Onion Pakoda Mix 200g", "Snacks & Confectionery", "pack", 40, 65, 12, 1.0, "monsoon", 6),
    # Staples & Grains
    ("STA-001", "Basmati Rice 5kg", "Staples & Grains", "bag", 520, 699, 5, 1.4, "staple", 5),
    ("STA-002", "Whole Wheat Atta 5kg", "Staples & Grains", "bag", 215, 285, 5, 1.8, "staple", 5),
    ("STA-003", "Toor Dal 1kg", "Staples & Grains", "pack", 135, 175, 5, 2.4, "staple", 5),
    ("STA-004", "Extra Virgin Olive Oil 1L", "Staples & Grains", "bottle", 690, 950, 5, 0.6, "staple", 5),
    ("STA-005", "Sunflower Oil 1L", "Staples & Grains", "pouch", 118, 150, 5, 2.8, "festive", 5),
    ("STA-006", "Refined Sugar 1kg", "Staples & Grains", "pack", 42, 52, 5, 3.0, "festive", 5),
    ("STA-007", "Organic Quinoa 500g", "Staples & Grains", "pack", 210, 320, 5, 0.6, "flat", 5),
    ("STA-008", "Rolled Oats 1kg", "Staples & Grains", "pack", 150, 215, 5, 1.4, "winter", 5),
    # Fruits & Vegetables
    ("FRV-001", "Robusta Bananas (dozen)", "Fruits & Vegetables", "dozen", 42, 60, 0, 5.5, "flat", 4),
    ("FRV-002", "Shimla Apples 1kg", "Fruits & Vegetables", "kg", 140, 199, 0, 2.6, "winter", 4),
    ("FRV-003", "Tomatoes 1kg", "Fruits & Vegetables", "kg", 30, 45, 0, 5.2, "flat", 4),
    ("FRV-004", "Red Onions 1kg", "Fruits & Vegetables", "kg", 32, 45, 0, 5.0, "flat", 4),
    ("FRV-005", "Hass Avocado", "Fruits & Vegetables", "pcs", 95, 149, 0, 1.0, "flat", 4),
    ("FRV-006", "Alphonso Mangoes 1kg", "Fruits & Vegetables", "kg", 320, 480, 0, 2.5, "mango", 4),
    ("FRV-007", "Baby Spinach 200g", "Fruits & Vegetables", "pack", 30, 49, 0, 2.2, "winter", 4),
    ("FRV-008", "Potatoes 1kg", "Fruits & Vegetables", "kg", 26, 38, 0, 4.4, "flat", 4),
    # Frozen & Ready-to-eat
    ("FRZ-001", "Frozen Green Peas 500g", "Frozen & Ready-to-eat", "pack", 75, 110, 5, 1.6, "flat", 7),
    ("FRZ-002", "Belgian Chocolate Ice Cream 500ml", "Frozen & Ready-to-eat", "tub", 165, 260, 18, 2.2, "summer", 7),
    ("FRZ-003", "Malabar Parotta (5 pcs)", "Frozen & Ready-to-eat", "pack", 62, 95, 5, 1.8, "flat", 7),
    ("FRZ-004", "Veg Momos 10 pcs", "Frozen & Ready-to-eat", "pack", 95, 150, 5, 1.6, "monsoon", 7),
    ("FRZ-005", "Ready-to-eat Veg Biryani", "Frozen & Ready-to-eat", "pack", 85, 135, 12, 1.4, "flat", 7),
    ("FRZ-006", "Mango Kulfi (4 pcs)", "Frozen & Ready-to-eat", "box", 90, 150, 18, 1.0, "summer", 7),
    # Sweets & Festive
    ("SWT-001", "Kaju Katli 250g", "Sweets & Festive", "box", 230, 340, 5, 0.9, "diwali", 6),
    ("SWT-002", "Gulab Jamun Tin 1kg", "Sweets & Festive", "tin", 160, 240, 5, 0.7, "diwali", 6),
    ("SWT-003", "Dry Fruit Gift Hamper", "Sweets & Festive", "box", 780, 1199, 12, 0.25, "diwali", 6),
    ("SWT-004", "Rasgulla Tin 1kg", "Sweets & Festive", "tin", 150, 225, 5, 0.5, "festive", 6),
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
    ("BAK-001", "DAI-004", 0.30), ("BAK-001", "DAI-005", 0.22), ("BAK-002", "DAI-004", 0.25),
    ("BAK-002", "DAI-006", 0.22), ("BAK-004", "DAI-004", 0.18), ("BAK-003", "BEV-004", 0.20),
    ("SNK-001", "BEV-007", 0.35), ("SNK-002", "BEV-007", 0.30), ("SNK-002", "BEV-006", 0.18),
    ("TEA-001", "DAI-001", 0.40), ("TEA-001", "STA-006", 0.30), ("TEA-003", "DAI-001", 0.40),
    ("TEA-005", "SNK-008", 0.28), ("DAI-003", "FRV-003", 0.30), ("DAI-003", "FRV-004", 0.25),
    ("STA-001", "STA-003", 0.30), ("STA-002", "STA-005", 0.22), ("FRV-005", "BAK-001", 0.25),
    ("FRZ-003", "DAI-003", 0.20), ("STA-008", "DAI-001", 0.30), ("SWT-001", "SNK-003", 0.30),
    ("FRZ-004", "BEV-005", 0.15), ("DAI-007", "FRV-001", 0.18),
]
