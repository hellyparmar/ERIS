# R-DIOS v5.0 Data Foundation
**Olist Brazilian E-Commerce Dataset + External Factors**

## 📁 Directory Structure

```
data/
├── raw/                  # Original CSV files from Kaggle
│   ├── olist_orders_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_customers_dataset.csv
│   ├── olist_sellers_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   └── olist_geolocation_dataset.csv
├── processed/            # Enriched data ready for PostgreSQL
│   ├── sales_enriched.csv
│   ├── products_enriched.csv
│   ├── customers_enriched.csv
│   └── inventory_enriched.csv
└── external/             # External factors
    ├── brazil_economy_2016_2018.csv
    ├── weather_sao_paulo_2016_2018.csv
    └── calendar_events_2016_2018.csv
```

## 📥 Dataset Download Instructions

### Step 1: Get Olist Dataset from Kaggle

**URL**: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

**Method 1: Manual Download**
1. Visit the URL above
2. Click "Download" button
3. Extract `archive.zip` to `data/raw/`

**Method 2: Kaggle API (Recommended)**
```bash
# Install Kaggle CLI
pip install kaggle

# Download dataset
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/

# Extract
cd data/raw
unzip brazilian-ecommerce.zip
rm brazilian-ecommerce.zip
```

### Step 2: Verify Files

Run verification script:
```bash
python scripts/data_processing/verify_dataset.py
```

Expected output:
```
✅ olist_orders_dataset.csv (99,441 rows)
✅ olist_order_items_dataset.csv (112,650 rows)
✅ olist_products_dataset.csv (32,951 rows)
✅ olist_customers_dataset.csv (99,441 rows)
✅ olist_sellers_dataset.csv (3,095 rows)
✅ olist_order_payments_dataset.csv (103,886 rows)
✅ olist_geolocation_dataset.csv (1,000,163 rows)
```

## 🔄 Data Processing Pipeline

### Phase 1: Data Quality Check
```bash
python scripts/data_processing/data_quality_check.py
```

Checks:
- Missing values
- Data types
- Date ranges
- Foreign key integrity
- Duplicate records

### Phase 2: Enrichment (Indian Context)
```bash
python scripts/data_processing/data_enricher.py
```

Adds:
- HSN codes (mapped from product category)
- GST tax rates (5%, 12%, 18%)
- Cost prices (70-80% of selling price)
- Stock levels (random initial inventory)
- Dead stock flags (no sales > 6 months)

### Phase 3: External Factors
```bash
python scripts/data_processing/fetch_external_factors.py
```

Fetches:
- Economic indicators (BCB API)
- Weather data (INMET)
- Holiday calendar
- Manual events (Truckers' Strike)

### Phase 4: Database Loading
```bash
python scripts/data_processing/load_to_database.py
```

Loads to PostgreSQL with:
- Monthly partitioning
- Foreign key constraints
- Indexes on critical columns

## 📊 Expected Dataset Size

| Table | Records | Size |
|-------|---------|------|
| sales | ~100k | ~15 MB |
| products | ~33k | ~5 MB |
| customers | ~100k | ~8 MB |
| payments | ~104k | ~10 MB |
| sellers/suppliers | ~3k | ~1 MB |
| inventory | ~33k | ~3 MB |
| **Total** | **~473k** | **~45 MB** |

## 🎯 Next Steps

1. Download Olist dataset
2. Run verification script
3. Execute enrichment pipeline
4. Load into PostgreSQL
5. Validate data quality

See `scripts/data_processing/README.md` for detailed instructions.
