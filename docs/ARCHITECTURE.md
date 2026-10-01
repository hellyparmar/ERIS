# ERIS architecture & methodology

## System overview

```
 Browser (React SPA)  ──/api──▶  FastAPI  ──▶  SQLAlchemy  ──▶  SQLite / PostgreSQL
   pages, charts                 routers          models
                                    │
                                    ├─ services/analytics     KPIs, trends, ABC, RFM, basket analysis
                                    ├─ services/forecasting   4 models + ensemble, back-testing, stock planning
                                    ├─ services/inventory     every stock change → movement log
                                    ├─ services/sales         billing logic (tax, discounts, stock, customers)
                                    ├─ services/importer      CSV validation & import
                                    ├─ services/alerts        live business alerts
                                    └─ services/assistant     NLU → analytics tools → answer (+ optional Ollama LLM)
```

The API is stateless (JWT bearer tokens). In production the same process serves the built web app (`web/dist`),
so ERIS deploys as a single container. Heavy analyses (forecasts, RFM, basket analysis) are cached in memory per
*data version* (sales count / last id / voids), so caches invalidate automatically when data changes.

## Data model

| Table | Purpose |
|---|---|
| `organization` | the business: name, currency, tax id, timezone |
| `outlets` | stores (code, city, manager, opened date, active flag) |
| `users` | admin / manager / staff; managers & staff belong to one outlet |
| `categories`, `products` | catalogue: SKU, cost, tax-inclusive selling price, GST rate, supplier |
| `suppliers` | contact, lead time (used for reorder planning), payment terms |
| `inventory` | stock per outlet × product with reorder level |
| `stock_movements` | audit log of every stock change (sale, void, purchase, adjustment, damage, transfer, import) |
| `customers` | loyalty / business customers, unique phone number |
| `sales`, `sale_items` | bills and lines; items keep a cost snapshot for margin analysis and denormalised outlet/date for fast analytics |
| `purchase_orders`, `purchase_order_items` | ordered → received (partial quantities) / cancelled |
| `chat_messages` | assistant history and context for follow-up questions |

**Money:** selling prices include GST (MRP style). Tax per line = line total × rate / (100 + rate).
Gross profit = revenue − tax − cost of goods.

**Access control:** every endpoint resolves the outlets a user may see (`scoped_outlet_ids`); managers and staff are
always restricted to their outlet, admins can filter to any outlet.

## Business rules

- A manual sale is rejected if any item lacks stock; stock is reduced and a movement is written per line.
- Voiding restores stock only if that sale actually reduced it (demo history and historic imports may not have).
- Credit sales require a customer. Staff can only record today's or yesterday's sales.
- Deleting an outlet / product / supplier with history deactivates it instead, so history stays intact.
- CSV imports run as a dry run first; a real import is all-or-nothing and duplicate invoice numbers are rejected.

## Forecasting

Series: daily revenue (total, outlet, category) or daily units (product), up to 2 years of history.

| Model | Idea |
|---|---|
| Seasonal naive | mean of the same weekday over the last 4 weeks — the baseline to beat |
| Holt-Winters | additive damped trend + weekly (multiplicative) seasonality, statsmodels |
| Gradient boosting | recursive `HistGradientBoostingRegressor` on scale-free lags (1, 7, 14, 28, 7-day mean ÷ 28-day level) plus weekday, day-of-year (sin/cos), month and festival-proximity features |
| Prophet | weekly + yearly seasonality and the festival calendar as holidays; with < 2 years of history a smoother yearly term and stiffer trend prevent over-fitting a single season |
| Ensemble | mean of the two best non-baseline models |

**Selection:** every candidate is scored on two consecutive 28-day folds at the end of the history (each fold
trained only on data before it; WAPE, MAPE, MAE, RMSE, bias). The ensemble of the two best is scored too.
Prophet is the incumbent and is replaced only when a challenger's WAPE is more than 10% lower; the winner is refit
on the full series. **Intervals:** the 10th/90th percentiles of the winner's relative back-test errors give an
empirical 80% range — honest about how accurate the model really was.

**Why this rule:** a rolling-origin study (`python -m app.evaluation`, results in
[FORECAST_EVALUATION.md](FORECAST_EVALUATION.md)) compared selection strategies on 26 series × 3 origins:

| Strategy | Mean WAPE |
|---|---|
| Seasonal naive baseline | 18.96% |
| Pick best on one 28-day window | 15.97% |
| Pick best on two 28-day folds | 15.73% |
| Two folds + Prophet incumbent, 10% switch margin (used) | 15.27% |
| Always Prophet | 15.25% |

Picking the winner of a single short window chases noise; the incumbent rule keeps Prophet's strong average while
still switching when another model is clearly better for a particular series (and when Prophet fails or history
is too short).

**Stock plan (product forecasts):** days of cover = stock ÷ forecast daily demand; projected stock-out = first day
cumulative forecast exceeds stock; order quantity = forecast over (lead time + 7 days) + safety stock − stock,
with safety stock = 1.65 · σ(daily demand) · √lead time (≈95% service level).

**Reorder suggestions (all items at once):** a fast version of the same logic using a trend-adjusted 28-day demand
rate (recent 14 vs prior 14 days, clipped to ±40%) and counting open purchase orders as incoming stock.

## AI assistant

1. **Understand** (`nlu.py`) — rule-based, deterministic and offline: intent scoring with weighted patterns,
   time periods (today, last week, March, last 90 days, this quarter, …), forecast horizon, top-N, and entity
   matching for outlets (name/code/city), categories (with synonyms) and products (token matching weighted by rarity).
   Short follow-ups (*"what about Pune?"*) reuse the previous question's intent and filters.
2. **Optional LLM** (`llm.py`) — if Ollama is reachable and the rules are unsure, a local model converts the question
   to the same structured JSON; free-form questions get an answer grounded in a fact sheet of live numbers.
3. **Answer** (`tools.py`) — 19 analytics tools (sales summary, period comparison, trends, top/slow products, outlet
   ranking, category mix, forecast, stock, reorder, customers/RFM, peak hours, payments, profitability, purchase orders,
   basket analysis, data-driven advice, help) return a narrative plus KPI tiles, charts and tables. Numbers always come
   from the database, never from the language model.

## Demo data generator

`app/seed/generator.py` simulates bills basket by basket:

```
bills/day  = 58 × outlet size × weekday factor × growth trend × season × festival × monsoon × new-outlet ramp × noise
basket mix = product popularity × product seasonality (summer, winter, monsoon, mango season, Diwali, Christmas, …)
             + companion items (bread → butter, chips → cola, tea → milk & sugar, …)
```

Customers have a home outlet, loyalty weight, join date and (for 22%) a churn date, which makes RFM segments
meaningful. Prices carry ~5.5% annual inflation; UPI share rises over time. Inventory, reorder levels and 16 weeks
of purchase orders are derived from the simulated demand. If an untouched demo database is opened later, dates are
shifted forward in whole weeks so the demo always looks current (`app/seed/refresh.py`); user-entered data is never
shifted.
