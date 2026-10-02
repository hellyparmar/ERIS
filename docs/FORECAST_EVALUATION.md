# Forecast model evaluation

Generated with `python -m app.evaluation` on the demo dataset: 25 series (total, outlets, categories, top products), 3 forecast origins each, 28-day horizon - 375 model runs. Every model is trained only on data before each origin.

## Mean WAPE (%) by series type

| model                              |   category |   outlet |   product |   total |   all series |
|:-----------------------------------|-----------:|---------:|----------:|--------:|-------------:|
| Seasonal naive                     |      20.97 |    23.08 |     18.82 |   12.15 |        20.18 |
| Holt-Winters exponential smoothing |      21.6  |    21.64 |     17.43 |   12.39 |        19.57 |
| XGBoost                            |      23.09 |    29.02 |     18.29 |   14.83 |        22.03 |
| Prophet                            |      17.41 |    20.47 |     16.14 |    8.6  |        17.16 |
| ERIS auto-selection                |      17.48 |    20.47 |     16.37 |    8.6  |        17.28 |

- **ERIS auto-selection: 17.3% WAPE** vs 20.2% for the seasonal-naive baseline (14% lower error).
- Best single model overall: **Prophet** (17.2%).
- 80% prediction-interval coverage of ERIS auto on the held-out windows: **80.0%** (target 80%).
- Product-level series are noisier (small daily counts), so their errors are naturally higher than revenue series that aggregate many products.

## All metrics (mean over series and origins)

| model                              |   wape |   smape |     mae |    rmse |   bias_pct |   seconds |
|:-----------------------------------|-------:|--------:|--------:|--------:|-----------:|----------:|
| Seasonal naive                     |  20.18 |   19.86 | 3655.91 | 4946.81 |      -2.7  |      0    |
| Holt-Winters exponential smoothing |  19.57 |   19.56 | 3746.33 | 4855.68 |      -3.06 |      0.12 |
| XGBoost                            |  22.03 |   21.07 | 4448.83 | 5732.4  |       3.18 |      0.25 |
| Prophet                            |  17.16 |   17.41 | 3032.68 | 4024.69 |      -1.82 |      0.19 |
| ERIS auto-selection                |  17.28 |   17.53 | 3043.93 | 4042.56 |      -1.33 |      1.25 |

sMAPE is symmetric MAPE; `seconds` is training + inference time per series and origin.

## How often each model was the most accurate

| model                              |   wins |
|:-----------------------------------|-------:|
| Prophet                            |     43 |
| Holt-Winters exponential smoothing |     14 |
| XGBoost                            |     11 |
| Seasonal naive                     |      7 |

## What auto-selection picked

| chosen                             |   times chosen |
|:-----------------------------------|---------------:|
| Prophet                            |             65 |
| Ensemble                           |              6 |
| Seasonal naive                     |              2 |
| XGBoost                            |              1 |
| Holt-Winters exponential smoothing |              1 |

![chart](images/eval_wape_by_model.png)

![chart](images/eval_holdout_total.png)

## Method

- **WAPE** = Σ|actual − forecast| ÷ Σ actual. Unlike MAPE it is stable when some days have tiny sales.
- **Rolling origin**: origins are spaced one horizon apart, ending at the last day of data, so each test window is unseen by the model.
- **Auto-selection** reproduces production exactly: it back-tests the candidates on two consecutive 28-day folds at the end of its own training data, keeps Prophet unless a challenger (including the ensemble of the two best models) cuts WAPE by more than 10%, and refits the choice on all training data.
- **Features**: XGBoost and Prophet use calendar and festival features plus promotions, price index, weather and stockouts; planned promotions and climatological weather are known for the test window, future stockouts are not (set to zero).
- **Honest reading**: on this synthetic dataset Prophet is the strongest model and the recursive XGBoost model is weaker than the seasonal-naive baseline on aggregate revenue, so auto-selection almost always keeps Prophet. XGBoost is kept as a challenger because it can win on individual series.
