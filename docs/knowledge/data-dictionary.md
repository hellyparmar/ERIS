# Data dictionary (main tables)

## Organization and outlets
organization holds the company name, currency, time zone, GSTIN (marked as demo when synthetic) and home state. outlets holds each store's code, name, city, state and GST state code, opening date and active flag. ERIS supports up to seven outlets.

## Users and roles
users have a role: admin (everything, all outlets), manager (their assigned outlets, purchasing and imports), staff (billing and stock at their outlets) or viewer (read-only). Managers, staff and viewers can be assigned to several outlets.

## Products and categories
products have a SKU, name, category, unit, cost price, selling price, GST rate, HSN code, reorder level and preferred supplier. categories group products such as Beverages, Dairy & Eggs or Bakery.

## Sales and sale items
sales are bills: invoice number, outlet, customer, time, channel, payment method, subtotal, discount, tax, total, status (completed or void) and source (synthetic, manual or import). sale_items are the lines: product, quantity, unit price, regular list price when a promotion applied, discount, line total including tax, tax amount and cost amount.

## Inventory and purchasing
inventory holds the stock quantity and reorder level per outlet and product. stock_movements records every change with a reason (sale, purchase, transfer, adjustment, import). suppliers and purchase_orders track ordering and receiving.

## Customers
customers have a name, phone, city, type (retail or business), optional GSTIN and state code.

## Demand drivers and ground truth
promotions, price_history, weather_daily, stockout_events and anomaly_labels hold the drivers and labelled events of the synthetic dataset. dataset_info records how the dataset was generated.

## Forecasts, imports, invoices and audit
forecast_runs and forecast_results store every forecast and evaluation with its metrics. import_jobs stores each CSV import and its errors. invoices stores demo GST invoices. audit_log records who created, changed or deleted business records and when.
