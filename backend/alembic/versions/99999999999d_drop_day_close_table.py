"""drop day close table

Revision ID: 99999999999d
Revises: 99999999999c
Create Date: 2026-09-01 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99999999999d'
down_revision: Union[str, None] = '99999999999c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'day_close' in tables:
        op.drop_table('day_close')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'day_close' not in tables:
        op.create_table(
            'day_close',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('outlet_id', sa.Integer(), sa.ForeignKey('outlets.id'), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('opening_float', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('closing_float', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('expected_cash', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('physical_cash', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('variance', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('reconciliation_status', sa.String(20), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('opened_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('closed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        )
