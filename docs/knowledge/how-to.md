# How to do common tasks in ERIS

## Record a bill (manual billing)
Open Sales and choose New bill. Pick the restaurant and the order type (dine-in, takeaway or delivery) and, for dine-in, the number of guests; search and add dishes, optionally enter the guest's mobile number (new guests are created automatically) and a bill discount, then Save bill. Each dish's ingredients are checked and drawn from the kitchen's stock immediately - if an ingredient has run out, the dish cannot be billed. Staff can record bills for today and yesterday; managers and admins can backdate.

## Void a sale or correct a mistake
Open the bill on the Sales page and choose Void (managers and admins). Give a reason; the ingredients are put back into stock and the void is recorded in the audit log. A voided bill stays in history with status Void and is excluded from all analytics.

## Issue a demo GST invoice
Open a completed bill on the Sales page and choose Issue GST invoice (demo). The invoice opens on the Invoices page, where the PDF can be printed. A buyer GSTIN set on the customer decides whether CGST + SGST or IGST applies.

## Add or edit a dish or an ingredient
Open Menu (managers and admins). On the Dishes tab choose Add dish: enter the code, name, menu category, how it is served and the menu price including GST, then build the recipe - the ingredients one portion uses - and ERIS shows the food cost and food cost % as you go. On the Ingredients tab choose Add ingredient: code, name, store category, unit (kg, L or pcs), cost per unit, supplier and a default reorder level; a new ingredient starts at zero stock in every kitchen. Items with sales or purchase history are deactivated instead of deleted, and an ingredient used in an active dish's recipe cannot be deleted.

## Count stock, record wastage or move ingredients between kitchens
Open Kitchen stock. Use Adjust on a row to set the counted quantity (closing stock count), add stock or record wastage (spoiled, spilled or expired); use Transfer stock to send ingredients from one kitchen to another. Every change is written to the stock movement history with the user and reason. Stock counts for many ingredients can also be imported from a CSV file on the Data import page.

## Order from suppliers and receive deliveries
Kitchen stock → Reorder suggestions lists what to order from recent ingredient use; select lines and create purchase orders in one click (one order per outlet and supplier). Or create an order on Suppliers & orders → New purchase order. When goods arrive, open the order and choose Record delivery with the quantities that arrived; a short delivery keeps the order open as part-delivered until the rest arrives, or it can be closed. Open orders count as incoming stock in reorder and stock-out calculations.

## Add a user or change what they can see
Settings → Users & roles (admins). Choose the role - admin, manager, staff or viewer - and tick the outlets the person may see; managers, staff and viewers can have several outlets. Deactivating a user signs them out; changing a password or choosing Sign out everywhere ends all of a user's sessions.

## Add or change an outlet
Open Outlets (admins). Each outlet needs a unique code, name, city and GST state; ERIS supports up to seven outlets. An outlet with sales history is deactivated instead of deleted.

## Export reports
Open Reports & export, pick a report and a period, and download it as CSV or as a formatted Excel file. The Excel file has an "About this report" sheet with the period, outlets and data source. The sales, menu and customer lists also have their own Export buttons.

## Compare forecasting models
Open Model comparison to see the latest rolling-origin evaluation and every saved forecast run. Managers and admins can start a new evaluation with Run evaluation; it takes a few minutes and runs in the background.

## Start using your own data
Settings → System & data → Clear transactions removes sales, stock levels, purchase orders and customers but keeps outlets, the menu with its recipes, ingredients, suppliers and users. Then import your history on the Data import page or record sales manually. Regenerate demo replaces everything with a fresh synthetic dataset.
