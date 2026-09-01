"""add loyalty odoo and community models

Revision ID: 99999999999c
Revises: 99999999999b
Create Date: 2026-08-31 15:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99999999999c'
down_revision: Union[str, None] = '99999999999b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. loyalty_accounts
    if 'loyalty_accounts' not in tables:
        op.create_table(
            'loyalty_accounts',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id', ondelete='CASCADE'), unique=True, nullable=False),
            sa.Column('points_balance', sa.Integer(), default=0, nullable=False),
            sa.Column('tier', sa.String(length=50), default='bronze', nullable=False),
            sa.Column('lifetime_points', sa.Integer(), default=0, nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        )
        op.create_index('idx_loyalty_accounts_customer_id', 'loyalty_accounts', ['customer_id'])

    # 2. loyalty_points
    if 'loyalty_points' not in tables:
        op.create_table(
            'loyalty_points',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('account_id', sa.BigInteger(), sa.ForeignKey('loyalty_accounts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('points', sa.Integer(), nullable=False),
            sa.Column('transaction_type', sa.String(length=50), nullable=False),
            sa.Column('reference_id', sa.String(length=100), nullable=True),
            sa.Column('expiry_date', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('idx_loyalty_points_account_id', 'loyalty_points', ['account_id'])

    # 3. loyalty_bonuses
    if 'loyalty_bonuses' not in tables:
        op.create_table(
            'loyalty_bonuses',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('account_id', sa.BigInteger(), sa.ForeignKey('loyalty_accounts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('bonus_points', sa.Integer(), nullable=False),
            sa.Column('reason', sa.String(length=255), nullable=False),
            sa.Column('is_claimed', sa.Boolean(), default=False, nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
        )
        op.create_index('idx_loyalty_bonuses_account_id', 'loyalty_bonuses', ['account_id'])

    # 4. odoo_configs
    if 'odoo_configs' not in tables:
        op.create_table(
            'odoo_configs',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), default=1, nullable=False),
            sa.Column('url', sa.String(length=500), nullable=False),
            sa.Column('database_name', sa.String(length=200), nullable=False),
            sa.Column('username', sa.String(length=200), nullable=False),
            sa.Column('api_key', sa.Text(), nullable=False),
            sa.Column('sync_products', sa.Boolean(), default=True, nullable=False),
            sa.Column('sync_customers', sa.Boolean(), default=True, nullable=False),
            sa.Column('sync_invoices', sa.Boolean(), default=True, nullable=False),
            sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
            sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        )
        op.create_index('idx_odoo_configs_org_id', 'odoo_configs', ['organization_id'])

    # 5. community_listings
    if 'community_listings' not in tables:
        op.create_table(
            'community_listings',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), default=1, nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=100), default='general', nullable=False),
            sa.Column('contact_name', sa.String(length=150), nullable=True),
            sa.Column('contact_info', sa.String(length=255), nullable=True),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        )
        op.create_index('idx_community_listings_org_id', 'community_listings', ['organization_id'])


def downgrade() -> None:
    op.drop_table('community_listings')
    op.drop_table('odoo_configs')
    op.drop_table('loyalty_bonuses')
    op.drop_table('loyalty_points')
    op.drop_table('loyalty_accounts')
