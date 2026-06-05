#!/usr/bin/env python
"""
Sample Data Generation Script

Generates synthetic sales data for forecasting model testing and demonstration.
Usage:
    python app/ml/data/generate_sample_data.py [--output PATH] [--days DAYS] [--products NUM]
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.ml.data.generate_sales_data import SalesDataGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic retail sales data for forecasting models"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/sample_sales.csv',
        help='Output CSV file path (default: data/sample_sales.csv)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days of data to generate (default: 365)'
    )
    parser.add_argument(
        '--products',
        type=int,
        default=1,
        help='Number of products to generate (default: 1)'
    )
    parser.add_argument(
        '--base-sales',
        type=float,
        default=125000,
        help='Average daily sales amount (default: 125000)'
    )
    parser.add_argument(
        '--seasonality',
        type=float,
        default=0.3,
        help='Seasonality strength 0-1 (default: 0.3)'
    )
    parser.add_argument(
        '--trend',
        type=float,
        default=0.001,
        help='Daily trend growth rate (default: 0.001)'
    )
    parser.add_argument(
        '--noise',
        type=float,
        default=0.1,
        help='Noise level as fraction of base sales (default: 0.1)'
    )
    parser.add_argument(
        '--correlation',
        type=float,
        default=0.5,
        help='Correlation between products 0-1 (default: 0.5)'
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Generating synthetic sales data...")
    logger.info(f"  Days: {args.days}")
    logger.info(f"  Products: {args.products}")
    logger.info(f"  Base Sales: ₹{args.base_sales:,.0f}")
    logger.info(f"  Seasonality: {args.seasonality}")
    logger.info(f"  Trend: {args.trend}")
    logger.info(f"  Noise: {args.noise}")
    
    generator = SalesDataGenerator(random_seed=42)
    
    if args.products == 1:
        df = generator.generate(
            days=args.days,
            base_sales=args.base_sales,
            seasonality_strength=args.seasonality,
            trend_strength=args.trend,
            noise_level=args.noise,
        )
    else:
        df = generator.generate_multi_product(
            days=args.days,
            num_products=args.products,
            correlation=args.correlation,
        )
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"\n✅ Data saved to: {output_path}")
    logger.info(f"   Shape: {df.shape}")
    logger.info(f"   Columns: {list(df.columns)}")
    
    # Print summary statistics
    if 'sales' in df.columns:
        logger.info(f"\nSummary Statistics:")
        logger.info(f"   Mean: ₹{df['sales'].mean():,.2f}")
        logger.info(f"   Std Dev: ₹{df['sales'].std():,.2f}")
        logger.info(f"   Min: ₹{df['sales'].min():,.2f}")
        logger.info(f"   Max: ₹{df['sales'].max():,.2f}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
