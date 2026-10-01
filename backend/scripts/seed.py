"""Seed the ERIS database with deterministic synthetic portfolio data."""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import logging
from app.database import AsyncSessionLocal
from app.seed_database import seed_database

logging.basicConfig(level=logging.INFO)


async def main():
    try:
        async with AsyncSessionLocal() as session:
            stats = await seed_database(session, skip_if_exists=False)
            print("Seed Stats:", stats)

            sys.exit(0 if stats.get("status") in ("success", "skipped") else 1)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
