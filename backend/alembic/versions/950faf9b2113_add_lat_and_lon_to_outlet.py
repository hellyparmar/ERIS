"""Add lat and lon to Outlet

Revision ID: 950faf9b2113
Revises: b04608c6d528
Create Date: 2026-07-16 08:57:01.099090+00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '950faf9b2113'
down_revision = 'b04608c6d528'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    columns = [c['name'] for c in insp.get_columns('outlets')]
    if 'latitude' not in columns:
        op.add_column('outlets', sa.Column('latitude', sa.Float(), nullable=True))
    if 'longitude' not in columns:
        op.add_column('outlets', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('outlets', 'longitude')
    op.drop_column('outlets', 'latitude')
