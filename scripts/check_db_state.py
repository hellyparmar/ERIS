import psycopg2
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

db_url = os.getenv("DATABASE_URL")
if db_url:
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

def main():
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("--- ROLES ---")
    cur.execute("SELECT id, name, description FROM roles")
    for r in cur.fetchall():
        print(r)
        
    print("\n--- OUTLETS ---")
    cur.execute("SELECT id, name, city FROM outlets")
    for o in cur.fetchall():
        print(o)
        
    print("\n--- USERS ---")
    cur.execute("SELECT u.id, u.username, u.email, r.name FROM users u JOIN roles r ON u.role_id = r.id")
    for u in cur.fetchall():
        print(u)
        
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
