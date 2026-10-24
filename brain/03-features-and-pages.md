# Features and pages

For each page: **purpose**, **what it does**, **why it exists**, **where the code is**, and **how it is verified**.
Page files are in `web/src/pages/`. Shared pieces are in `web/src/components/`.

Navigation (from `Layout.jsx`): Overview (Dashboard, AI Assistant) · Operate (Sales, Menu, Kitchen stock, Suppliers
and orders, Customers, Invoices) · Insights (Forecasts, Anomalies and drivers, Analytics, Reports and export) ·
Business (Outlets, Data import, Audit log) · Help and Settings.

---

## Login — `Login.jsx`
- **Does:** Email and password sign-in, with a "Demo account" dropdown that fills the password. The list of demo accounts comes from the API (be50e29), not from the web code.
- **Why:** A visitor can try each role in one click, and the page states the data is synthetic.
- **Verify:** E2E sign-in tests; API auth tests.

## Dashboard — `Dashboard.jsx`
- **Does:** Five KPIs with change pills (revenue, gross profit, dine-in guests, average bill, food cost), revenue against the previous period, a 14-day forecast card (dark), outlet ranking, top dishes, and an alerts card ("Needs attention").
- **Why:** The first screen a manager sees should answer "how are we doing, and what needs attention" without drill-down.
- **Design note:** The dashboard answers without its forecast if the forecast is busy (D7), so it never hangs.
- **Verify:** E2E `dashboard` and roles specs.

## Sales — `Sales.jsx`
- **Does:** Bill history with search, date range, payment, channel and status filters; a bill drawer; a "New bill" modal (outlet, channel, guests for dine-in, payment, optional customer); voids that restore stock (D13); demo GST invoice for a bill; CSV export; Import CSV button.
- **Why:** Billing is the core operation. Stock must follow each sale, so billing checks ingredients before it saves.
- **Performance:** Filtered lists are cached; the default list is prepared at build time (`06`).
- **Verify:** API sales tests; E2E core spec; screenshot `sales.png`.

## Menu — `Products.jsx`
- **Does:** Two tabs. **Dishes**: price, category, code, a recipe editor showing food cost live, portions the kitchen can make now, and sales charts for each dish. **Ingredients**: unit, cost, supplier, stock.
- **Why:** The menu and its recipes are the source of food cost and stock draw-down. They must be edited in one place.
- **Note:** Originally the product list (for a supermarket); rewritten for the restaurant (90c91d2). The file name was kept.
- **Verify:** API catalog tests; E2E core spec; screenshot `menu.png`.

## Kitchen stock — `Inventory.jsx`
- **Does:** Three tabs. **Ingredients**: stock per outlet, uses per day, days of cover, counts, wastage, transfers between kitchens. **Reorder suggestions**: what to order now, based on recent use, supplier lead time and orders on the way, with "Create N PO lines". **Stock movements**: the full history.
- **Why:** Restaurants run out of ingredients, not dishes. Suggestions use real use per day.
- **Performance:** The default view loads in about 0.1–0.4 s on 0.1 CPU (`06`).
- **Verify:** API inventory tests; E2E `reorder` shot; screenshot `reorder.png`.

## Suppliers and orders — `Suppliers.jsx`
- **Does:** Suppliers, purchase orders, partial receiving, and status.
- **Why:** Closes the loop from reorder suggestion to received stock.
- **Verify:** API tests for partial receiving.

## Customers — `Customers.jsx`
- **Does:** Guests and company accounts with GSTIN, RFM segment (recency, frequency, monetary), history, repeat rate, top customers and an at-risk list.
- **Why:** Repeat business and churn are the customer questions a restaurant chain asks.
- **Verify:** API customer tests.

## Invoices (demo GST) — `Invoices.jsx`
- **Does:** A list of demo GST invoices, each issued from a bill. Shows seller GSTIN (synthetic), place of supply, CGST and SGST or IGST, tax summary, and a PDF action.
- **Why:** Shows the invoice flow end to end. Watermarked, and the GSTINs are synthetic, so it is not usable for tax filing.
- **Verify:** API invoice tests; screenshot `invoice.png`.

## Forecasts — `Forecasts.jsx`
- **Does:** Choose a scope (total sales, outlet, menu category, dish), a category or item, a horizon (7, 14 or 30 days), and a model (auto or a named model). Shows next-7 and next-30 totals, peak day, back-test error, a chart with an 80% band and optional back-test overlay, "What this means" notes, upcoming festivals, a model leaderboard, and a CSV download.
- **Why:** Forecasts are useful only if the user can see which model was used and how accurate it was on past data (D6).
- **Verify:** API forecasting tests; E2E `forecasts` shot.

## Anomalies and drivers — `Insights.jsx`
- **Does:** "Why did revenue change?" for 7 days, 14 days, 30 days or month-to-date, against the same weekdays before. Shows revenue, bills, average bill and change; plain-language explanations; an estimated contribution per driver (bills, average bill, calendar, promotions, stock-outs, rain, unusual days); changes by outlet and by category; and a list of unusual outlet-days and suspicious bill lines.
- **Why:** Managers ask "why" more than "what". The bills × average-bill split is exact, while the other drivers are estimates and labelled as such.
- **Verify:** API insight tests; E2E `drivers` and `anomalies` shots.

## Analytics — `Analytics.jsx`
- **Does:** Four tabs: sales patterns, dishes, outlets, customers. Revenue and gross-profit trend (auto, day, week or month), a weekday-by-hour heatmap titled "When do guests come in?", payment-method mix, KPIs (revenue, bills, average bill, gross margin).
- **Why:** Patterns for planning staffing and promotions.
- **Verify:** E2E analytics shot; `analytics.png`.

## Model comparison — `ModelComparison.jsx`
- **Does:** A rolling-origin evaluation. Scope: whole business, outlets, categories and top dishes. Shows the most accurate single model, the auto-selection's error, the 80% band coverage, WAPE by model, sMAPE, bias, fit time, and how often each model was best.
- **Why:** The honest answer to "is the forecast any good?" for a reviewer.
- **Verify:** Evaluation report; `model-comparison.png`.

## Reports and export — `Reports.jsx`
- **Does:** Nine reports with preview, CSV, and formatted XLSX with an "About this report" sheet.
- **Why:** The owner needs to take numbers out of the app.
- **Verify:** API report tests; `reports.png`.

## Outlets — `Outlets.jsx`
- **Does:** Outlet CRUD, GST state, and a "deactivate instead of delete" rule once history exists. Up to seven outlets (the API rejects an eighth). Outlet buttons switch an eight-KPI detail with weekly revenue and average-bill charts.
- **Why:** Outlets are the main unit of comparison. Deleting one with history would break reports, so it is deactivated.
- **Verify:** API outlet-cap test; E2E.

## Data import — `DataImport.jsx`
- **Does:** Choose a kind: sales / bills, menu and ingredients, customers, suppliers, or ingredient stock counts (default: sales). For each kind it offers an empty template, a valid sample, a sample with mistakes, and a link to enter records by hand. Upload a CSV, map columns with suggested mappings (POS aliases such as "Bill No", "Store", "Item Code"), dry-run check, a "Rows to fix" list, error report, atomic commit, and history.
- **Why:** Real POS exports never match the app's column names, and a bad file must never half-import.
- **Verify:** API import tests; E2E `import with column mapping`; `import.png`.

## Audit log — `AuditLog.jsx`
- **Does:** Every change to business records, and one summary per import or bulk reset.
- **Why:** Accountability. Automatic, so new record types are covered without extra code.
- **Verify:** API test `test_audit_log_records_changes`.

## Settings — `Settings.jsx`
- **Does:** Organisation (GSTIN, state, time zone, currency), users and roles, profile, system and dataset information, demo reset, clear transactions.
- **Verify:** API settings tests.

## AI Assistant — `Assistant.jsx`
- **Does:** A chat with a conversation list grouped by day, New chat, copy and regenerate, suggested questions, a composer, voice input, and a "Source and method" panel under each answer. Table answers open as a spreadsheet (copy or CSV). Requests to change data are refused.
- **Why:** A natural-language way in, with every answer traceable (D8).
- **Verify:** Assistant evaluation (31/31 intents, 21/21 numbers); E2E; `assistant.png`. See `07`.

## Help and support — `Help.jsx`
- **Does:** Topics answered by the assistant from the docs in `docs/knowledge/`.
- **Why:** Users can ask "how do I…" and get the project's own answer.
- **Verify:** Assistant documentation-retrieval tests.

## Shared components
- `components/Layout.jsx`: framed workspace, collapsible sidebar, breadcrumbs, outlet picker, notifications, page-change scroll reset (4b2ad6f).
- `components/charts.jsx`: the chart set. Axis labels use compact money. Trailing zeros are trimmed (₹26 L, not ₹26.00 L) so labels do not wrap (a595a26). Colours from `useChartColors`, which reads CSS variables so both themes work.
- `components/pickers.jsx`: searchable product and customer pickers. The dish search keeps its dropdown open on quick refocus (fixed in 90c91d2).
- `components/ui.jsx`: cards, KPI tiles, buttons, tables, drawers, modals, toasts.
- `lib/format.js`: money, numbers, dates, and `qty()` for measured quantities (0.012 kg, 2.5 L, 40 pcs).
- `lib/api.js`: API client with retry on 503 (`Retry-After`) and token refresh.
- `lib/app.jsx`: session, outlet selection, roles.
