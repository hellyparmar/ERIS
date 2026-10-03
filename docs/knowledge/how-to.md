# How to do common tasks in ERIS

## Record a sale (manual billing)
Open Sales and choose New sale. Pick the outlet, search and add products, optionally enter the customer's mobile number (new customers are created automatically) and a bill discount, then Save bill. Stock is checked and reduced immediately. Staff can record sales for today and yesterday; managers and admins can backdate.

## Void a sale or correct a mistake
Open the bill on the Sales page and choose Void (managers and admins). Give a reason; the stock is restored and the void is recorded in the audit log. A voided bill stays in history with status Void and is excluded from all analytics.

## Issue a demo GST invoice
Open a completed bill on the Sales page and choose Issue GST invoice (demo). The invoice opens on the Invoices page, where the PDF can be printed. A buyer GSTIN set on the customer decides whether CGST + SGST or IGST applies.

## Add or edit a product
Open Products and choose Add product (managers and admins). Enter the SKU, name, category, unit, cost price, selling price including GST, GST rate, HSN code, reorder level and preferred supplier. The selling price cannot be below the cost price. A new product starts at zero stock in every outlet. Products with sales history are deactivated instead of deleted.

## Adjust stock or move it between outlets
Open Inventory. Use Adjust on a row to set a counted quantity, add stock or remove damaged stock; use Transfer stock to move goods between two outlets. Every change is written to the stock movement history with the user and reason. Stock counts for many items can also be imported from a CSV file on the Data import page.

## Order from suppliers and receive deliveries
Inventory → Reorder lists demand-based suggestions; select lines and create purchase orders in one click (one order per outlet and supplier). Or create an order on Suppliers & orders → New purchase order. When goods arrive, open the order and choose Record delivery with the quantities that arrived; a short delivery keeps the order open as part-delivered until the rest arrives, or it can be closed. Open orders count as incoming stock in reorder and stock-out calculations.

## Add a user or change what they can see
Settings → Users & roles (admins). Choose the role - admin, manager, staff or viewer - and tick the outlets the person may see; managers, staff and viewers can have several outlets. Deactivating a user signs them out; changing a password or choosing Sign out everywhere ends all of a user's sessions.

## Add or change an outlet
Open Outlets (admins). Each outlet needs a unique code, name, city and GST state; ERIS supports up to seven outlets. An outlet with sales history is deactivated instead of deleted.

## Export reports
Open Reports & export, pick a report and a period, and download it as CSV or as a formatted Excel file. The Excel file has an "About this report" sheet with the period, outlets and data source. Sales, products and customers lists also have their own Export buttons.

## Compare forecasting models
Open Model comparison to see the latest rolling-origin evaluation and every saved forecast run. Managers and admins can start a new evaluation with Run evaluation; it takes a few minutes and runs in the background.

## Start using your own data
Settings → System & data → Clear transactions removes sales, stock levels, purchase orders and customers but keeps outlets, products, suppliers and users. Then import your history on the Data import page or record sales manually. Regenerate demo replaces everything with a fresh synthetic dataset.
