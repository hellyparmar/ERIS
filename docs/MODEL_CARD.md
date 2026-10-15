# Model card: ERIS forecasting and anomaly detection

## Forecasting (model version 3.0)

| | |
|---|---|
| **Task** | Daily forecasts 7-30 days ahead (UI) of revenue (whole business, outlet, menu category) and portions (dish), with an 80% prediction interval. A dish forecast also shows how many portions the kitchens' ingredient stock allows. |
| **Users** | Owners and restaurant managers planning prep, staffing and ingredient purchasing. The output is advice, not an automatic order. |
| **Code** | `api/app/services/forecasting.py`, `api/app/services/features.py` |
| **Candidates** | Seasonal naive (baseline), Holt-Winters, XGBoost (recursive), Prophet (with holidays and regressors), ensemble of the best two |
| **Selection** | Two 28-day back-test folds, scored with WAPE. Prophet is the incumbent; a challenger must lower WAPE by more than 10% to replace it. |
| **Inputs** | Daily sales history (up to 730 days); calendar; Indian festival calendar; promotion depth; price index; temperature and rain (climatology for future days); share of dishes off the menu because an ingredient ran out (history only) |
| **Training data** | The synthetic Saffron Table restaurant dataset (see [DATASET.md](DATASET.md)) or the user's own data |
| **Persistence** | Every run is stored with its data range, features, parameters, candidate metrics, chosen model, version, timing and forecast (`forecast_runs`) |

### Evaluation

Rolling-origin evaluation on the default demo dataset (seed 42):

- 25 series: total, 5 outlets, 9 menu categories and the 10 most-ordered dishes.
- 3 origins, each followed by a 28-day test window.
- 375 model fits.
- Command: `python -m app.evaluation`. Full report: [FORECAST_EVALUATION.md](FORECAST_EVALUATION.md).

| Model | Mean WAPE | sMAPE | Bias |
|---|---:|---:|---:|
| Seasonal naive (baseline) | 15.9% | 16.3% | −1.0% |
| Holt-Winters | 14.7% | 15.0% | −1.3% |
| XGBoost | 15.2% | 15.4% | +1.8% |
| **Prophet** | **14.1%** | 14.5% | −2.4% |
| ERIS auto-selection (production) | 14.1% | 14.5% | −2.1% |

- Auto-selection has about **11% lower error than the baseline**. It beats the baseline in 81% of the
  series-and-origin pairs.
- The error is lowest for the whole-business series (8.5% WAPE) and highest for outlets (17.1%), because the
  newest outlet is still ramping up and one outlet is declining; menu categories average 12.3% and single dishes
  14.8%.
- The 80% band covered **84.8%** of held-out days (slightly conservative). It uses split-conformal quantile levels
  of the back-test errors.

### Known limitations

- **XGBoost is uneven** on this data: it is good on menu categories and dishes but its errors compound over a
  28-day recursive horizon on the outlet series (20.6% WAPE, worse than the baseline). It stays as a challenger
  because it is the most accurate model on 26 of 75 series-and-origin pairs.
- **Accuracy is measured on synthetic data.** It shows that the pipeline works and how the models compare
  against a known demand process. It is not a promise of accuracy on a real business.
- **No knowledge of unrecorded events,** such as a competitor opening or a road closure. Future ingredient
  outages are assumed to be zero, so a forecast describes *demand*, not orders lost to dishes being off the menu.
- **Low-volume dishes** (a few portions per day) have high percentage errors. Ingredient reordering therefore
  works from recent ingredient use plus safety stock based on its variability, not from dish point forecasts.
- **The band can be too narrow** around festivals that fall outside the back-test window.

### Ethical and practical notes

- Forecasts drive purchase suggestions that a person must approve. Nothing is ordered automatically.
- The UI and the assistant always show the model, its back-test error, the data range and the run id.

## Anomaly detection

| | |
|---|---|
| **Task** | Flag unusual outlet-days (revenue far from expected) and implausible bill lines (likely typing errors) |
| **Code** | `api/app/services/anomalies.py` |
| **Method** | Weekday-normalised revenue against a centred 15-day rolling median. The log ratio becomes a robust z-score (MAD). The threshold is \|z\| ≥ 3.5, or 6 on festival days. Zero-sales open days are always flagged. Heavy-rain dips are reported as explained by weather. A bill line is flagged when its quantity is more than 20× the typical quantity for that dish and customer type (and at least 30 portions). |
| **Training** | None. The method is unsupervised and has no fitted parameters to drift. |

### Evaluation against injected ground truth

The 26 anomalies the generator injected over the full history were used only for scoring. Detection was
scored from day 60 onwards, so every scored day has 60 days of context.

| Metric | Value |
|---|---:|
| Precision (flagged days that were injected anomalies) | 0.64 |
| Recall (injected anomalies found) | 0.69 |
| F1 | 0.67 |

| Kind | Found |
|---|---:|
| Bulk order | 4 / 6 |
| Closure | 3 / 3 |
| Entry error (day level) | 4 / 5 |
| POS outage | 6 / 7 |
| Local event | 1 / 5 |

- At bill level, all 5 injected entry errors are found by the suspicious-line check, with no false alarms. Company party orders are
  compared with typical company orders, so they are not mistaken for typing errors.
- Local events (a modest +40-100% bump) and smaller party orders are the hardest to separate from normal
  variation.
- Precision is lower than on a high-volume retail series: a restaurant has fewer, larger bills (party size and
  bill value vary a lot), so ordinary days occasionally land 50% off their usual level. The remaining false
  positives are such days, all with |z| between 3.5 and 4.5 and no festival or rain behind them. Raising the
  threshold to 4.5 would remove most of them at the cost of missing smaller outages.

## Driver analysis ("why did revenue change?")

- **Exact part.** The traffic (bills) and basket (average bill) effects add up exactly to the change. The
  change by outlet and by category also adds up.
- **Estimates.** The calendar, promotion uplift, stockout losses and unusual-day effects are estimates. The
  rainfall effect is a statistical association measured on the past year, **not a causal effect**, and the UI
  says so.
