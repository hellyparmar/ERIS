#!/bin/bash
# R-DIOS Dataset Download Script
# Downloads Olist Brazilian E-Commerce and Indian Retail Store Sales datasets

set -e  # Exit on error

echo "🚀 R-DIOS Dataset Download Script"
echo "================================="
echo ""

# Check if Kaggle is installed
if ! command -v kaggle &> /dev/null; then
    echo "❌ Kaggle CLI not found. Installing..."
    pip install -q kaggle
    echo "✅ Kaggle installed"
fi

# Check for Kaggle credentials
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo "⚠️  Kaggle API credentials not found!"
    echo ""
    echo "📋 Setup Instructions:"
    echo "1. Go to https://www.kaggle.com/settings"
    echo "2. Scroll to 'API' section"
    echo "3. Click 'Create New Token'"
    echo "4. Download kaggle.json"
    echo "5. Move it to ~/.kaggle/"
    echo ""
    echo "Run these commands:"
    echo "  mkdir -p ~/.kaggle"
    echo "  mv ~/Downloads/kaggle.json ~/.kaggle/"
    echo "  chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    exit 1
fi

# Create data directories
echo "📁 Creating data directories..."
cd "$(dirname "$0")/../data"
mkdir -p raw processed external

# Download Olist Brazilian E-Commerce
echo ""
echo "📥 Downloading Olist Brazilian E-Commerce dataset..."
echo "   Source: olistbr/brazilian-ecommerce"
echo "   Size: ~45 MB"
echo ""

cd raw
if kaggle datasets download -d olistbr/brazilian-ecommerce --quiet; then
    echo "✅ Download complete"
    
    echo "📦 Extracting files..."
    unzip -q brazilian-ecommerce.zip
    rm brazilian-ecommerce.zip
    echo "✅ Extraction complete"
    
    # Count files
    file_count=$(ls -1 olist_*.csv 2>/dev/null | wc -l)
    echo "📊 Found $file_count CSV files"
else
    echo "❌ Download failed. Check your Kaggle credentials and internet connection."
    exit 1
fi

# Download Indian Retail Store Sales (optional)
echo ""
read -p "📥 Download Indian Retail Store Sales dataset? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading Indian Retail Store Sales..."
    mkdir -p indian_retail
    
    if kaggle datasets download -d sahilprajapati143/retail-store-sales-data-across-india --quiet; then
        unzip -q retail-store-sales-data-across-india.zip -d indian_retail/
        rm retail-store-sales-data-across-india.zip
        echo "✅ Indian retail dataset downloaded"
    else
        echo "⚠️  Download failed or dataset not available. Skipping."
    fi
fi

# Move back to project root
cd ../../

# Run verification
echo ""
echo "🔍 Verifying dataset..."
if python scripts/data_processing/verify_dataset.py; then
    echo ""
    echo "🎉 Dataset download complete!"
    echo ""
    echo "📊 Next steps:"
    echo "   1. python scripts/data_processing/data_quality_check.py"
    echo "   2. python scripts/data_processing/data_enricher.py"
    echo "   3. python scripts/data_processing/fetch_external_factors.py"
    echo "   4. python scripts/data_processing/load_to_database.py"
else
    echo "❌ Verification failed. Please check the output above."
    exit 1
fi
