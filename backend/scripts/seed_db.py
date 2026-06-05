#!/usr/bin/env python
"""
CLI Database Seeding Script
Provides command-line interface for seeding the database with synthetic data.

Usage:
    python backend/scripts/seed_db.py --help
    python backend/scripts/seed_db.py                              # Default seed
    python backend/scripts/seed_db.py --days 90 --products 30      # Custom parameters
    python backend/scripts/seed_db.py --check                      # Check current data
    python backend/scripts/seed_db.py --reset                      # Force reseed
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent directories to Python path
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
root_dir = backend_dir.parent

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database Seeding CLI - Populate ERIS database with synthetic data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/scripts/seed_db.py                    # Seed with defaults (365 days, 50 products)
  python backend/scripts/seed_db.py --days 90          # Seed with 90 days of history
  python backend/scripts/seed_db.py --check            # Check current database contents
  python backend/scripts/seed_db.py --reset            # Force reseed even if data exists
  python backend/scripts/seed_db.py --days 180 --products 100 --reset
        """
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days of sales history to generate (default: 365)'
    )
    parser.add_argument(
        '--products',
        type=int,
        default=50,
        help='Number of products to create (default: 50)'
    )
    parser.add_argument(
        '--customers',
        type=int,
        default=20,
        help='Number of customers to create (default: 20)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check current database contents without seeding'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Force seeding even if database already has data'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        from app.core.database_seeder import DatabaseSeeder
        
        seeder = DatabaseSeeder()
        
        # Show current database summary
        logger.info("=" * 70)
        logger.info("📊 CURRENT DATABASE STATUS")
        logger.info("=" * 70)
        
        summary = seeder.get_data_summary()
        total = sum(summary.values())
        
        for key, count in summary.items():
            logger.info(f"  {key:12} : {count:6} records")
        
        logger.info("-" * 70)
        logger.info(f"  {'TOTAL':12} : {total:6} records")
        logger.info("=" * 70)
        
        # If --check flag, just show summary and exit
        if args.check:
            logger.info("✅ Database check complete. Use --reset to seed anyway.")
            return 0
        
        # Check if seeding is needed
        if total > 0 and not args.reset:
            logger.warning("⚠️  Database already contains data.")
            logger.warning("   Use --reset flag to force seeding: python backend/scripts/seed_db.py --reset")
            return 1
        
        # Confirm seeding parameters
        logger.info("\n" + "=" * 70)
        logger.info("📋 SEEDING PARAMETERS")
        logger.info("=" * 70)
        logger.info(f"  Days of history    : {args.days}")
        logger.info(f"  Products to create : {args.products}")
        logger.info(f"  Customers to create: {args.customers}")
        logger.info("=" * 70)
        
        if not args.reset and total > 0:
            logger.warning("⚠️  Database is not empty. Use --reset to overwrite.")
            return 1
        
        # Proceed with seeding
        logger.info("\n🌱 Starting database seeding...")
        
        success = seeder.seed_database(
            num_days=args.days,
            num_products=args.products,
            num_customers=args.customers
        )
        
        if success:
            logger.info("\n" + "=" * 70)
            logger.info("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
            logger.info("=" * 70)
            
            # Show final summary
            final_summary = seeder.get_data_summary()
            final_total = sum(final_summary.values())
            
            logger.info("\n📊 FINAL DATABASE STATUS")
            for key, count in final_summary.items():
                logger.info(f"  {key:12} : {count:6} records")
            logger.info("-" * 70)
            logger.info(f"  {'TOTAL':12} : {final_total:6} records")
            logger.info("=" * 70)
            
            logger.info("\n✨ System is ready for testing and development!")
            logger.info("   Start the backend: python -m uvicorn app.main:app --reload")
            logger.info("   API Docs: http://localhost:8000/docs")
            
            return 0
        else:
            logger.error("\n❌ Database seeding failed!")
            logger.error("   Check the logs above for details.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
