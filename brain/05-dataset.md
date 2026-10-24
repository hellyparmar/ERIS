# The synthetic dataset

The demo business is **Saffron Table**, a five-outlet casual-dining restaurant chain. Everything is synthetic.
The generator is deterministic: the same seed and version give the same data.

Sources: `api/app/seed/catalog.py`, `api/app/seed/generator.py` (version 4.0.0), `docs/DATASET.md`, `docs/MODEL_CARD.md`.

## Why a restaurant, and why synthetic
- **Restaurant** (D14): the owner asked for a restaurant chain. Restaurants have a clear link between dishes and ingredients, which lets the app show stock draw-down by recipe (D13).
- **Synthetic** (D9): the results must be reproducible, and anomaly detection can only be scored against known labels. Real data is not available for a public portfolio.

## The outlets

Values are read from `OUTLET_TASTE` in `catalog.py`. `nonveg` is a demand multiplier for non-vegetarian dishes
(1.0 = neutral). `delivery` is the share of bills that are delivery orders.

| Code | Outlet | City | Invoice prefix | nonveg | delivery share | In the demo |
|---|---|---|---|---|---|---|
| MUM-AND | Andheri West | Mumbai | MUMAND | 1.05 | 0.30 | yes |
| BLR-IND | Indiranagar | Bengaluru | BLRIND | 1.15 | 0.40 | yes |
| PUN-KOR | Koregaon Park | Pune | PUNKOR | 1.00 | 0.28 | yes |
| BLR-WHF | Whitefield | Bengaluru | BLRWHF | 1.10 | 0.42 | yes |
| AMD-SGH | SG Highway | Ahmedabad | AMDSGH | 0.45 | 0.24 | yes |
| MUM-BAN | (sixth profile) | Mumbai | — | 1.10 | 0.32 | defined only |
| HYD-JUB | (seventh profile) | Hyderabad | — | 1.35 | 0.34 | defined only |

The five in the demo are the ones shown in the screenshots. The sixth and seventh profiles are defined so that the
catalogue can supply up to seven outlets (the API cap). Which outlets a given demo uses is set by `SEED_OUTLETS`.
Outlet growth over time is not in `OUTLET_TASTE`; it comes from the generator.

## The catalogue
- **50 menu items** in nine categories, each with a recipe.
- **38 ingredients**, each with a unit, cost and supplier. Costs are seasonal (the generator varies them through the year).
- **7 suppliers**.
- **Courses:** `COURSE_OF` maps each item to a course (starter, main, bread, rice, dessert, drink). Bills are built course by course.
- **Rice sides:** `RICE_SIDES` lists the dishes that are typically ordered with rice.

## How bills are generated (4.0.0)
- A bill has a party size, a channel (dine-in, takeaway, delivery) and a meal time.
- Dine-in bills record **covers** (guests). Takeaway and delivery bills do not.
- The order is built course by course: starter, mains, breads, rice, drinks, dessert. Mains are paired with breads (rule: party naan ×2).
- **Peaks:** lunch and dinner peaks; weekend rush.
- **Festivals:** Navratri lowers non-veg dishes. Diwali and other festivals shift demand (`holidays.py`).
- **Weather:** rain shifts orders to delivery.
- **Promotions and price changes:** planned promotions and price elasticity.
- **Outages:** an ingredient can run out, taking the dishes that use it off the menu. **Only ingredients used in at most eight dishes can go out** (`MAX_OUTAGE_DISHES = 8`). The reason: ubiquitous ingredients such as oil or onion going out produced hundreds of false anomalies in the detector (see `08`).
- **Company orders:** bulk business orders are grouped (`_group_order`) into one bill rather than split across many. Before grouping, the detector flagged each fragment as a suspicious bill.

## Labelled anomalies
- **26 unusual outlet-days** are injected and labelled. The detector is scored against them (`08`).
- **5 bill-line typing errors** are injected and labelled.
- Labels are stored with the data so the evaluation can compare.

## Provenance
- `dataset_info` records source, generator version, seed, timestamp and period.
- Every synthetic sale references its dataset through `sales.dataset_id`.
- Invalid-row samples for the importer are produced as downloadable files, not stored in the database, so they never pollute analytics.

## Configuration
- Seed defaults to 42. End date configurable with `SEED_END_DATE` or `--end-date`.
- The generator only uses information that would be known at forecast time: planned promotions and climatological weather. This prevents leakage in the forecast evaluation.

## Known limits
- Two years of data. Not enough for some yearly seasonality, which is why festivals are modelled explicitly.
- Outlets are fictional; their cities are used for realism only.
- Prices and costs are plausible for India, not sourced from a market dataset.
