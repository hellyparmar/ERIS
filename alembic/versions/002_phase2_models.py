"""
Phase 2 Models Database Migration
Add invoice, khata, and GST management capabilities

Revision ID: 002_phase2_models
Revises: 001_initial_schema
Create Date: 2026-03-27

Adds Phase 2 database tables for:
- Business management
- GST-compliant invoicing
- Customer credit/khata management
- GST configuration
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_phase2_models'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Create Phase 2 database tables and extend existing ones"""

    # Add new columns to existing products table
    op.add_column('products', sa.Column('hsn_code', sa.String(8), nullable=True))

    # Add new columns to existing customers table
    op.add_column('customers', sa.Column('gst_number', sa.String(15), nullable=True))

    # Create inventory table
    op.create_table(
        'inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('outlet_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reserved_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_restocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['outlet_id'], ['outlets.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_inventory_outlet_product', 'outlet_id', 'product_id')
    )

    # Create businesses table
    op.create_table(
        'businesses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('gst_number', sa.String(15), unique=True, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # NOTE: invoices table is already created in 001_initial_schema, skip duplicate creation
    # Just create the remaining Phase 2 tables

    # Create invoice_line_items table
    op.create_table(
        'invoice_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('hsn_code', sa.String(10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit', sa.String(20), server_default='PCS', nullable=True),
        sa.Column('unit_rate', sa.Numeric(12, 2), nullable=False),
        sa.Column('line_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('cgst_amount', sa.Numeric(12, 2), server_default='0', nullable=True),
        sa.Column('sgst_amount', sa.Numeric(12, 2), server_default='0', nullable=True),
        sa.Column('igst_amount', sa.Numeric(12, 2), server_default='0', nullable=True),
        sa.Column('line_total', sa.Numeric(12, 2), nullable=False),
        sa.Column('discount_percentage', sa.Numeric(5, 2), server_default='0', nullable=True),
        sa.Column('discount_amount', sa.Numeric(12, 2), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create invoice_payments table
    op.create_table(
        'invoice_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create customer_credit table
    op.create_table(
        'customer_credit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('credit_limit', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('current_balance', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('credit_score', sa.Integer(), server_default='100', nullable=True),
        sa.Column('credit_rating', sa.String(20), server_default='GOOD', nullable=True),
        sa.Column('total_transactions', sa.Integer(), server_default='0', nullable=True),
        sa.Column('on_time_payments', sa.Integer(), server_default='0', nullable=True),
        sa.Column('late_payments', sa.Integer(), server_default='0', nullable=True),
        sa.Column('missed_payments', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_payment_date', sa.Date(), nullable=True),
        sa.Column('last_transaction_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_blocked', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', name='uq_customer_credit_customer_id')
    )

    # Create credit_transactions table
    op.create_table(
        'credit_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('credit_account_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('reference_id', sa.String(100), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_after', sa.Numeric(12, 2), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('payment_due', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['credit_account_id'], ['customer_credit.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create credit_reminders table
    op.create_table(
        'credit_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('credit_account_id', sa.Integer(), nullable=False),
        sa.Column('outstanding_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('days_overdue', sa.Integer(), server_default='0', nullable=True),
        sa.Column('reminder_type', sa.String(20), nullable=False),
        sa.Column('reminder_number', sa.Integer(), server_default='1', nullable=True),
        sa.Column('sent', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('message_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['credit_account_id'], ['customer_credit.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create gst_configuration table
    op.create_table(
        'gst_configuration',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('gst_number', sa.String(15), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=False),
        sa.Column('business_address', sa.Text(), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('pincode', sa.String(10), nullable=False),
        sa.Column('financial_year_start', sa.Date(), nullable=False),
        sa.Column('financial_year_end', sa.Date(), nullable=False),
        sa.Column('is_registered', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_composition', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('default_tax_rate', sa.Numeric(5, 2), server_default='18', nullable=True),
        sa.Column('enable_e_invoice', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('e_invoice_username', sa.String(255), nullable=True),
        sa.Column('e_invoice_password', sa.String(255), nullable=True),
        sa.Column('returns_filing_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', name='uq_gst_configuration_business_id')
    )


def downgrade():
    """Drop Phase 2 database tables and remove added columns"""

    # Drop new tables in reverse order (due to foreign key dependencies)
    op.drop_table('gst_configuration')
    op.drop_table('credit_reminders')
    op.drop_table('credit_transactions')
    op.drop_table('customer_credit')
    op.drop_table('invoice_payments')
    op.drop_table('invoice_line_items')
    # NOTE: invoices table is created in 001_initial_schema, don't drop it here
    op.drop_table('businesses')
    op.drop_table('inventory')

    # Remove added columns from existing tables
    op.drop_column('customers', 'gst_number')
    op.drop_column('products', 'hsn_code')
