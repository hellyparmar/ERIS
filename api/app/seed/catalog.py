"""Static reference data for the demo organization, a casual-dining restaurant chain: outlets, suppliers, the
ingredients its kitchens stock, and its menu with a recipe for every dish (how much of each ingredient one portion
uses). Food costs follow from the recipes; prices are typical for Indian metro casual dining (2026)."""

ORGANIZATION = {
    "name": "Saffron Table Restaurants Pvt. Ltd.",
    "industry": "Restaurants (Casual Dining)",
    "currency": "INR",
    "currency_symbol": "₹",
    "timezone": "Asia/Kolkata",
    "email": "hello@saffrontable.example",
    "phone": "+91 22 4000 1234",
    "address": "4th Floor, Lotus Corporate Park, Goregaon East, Mumbai 400063",
    "state": "Maharashtra",
    "state_code": "27",
    # tax_id: a synthetic, checksum-valid GSTIN is generated from the seed (see services/gst.py) and marked demo.
}

# The chain runs five restaurants by default (SEED_OUTLETS, up to 7) - each with a different demand profile.
# code, name, city, state, state code, address, manager, size, growth/yr, opened N days before data end (None = long open)
OUTLETS = [
    ("MUM-AND", "Andheri West", "Mumbai", "Maharashtra", "27", "Lokhandwala Complex, Andheri West, Mumbai",
     "Priya Sharma", 1.30, 0.12, None),   # flagship, steady growth, monsoon city
    ("PUN-KOR", "Koregaon Park", "Pune", "Maharashtra", "27", "North Main Road, Koregaon Park, Pune",
     "Sneha Kulkarni", 0.95, 0.16, None),  # fastest-growing established outlet
    ("BLR-IND", "Indiranagar", "Bengaluru", "Karnataka", "29", "100 Feet Road, Indiranagar, Bengaluru",
     "Arjun Rao", 1.10, 0.10, None),       # tech crowd: high delivery share
    ("AMD-SGH", "SG Highway", "Ahmedabad", "Gujarat", "24", "Sindhu Bhavan Road, SG Highway, Ahmedabad",
     "Kavya Patel", 0.85, -0.08, None),    # mostly vegetarian guests; losing ground to a new competitor
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

# Taste differences between the restaurants: how much non-vegetarian food sells (1 = chain average) and the share
# of orders that come through delivery apps.
OUTLET_TASTE = {
    "MUM-AND": {"nonveg": 1.05, "delivery": 0.30},
    "PUN-KOR": {"nonveg": 1.0, "delivery": 0.28},
    "BLR-IND": {"nonveg": 1.15, "delivery": 0.40},
    "AMD-SGH": {"nonveg": 0.45, "delivery": 0.24},
    "BLR-WHF": {"nonveg": 1.1, "delivery": 0.42},
    "MUM-BAN": {"nonveg": 1.1, "delivery": 0.32},
    "HYD-JUB": {"nonveg": 1.35, "delivery": 0.34},
}

RESTAURANT_SAC = "996331"  # GST services code for restaurant food & beverage, printed on demo invoices
MENU_TAX_RATE = 5.0  # GST on restaurant service (no input tax credit)

# name, contact, phone, email, city, lead time days, payment terms
SUPPLIERS = [
    ("Gokul Dairy Co-operative", "Suresh Patil", "+91 98200 11223", "orders@gokuldairy.example", "Kolhapur", 1, "Weekly"),
    ("Fresh Catch Meats & Poultry", "Imran Qureshi", "+91 98201 33445", "orders@freshcatch.example", "Mumbai", 1, "Weekly"),
    ("AgroFresh Farms", "Mahesh Jadhav", "+91 97300 99001", "fresh@agrofresh.example", "Nashik", 1, "Cash on delivery"),
    ("Bharat Staples Wholesale", "Rakesh Agarwal", "+91 98250 12121", "orders@bharatstaples.example", "Ahmedabad", 3, "Net 30"),
    ("Coastal Beverages Distributors", "Imran Shaikh", "+91 98673 55667", "dispatch@coastalbev.example", "Mumbai", 3, "Net 15"),
    ("Nilgiri Tea & Coffee Traders", "Lakshmi Iyer", "+91 94430 77889", "trade@nilgiritc.example", "Coimbatore", 5, "Net 30"),
    ("Polar Frozen Desserts", "Joseph Mathew", "+91 98450 56565", "orders@polarfrozen.example", "Bengaluru", 3, "Net 15"),
]

# Ingredients the kitchens stock: sku, name, store category, unit, cost per unit (₹), supplier index,
# cost profile ("" = steady inflation, "tomato" / "onion" = seasonal price spikes, "carrot" = winter crop).
INGREDIENTS = [
    ("ING-001", "Paneer", "Dairy", "kg", 400, 0, ""),
    ("ING-002", "Fresh Cream", "Dairy", "L", 250, 0, ""),
    ("ING-003", "Butter", "Dairy", "kg", 520, 0, ""),
    ("ING-004", "Curd", "Dairy", "kg", 70, 0, ""),
    ("ING-005", "Milk", "Dairy", "L", 58, 0, ""),
    ("ING-006", "Ghee", "Dairy", "kg", 620, 0, ""),
    ("ING-007", "Khoya", "Dairy", "kg", 380, 0, ""),
    ("ING-008", "Chicken (Boneless)", "Meat & Seafood", "kg", 340, 1, ""),
    ("ING-009", "Chicken (Curry Cut)", "Meat & Seafood", "kg", 240, 1, ""),
    ("ING-010", "Mutton", "Meat & Seafood", "kg", 720, 1, ""),
    ("ING-011", "Basa Fish Fillet", "Meat & Seafood", "kg", 380, 1, ""),
    ("ING-012", "Eggs", "Meat & Seafood", "pcs", 6.5, 1, ""),
    ("ING-013", "Onion", "Vegetables", "kg", 32, 2, "onion"),
    ("ING-014", "Tomato", "Vegetables", "kg", 36, 2, "tomato"),
    ("ING-015", "Potato", "Vegetables", "kg", 28, 2, ""),
    ("ING-016", "Capsicum", "Vegetables", "kg", 70, 2, ""),
    ("ING-017", "Ginger-Garlic Paste", "Vegetables", "kg", 120, 2, ""),
    ("ING-018", "Coriander & Green Chilli", "Vegetables", "kg", 120, 2, ""),
    ("ING-019", "Mixed Vegetables", "Vegetables", "kg", 90, 2, ""),
    ("ING-020", "Carrot", "Vegetables", "kg", 45, 2, "carrot"),
    ("ING-021", "Lemon", "Vegetables", "pcs", 4, 2, ""),
    ("ING-022", "Basmati Rice", "Dry Store", "kg", 120, 3, ""),
    ("ING-023", "Wheat Flour (Atta)", "Dry Store", "kg", 38, 3, ""),
    ("ING-024", "Refined Flour (Maida)", "Dry Store", "kg", 40, 3, ""),
    ("ING-025", "Black Urad Dal", "Dry Store", "kg", 140, 3, ""),
    ("ING-026", "Toor Dal", "Dry Store", "kg", 135, 3, ""),
    ("ING-027", "Kabuli Chana", "Dry Store", "kg", 110, 3, ""),
    ("ING-028", "Cooking Oil", "Dry Store", "L", 165, 3, ""),
    ("ING-029", "Spice Mix & Masalas", "Dry Store", "kg", 650, 3, ""),
    ("ING-030", "Hakka Noodles", "Dry Store", "kg", 160, 3, ""),
    ("ING-031", "Soy & Chilli Sauces", "Dry Store", "L", 140, 3, ""),
    ("ING-032", "Sugar", "Dry Store", "kg", 44, 3, ""),
    ("ING-033", "Alphonso Mango Pulp", "Dry Store", "kg", 160, 3, ""),
    ("ING-034", "Tea Leaves", "Beverage Stock", "kg", 520, 5, ""),
    ("ING-035", "Filter Coffee Powder", "Beverage Stock", "kg", 900, 5, ""),
    ("ING-036", "Soft Drink Can 300ml", "Beverage Stock", "pcs", 28, 4, ""),
    ("ING-037", "Mineral Water 1L", "Beverage Stock", "pcs", 14, 4, ""),
    ("ING-038", "Vanilla Ice Cream", "Frozen", "L", 260, 6, ""),
]

# The menu: sku, name, category, unit, price (₹, GST inclusive), popularity weight, demand profile,
# vegetarian?, recipe {ingredient sku: quantity per portion in the ingredient's unit}.
# Demand profiles: "" steady, "summer" (hot days), "winter", "monsoon" (rainy days), "mango" (Apr-Jun),
# "weekend", "festive" (sweets around festivals), "date" (Valentine's / New Year desserts).
MENU = [
    # Soups
    ("SUP-001", "Tomato Shorba", "Soups", "bowl", 179, 0.9, "winter", True,
     {"ING-014": 0.15, "ING-002": 0.01, "ING-003": 0.005, "ING-029": 0.004, "ING-018": 0.012, "ING-028": 0.01}),
    ("SUP-002", "Sweet Corn Soup", "Soups", "bowl", 189, 0.8, "winter", True,
     {"ING-019": 0.08, "ING-031": 0.01, "ING-024": 0.01, "ING-018": 0.012, "ING-028": 0.01}),
    ("SUP-003", "Chicken Manchow Soup", "Soups", "bowl", 219, 0.7, "winter", False,
     {"ING-008": 0.05, "ING-019": 0.05, "ING-031": 0.015, "ING-030": 0.02, "ING-018": 0.012, "ING-028": 0.01}),
    # Starters
    ("STR-001", "Paneer Tikka", "Starters", "plate", 329, 2.2, "", True,
     {"ING-001": 0.18, "ING-004": 0.05, "ING-016": 0.05, "ING-013": 0.05, "ING-029": 0.008, "ING-028": 0.01, "ING-018": 0.012}),
    ("STR-002", "Hara Bhara Kebab", "Starters", "plate", 259, 1.0, "", True,
     {"ING-019": 0.12, "ING-015": 0.06, "ING-029": 0.006, "ING-028": 0.02, "ING-018": 0.012}),
    ("STR-003", "Onion & Veg Pakora", "Starters", "plate", 219, 0.9, "monsoon", True,
     {"ING-019": 0.08, "ING-013": 0.1, "ING-015": 0.05, "ING-024": 0.05, "ING-028": 0.05, "ING-018": 0.012}),
    ("STR-004", "Chicken Tikka", "Starters", "plate", 389, 2.4, "", False,
     {"ING-008": 0.22, "ING-004": 0.05, "ING-029": 0.01, "ING-028": 0.01, "ING-021": 1, "ING-018": 0.012}),
    ("STR-005", "Tandoori Chicken (Half)", "Starters", "plate", 419, 1.8, "weekend", False,
     {"ING-009": 0.45, "ING-004": 0.06, "ING-029": 0.012, "ING-003": 0.01, "ING-021": 1, "ING-018": 0.012, "ING-028": 0.01}),
    ("STR-006", "Chilli Paneer (Dry)", "Starters", "plate", 309, 1.4, "", True,
     {"ING-001": 0.16, "ING-016": 0.06, "ING-013": 0.05, "ING-031": 0.02, "ING-024": 0.02, "ING-028": 0.03, "ING-018": 0.012}),
    ("STR-007", "Fish Amritsari", "Starters", "plate", 429, 0.7, "", False,
     {"ING-011": 0.2, "ING-024": 0.03, "ING-029": 0.008, "ING-028": 0.05, "ING-021": 1, "ING-018": 0.012}),
    ("STR-008", "Chicken 65", "Starters", "plate", 359, 1.5, "", False,
     {"ING-008": 0.2, "ING-004": 0.03, "ING-029": 0.01, "ING-028": 0.05, "ING-017": 0.01, "ING-018": 0.012}),
    # Main Course
    ("MNC-001", "Paneer Butter Masala", "Main Course", "bowl", 349, 2.6, "", True,
     {"ING-001": 0.18, "ING-014": 0.15, "ING-003": 0.02, "ING-002": 0.03,
      "ING-029": 0.008, "ING-017": 0.01, "ING-018": 0.012, "ING-028": 0.01}),
    ("MNC-002", "Kadai Paneer", "Main Course", "bowl", 339, 1.3, "", True,
     {"ING-001": 0.17, "ING-016": 0.07, "ING-013": 0.08, "ING-014": 0.1, "ING-029": 0.01, "ING-028": 0.02, "ING-018": 0.012}),
    ("MNC-003", "Dal Makhani", "Main Course", "bowl", 289, 2.8, "", True,
     {"ING-025": 0.09, "ING-003": 0.02, "ING-002": 0.025, "ING-014": 0.06, "ING-029": 0.006, "ING-018": 0.012, "ING-028": 0.01}),
    ("MNC-004", "Dal Tadka", "Main Course", "bowl", 239, 1.9, "", True,
     {"ING-026": 0.1, "ING-006": 0.01, "ING-014": 0.04, "ING-013": 0.04, "ING-029": 0.005, "ING-018": 0.012, "ING-028": 0.01}),
    ("MNC-005", "Chole Masala", "Main Course", "bowl", 259, 1.2, "", True,
     {"ING-027": 0.1, "ING-013": 0.07, "ING-014": 0.07, "ING-029": 0.01, "ING-028": 0.02, "ING-018": 0.012}),
    ("MNC-006", "Mix Veg Curry", "Main Course", "bowl", 269, 1.0, "", True,
     {"ING-019": 0.2, "ING-013": 0.06, "ING-014": 0.06, "ING-029": 0.008, "ING-028": 0.02, "ING-018": 0.012}),
    ("MNC-007", "Butter Chicken", "Main Course", "bowl", 419, 3.0, "", False,
     {"ING-008": 0.22, "ING-014": 0.15, "ING-003": 0.03, "ING-002": 0.04, "ING-029": 0.01, "ING-018": 0.012, "ING-028": 0.01}),
    ("MNC-008", "Chicken Kadai", "Main Course", "bowl", 399, 1.3, "", False,
     {"ING-009": 0.28, "ING-016": 0.06, "ING-013": 0.08, "ING-014": 0.1, "ING-029": 0.012, "ING-028": 0.02, "ING-018": 0.012}),
    ("MNC-009", "Mutton Rogan Josh", "Main Course", "bowl", 579, 1.0, "weekend", False,
     {"ING-010": 0.25, "ING-004": 0.05, "ING-013": 0.08, "ING-029": 0.015, "ING-006": 0.02, "ING-018": 0.012, "ING-028": 0.01}),
    ("MNC-010", "Goan Fish Curry", "Main Course", "bowl", 449, 0.6, "", False,
     {"ING-011": 0.22, "ING-014": 0.08, "ING-013": 0.06, "ING-029": 0.01, "ING-028": 0.02, "ING-018": 0.012}),
    ("MNC-011", "Egg Curry", "Main Course", "bowl", 249, 0.6, "", False,
     {"ING-012": 2, "ING-013": 0.08, "ING-014": 0.08, "ING-029": 0.008, "ING-028": 0.02, "ING-018": 0.012}),
    # Breads
    ("BRD-001", "Butter Naan", "Breads", "pcs", 79, 4.0, "", True, {"ING-024": 0.09, "ING-003": 0.01, "ING-004": 0.01}),
    ("BRD-002", "Tandoori Roti", "Breads", "pcs", 45, 3.2, "", True, {"ING-023": 0.08}),
    ("BRD-003", "Garlic Naan", "Breads", "pcs", 95, 2.2, "", True, {"ING-024": 0.09, "ING-003": 0.012, "ING-017": 0.005}),
    ("BRD-004", "Lachha Paratha", "Breads", "pcs", 85, 1.5, "", True, {"ING-023": 0.09, "ING-006": 0.012}),
    ("BRD-005", "Amritsari Kulcha", "Breads", "pcs", 129, 0.9, "", True,
     {"ING-024": 0.1, "ING-015": 0.06, "ING-003": 0.01}),
    # Rice & Biryani
    ("RIC-001", "Jeera Rice", "Rice & Biryani", "bowl", 199, 1.8, "", True, {"ING-022": 0.12, "ING-006": 0.008, "ING-029": 0.002}),
    ("RIC-002", "Steamed Rice", "Rice & Biryani", "bowl", 159, 1.1, "", True, {"ING-022": 0.13}),
    ("RIC-003", "Veg Dum Biryani", "Rice & Biryani", "plate", 329, 1.6, "weekend", True,
     {"ING-022": 0.16, "ING-019": 0.12, "ING-004": 0.04, "ING-006": 0.015,
      "ING-029": 0.01, "ING-013": 0.05, "ING-018": 0.012, "ING-028": 0.01}),
    ("RIC-004", "Chicken Dum Biryani", "Rice & Biryani", "plate", 399, 2.8, "weekend", False,
     {"ING-022": 0.16, "ING-009": 0.22, "ING-004": 0.05, "ING-006": 0.02,
      "ING-029": 0.012, "ING-013": 0.06, "ING-018": 0.012, "ING-028": 0.01}),
    ("RIC-005", "Mutton Biryani", "Rice & Biryani", "plate", 519, 1.1, "weekend", False,
     {"ING-022": 0.16, "ING-010": 0.2, "ING-004": 0.05, "ING-006": 0.02,
      "ING-029": 0.014, "ING-013": 0.06, "ING-018": 0.012, "ING-028": 0.01}),
    # Indo-Chinese
    ("CHN-001", "Veg Hakka Noodles", "Indo-Chinese", "plate", 249, 1.6, "", True,
     {"ING-030": 0.14, "ING-019": 0.1, "ING-031": 0.02, "ING-028": 0.02, "ING-018": 0.012}),
    ("CHN-002", "Chicken Hakka Noodles", "Indo-Chinese", "plate", 299, 1.3, "", False,
     {"ING-030": 0.14, "ING-008": 0.1, "ING-019": 0.06, "ING-031": 0.02, "ING-028": 0.02, "ING-018": 0.012}),
    ("CHN-003", "Veg Fried Rice", "Indo-Chinese", "plate", 239, 1.4, "", True,
     {"ING-022": 0.14, "ING-019": 0.1, "ING-031": 0.015, "ING-028": 0.02, "ING-018": 0.012}),
    ("CHN-004", "Veg Manchurian (Gravy)", "Indo-Chinese", "plate", 269, 1.2, "monsoon", True,
     {"ING-019": 0.18, "ING-024": 0.04, "ING-031": 0.025, "ING-028": 0.04, "ING-018": 0.012}),
    ("CHN-005", "Chicken Manchurian", "Indo-Chinese", "plate", 319, 0.9, "", False,
     {"ING-008": 0.18, "ING-024": 0.03, "ING-031": 0.025, "ING-028": 0.04, "ING-018": 0.012}),
    # Desserts
    ("DST-001", "Gulab Jamun (2 pcs)", "Desserts", "plate", 119, 1.6, "festive", True,
     {"ING-007": 0.06, "ING-032": 0.06, "ING-028": 0.02}),
    ("DST-002", "Gajar Ka Halwa", "Desserts", "bowl", 159, 0.9, "winter", True,
     {"ING-020": 0.2, "ING-005": 0.1, "ING-032": 0.04, "ING-006": 0.015, "ING-007": 0.02}),
    ("DST-003", "Kulfi Falooda", "Desserts", "glass", 179, 0.9, "summer", True,
     {"ING-005": 0.2, "ING-032": 0.04, "ING-038": 0.05}),
    ("DST-004", "Sizzling Brownie with Ice Cream", "Desserts", "plate", 249, 0.8, "date", True,
     {"ING-024": 0.04, "ING-032": 0.04, "ING-003": 0.02, "ING-038": 0.08}),
    ("DST-005", "Vanilla Ice Cream (2 scoops)", "Desserts", "bowl", 129, 0.8, "summer", True, {"ING-038": 0.12}),
    # Hot Beverages
    ("HBV-001", "Masala Chai", "Hot Beverages", "cup", 69, 1.8, "monsoon", True,
     {"ING-005": 0.1, "ING-034": 0.004, "ING-032": 0.012, "ING-017": 0.002}),
    ("HBV-002", "Filter Coffee", "Hot Beverages", "cup", 89, 1.2, "winter", True,
     {"ING-005": 0.12, "ING-035": 0.008, "ING-032": 0.012}),
    # Cold Beverages
    ("CBV-001", "Sweet Lassi", "Cold Beverages", "glass", 119, 1.4, "summer", True, {"ING-004": 0.25, "ING-032": 0.03}),
    ("CBV-002", "Fresh Lime Soda", "Cold Beverages", "glass", 99, 2.0, "summer", True, {"ING-021": 1, "ING-032": 0.02}),
    ("CBV-003", "Mango Lassi", "Cold Beverages", "glass", 149, 0.9, "mango", True,
     {"ING-004": 0.2, "ING-033": 0.1, "ING-032": 0.02}),
    ("CBV-004", "Soft Drink (300ml)", "Cold Beverages", "can", 70, 1.8, "summer", True, {"ING-036": 1}),
    ("CBV-005", "Mineral Water (1L)", "Cold Beverages", "bottle", 40, 2.2, "", True, {"ING-037": 1}),
    ("CBV-006", "Cold Coffee", "Cold Beverages", "glass", 169, 1.1, "summer", True,
     {"ING-005": 0.25, "ING-035": 0.008, "ING-032": 0.03, "ING-038": 0.04}),
]

# How a bill is built: each menu category is a course. Curries (Main Course) come with breads or a rice side.
COURSE_OF = {"Soups": "soup", "Starters": "starter", "Main Course": "main", "Rice & Biryani": "main",
             "Indo-Chinese": "main", "Breads": "bread", "Desserts": "dessert", "Hot Beverages": "drink",
             "Cold Beverages": "drink"}
RICE_SIDES = ("RIC-001", "RIC-002")  # served with curries; biryanis are a meal on their own

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
# companies that order on account (office lunches, team dinners, party orders)
BUSINESS_NAMES = [
    "Infosys Campus Events", "Lotus Corporate Park Office", "Brightstar Consulting", "Northwind Software",
    "Sunrise Event Planners", "Apex Realty", "Bluewave Media", "Greenleaf Pharma", "Orbit Fintech",
    "Harbour Logistics", "Vertex Architects", "Crimson Advertising",
]
