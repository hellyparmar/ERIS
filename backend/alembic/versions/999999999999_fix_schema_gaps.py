"""fix schema gaps

Revision ID: 999999999999
Revises: da04c5929846
Create Date: 2026-07-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision: str = '999999999999'
down_revision: Union[str, None] = '995b586cb536'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # 1. Add outlet_id to sales
    sales_columns = [c['name'] for c in inspector.get_columns('sales')]
    if 'outlet_id' not in sales_columns:
        op.add_column('sales', sa.Column('outlet_id', sa.Integer(), nullable=True))
        op.create_foreign_key('sales_outlet_id_fkey', 'sales', 'outlets', ['outlet_id'], ['id'], ondelete='CASCADE')
    
    # 2. Rename store_id to outlet_id in employees
    emp_columns = [c['name'] for c in inspector.get_columns('employees')]
    if 'store_id' in emp_columns and 'outlet_id' not in emp_columns:
        op.alter_column('employees', 'store_id', new_column_name='outlet_id')
        try:
            op.drop_constraint('employees_store_id_fkey', 'employees', type_='foreignkey')
        except Exception:
            pass
        op.create_foreign_key('employees_outlet_id_fkey', 'employees', 'outlets', ['outlet_id'], ['id'], ondelete='CASCADE')
    elif 'store_id' in emp_columns and 'outlet_id' in emp_columns:
        op.drop_column('employees', 'store_id')

def downgrade() -> None:
    pass
