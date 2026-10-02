# Unusual days and revenue drivers

## How unusual days (anomalies) are detected
For each outlet, daily revenue is divided by the outlet's weekday profile and compared with a centred 15-day rolling median, which gives the expected revenue for that day. The log ratio of actual to expected revenue is turned into a robust z-score. Days with an absolute score of 3.5 or more are flagged; festival days must reach 6 because festivals legitimately move sales a lot. Open days with no sales at all are always flagged as a closure or billing outage.

## Context and evidence
A drop on a day with heavy rain (40 mm or more in the outlet's city) is reported as explained by weather rather than counted as an incident. For every flagged day ERIS lists the evidence it finds: bills compared with a typical day, a single very large bill, heavy rain, promotions running, products out of stock or a festival.

## Suspicious bill lines
A bill line whose quantity is more than 20 times the product's typical quantity, and at least 30 units, is flagged as a likely data-entry error. Business customers such as caterers are compared with typical business purchases so their bulk orders are not flagged.

## Detection quality
On the demo dataset the detector is scored against the generator's labelled anomalies with precision (share of flagged days that were real anomalies) and recall (share of real anomalies that were found). Local events with a modest effect are the hardest to detect.

## Why revenue changed (driver analysis)
To explain a change between two periods ERIS first splits it exactly into a traffic effect, from the change in the number of bills, and a basket effect, from the change in the average bill value. It then shows the change by outlet and by category, and estimates the contribution of the weekday mix and festivals, promotions (uplift over the products' normal sales), stockouts (estimated lost sales), rainfall and unusual days. The weather figure is a statistical association from the past year of data, not proof of cause.
