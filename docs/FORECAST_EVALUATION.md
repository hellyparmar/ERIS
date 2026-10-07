# Forecast model evaluation

Generated with `python -m app.evaluation` on the demo dataset: 26 series (total, outlets, categories, top products), 3 forecast origins each, 28-day horizon - 390 model runs. Every model is trained only on data before each origin.

## Mean WAPE (%) by series type

| model                              |   category |   outlet |   product |   total |   all series |
|:-----------------------------------|-----------:|---------:|----------:|--------:|-------------:|
| Seasonal naive                     |      18.7  |    22.55 |     18.2  |   12.97 |        19.03 |
| Holt-Winters exponential smoothing |      19.09 |    21.44 |     17.51 |   12.25 |        18.67 |
| XGBoost                            |      19    |    24.44 |     17.96 |   10.61 |        19.32 |
| Prophet                            |      16.92 |    20.99 |     16.86 |    9.55 |        17.4  |
| ERIS auto-selection                |      17.01 |    20.98 |     17.14 |   11.61 |        17.62 |

- **ERIS auto-selection: 17.6% WAPE** vs 19.0% for the seasonal-naive baseline (7% lower error).
- Best single model overall: **Prophet** (17.4%).
- 80% prediction-interval coverage of ERIS auto on the held-out windows: **80.5%** (target 80%).
- Product-level series are noisier (small daily counts), so their errors are naturally higher than revenue series that aggregate many products.

## All metrics (mean over series and origins)

| model                              |   wape |   smape |     mae |    rmse |   bias_pct |   seconds |
|:-----------------------------------|-------:|--------:|--------:|--------:|-----------:|----------:|
| Seasonal naive                     |  19.03 |   19.21 | 3848.35 | 5201.33 |      -4.71 |      0    |
| Holt-Winters exponential smoothing |  18.67 |   18.62 | 3736.52 | 5053.97 |      -5.27 |      0.11 |
| XGBoost                            |  19.32 |   19.04 | 3784.93 | 5028.6  |      -1.49 |      0.25 |
| Prophet                            |  17.4  |   17.44 | 3331.69 | 4374.82 |      -2.07 |      0.24 |
| ERIS auto-selection                |  17.62 |   17.67 | 3486.32 | 4630.48 |      -2.77 |      1.28 |

sMAPE is symmetric MAPE; `seconds` is training + inference time per series and origin.

## How often each model was the most accurate

| model                              |   wins |
|:-----------------------------------|-------:|
| Prophet                            |     32 |
| Holt-Winters exponential smoothing |     19 |
| XGBoost                            |     18 |
| Seasonal naive                     |      9 |

## What auto-selection picked

| chosen                             |   times chosen |
|:-----------------------------------|---------------:|
| Prophet                            |             62 |
| Ensemble                           |              6 |
| XGBoost                            |              5 |
| Holt-Winters exponential smoothing |              3 |
| Seasonal naive                     |              2 |

![chart](images/eval_wape_by_model.png)

![chart](images/eval_holdout_total.png)

## Method

- **WAPE** = Σ|actual − forecast| ÷ Σ actual. Unlike MAPE it is stable when some days have tiny sales.
- **Rolling origin**: origins are spaced one horizon apart, ending at the last day of data, so each test window is unseen by the model.
- **Auto-selection** reproduces production exactly: it back-tests the candidates on two consecutive 28-day folds at the end of its own training data, keeps Prophet unless a challenger (including the ensemble of the two best models) cuts WAPE by more than 10%, and refits the choice on all training data.
- **Features**: XGBoost and Prophet use calendar and festival features plus promotions, price index, weather and stockouts; planned promotions and climatological weather are known for the test window, future stockouts are not (set to zero).
- **Honest reading**: on this synthetic dataset Prophet is the strongest model and the recursive XGBoost model is weaker than the seasonal-naive baseline on aggregate revenue, so auto-selection almost always keeps Prophet. XGBoost is kept as a challenger because it can win on individual series.
