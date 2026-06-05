import logging
from datetime import datetime

import pandas as pd

from .generate_sales_data import SalesDataGenerator

logger = logging.getLogger(__name__)


def make_sales_data(days: int = 365, num_products: int = 10):
    """Generate synthetic multi-product retail sales data."""
    generator = SalesDataGenerator(random_seed=42)
    df = generator.generate_multi_product(days=days, num_products=num_products)

    logger.info(f"Synthetic sales data frame created: {df.shape[0]} rows")
    return df


if __name__ == "__main__":
    df = make_sales_data(days=365, num_products=5)
    print(df.head())
    print(df.tail())
    print(f"Generated {len(df)} rows")
    df.to_csv("synthetic_sales_data.csv", index=False)
