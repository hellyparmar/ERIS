# Portfolio summary

## One line

**ERIS** is a full-stack intelligence platform for a multi-outlet restaurant chain. It covers forecasting with
model comparison, a grounded natural-language analytics assistant, anomaly and revenue-driver analysis, and
the underlying operations: dine-in, takeaway and delivery bills, the menu with recipes, kitchen stock drawn down
by recipe, purchasing, imports and demo GST invoices. It is built on a
reproducible synthetic dataset. (Python, FastAPI, React, Prophet, XGBoost.)

## Résumé bullets

- Built **ERIS**, an open-source restaurant analytics platform (FastAPI, SQLAlchemy/Alembic, PostgreSQL or SQLite,
  React) for a 5-outlet chain. It has 18 working pages, 4 roles with outlet-level access control,
  refresh-token auth and an automatic audit trail. Verified by 120 API tests on SQLite and PostgreSQL and 14
  Playwright end-to-end tests in CI.
- Designed a **deterministic synthetic data generator**: 2 years, about 153K bills and 864K line items for a
  50-dish menu made from 38 ingredients. Bills are built course by course from party size and channel; it models
  meal-time and weekday peaks, Indian festivals (including non-veg dips in Navratri), weather-driven delivery
  shifts, promotion and price elasticity, ingredient outages that take dishes off the menu, seasonal ingredient
  costs, and 26 injected, labelled anomalies, with full provenance (generator version, seed, period).
- Built a **forecasting pipeline** that compares seasonal-naive, Holt-Winters, XGBoost and Prophet models and
  an ensemble.
  - Features: calendar, festival, promotion, price, weather and dish-outage features.
  - Back-test-based selection with empirical 80% intervals; every run is persisted.
  - In a rolling-origin evaluation (25 series × 3 origins, 375 fits) the production pipeline had **11% lower
    WAPE than the seasonal-naive baseline** (14.1% vs 15.9%). The evaluation also showed, and the docs
    report, that XGBoost is weaker than the baseline on the outlet series.
- Built a **safe natural-language analytics assistant**.
  - Rule-based intent and entity parsing maps questions to 29 validated answer templates, with no generated
    SQL.
  - TF-IDF retrieval over the project's own documentation answers how-it-works questions.
  - Optional local LLM through Ollama.
  - Every answer shows its data source, filters, timing, model version and caveats.
  - Scored **31/31 on intent recognition and 21/21 on numbers checked against independent SQL**.
- Implemented **unsupervised anomaly detection**: a weekday-normalised robust z-score with MAD, plus a
  quantity-outlier check on bill lines. Against injected ground truth it reached **precision 0.64 and recall 0.69**
  on unusual days (restaurant revenue is noisier than retail) and caught every injected typing error with no false
  alarms. Added an exact revenue decomposition (traffic × basket, by outlet and category) with estimated
  calendar, promotion, dish-outage and weather contributions.
- Delivered a **CSV ingestion workflow** with:
  - header inspection and automatic column mapping for POS exports;
  - dry-run validation and duplicate detection;
  - atomic commits and downloadable error reports;
  - import history.

  Also delivered **Excel/CSV reporting** and **demo GST invoicing**: CGST/SGST vs IGST by place of supply,
  HSN codes and a PDF output.

## Skills shown

| Area | Evidence |
|---|---|
| Time-series forecasting | Five-model comparison, feature engineering with exogenous drivers, leakage-safe features, rolling-origin evaluation, prediction intervals with measured coverage |
| Statistics | Robust z-scores (MAD), exact decomposition of change, elasticity-based simulation, ABC/RFM, market-basket lift |
| ML engineering | Persisted model runs with metrics and versioning, honest failure handling, reproducible notebook and evaluation scripts, model card |
| Applied NLP / LLM safety | Intent templates instead of text-to-SQL, retrieval limited to project docs, provenance on every answer, grounding evaluation |
| Data engineering | Synthetic data generation with ground truth, validated CSV import pipeline, Alembic migrations, SQLite and PostgreSQL |
| Software engineering | FastAPI, React, auth with refresh tokens, RBAC, audit logging, pytest and Playwright, GitHub Actions, Docker |

## How to describe it honestly

ERIS uses a **synthetic** dataset that I designed. Its accuracy figures show how the models compare against a
known demand process and that the pipeline is correct; they are not results from a real retailer. The GST
features are demonstrations: the GSTINs are synthetic and there is no filing or IRN. The goal was to make
every claim reproducible: `docker compose up`, then run `python -m app.evaluation` and
`python -m app.assistant_eval`.
