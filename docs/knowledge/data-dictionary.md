# Data dictionary (main tables)

## Organization and outlets
organization holds the company name, currency, time zone, GSTIN (marked as demo when synthetic) and home state. outlets holds each restaurant's code, name, city, state and GST state code, opening date and active flag. ERIS supports up to seven outlets.

## Users and roles
users have a role: admin (everything, all outlets), manager (their assigned outlets, purchasing and imports), staff (billing and stock at their outlets) or viewer (read-only). Managers, staff and viewers can be assigned to several outlets.

## Menu, ingredients and recipes
products holds two kinds of item. Menu items (kind "menu") are the dishes and drinks that are sold: code, name, menu category, serving unit, menu price including GST, GST rate (5% for restaurant service) and SAC code 996331; their cost price is the recipe's food cost. Ingredients (kind "ingredient") are what the kitchens stock: code, name, store category (Dairy, Meat & Seafood, Vegetables, Dry Store, Beverage Stock, Frozen), unit (kg, L or pcs), cost per unit, reorder level and preferred supplier. recipes lists, for each dish, how much of each ingredient one portion uses.

## Sales and sale items
sales are bills: invoice number, outlet, customer, time, channel (dine_in, takeaway or delivery), covers (guests at the table, for dine-in), payment method, subtotal, discount, tax, total, status (completed or void) and source (synthetic, manual or import). sale_items are the lines: dish, quantity, unit price, regular price when a promotion applied, discount, line total including tax, tax amount and food cost.

## Kitchen stock and purchasing
inventory holds the stock and reorder level per outlet and ingredient. Every bill draws its dishes' ingredients down by the recipe quantities. stock_movements records every change with a reason (sale, sale void, purchase, transfer, adjustment, wastage, import). suppliers and purchase_orders track ordering and receiving.

## Customers
customers (guests) have a name, phone, city, type (retail or business - companies ordering on account), optional GSTIN and state code.

## Demand drivers and ground truth
promotions, price_history (menu prices and ingredient costs), weather_daily, stockout_events (dishes off the menu because an ingredient ran out) and anomaly_labels hold the drivers and labelled events of the synthetic dataset. dataset_info records how the dataset was generated.

## Forecasts, imports, invoices and audit
forecast_runs and forecast_results store every forecast and evaluation with its metrics. import_jobs stores each CSV import and its errors. invoices stores demo GST invoices. audit_log records who created, changed or deleted business records and when.
