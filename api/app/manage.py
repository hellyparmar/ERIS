"""Administration commands.

    python -m app.manage create-admin --email owner@shop.in --name "Owner" [--password ...] [--org "My Shop"]

Use this to start ERIS with your own data instead of the demo (set SEED_DEMO_DATA=false): it creates the
organisation (if there is none) and an admin account. Without --password you are prompted for one.
Alternatively set INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD; the API then creates that admin on first start.
"""
from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import func, select

from app.db import SessionLocal, migrate
from app.models import Organization, User
from app.security import hash_password


def create_admin(email: str, password: str, name: str, org_name: str | None = None) -> str:
    email = email.strip().lower()
    if len(password) < 8:
        raise ValueError("The password must have at least 8 characters")
    if "@" not in email:
        raise ValueError("Enter a valid email address")
    migrate()
    with SessionLocal() as db:
        if db.scalar(select(func.count(User.id)).where(func.lower(User.email) == email)):
            raise ValueError(f"A user with the email {email} already exists")
        if db.scalar(select(Organization)) is None:
            db.add(Organization(name=org_name or "My Business", tax_id_is_demo=False))
        db.add(User(email=email, full_name=name, role="admin", password_hash=hash_password(password)))
        db.commit()
    return email


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.manage", description="ERIS administration commands")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create-admin", help="create the organisation (if missing) and an admin user")
    c.add_argument("--email", required=True)
    c.add_argument("--name", default="Administrator")
    c.add_argument("--password")
    c.add_argument("--org", help="organisation name when the database has none yet")
    a = p.parse_args(argv)
    if a.cmd == "create-admin":
        password = a.password or getpass.getpass("Password for the new admin: ")
        try:
            email = create_admin(a.email, password, a.name, a.org)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Admin {email} created. Sign in, then add your outlets, products and users.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
