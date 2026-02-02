# Limitations and Lessons Learned

## 1. Technical Limitations

### 1.1 Cold Start Problem

The system struggles to generate accurate forecasts for new products with less than 30 days of historical data.

* **Impact:** New menu items will default to the "Naive Baseline" which may underpredict initial launch demand.
* **Mitigation:** Implemented a "Category Average" fallback strategy for items with <14 days of data (though not fully validated).

### 1.2 Seasonal Granularity

While Prophet handles weekly and yearly seasonality, it occasionally misses micro-seasonality (e.g., local events not in the standard Indian Holiday calendar).

* **Impact:** Demand spikes during localized events (e.g., college exams nearby) are missed.
* **Mitigation:** Manual override feature in the dashboard allows managers to input expected "event days".

### 1.3 LLM Latency

The AI Assistant's NL-to-SQL pipeline has an average latency of ~3.2 seconds due to the semantic layer validation steps.

* **Impact:** Not suitable for instant, real-time query spamming.
* **Optimization:** Added aggressive caching for repeat queries (e.g., "sales today") reducing hit time to <50ms.

---

## 2. Scope Constraints (Thesis Boundaries)

### 2.1 ERP Integration Depth

Validated integration with Tally/Zoho is limited to **Sales Sync** only.

* **Limitation:** Purchase Orders generated in R-DIOS do not yet automatically push to Tally; they must be exported as CSV first.
* **Reason:** Complexity of different accounting software versions and lack of unified API access during the internship.

### 2.2 SKU Coverage

Validation was focused on the top 20% of SKUs driving 80% of revenue (Pareto Principle).

* **Limitation:** Long-tail, slow-moving items (e.g., specific spices) were excluded from deep forecast validation.
* **Reason:** Forecasting intermittent demand requires specialized "Croston's Method" models which were out of scope for Phase 1.

---

## 3. Lessons Learned (Retrospective)

### 3.1 Simplicity Wins 🏆

The biggest surprise was the **Naive Baseline (13.24% MAPE)** outperforming complex models like Prophet and LSTM for daily stable demand.

* **Lesson:** Do not reach for Deep Learning immediately. Retail data often has high autocorrelation where "tomorrow = today" is a hard baseline to beat.

### 3.2 Data Quality > Model Quality

Spending 3 days cleaning the "Unit of Measure" issues (grams vs kgs) yields better improvements than 3 days of hyperparameter tuning.

* **Lesson:** The initial architecture's robust ETL pipeline was the best investment of time.

### 3.3 Explainability Builds Trust

Users rejected the black-box LSTM model (even when accurate) but embraced the simple Rule-Based Alerts and "Show SQL" AI feature.

* **Lesson:** For non-technical restaurant owners, "Why?" is as important as "What?".

---

## 4. Future Roadmap

1. **Phase 3:** Integrate "Intermittent Demand" forecasting for slow-moving inventory.
2. **Phase 4:** Direct write-back APIs for Tally/Zoho to automate PO creation.
3. **Phase 5:** Vision-based inventory tracking (camera integration) to reduce manual waste logging.
