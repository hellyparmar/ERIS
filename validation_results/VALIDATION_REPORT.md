# R-DIOS Forecast Validation Report

**Generated:** 2026-01-30T11:42:27.333199

---

## Configuration

- **Forecast Horizon:** 7 days
- **Train/Val/Test Split:** 70% / 15% / 15%
- **Cross-Validation Folds:** 5
- **Confidence Level:** 95%

## Model Performance Summary

| Model | MAPE | RMSE | MAE | R² | 95% CI |
|-------|------|------|-----|----|---------|
| Naive Baseline | 13.24% | ₹95,620 | ₹65,499 | -0.0438 | [10.99%, 15.50%] |
| ARIMA | 23.59% | ₹128,258 | ₹106,119 | -0.8780 | [20.14%, 27.03%] |
| Prophet | 26.75% | ₹142,172 | ₹117,092 | -1.3075 | [22.53%, 30.97%] |
| Seasonal Naive | 30.51% | ₹159,506 | ₹132,307 | -1.9045 | [25.68%, 35.33%] |

## Improvement Over Baseline

- **ARIMA:** -78.1% improvement
- **Prophet:** -102.0% improvement

## Statistical Significance Tests

- **Prophet:** ✅ Not significantly different (p=0.0000)
- **ARIMA:** ✅ Not significantly different (p=0.0000)
- **Seasonal Naive:** ✅ Not significantly different (p=0.0000)

## Error Analysis

### Prophet

- Mean Error: ₹-59,767
- Std Dev: ₹129,747
- Median % Error: -15.45%
- Max Overestimate: ₹256,925
- Max Underestimate: ₹332,008

### ARIMA

- Mean Error: ₹-33,066
- Std Dev: ₹124,641
- Median % Error: -10.02%
- Max Overestimate: ₹216,358
- Max Underestimate: ₹354,955

### Naive Baseline

- Mean Error: ₹19,590
- Std Dev: ₹94,135
- Median % Error: 0.98%
- Max Overestimate: ₹108,528
- Max Underestimate: ₹381,158

### Seasonal Naive

- Mean Error: ₹-76,784
- Std Dev: ₹140,618
- Median % Error: -18.32%
- Max Overestimate: ₹300,230
- Max Underestimate: ₹381,158

