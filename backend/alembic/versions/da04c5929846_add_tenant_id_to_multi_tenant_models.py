"""add_tenant_id_to_multi_tenant_models

Revision ID: da04c5929846
Revises: f28595157a94
Create Date: 2026-07-20 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'da04c5929846'
down_revision = '94ac9a572741'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Add tenant_id to organizations and backfill so we can FK to it with UUID
    op.add_column('organizations', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE organizations SET tenant_id = gen_random_uuid() WHERE tenant_id IS NULL")
    op.alter_column('organizations', 'tenant_id', nullable=False)
    op.create_unique_constraint('uq_organizations_tenant_id', 'organizations', ['tenant_id'])
    
    # 2. Add tenant_id to the 6 tables
    tables = ['outlets', 'products', 'inventory', 'sales', 'customers', 'invoices']
    for table in tables:
        op.add_column(table, sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
        
    # 3. Create a default organization for backfill if no orgs exist
    op.execute("""
        INSERT INTO organizations (name, tenant_id, is_active, is_deleted)
        SELECT 'Default Default', gen_random_uuid(), true, false
        WHERE NOT EXISTS (SELECT 1 FROM organizations);
    """)
    
    # Backfill tables
    for table in tables:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.execute(f"""
            UPDATE {table} 
            SET tenant_id = (SELECT tenant_id FROM organizations ORDER BY id LIMIT 1) 
            WHERE tenant_id IS NULL;
        """)
    
    # 4. Make tenant_id NOT NULL and add FK & RLS
    for table in tables:
        op.alter_column(table, 'tenant_id', nullable=False)
        op.create_foreign_key(f"fk_{table}_tenant_id", table, 'organizations', ['tenant_id'], ['tenant_id'])
        
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        # Apply the exact policy required by the prompt
        op.execute(f"CREATE POLICY {table}_tenant_isolation ON {table} USING (tenant_id = current_setting('app.current_tenant_id')::uuid);")
        
def downgrade() -> None:
    tables = ['outlets', 'products', 'inventory', 'sales', 'customers', 'invoices']
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.drop_constraint(f"fk_{table}_tenant_id", table, type_='foreignkey')
        op.drop_column(table, 'tenant_id')
    
    op.drop_constraint('uq_organizations_tenant_id', 'organizations', type_='unique')
    op.drop_column('organizations', 'tenant_id')
