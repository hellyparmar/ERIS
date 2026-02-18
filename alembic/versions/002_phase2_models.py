"""
Phase 2 Models Database Migration
Initial migration for Phase 2 database schema
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_phase2_models'
down_revision = '001_phase1_complete'  # Reference to Phase 1 migration
branch_labels = None
depends_on = None


def upgrade():
    """Create Phase 2 database tables"""
    
    # ==================== Invoices Table ====================
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('invoice_number', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('business_id', sa.String(100), nullable=False, index=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('customer_email', sa.String(255)),
        sa.Column('customer_phone', sa.String(20)),
        sa.Column('customer_gst_number', sa.String(15)),
        sa.Column('billing_address', sa.Text),
        sa.Column('shipping_address', sa.Text),
        sa.Column('invoice_date', sa.Date, nullable=False, index=True),
        sa.Column('due_date', sa.Date),
        sa.Column('total_taxable', sa.Numeric(15, 2), nullable=False),
        sa.Column('total_cgst', sa.Numeric(12, 2), default=0),
        sa.Column('total_sgst', sa.Numeric(12, 2), default=0),
        sa.Column('total_igst', sa.Numeric(12, 2), default=0),
        sa.Column('total_tax', sa.Numeric(15, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('payment_status', sa.String(20), default='UNPAID'),
        sa.Column('is_inter_state', sa.Boolean, default=False),
        sa.Column('payment_terms', sa.String(100)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index('idx_invoices_business_date', 'business_id', 'invoice_date'),
        sa.Index('idx_invoices_customer', 'customer_id'),
        sa.Index('idx_invoices_status', 'payment_status')
    )
    
    # ==================== Invoice Line Items Table ====================
    op.create_table(
        'invoice_line_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', sa.String(100), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('hsn_code', sa.String(8), nullable=False, index=True),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit_rate', sa.Numeric(15, 2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('discount_percentage', sa.Numeric(5, 2), default=0),
        sa.Column('line_subtotal', sa.Numeric(15, 2), nullable=False),
        sa.Column('line_tax', sa.Numeric(15, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(15, 2), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # ==================== Invoice Payments Table ====================
    op.create_table(
        'invoice_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('payment_date', sa.DateTime, nullable=False, index=True),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('reference_number', sa.String(100)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # ==================== Customer Credit Accounts Table ====================
    op.create_table(
        'customer_credit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('business_id', sa.String(100), nullable=False, index=True),
        sa.Column('customer_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('credit_limit', sa.Numeric(15, 2), nullable=False),
        sa.Column('used_credit', sa.Numeric(15, 2), default=0),
        sa.Column('payment_terms_days', sa.Integer, default=30),
        sa.Column('credit_score', sa.Integer, default=50),
        sa.Column('credit_status', sa.String(20), default='FAIR'),
        sa.Column('total_transactions', sa.Integer, default=0),
        sa.Column('on_time_payments', sa.Integer, default=0),
        sa.Column('late_payments', sa.Integer, default=0),
        sa.Column('missed_payments', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index('idx_credit_score', 'credit_score'),
        sa.Index('idx_credit_status', 'credit_status')
    )
    
    # ==================== Credit Transactions Table ====================
    op.create_table(
        'credit_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('customer_id', sa.String(100), sa.ForeignKey('customer_credit.customer_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transaction_type', sa.String(20), nullable=False),  # CREDIT or PAYMENT
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('invoice_id', sa.String(100)),
        sa.Column('reference_number', sa.String(100)),
        sa.Column('due_date', sa.Date),
        sa.Column('is_on_time', sa.Boolean, default=True),
        sa.Column('is_late', sa.Boolean, default=False),
        sa.Column('is_missed', sa.Boolean, default=False),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Index('idx_credit_trans_date', 'created_at'),
        sa.Index('idx_credit_trans_type', 'transaction_type')
    )
    
    # ==================== Credit Reminders Table ====================
    op.create_table(
        'credit_reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('customer_id', sa.String(100), sa.ForeignKey('customer_credit.customer_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('invoice_id', sa.String(100)),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('amount_due', sa.Numeric(15, 2), nullable=False),
        sa.Column('reminder_type', sa.String(20)),  # AUTO, MANUAL
        sa.Column('channels', sa.String(100)),  # SMS,EMAIL,WHATSAPP
        sa.Column('status', sa.String(20), default='PENDING'),  # PENDING, SENT, ACKNOWLEDGED
        sa.Column('sent_at', sa.DateTime),
        sa.Column('acknowledged_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_reminder_status', 'status'),
        sa.Index('idx_reminder_due_date', 'due_date')
    )
    
    # ==================== GST Configuration Table ====================
    op.create_table(
        'gst_configuration',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('business_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('gst_number', sa.String(15), nullable=False),
        sa.Column('state_code', sa.String(2), nullable=False),
        sa.Column('tax_0_enabled', sa.Boolean, default=True),
        sa.Column('tax_5_enabled', sa.Boolean, default=True),
        sa.Column('tax_12_enabled', sa.Boolean, default=True),
        sa.Column('tax_18_enabled', sa.Boolean, default=True),
        sa.Column('tax_28_enabled', sa.Boolean, default=True),
        sa.Column('default_tax_rate', sa.Numeric(5, 2), default=18),
        sa.Column('financial_year_start_month', sa.Integer, default=4),
        sa.Column('auto_calculate_gst', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )


def downgrade():
    """Drop Phase 2 database tables"""
    op.drop_table('gst_configuration')
    op.drop_table('credit_reminders')
    op.drop_table('credit_transactions')
    op.drop_table('customer_credit')
    op.drop_table('invoice_payments')
    op.drop_table('invoice_line_items')
    op.drop_table('invoices')
