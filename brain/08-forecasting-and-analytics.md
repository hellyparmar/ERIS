# Forecasting, anomalies and drivers

Code: `services/forecasting.py`, `services/features.py`, `services/holidays.py`, `evaluation.py`,
`services/anomalies.py`, `services/drivers.py`, `services/alerts.py`.
Docs: `docs/FORECAST_EVALUATION.md`, `docs/MODEL_CARD.md`, `docs/knowledge/forecasting.md`,
`docs/knowledge/anomalies-and-drivers.md`.

## Forecasting

### Models (D6)
| Model | What it uses | Why it is there |
|---|---|---|
| Seasonal naive | The same day last week | A baseline every other model must beat |
| Holt-Winters exponential smoothing | Level, trend and weekly season | Strong on stable series, cheap |
| XGBoost | Lags, calendar, promotions, weather | Uses exogenous features; handles interactions |
| Prophet | Seasonality, the Indian festival calendar, regressors | Explicit holidays and events |
| Ensemble | Average of the good models | Hedge against any one model failing |
| **Auto** | Best model on back-test, per series | What users get by default |

### Selection
Each series is back-tested on **two 28-day folds**. The model with the lowest error on those folds is used for the
forecast. The run is saved with its data range, features, parameters and metrics, so it can be reproduced.

### Bands
An 80% band is produced for each forecast. The band is **calibrated**: the share of actuals that fall inside it should be
close to 80%. Commit 63d38ea, "calibrated forecast band", changed the band width to meet this.

### Results
From the rolling-origin study (25 series across whole business, outlets, menu categories and dishes):
- Auto selection: **14.1% WAPE**.
- Seasonal naive: **15.9% WAPE**.
- Improvement: about **11%** lower error.
- Band coverage: **84.8%** (target ≈ 80%).

Metric note: **WAPE** is weighted absolute percentage error, the total absolute error divided by total actual. It is
robust to small values, which matter for dishes with few sales.

### Limits, stated plainly
- Two years of history means yearly seasonality is weakly learned. Festivals are modelled explicitly to compensate.
- Forecasts assume the planned promotions and climatological weather. Surprise promotions or weather are not forecast.
- New dishes and new outlets have no history, so their forecasts are weak until data accumulates.

## Evaluation scope vs README
- The README text quotes the **25-series** study.
- The Model comparison screenshot shows a **20-series** scope, because it runs the in-app evaluation (`store_evaluation`), which samples fewer series.
- Both are real. They measure different subsets. This is recorded as an open item in `11`.

## Anomaly detection

### Method (as in `services/anomalies.py`)
1. Daily revenue per outlet is divided by the outlet's **weekday profile** (median revenue for each weekday, over the overall median). This removes the weekly pattern, so a quiet Monday is not an anomaly.
2. The de-seasonalised series is compared with a **centred 15-day rolling median**, the "expected level".
3. The log ratio of actual to expected is turned into a **robust z-score**, using the **median absolute deviation (MAD)**, scaled by 1.4826 so it matches a standard deviation for normal data. A median-based scale is used because the anomalies themselves would inflate a mean and standard deviation.

Transaction-level check: a bill line whose quantity is more than **20 times** the product's median line quantity is flagged as a suspicious bill. This is what catches the injected typing errors.

No model is trained, which is why the method is described as robust and explainable.

### Why these rules (D-level detail)
- **Outages only for ingredients used in at most eight dishes.** Outages of common ingredients (oil, onion, salt) affected most dishes at once and made hundreds of outlet-days look unusual. Limiting outages to less-common ingredients fixed it.
- **Company orders are grouped.** A bulk business order was split across many bills, and each fragment looked suspicious. Grouping by order fixed it.

### Results (against the 26 labelled anomalies)
- **Outlet-days: precision 0.64, recall 0.69.**
- **Bill lines: all 5 injected typing errors caught, with no false alarms.**

Precision and recall are reported honestly. A precision of 0.64 means about a third of the flagged days are not injected anomalies. In real use they could still be worth a look, but the app does not claim otherwise.

## Driver analysis ("why did revenue change?")

### Method
- **Exact decomposition:** revenue = bills × average bill. The change splits exactly into a bills effect and an average-bill effect. No estimate involved.
- **Attribution by outlet and by category.** Exact.
- **Estimated drivers:** calendar, promotions, stock-outs, rain, unusual days. These are *estimates*.

### Labelling
- Rainfall is labelled as **association**, not cause. Rain and order volume move together, but rain is not proven to cause the change.
- Each estimate says it is an estimate.

### Why this split
A manager needs to know the exact part first (bills or average bill), then the likely reasons. Mixing exact and estimated figures without labels would overstate what the app knows.

## Alerts
`services/alerts.py` builds the list shown by the bell and the dashboard: ingredients out or low, overdue purchase orders, unusual outlet-days, suspicious bills, upcoming festivals. Each alert links to its page.
