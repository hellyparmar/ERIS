"""Generate the demo dataset:  python -m app.seed [--days 540] [--seed 42]

WARNING: wipes all existing data in the configured database.
"""
import argparse

from app.config import settings
from app.db import SessionLocal, create_tables
from app.seed.generator import DEMO_PASSWORDS, generate_demo_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ERIS demo data (wipes existing data)")
    parser.add_argument("--days", type=int, default=settings.SEED_DAYS, help="days of sales history")
    parser.add_argument("--seed", type=int, default=settings.SEED_RANDOM_STATE, help="random seed")
    args = parser.parse_args()

    create_tables()
    print(f"Generating {args.days} days of demo data into {settings.DATABASE_URL} ...")
    with SessionLocal() as db:
        generate_demo_data(db, days=args.days, seed=args.seed)
    print("\nDemo logins:")
    print(f"  admin    admin@eris.demo          / {DEMO_PASSWORDS['admin']}")
    print(f"  manager  priya.and@eris.demo      / {DEMO_PASSWORDS['manager']}")
    print(f"  staff    staff.andheri@eris.demo  / {DEMO_PASSWORDS['staff']}")


if __name__ == "__main__":
    main()
