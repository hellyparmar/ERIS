"""add supplier fields

Revision ID: 99999999999b
Revises: 99999999999a
Create Date: 2026-07-29 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99999999999b'
down_revision: Union[str, None] = '99999999999a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to suppliers table if they don't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('suppliers')]

    if 'avg_lead_time_days' not in columns:
        op.add_column('suppliers', sa.Column('avg_lead_time_days', sa.Integer(), nullable=True))
    if 'quality_rating' not in columns:
        op.add_column('suppliers', sa.Column('quality_rating', sa.Numeric(precision=3, scale=2), nullable=True))
    if 'on_time_delivery_rate' not in columns:
        op.add_column('suppliers', sa.Column('on_time_delivery_rate', sa.Numeric(precision=5, scale=2), nullable=True))
    if 'payment_terms_days' not in columns:
        op.add_column('suppliers', sa.Column('payment_terms_days', sa.Integer(), nullable=True))
    if 'outstanding_payable' not in columns:
        op.add_column('suppliers', sa.Column('outstanding_payable', sa.Numeric(precision=15, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('suppliers', 'outstanding_payable')
    op.drop_column('suppliers', 'payment_terms_days')
    op.drop_column('suppliers', 'on_time_delivery_rate')
    op.drop_column('suppliers', 'quality_rating')
    op.drop_column('suppliers', 'avg_lead_time_days')
