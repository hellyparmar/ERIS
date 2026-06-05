
import asyncio
import asyncpg
import os
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def main():
    url = os.environ.get('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    h = pwd_context.hash('admin123')
    await conn.execute('UPDATE users SET email = $1, password_hash = $2 WHERE id = 1', 'admin@rdios.com', h)
    await conn.close()
    print('Updated admin user successfully')

if __name__ == '__main__':
    asyncio.run(main())
