import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os

async def check():
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://eris_admin:admin1234@localhost:5432/eris_production")
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'outlets'"))
        columns = res.fetchall()
        print("Columns in 'outlets' table:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
