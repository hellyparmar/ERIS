# R-DIOS Dataset Evaluation Report
**Research Date**: 2026-01-19

---

## 🎯 Evaluation Criteria

| Criterion | Weight | Rationale |
|-----------|--------|-----------|
| **Relational Structure** | 30% | Need multi-table JOINs for ERP simulation |
| **Transaction Depth** | 25% | Requires payment details, partial payments |
| **Time Period** | 20% | Need 2+ years for seasonality & forecasting |
| **Indian Context** | 15% | GST codes, regional data preferred |
| **Data Quality** | 10% | Minimal nulls, clean data types |

---

## 📊 DATASET COMPARISON

### Option 1: Olist Brazilian E-Commerce ⭐ TOP CHOICE
**Source**: Kaggle - `olistbr/brazilian-ecommerce`  
**Period**: 2016-2018 (2 years)  
**Records**: ~100k orders, 473k total rows across 9 tables

**Pros**:
- ✅ **Relational database dump** (9 interconnected CSV files)
- ✅ Payment details (installments, method, timing)
- ✅ Geolocation data (delivery zones)
- ✅ Product categories (32k products)
- ✅ Customer demographics
- ✅ Seller/supplier data (3k sellers)
- ✅ Real-world transaction complexity

**Cons**:
- ❌ Brazilian market (not Indian)
- ❌ No GST/HSN codes (requires synthetic enrichment)
- ❌ Older data (2016-2018)

**R-DIOS Compatibility**: 95%
- Maps perfectly to our 7-table schema
- Can simulate ERP integration via sellers table
- Supports partial payment workflows (installments column)

**Download**:
```bash
kaggle datasets download -d olistbr/brazilian-ecommerce
```

---

### Option 2: Indian Retail Store Sales (2019-2023)
**Source**: Kaggle - Indian retail transaction data  
**Period**: 2019-2023 (4 years)  
**Records**: 100k sales records

**Pros**:
- ✅ **Indian market context** (regions, cities)
- ✅ Recent data (2019-2023)
- ✅ Product categories relevant to India
- ✅ Discount/profit margin data
- ✅ Multiple outlet types

**Cons**:
- ❌ **Single CSV file** (no relational structure)
- ❌ Limited payment details
- ❌ No customer or supplier tables
- ❌ No geolocation granularity

**R-DIOS Compatibility**: 60%
- Needs major restructuring to create relational tables
- Good for supplementary regional insights
- Cannot test JOIN operations or ERP workflows

**Use Case**: Supplementary dataset for regional analysis

---

### Option 3: UCI Online Retail (UK)
**Source**: UCI ML Repository / Kaggle  
**Period**: Dec 2010 - Dec 2011 (1 year)  
**Records**: 540k transactions

**Pros**:
- ✅ High transaction volume
- ✅ Product-level detail (SKU, description, price)
- ✅ Customer segmentation possible
- ✅ Well-documented classic dataset

**Cons**:
- ❌ **Flat structure** (single table)
- ❌ Old data (2010-2011)
- ❌ UK market only
- ❌ No payment method details
- ❌ Many missing CustomerID values (~25%)

**R-DIOS Compatibility**: 50%
- Good for forecasting practice
- Poor for relational database testing
- Missing critical fields (payment, supplier)

---

### Option 4: Store Item Demand Forecasting
**Source**: Kaggle  
**Period**: 5 years  
**Records**: Store-item-daily sales

**Pros**:
- ✅ Clean time-series data
- ✅ Perfect for forecasting algorithms
- ✅ Seasonality patterns

**Cons**:
- ❌ **Too simplified** (store, item, date, sales)
- ❌ No transactions, customers, or payments
- ❌ No business context

**R-DIOS Compatibility**: 40%
- Only useful for Phase 5 (Analytics)
- Cannot test operational features (invoicing, inventory)

---

## 🏆 RECOMMENDED STRATEGY

### PRIMARY DATASET: Olist Brazilian E-Commerce
**Why**: Only dataset with full relational structure matching our needs

**Usage Plan**:
1. Use as **structural backbone** (9 tables → PostgreSQL)
2. **Enrich** with Indian context:
   - Map Brazilian product categories → Indian HSN codes
   - Convert BRL → INR for familiarity
   - Add GST tax rates (5%/12%/18%)
   - Synthesize cost prices for profit calculations

### SUPPLEMENTARY DATASET: Indian Retail Store Sales
**Why**: Provides Indian market context and regional insights

**Usage Plan**:
1. Use for **regional analytics** (Mumbai, Delhi, Bangalore)
2. Validate forecasting models on Indian data
3. Extract product category insights for Indian market
4. Test Hindi/regional language translations

### EXTERNAL FACTORS (Essential)
1. **Economic Data**: Brazilian Central Bank (BCB) API
   - IPCA (inflation), SELIC (interest rate), USD/BRL exchange
2. **Weather Data**: INMET (Brazilian meteorological institute)
   - Focus on São Paulo, Rio de Janeiro
3. **Calendar Events**: `holidays` Python library + manual events
   - 2018 Truckers' Strike (critical causal test case)

---

## 📥 D OWNLOAD PLAN

### Step 1: Install Kaggle CLI
```bash
pip install kaggle
```

### Step 2: Setup Kaggle API credentials
```bash
mkdir -p ~/.kaggle
# Download kaggle.json from https://www.kaggle.com/settings
cp kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### Step 3: Download Olist (Primary)
```bash
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System/data/raw
kaggle datasets download -d olistbr/brazilian-ecommerce
unzip brazilian-ecommerce.zip
rm brazilian-ecommerce.zip
```

### Step 4: Download Indian Retail (Supplementary)
```bash
kaggle datasets download -d sahilprajapati143/retail-store-sales-data-across-india
unzip retail-store-sales-data-across-india.zip -d indian_retail/
rm retail-store-sales-data-across-india.zip
```

### Step 5: Verify Downloads
```bash
python scripts/data_processing/verify_dataset.py
```

---

## 📊 EXPECTED FINAL DATASET

| Table | Source | Records | External Enrichment |
|-------|--------|---------|---------------------|
| **sales** | Olist orders + items | ~100k | Weather, economy, holidays |
| **products** | Olist products | ~33k | HSN codes, GST rates |
| **customers** | Olist customers | ~100k | WhatsApp numbers (synthetic) |
| **payments** | Olist payments | ~104k | - |
| **suppliers** | Olist sellers | ~3k | - |
| **inventory** | Derived from products | ~33k | Stock levels (synthetic) |
| **geolocation** | Olist geo |  ~1M | - |
| **regional_insights** | Indian Retail | 100k | Market trends |

**Total**: ~1.5M records across 8 tables

---

## ✅ VALIDATION CRITERIA

Before proceeding to enrichment, verify:
- [ ] All 9 Olist CSV files downloaded
- [ ] Row counts match expected (see verify_dataset.py)
- [ ] No corrupted files
- [ ] File sizes total ~45 MB
- [ ] Indian Retail CSV downloaded (backup dataset)

---

## 🎯 DECISION RATIONALE

**Why NOT use Indian datasets as primary?**
- Indian retail datasets lack relational structure
- Single CSV files cannot test JOINs, foreign keys
- Missing payment/supplier data critical for invoicing module

**Why NOT use UCI Online Retail?**
- Single table (540k flat rows)
- 25% missing customer IDs breaks CRM features
- No payment method data for Transaction Engine testing

**Why Olist wins despite being Brazilian?**
- **Only dataset** with multi-table structure we need
- Installments column enables Khata/partial payment simulation
- Seller table enables B2B features (POs, supplier communication)
- Can "Indianize" via enrichment (HSN codes, GST, INR)

**Trade-off**: Use Brazilian data structure + Indian market context enrichment = **Best of both worlds**

---

## 🚀 NEXT STEPS

1. Download Olist dataset *(in progress)*
2. Download Indian Retail dataset *(supplementary)*
3. Run verification script
4. Begin enrichment with GST/HSN codes
5. Fetch external factors (BCB API, weather)
6. Load into PostgreSQL with partitioning

**Estimated Time**: 4-6 hours (mostly API fetch time)
