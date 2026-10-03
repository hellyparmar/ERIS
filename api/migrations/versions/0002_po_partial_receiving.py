"""Partial receiving of purchase orders: received quantity per line, 'partial' and 'closed' statuses.

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("purchase_order_items") as batch:
        batch.add_column(sa.Column("received_quantity", sa.Float(), nullable=False, server_default="0"))
    # before this revision a received order's quantity was overwritten with what arrived
    op.execute("""
        UPDATE purchase_order_items SET received_quantity = quantity
        WHERE order_id IN (SELECT id FROM purchase_orders WHERE status = 'received')
    """)


def downgrade() -> None:
    with op.batch_alter_table("purchase_order_items") as batch:
        batch.drop_column("received_quantity")
