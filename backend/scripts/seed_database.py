"""
seed_database.py  (backend/scripts/)
Thin CLI wrapper that invokes the main seeding pipeline via asyncio.
Intended for one-shot use during local dev setup or staging resets.

Usage:
    python -m backend.scripts.seed_database
    python -m backend.scripts.seed_database --skip-if-exists
"""
import asyncio
import argparse
import logging
import sys

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the Eris database with demo data.")
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        default=True,
        help="Skip seeding if records already exist (default: True)",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging verbosity",
    )
    return parser.parse_args()


async def _run(skip_if_exists: bool) -> None:
    """Async entry point — imports are deferred to avoid circular deps at import time."""
    from app.database import AsyncSessionLocal
    from app.seed_database import seed_database  # the real seeding module

    logger.info("Connecting to database…")
    async with AsyncSessionLocal() as session:
        stats = await seed_database(session, skip_if_exists=skip_if_exists)
    logger.info("Seeding result: %s", stats)


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.loglevel),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    try:
        asyncio.run(_run(skip_if_exists=args.skip_if_exists))
        print("Done — database seeded successfully.")
    except Exception as exc:
        logger.error("Seeding failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
