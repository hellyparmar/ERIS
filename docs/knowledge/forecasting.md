# How ERIS forecasts sales and demand

## What can be forecast
ERIS forecasts daily revenue for the whole business, for each outlet and for each category, and daily units for each product. Every forecast can be limited to one or more outlets. Forecast horizons are 7, 14 or 30 days (up to 90 through the API).

## Candidate models
Five candidates are compared for every forecast. Seasonal naive repeats the average of the same weekday over the last four weeks and is the baseline every model must beat. Holt-Winters is exponential smoothing with a damped trend and weekly seasonality. XGBoost is a gradient-boosted tree model that forecasts day by day using weekly lags, calendar, festival and external features. Prophet is Meta's additive model with weekly and yearly seasonality, the Indian festival calendar as holidays and promotions, price and weather as extra regressors. The ensemble averages the two best non-baseline models.

## Features used
Calendar features are day of week, weekend flag, day of month, month, quarter and day-of-year seasonality. Festival features mark Diwali, Holi, Ganesh Chaturthi, Christmas and other events with a build-up window. Lag features are sales 7, 14, 21 and 28 days earlier, scaled by the recent 28-day level. External drivers are promotion depth, a price index, maximum temperature, rainfall and the share of products that were out of stock. Planned promotions and climatological weather are known in advance, so they are also used for future days; future stockouts are unknown and set to zero to avoid leakage.

## How the model is chosen
Each candidate is trained only on data before two consecutive 28-day validation folds at the end of the history and scored with WAPE. Prophet is the incumbent model; another model replaces it only when its WAPE is more than 10% lower. This rule came from the rolling-origin study, which showed that switching models on small differences adds noise rather than accuracy. The selected model is then refitted on the full history to produce the forecast.

## Prediction intervals
The 80% band comes from the distribution of the selected model's relative errors in the back-test, using split-conformal quantile levels (a small-sample correction that widens the band slightly so it covers about 80% of new days). Its coverage on the most recent fold, using a band estimated on the earlier fold, is reported so users can see whether the band is too narrow or too wide.

## Model runs and versions
Every forecast request is saved as a forecast run with the series, the data range used, the feature list, the model parameters, the back-test metrics of every candidate, the selected model, the model version (currently 3.0), the run time and the forecast values. Failed runs are saved with their error. The Model Comparison page lists these runs and the latest rolling-origin evaluation.

## Limitations
Forecasts are trained on a synthetic dataset, so their accuracy describes the generator's demand patterns rather than a real shop. At least three weeks of sales are required; Prophet needs 120 days and XGBoost 70 days of history. Product-level series with very low daily sales are noisy and have high percentage errors. Forecasts do not know about events that are not in the data, such as a new competitor or a road closure.
