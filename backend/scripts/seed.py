"""
seed.py - Canonical database & RAG knowledge seed entrypoint.

Run this script to seed the database and ingest RAG knowledge:
python scripts/seed.py
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import logging
from app.database import AsyncSessionLocal
from app.seed_database import seed_database
from app.seed_rag import seed_unstructured_data

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        async with AsyncSessionLocal() as session:
            stats = await seed_database(session, skip_if_exists=False)
            print("Seed Stats:", stats)
            
            print("Starting RAG ingestion...")
            await seed_unstructured_data()
            
            sys.exit(0 if stats.get('status') in ('success', 'skipped') else 1)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
