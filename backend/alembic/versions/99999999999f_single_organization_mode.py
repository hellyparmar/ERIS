"""disable tenant RLS for the single-organization portfolio architecture

Revision ID: 99999999999f
Revises: 99999999999e
"""

from alembic import op


revision = "99999999999f"
down_revision = "99999999999e"
branch_labels = None
depends_on = None

TABLES = ("outlets", "products", "inventory", "sales", "customers", "invoices")


def upgrade() -> None:
    # Retain tenant_id columns temporarily so existing databases and generated
    # data remain readable. The canonical-schema phase can remove them after
    # all ORM references have been migrated to organization_id.
    for table in TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table} "
            "USING (tenant_id = current_setting('app.current_tenant_id')::uuid) "
            "WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid)"
        )
