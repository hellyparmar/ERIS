# Glossary of metrics and terms

## Revenue, bills and average bill value
Revenue is the amount customers paid, including GST and after discounts. A bill is one completed sale (voided sales are excluded everywhere). Average bill value (AOV, average basket) is revenue divided by the number of bills. Items per bill is units sold divided by bills.

## Gross profit and margin
Gross profit is revenue minus GST minus the cost of goods sold (the product cost recorded on each bill line at the time of sale). Margin % is gross profit divided by net sales (revenue excluding GST).

## WAPE (weighted absolute percentage error)
WAPE is the sum of absolute forecast errors divided by the sum of actual values, as a percentage. A WAPE of 12% means the forecast was off by 12% of total actual sales over the test window. ERIS uses WAPE to choose forecasting models because it is stable when some days have very low sales. Lower is better.

## MAE and RMSE
MAE (mean absolute error) is the average size of the daily forecast error in the series' unit (rupees or units). RMSE (root mean squared error) also measures daily error but punishes large misses more strongly than MAE.

## sMAPE and MAPE
MAPE is the average of daily absolute percentage errors; it explodes on days with near-zero sales, so ERIS reports it but does not select models on it. sMAPE (symmetric MAPE) divides the error by the average of actual and forecast, which keeps it bounded between 0% and 200%.

## Bias
Bias % is the total forecast minus total actual, divided by total actual. Positive bias means the model over-forecasts; negative means it under-forecasts.

## Prediction interval and interval coverage
The shaded band on forecast charts is an 80% prediction interval: ERIS expects about 8 out of 10 future days to fall inside it. It is built from the chosen model's own back-test errors. Interval coverage is the share of actual test days that really fell inside the band; close to 80% means the band is honest.

## Back-test, fold and rolling-origin evaluation
A back-test hides the most recent days, trains the model on the earlier history and compares the forecast with what really happened. A fold is one such hidden window (28 days in ERIS). Rolling-origin evaluation repeats this at several cut-off dates to measure how the models perform over time.

## ABC analysis
ABC classes rank products by their share of revenue: A products make up roughly the first 80% of revenue, B the next 15% and C the last 5%. A items deserve the most attention for stock availability.

## RFM segmentation
RFM scores each identified customer from 1 to 5 on Recency (days since last purchase), Frequency (number of bills) and Monetary value (spend) over the last 12 months. Segments: Champions, Loyal, Potential Loyalists, New, Needs Attention, At Risk and Lost.

## Market-basket lift
Lift measures how much more often two products are bought on the same bill than would happen by chance. A lift of 3 means the pair appears together three times as often as expected. Confidence is the share of bills with one product that also contain the other.

## Days of cover, reorder level and safety stock
Days of cover is current stock divided by average daily demand. The reorder level is the stock quantity at which a new order should be placed. Safety stock is extra stock held to absorb demand swings during the supplier lead time.

## Robust z-score
A robust z-score measures how unusual a value is using the median and the median absolute deviation (MAD) instead of the mean and standard deviation, so a few extreme days do not hide other anomalies. ERIS flags outlet-days with an absolute robust z-score of 3.5 or more.

## GST terms
GSTIN is the 15-character GST registration number (state code, PAN, entity number, Z, check digit). HSN is the Harmonized System of Nomenclature code that classifies goods. CGST and SGST are the central and state halves of GST charged on a supply within one state; IGST is charged on a supply between states. Place of supply decides which applies.
