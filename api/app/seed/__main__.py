"""Generate the demo dataset:  python -m app.seed [--days 730] [--outlets 5] [--seed 42] [--end-date YYYY-MM-DD]

WARNING: wipes all existing data in the configured database.
"""
import argparse
from datetime import date

from app.config import settings
from app.db import SessionLocal, migrate
from app.seed.generator import DEMO_PASSWORDS, generate_demo_data


def seed_kwargs(days=None, outlets=None, seed=None, end_date=None) -> dict:
    end = end_date or settings.SEED_END_DATE
    return {"days": days or settings.SEED_DAYS, "n_outlets": outlets or settings.SEED_OUTLETS,
            "seed": settings.SEED_RANDOM_STATE if seed is None else seed,
            "end_date": date.fromisoformat(end) if end else None}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ERIS demo data (wipes existing data)")
    parser.add_argument("--days", type=int, help=f"days of history (default {settings.SEED_DAYS})")
    parser.add_argument("--outlets", type=int, help=f"number of outlets 1-7 (default {settings.SEED_OUTLETS})")
    parser.add_argument("--seed", type=int, help=f"random seed (default {settings.SEED_RANDOM_STATE})")
    parser.add_argument("--end-date", help="last day of data, YYYY-MM-DD (default: yesterday)")
    a = parser.parse_args()
    from app.seed.generator import MIN_DAYS

    if a.days is not None and a.days < MIN_DAYS:
        parser.error(f"--days must be at least {MIN_DAYS}")
    if a.outlets is not None and not 1 <= a.outlets <= 7:
        parser.error("--outlets must be between 1 and 7")
    migrate()
    kwargs = seed_kwargs(a.days, a.outlets, a.seed, a.end_date)
    print(f"Generating demo data {kwargs} into {settings.DATABASE_URL} ...")
    with SessionLocal() as db:
        generate_demo_data(db, **kwargs)
    print("\nDemo logins:")
    print(f"  admin    admin@eris.demo          / {DEMO_PASSWORDS['admin']}")
    print(f"  manager  priya.and@eris.demo      / {DEMO_PASSWORDS['manager']}")
    print(f"  manager  arjun.ind@eris.demo      / {DEMO_PASSWORDS['manager']}  (two Bengaluru outlets)")
    print(f"  staff    staff.andheri@eris.demo  / {DEMO_PASSWORDS['staff']}")
    print(f"  viewer   analyst@eris.demo        / {DEMO_PASSWORDS['viewer']}")


if __name__ == "__main__":
    main()
