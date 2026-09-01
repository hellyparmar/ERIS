"""add_organization_id_to_core_models

Revision ID: 94ac9a572741
Revises: 950faf9b2113
Create Date: 2026-07-17 04:07:26.054765+00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94ac9a572741'
down_revision = '950faf9b2113'
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = [
        'products', 'inventory', 'suppliers', 'product_categories', 
        'sales', 'sale_items', 'credit_accounts', 'purchase_orders', 
        'purchase_order_items', 'stock_movements', 'customers'
    ]
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables_in_db = insp.get_table_names()

    for table in tables:
        if table in tables_in_db:
            columns = [c['name'] for c in insp.get_columns(table)]
            if 'organization_id' not in columns:
                op.add_column(table, sa.Column('organization_id', sa.Integer(), nullable=True))
                op.execute(f"UPDATE {table} SET organization_id = 1 WHERE organization_id IS NULL")
                op.alter_column(table, 'organization_id', existing_type=sa.Integer(), nullable=False)
                op.create_foreign_key(f"fk_{table}_org_id", table, 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
                op.create_index(f"idx_{table}_org_id", table, ['organization_id'])

def downgrade() -> None:
    tables = [
        'products', 'inventory', 'suppliers', 'product_categories', 
        'sales', 'sale_items', 'credit_accounts', 'purchase_orders', 
        'purchase_order_items', 'stock_movements', 'customers'
    ]
    for table in tables:
        try:
            op.drop_index(f"idx_{table}_org_id", table_name=table)
            op.drop_constraint(f"fk_{table}_org_id", table_name=table, type_='foreignkey')
            op.drop_column(table, 'organization_id')
        except Exception as e:
            pass
