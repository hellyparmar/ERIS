import asyncio
from app.database import AsyncSessionLocal
from app.models.users import User
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == 'admin@rdios.com'))
        user = result.scalar_one_or_none()
        if user:
            print(f"Found user: {user.email}")
        else:
            print("User not found")

asyncio.run(main())
