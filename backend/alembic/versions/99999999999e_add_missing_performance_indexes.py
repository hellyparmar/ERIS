"""add missing performance indexes for high frequency queries

Revision ID: 99999999999e
Revises: 99999999999d
Create Date: 2026-09-21 16:00:00.000000

This migration adds genuine composite and foreign key indexes identified
during the production database query performance audit:
1. sales: (outlet_id, sale_date) - eliminates table scans on date-range queries per outlet
2. sales: (organization_id, sale_date) - optimizes multi-tenant organization dashboard & analytics
3. sale_items: (sale_id) - eliminates 730k+ row full table scan when joining sales to items
4. forecast_results: (outlet_id, product_id, created_at) - optimizes cached forecast retrieval & eliminates temp B-tree sort
5. alerts: (outlet_id, is_acknowledged) - accelerates unacknowledged alert filtering on dashboard
6. chat_messages: (user_id, created_at) - accelerates conversation history retrieval per user
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '99999999999e'
down_revision: Union[str, None] = '99999999999d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    def get_existing_indexes(table_name: str):
        try:
            return {ix['name'] for ix in inspector.get_indexes(table_name)}
        except Exception:
            return set()

    sales_indexes = get_existing_indexes('sales')
    if 'idx_sales_outlet_date' not in sales_indexes:
        op.create_index(
            'idx_sales_outlet_date',
            'sales',
            ['outlet_id', 'sale_date'],
            if_not_exists=True
        )
    if 'idx_sales_org_date' not in sales_indexes:
        op.create_index(
            'idx_sales_org_date',
            'sales',
            ['organization_id', 'sale_date'],
            if_not_exists=True
        )

    sale_items_indexes = get_existing_indexes('sale_items')
    if 'idx_sale_items_sale_id' not in sale_items_indexes:
        op.create_index(
            'idx_sale_items_sale_id',
            'sale_items',
            ['sale_id'],
            if_not_exists=True
        )

    forecast_results_indexes = get_existing_indexes('forecast_results')
    if 'idx_forecast_results_outlet_product_created' not in forecast_results_indexes:
        op.create_index(
            'idx_forecast_results_outlet_product_created',
            'forecast_results',
            ['outlet_id', 'product_id', 'created_at'],
            if_not_exists=True
        )

    alerts_indexes = get_existing_indexes('alerts')
    if 'idx_alerts_outlet_is_acknowledged' not in alerts_indexes:
        op.create_index(
            'idx_alerts_outlet_is_acknowledged',
            'alerts',
            ['outlet_id', 'is_acknowledged'],
            if_not_exists=True
        )

    chat_messages_indexes = get_existing_indexes('chat_messages')
    if 'idx_chat_messages_user_created_at' not in chat_messages_indexes:
        op.create_index(
            'idx_chat_messages_user_created_at',
            'chat_messages',
            ['user_id', 'created_at'],
            if_not_exists=True
        )


def downgrade() -> None:
    op.drop_index('idx_chat_messages_user_created_at', table_name='chat_messages', if_exists=True)
    op.drop_index('idx_alerts_outlet_is_acknowledged', table_name='alerts', if_exists=True)
    op.drop_index('idx_forecast_results_outlet_product_created', table_name='forecast_results', if_exists=True)
    op.drop_index('idx_sale_items_sale_id', table_name='sale_items', if_exists=True)
    op.drop_index('idx_sales_org_date', table_name='sales', if_exists=True)
    op.drop_index('idx_sales_outlet_date', table_name='sales', if_exists=True)
