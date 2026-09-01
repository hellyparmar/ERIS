"""convert_all_primary_keys_to_uuid

Revision ID: 459541e7af7d
Revises: 002_phase2_models
Create Date: 2026-04-08 13:17:53.906378
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '459541e7af7d'
down_revision = '002_phase2_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert all primary keys from Integer to UUID with server-side generation"""
    # NOTE: This migration is complex and has dependencies on specific table/FK states
    # For now, skip UUID conversion and use integer PKs
    return
    
    # PHASE 1: Drop ALL foreign key constraints to free up parent tables
    # Drop FKs referencing users
    op.drop_constraint('user_outlets_user_id_fkey', 'user_outlets', type_='foreignkey')
    op.drop_constraint('sales_user_id_fkey', 'sales', type_='foreignkey')
    op.drop_constraint('alerts_user_id_fkey', 'alerts', type_='foreignkey')
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')

    # Drop FKs referencing outlets
    op.drop_constraint('user_outlets_outlet_id_fkey', 'user_outlets', type_='foreignkey')
    op.drop_constraint('employees_outlet_id_fkey', 'employees', type_='foreignkey')
    op.drop_constraint('stock_levels_outlet_id_fkey', 'stock_levels', type_='foreignkey')
    op.drop_constraint('inventory_movements_outlet_id_fkey', 'inventory_movements', type_='foreignkey')
    op.drop_constraint('sales_outlet_id_fkey', 'sales', type_='foreignkey')
    op.drop_constraint('alerts_outlet_id_fkey', 'alerts', type_='foreignkey')
    op.drop_constraint('forecast_models_outlet_id_fkey', 'forecast_models', type_='foreignkey')

    # Drop FKs referencing organizations
    op.drop_constraint('users_organization_id_fkey', 'users', type_='foreignkey')
    op.drop_constraint('outlets_organization_id_fkey', 'outlets', type_='foreignkey')
    op.drop_constraint('customers_organization_id_fkey', 'customers', type_='foreignkey')
    op.drop_constraint('suppliers_organization_id_fkey', 'suppliers', type_='foreignkey')
    op.drop_constraint('categories_organization_id_fkey', 'categories', type_='foreignkey')
    op.drop_constraint('products_organization_id_fkey', 'products', type_='foreignkey')

    # Drop FKs referencing suppliers
    op.drop_constraint('products_supplier_id_fkey', 'products', type_='foreignkey')

    # Drop FKs referencing products
    op.drop_constraint('stock_levels_product_id_fkey', 'stock_levels', type_='foreignkey')
    op.drop_constraint('inventory_movements_product_id_fkey', 'inventory_movements', type_='foreignkey')
    op.drop_constraint('sale_items_product_id_fkey', 'sale_items', type_='foreignkey')
    op.drop_constraint('alerts_product_id_fkey', 'alerts', type_='foreignkey')
    op.drop_constraint('forecast_models_product_id_fkey', 'forecast_models', type_='foreignkey')

    # PHASE 2: Convert ALL child table FK columns to UUID (in parallel where safe)
    # Convert user_id columns in child tables
    op.add_column('user_outlets', sa.Column('user_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE user_outlets SET user_id_new = gen_random_uuid() WHERE user_id_new IS NULL')
    op.execute('ALTER TABLE user_outlets DROP COLUMN user_id')
    op.execute('ALTER TABLE user_outlets RENAME COLUMN user_id_new TO user_id')

    op.add_column('sales', sa.Column('user_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE sales SET user_id_new = gen_random_uuid() WHERE user_id_new IS NULL')
    op.execute('ALTER TABLE sales DROP COLUMN user_id')
    op.execute('ALTER TABLE sales RENAME COLUMN user_id_new TO user_id')

    op.add_column('alerts', sa.Column('user_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE alerts SET user_id_new = gen_random_uuid() WHERE user_id_new IS NULL')
    op.execute('ALTER TABLE alerts DROP COLUMN user_id')
    op.execute('ALTER TABLE alerts RENAME COLUMN user_id_new TO user_id')

    op.add_column('audit_logs', sa.Column('user_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE audit_logs SET user_id_new = gen_random_uuid() WHERE user_id_new IS NULL')
    op.execute('ALTER TABLE audit_logs DROP COLUMN user_id')
    op.execute('ALTER TABLE audit_logs RENAME COLUMN user_id_new TO user_id')

    # Convert outlet_id columns in child tables
    op.add_column('user_outlets', sa.Column('outlet_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE user_outlets SET outlet_id_new = gen_random_uuid() WHERE outlet_id_new IS NULL')
    op.execute('ALTER TABLE user_outlets DROP COLUMN outlet_id')
    op.execute('ALTER TABLE user_outlets RENAME COLUMN outlet_id_new TO outlet_id')

    op.add_column('employees', sa.Column('outlet_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE employees SET outlet_id_new = gen_random_uuid() WHERE outlet_id_new IS NULL')
    op.execute('ALTER TABLE employees DROP COLUMN outlet_id')
    op.execute('ALTER TABLE employees RENAME COLUMN outlet_id_new TO outlet_id')

    op.add_column('stock_levels', sa.Column('outlet_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE stock_levels SET outlet_id_new = gen_random_uuid() WHERE outlet_id_new IS NULL')
    op.execute('ALTER TABLE stock_levels DROP COLUMN outlet_id')
    op.execute('ALTER TABLE stock_levels RENAME COLUMN outlet_id_new TO outlet_id')

    op.add_column('inventory_movements', sa.Column('outlet_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE inventory_movements SET outlet_id_new = gen_random_uuid() WHERE outlet_id_new IS NULL')
    op.execute('ALTER TABLE inventory_movements DROP COLUMN outlet_id')
    op.execute('ALTER TABLE inventory_movements RENAME COLUMN outlet_id_new TO outlet_id')

    op.add_column('sales', sa.Column('outlet_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE sales SET outlet_id_new = gen_random_uuid() WHERE outlet_id_new IS NULL')
    op.execute('ALTER TABLE sales DROP COLUMN outlet_id')
    op.execute('ALTER TABLE sales RENAME COLUMN outlet_id_new TO outlet_id')

    op.add_column('alerts', sa.Column('outlet_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE alerts SET outlet_id_new = gen_random_uuid() WHERE outlet_id_new IS NULL')
    op.execute('ALTER TABLE alerts DROP COLUMN outlet_id')
    op.execute('ALTER TABLE alerts RENAME COLUMN outlet_id_new TO outlet_id')

    op.add_column('forecast_models', sa.Column('outlet_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE forecast_models SET outlet_id_new = gen_random_uuid() WHERE outlet_id_new IS NULL')
    op.execute('ALTER TABLE forecast_models DROP COLUMN outlet_id')
    op.execute('ALTER TABLE forecast_models RENAME COLUMN outlet_id_new TO outlet_id')

    # Convert organization_id columns in child tables
    op.add_column('users', sa.Column('organization_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE users SET organization_id_new = gen_random_uuid() WHERE organization_id_new IS NULL')
    op.execute('ALTER TABLE users DROP COLUMN organization_id')
    op.execute('ALTER TABLE users RENAME COLUMN organization_id_new TO organization_id')

    op.add_column('outlets', sa.Column('organization_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE outlets SET organization_id_new = gen_random_uuid() WHERE organization_id_new IS NULL')
    op.execute('ALTER TABLE outlets DROP COLUMN organization_id')
    op.execute('ALTER TABLE outlets RENAME COLUMN organization_id_new TO organization_id')

    op.add_column('customers', sa.Column('organization_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE customers SET organization_id_new = gen_random_uuid() WHERE organization_id_new IS NULL')
    op.execute('ALTER TABLE customers DROP COLUMN organization_id')
    op.execute('ALTER TABLE customers RENAME COLUMN organization_id_new TO organization_id')

    op.add_column('suppliers', sa.Column('organization_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE suppliers SET organization_id_new = gen_random_uuid() WHERE organization_id_new IS NULL')
    op.execute('ALTER TABLE suppliers DROP COLUMN organization_id')
    op.execute('ALTER TABLE suppliers RENAME COLUMN organization_id_new TO organization_id')

    op.add_column('categories', sa.Column('organization_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE categories SET organization_id_new = gen_random_uuid() WHERE organization_id_new IS NULL')
    op.execute('ALTER TABLE categories DROP COLUMN organization_id')
    op.execute('ALTER TABLE categories RENAME COLUMN organization_id_new TO organization_id')

    op.add_column('products', sa.Column('organization_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE products SET organization_id_new = gen_random_uuid() WHERE organization_id_new IS NULL')
    op.execute('ALTER TABLE products DROP COLUMN organization_id')
    op.execute('ALTER TABLE products RENAME COLUMN organization_id_new TO organization_id')

    # Convert supplier_id column in products
    op.add_column('products', sa.Column('supplier_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE products SET supplier_id_new = gen_random_uuid() WHERE supplier_id_new IS NULL')
    op.execute('ALTER TABLE products DROP COLUMN supplier_id')
    op.execute('ALTER TABLE products RENAME COLUMN supplier_id_new TO supplier_id')

    # Convert product_id columns in child tables
    op.add_column('stock_levels', sa.Column('product_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE stock_levels SET product_id_new = gen_random_uuid() WHERE product_id_new IS NULL')
    op.execute('ALTER TABLE stock_levels DROP COLUMN product_id')
    op.execute('ALTER TABLE stock_levels RENAME COLUMN product_id_new TO product_id')

    op.add_column('inventory_movements', sa.Column('product_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE inventory_movements SET product_id_new = gen_random_uuid() WHERE product_id_new IS NULL')
    op.execute('ALTER TABLE inventory_movements DROP COLUMN product_id')
    op.execute('ALTER TABLE inventory_movements RENAME COLUMN product_id_new TO product_id')

    op.add_column('sale_items', sa.Column('product_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE sale_items SET product_id_new = gen_random_uuid() WHERE product_id_new IS NULL')
    op.execute('ALTER TABLE sale_items DROP COLUMN product_id')
    op.execute('ALTER TABLE sale_items RENAME COLUMN product_id_new TO product_id')

    op.add_column('alerts', sa.Column('product_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE alerts SET product_id_new = gen_random_uuid() WHERE product_id_new IS NULL')
    op.execute('ALTER TABLE alerts DROP COLUMN product_id')
    op.execute('ALTER TABLE alerts RENAME COLUMN product_id_new TO product_id')

    op.add_column('forecast_models', sa.Column('product_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE forecast_models SET product_id_new = gen_random_uuid() WHERE product_id_new IS NULL')
    op.execute('ALTER TABLE forecast_models DROP COLUMN product_id')
    op.execute('ALTER TABLE forecast_models RENAME COLUMN product_id_new TO product_id')

    # Convert acknowledged_by in alerts (only if column exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'alerts' AND column_name = 'acknowledged_by'
            ) THEN
                ALTER TABLE alerts ADD COLUMN acknowledged_by_new UUID;
                UPDATE alerts SET acknowledged_by_new = gen_random_uuid() WHERE acknowledged_by_new IS NULL;
                ALTER TABLE alerts DROP COLUMN acknowledged_by;
                ALTER TABLE alerts RENAME COLUMN acknowledged_by_new TO acknowledged_by;
            END IF;
        END $$;
    """)

    # Convert inventory FK columns
    op.add_column('inventory', sa.Column('outlet_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE inventory SET outlet_id_new = gen_random_uuid() WHERE outlet_id_new IS NULL')
    op.execute('ALTER TABLE inventory DROP COLUMN outlet_id')
    op.execute('ALTER TABLE inventory RENAME COLUMN outlet_id_new TO outlet_id')

    op.add_column('inventory', sa.Column('product_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute('UPDATE inventory SET product_id_new = gen_random_uuid() WHERE product_id_new IS NULL')
    op.execute('ALTER TABLE inventory DROP COLUMN product_id')
    op.execute('ALTER TABLE inventory RENAME COLUMN product_id_new TO product_id')

    # PHASE 3: Convert all primary keys to UUID
    # Convert users PK
    op.add_column('users', sa.Column('id_new', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.execute('UPDATE users SET id_new = gen_random_uuid() WHERE id_new IS NULL')
    op.drop_constraint('users_pkey', 'users', type_='primary')
    op.execute('ALTER TABLE users RENAME COLUMN id TO old_id')
    op.execute('ALTER TABLE users RENAME COLUMN id_new TO id')
    op.create_primary_key('users_pkey', 'users', ['id'])

    # Convert outlets PK
    op.add_column('outlets', sa.Column('id_new', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.execute('UPDATE outlets SET id_new = gen_random_uuid() WHERE id_new IS NULL')
    op.drop_constraint('outlets_pkey', 'outlets', type_='primary')
    op.execute('ALTER TABLE outlets RENAME COLUMN id TO old_id')
    op.execute('ALTER TABLE outlets RENAME COLUMN id_new TO id')
    op.create_primary_key('outlets_pkey', 'outlets', ['id'])

    # Convert organizations PK
    op.add_column('organizations', sa.Column('id_new', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.execute('UPDATE organizations SET id_new = gen_random_uuid() WHERE id_new IS NULL')
    op.drop_constraint('organizations_pkey', 'organizations', type_='primary')
    op.execute('ALTER TABLE organizations RENAME COLUMN id TO old_id')
    op.execute('ALTER TABLE organizations RENAME COLUMN id_new TO id')
    op.create_primary_key('organizations_pkey', 'organizations', ['id'])

    # Convert suppliers PK
    op.add_column('suppliers', sa.Column('id_new', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.execute('UPDATE suppliers SET id_new = gen_random_uuid() WHERE id_new IS NULL')
    op.drop_constraint('suppliers_pkey', 'suppliers', type_='primary')
    op.execute('ALTER TABLE suppliers RENAME COLUMN id TO old_id')
    op.execute('ALTER TABLE suppliers RENAME COLUMN id_new TO id')
    op.create_primary_key('suppliers_pkey', 'suppliers', ['id'])

    # Convert products PK
    op.add_column('products', sa.Column('id_new', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.execute('UPDATE products SET id_new = gen_random_uuid() WHERE id_new IS NULL')
    op.drop_constraint('products_pkey', 'products', type_='primary')
    op.execute('ALTER TABLE products RENAME COLUMN id TO old_id')
    op.execute('ALTER TABLE products RENAME COLUMN id_new TO id')
    op.create_primary_key('products_pkey', 'products', ['id'])

    # Convert inventory PK
    op.add_column('inventory', sa.Column('id_new', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.execute('UPDATE inventory SET id_new = gen_random_uuid() WHERE id_new IS NULL')
    op.drop_constraint('inventory_pkey', 'inventory', type_='primary')
    op.execute('ALTER TABLE inventory RENAME COLUMN id TO old_id')
    op.execute('ALTER TABLE inventory RENAME COLUMN id_new TO id')
    op.create_primary_key('inventory_pkey', 'inventory', ['id'])

    # Convert alerts PK
    op.add_column('alerts', sa.Column('id_new', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.execute('UPDATE alerts SET id_new = gen_random_uuid() WHERE id_new IS NULL')
    op.drop_constraint('alerts_pkey', 'alerts', type_='primary')
    op.execute('ALTER TABLE alerts RENAME COLUMN id TO old_id')
    op.execute('ALTER TABLE alerts RENAME COLUMN id_new TO id')
    op.create_primary_key('alerts_pkey', 'alerts', ['id'])

    # PHASE 4: Recreate all foreign key constraints
    op.create_foreign_key('user_outlets_user_id_fkey', 'user_outlets', 'users', ['user_id'], ['id'])
    op.create_foreign_key('sales_user_id_fkey', 'sales', 'users', ['user_id'], ['id'])
    op.create_foreign_key('alerts_user_id_fkey', 'alerts', 'users', ['user_id'], ['id'])
    op.create_foreign_key('audit_logs_user_id_fkey', 'audit_logs', 'users', ['user_id'], ['id'])

    op.create_foreign_key('user_outlets_outlet_id_fkey', 'user_outlets', 'outlets', ['outlet_id'], ['id'])
    op.create_foreign_key('employees_outlet_id_fkey', 'employees', 'outlets', ['outlet_id'], ['id'])
    op.create_foreign_key('stock_levels_outlet_id_fkey', 'stock_levels', 'outlets', ['outlet_id'], ['id'])
    op.create_foreign_key('inventory_movements_outlet_id_fkey', 'inventory_movements', 'outlets', ['outlet_id'], ['id'])
    op.create_foreign_key('sales_outlet_id_fkey', 'sales', 'outlets', ['outlet_id'], ['id'])
    op.create_foreign_key('alerts_outlet_id_fkey', 'alerts', 'outlets', ['outlet_id'], ['id'])
    op.create_foreign_key('forecast_models_outlet_id_fkey', 'forecast_models', 'outlets', ['outlet_id'], ['id'])

    op.create_foreign_key('users_organization_id_fkey', 'users', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('outlets_organization_id_fkey', 'outlets', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('customers_organization_id_fkey', 'customers', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('suppliers_organization_id_fkey', 'suppliers', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('categories_organization_id_fkey', 'categories', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('products_organization_id_fkey', 'products', 'organizations', ['organization_id'], ['id'])

    op.create_foreign_key('products_supplier_id_fkey', 'products', 'suppliers', ['supplier_id'], ['id'])

    op.create_foreign_key('stock_levels_product_id_fkey', 'stock_levels', 'products', ['product_id'], ['id'])
    op.create_foreign_key('inventory_movements_product_id_fkey', 'inventory_movements', 'products', ['product_id'], ['id'])
    op.create_foreign_key('sale_items_product_id_fkey', 'sale_items', 'products', ['product_id'], ['id'])
    op.create_foreign_key('alerts_product_id_fkey', 'alerts', 'products', ['product_id'], ['id'])
    op.create_foreign_key('forecast_models_product_id_fkey', 'forecast_models', 'products', ['product_id'], ['id'])


def downgrade() -> None:
    """Convert all primary keys back from UUID to Integer - NOT IMPLEMENTED"""
    pass
