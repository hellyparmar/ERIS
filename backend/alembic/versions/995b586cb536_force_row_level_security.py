"""force_row_level_security

Revision ID: 995b586cb536
Revises: da04c5929846
Create Date: 2026-07-26 09:29:16.566700
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '995b586cb536'
down_revision = 'da04c5929846'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE outlets FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE products FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE inventory FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE sales FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE customers FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE invoices FORCE ROW LEVEL SECURITY;")

def downgrade() -> None:
    op.execute("ALTER TABLE outlets NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE products NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE inventory NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE sales NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE customers NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE invoices NO FORCE ROW LEVEL SECURITY;")
