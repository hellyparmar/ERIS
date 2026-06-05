import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

async def test_connection():
    # Use the credentials we suspect are correct
    db_url = "postgresql+asyncpg://eris_admin:admin1234@db:5432/eris_production"
    print(f"Testing connection to {db_url}...")
    try:
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"Success! Result: {result.scalar()}")
        await engine.dispose()
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
