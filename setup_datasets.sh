#!/bin/bash

# ============================================================================
# Enterprise Retail Intelligence System v3.0
# KAGGLE DATASET SETUP SCRIPT
#
# This script downloads the 5-layer dataset architecture from Kaggle.
# Prerequisites:
#   1. Kaggle account (kaggle.com)
#   2. Kaggle API token (~/.kaggle/kaggle.json)
#   3. Kaggle CLI installed: pip install kaggle
#
# Usage: bash setup_datasets.sh
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "R-DIOS DATASET SETUP - 5-Layer Architecture"
echo "============================================================================"

# Check if kaggle CLI is installed
if ! command -v kaggle &> /dev/null; then
    echo "❌ Kaggle CLI not found!"
    echo "   Install with: pip install kaggle"
    exit 1
fi

# Check if kaggle credentials exist
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo "❌ Kaggle API credentials not found!"
    echo "   1. Go to https://www.kaggle.com/account"
    echo "   2. Click 'Create New API Token'"
    echo "   3. Place kaggle.json in ~/.kaggle/"
    echo "   4. Run: chmod 600 ~/.kaggle/kaggle.json"
    exit 1
fi

echo "✅ Kaggle CLI found"
echo "✅ Kaggle credentials found"
echo ""

# Create data directory
mkdir -p data/kaggle
cd data/kaggle

echo "============================================================================"
echo "LAYER 1: SALES DATA"
echo "============================================================================"

# Dataset 1: Retail Grocery Sales 2024
echo ""
echo "📊 Downloading: Retail Grocery Sales 2024"
kaggle datasets download -d mithesh/retail-grocery-sales-2024 || echo "⚠️  Failed to download (check dataset name)"

# Dataset 2: Store Sales Favorita
echo ""
echo "📊 Downloading: Store Sales - Time Series Forecasting"
kaggle competitions download -c store-sales-time-series-forecasting || echo "⚠️  Failed to download (may require competition acceptance)"

echo ""
echo "============================================================================"
echo "LAYER 2: INVENTORY DATA"
echo "============================================================================"

# Dataset 3: Retail Store Inventory Forecasting
echo ""
echo "📦 Downloading: Retail Store Inventory Forecasting"
kaggle datasets download -d shantanudhakadd/retail-store-inventory-forecasting || echo "⚠️  Failed to download"

echo ""
echo "============================================================================"
echo "LAYER 3: CUSTOMER BEHAVIOR"
echo "============================================================================"

# Dataset 4: Customer Purchase Behavior
echo ""
echo "👤 Downloading: Customer Purchase Behavior"
kaggle datasets download -d bhadramohit/customer-purchase-behavior-dataset || echo "⚠️  Failed to download"

# Dataset 5: E-commerce Behavior 2024
echo ""
echo "🛒 Downloading: E-commerce Customer Behavior 2024"
kaggle datasets download -d uom190346a/e-commerce-customer-behavior-dataset || echo "⚠️  Failed to download"

echo ""
echo "============================================================================"
echo "LAYER 5: VALIDATION DATASETS"
echo "============================================================================"

# Dataset 6: UCI Online Retail
echo ""
echo "🔬 Downloading: Online Retail Dataset"
kaggle datasets download -d vijayuv/onlineretail || echo "⚠️  Failed to download"

echo ""
echo "============================================================================"
echo "EXTRACTING DATASETS"
echo "============================================================================"

# Extract all zip files
echo ""
echo "📂 Extracting archives..."
for file in *.zip; do
    if [ -f "$file" ]; then
        echo "   Extracting: $file"
        unzip -q -o "$file" || echo "⚠️  Failed to extract $file"
    fi
done

echo ""
echo "============================================================================"
echo "SETUP COMPLETE"
echo "============================================================================"
echo ""
echo "✅ Datasets downloaded to: $(pwd)"
echo ""
echo "📁 Directory contents:"
ls -lh
echo ""
echo "💡 Next steps:"
echo "   1. Run: python test_data_loader.py"
echo "   2. Verify data integrity"
echo "   3. Proceed with feature engineering"
echo ""
echo "============================================================================"
