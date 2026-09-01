"""create_notifications_table

Revision ID: b04608c6d528
Revises: f28595157a94
Create Date: 2026-06-18 12:03:11.414763
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b04608c6d528'
down_revision = 'f28595157a94'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('DROP TYPE IF EXISTS notificationtypeenum CASCADE')
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('outlet_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('low_stock', 'day_close_reminder', 'new_alert', 'system', name='notificationtypeenum'), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('link', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['outlet_id'], ['outlets.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_outlet_id'), 'notifications', ['outlet_id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_outlet_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.execute('DROP TYPE notificationtypeenum')
