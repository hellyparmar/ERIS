"""add communication and audit models

Revision ID: 99999999999a
Revises: 999999999999
Create Date: 2026-07-28 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '99999999999a'
down_revision: Union[str, None] = '999999999999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # create audit_log_entries
    op.create_table(
        'audit_log_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_entries_id'), 'audit_log_entries', ['id'], unique=False)

    # create messages
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.String(length=200), nullable=True),
        sa.Column('sender_type', sa.String(length=50), nullable=True),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('recipient_type', sa.String(length=50), nullable=True),
        sa.Column('recipient_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.Enum('IN_APP', 'EMAIL', 'SMS', name='messagechannel'), nullable=True),
        sa.Column('subject', sa.String(length=200), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('related_entity_type', sa.String(length=50), nullable=True),
        sa.Column('related_entity_id', sa.Integer(), nullable=True),
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_thread_id'), 'messages', ['thread_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_messages_thread_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    
    op.drop_index(op.f('ix_audit_log_entries_id'), table_name='audit_log_entries')
    op.drop_table('audit_log_entries')
    
    # Drop enum
    sa.Enum('IN_APP', 'EMAIL', 'SMS', name='messagechannel').drop(op.get_bind())
