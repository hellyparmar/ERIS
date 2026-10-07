# Model card: ERIS forecasting and anomaly detection

## Forecasting (model version 3.0)

| | |
|---|---|
| **Task** | Daily forecasts 7-30 days ahead (UI) of revenue (whole business, outlet, category) and units (product), with an 80% prediction interval |
| **Users** | Owners and outlet managers planning stock, staffing and purchasing. The output is advice, not an automatic order. |
| **Code** | `api/app/services/forecasting.py`, `api/app/services/features.py` |
| **Candidates** | Seasonal naive (baseline), Holt-Winters, XGBoost (recursive), Prophet (with holidays and regressors), ensemble of the best two |
| **Selection** | Two 28-day back-test folds, scored with WAPE. Prophet is the incumbent; a challenger must lower WAPE by more than 10% to replace it. |
| **Inputs** | Daily sales history (up to 730 days); calendar; Indian festival calendar; promotion depth; price index; temperature and rain (climatology for future days); stockout share (history only) |
| **Training data** | The synthetic Urban Harvest Supermarkets dataset (see [DATASET.md](DATASET.md)) or the user's own data |
| **Persistence** | Every run is stored with its data range, features, parameters, candidate metrics, chosen model, version, timing and forecast (`forecast_runs`) |

### Evaluation

Rolling-origin evaluation on the default demo dataset (seed 42):

- 26 series: total, 5 outlets, 10 categories and the top 10 products.
- 3 origins, each followed by a 28-day test window.
- 390 model fits.
- Command: `python -m app.evaluation`. Full report: [FORECAST_EVALUATION.md](FORECAST_EVALUATION.md).

| Model | Mean WAPE | sMAPE | Bias |
|---|---:|---:|---:|
| Seasonal naive (baseline) | 19.0% | 19.2% | −4.7% |
| Holt-Winters | 18.7% | 18.6% | −5.3% |
| XGBoost | 19.3% | 19.0% | −1.5% |
| **Prophet** | **17.4%** | 17.4% | −2.1% |
| ERIS auto-selection (production) | 17.6% | 17.7% | −2.8% |

- Auto-selection has about **7% lower error than the baseline**. It beats the baseline in 76% of the
  series-and-origin pairs.
- The error is lowest for the whole-business series (11.6% WAPE) and highest for outlets (21.0%), because the
  newest outlet is still ramping up and one outlet is declining.
- The 80% band covered **80.5%** of held-out days. It uses split-conformal quantile levels of the back-test
  errors; plain 10th/90th percentiles covered only 75.5%.

### Known limitations

- **XGBoost underperforms** on this data: its errors compound over a 28-day recursive horizon, and two years
  of history is short for a tree model. It stays as a challenger because it wins on some individual series
  (17 of 78 series-and-origin pairs).
- **Accuracy is measured on synthetic data.** It shows that the pipeline works and how the models compare
  against a known demand process. It is not a promise of accuracy on a real business.
- **No knowledge of unrecorded events,** such as a competitor opening or a road closure. Future stockouts are
  assumed to be zero, so a forecast describes *demand*, not sales lost to empty shelves.
- **Low-volume products** (a few units per day) have high percentage errors. Reorder planning therefore adds
  safety stock based on demand variability instead of trusting the point forecast.
- **The band can be too narrow** around festivals that fall outside the back-test window.

### Ethical and practical notes

- Forecasts drive purchase suggestions that a person must approve. Nothing is ordered automatically.
- The UI and the assistant always show the model, its back-test error, the data range and the run id.

## Anomaly detection

| | |
|---|---|
| **Task** | Flag unusual outlet-days (revenue far from expected) and implausible bill lines (likely typing errors) |
| **Code** | `api/app/services/anomalies.py` |
| **Method** | Weekday-normalised revenue against a centred 15-day rolling median. The log ratio becomes a robust z-score (MAD). The threshold is \|z\| ≥ 3.5, or 6 on festival days. Zero-sales open days are always flagged. Heavy-rain dips are reported as explained by weather. A bill line is flagged when its quantity is more than 20× the typical quantity for that product and customer type (and at least 30 units). |
| **Training** | None. The method is unsupervised and has no fitted parameters to drift. |

### Evaluation against injected ground truth

The 26 anomalies the generator injected over the full history were used only for scoring. Detection was
scored from day 60 onwards, so every scored day has 60 days of context.

| Metric | Value |
|---|---:|
| Precision (flagged days that were injected anomalies) | 0.94 |
| Recall (injected anomalies found) | 0.65 |
| F1 | 0.77 |

| Kind | Found |
|---|---:|
| Bulk order | 2 / 6 |
| Closure | 3 / 3 |
| Entry error (day level) | 5 / 5 |
| POS outage | 6 / 7 |
| Local event | 1 / 5 |

- At bill level, all 5 injected entry errors are found by the suspicious-line check, with no false alarms on
  business bulk purchases.
- Local events (a modest +30-60% bump) and smaller bulk orders are the hardest to separate from normal
  variation.
- The remaining false positives are genuine sharp dips in the synthetic data, caused by heavy noise days or
  stockouts. Lowering the threshold would raise recall at the cost of precision.

## Driver analysis ("why did revenue change?")

- **Exact part.** The traffic (bills) and basket (average bill) effects add up exactly to the change. The
  change by outlet and by category also adds up.
- **Estimates.** The calendar, promotion uplift, stockout losses and unusual-day effects are estimates. The
  rainfall effect is a statistical association measured on the past year, **not a causal effect**, and the UI
  says so.
