# R-DIOS v6.0 - Thesis Summary

## Research Questions & Findings

### RQ1: What are the causal effects of external factors on retail sales?

**Methodology**: Doubly Robust (AIPW) estimation with propensity score adjustment

**Findings**:

| Factor | Effect | 95% CI | p-value | Significance |
|--------|--------|--------|---------|--------------|
| Holidays | +₹17,523/day | [₹12,934, ₹22,112] | <0.001 | *** |
| Monsoon | -₹7,846/day | [-₹10,832, -₹4,860] | <0.001 | *** |

**Holiday Breakdown**:

- Diwali: +35%
- Eid: +30%
- Holi: +25%
- Christmas: +25%
- Independence Day: +10%

**Business Implication**: Retailers should stock up 2 weeks before major holidays and reduce perishable inventory during monsoon.

---

### RQ2: Does multi-source data fusion improve demand forecasting accuracy?

**Methodology**: 5-fold walk-forward time-series cross-validation (365-day training, 30-day horizon)

**Validated Findings** (January 2026):

| Model | Without Factors (MAPE) | With Factors (MAPE) | Improvement |
|-------|------------------------|---------------------|-------------|
| **Prophet** | 8.74% | **4.57%** | **47.7%** |
| LSTM | 13.10% | - | Baseline |
| Seasonal Naive | 13.16% | - | Baseline |
| Naive | 18.93% | - | Baseline |

**Key Metrics (Prophet + Regressors)**:

- **MAPE:** 4.57% [95% CI: 3.26%-5.88%]
- **R²:** 0.877 [95% CI: 0.820-0.935]
- **Improvement over Naive:** 76%

**Conclusion**: Integrating holidays (Diwali, Eid, Holi) and monsoon indicators improved Prophet accuracy by **48%**, validating the data fusion hypothesis.

---

## Key Contributions

1. **Causal Inference Engine**: 5 estimation methods for retail causal analysis
2. **Counterfactual Framework**: What-if scenario analysis for decision support
3. **Multi-Model Forecasting**: Prophet, ARIMA, LSTM, Ensemble with external factors
4. **Unified Analytics Platform**: 57+ API endpoints for retail intelligence

---

## Technical Deliverables

| Component | Files | Features |
|-----------|-------|----------|
| Database | 15 tables | Partitioning, materialized views |
| ML Models | 4 forecasters | Cross-validation, external factors |
| Causal | 5 estimators | IPW, DML, matching |
| API | 57+ endpoints | REST, OpenAPI documented |
| Tests | 40+ cases | Unit, integration, performance |

---

## Practical Impact

- **Inventory Optimization**: EOQ, safety stock, reorder alerts
- **Customer Segmentation**: RFM + K-means clustering
- **Explainable AI**: Feature importance for predictions
- **Actionable Insights**: Prioritized recommendations

---

## Future Work

1. Real-time streaming integration
2. A/B testing framework
3. Reinforcement learning for pricing
4. Mobile application
