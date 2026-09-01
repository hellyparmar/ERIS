"""simplified_role_system_and_outlet_access

Revision ID: ab696fc771ed
Revises: 0002_production_ready
Create Date: 2026-06-16 08:22:06.697454+00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab696fc771ed'
down_revision = '0002_production_ready'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create user_outlet_access table
    op.create_table(
        'user_outlet_access',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('outlet_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['outlet_id'], ['outlets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_outlet_access_id', 'user_outlet_access', ['id'], unique=False)

    # 2. Add outlet_id to users
    op.add_column('users', sa.Column('outlet_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_outlet_id_outlets', 'users', 'outlets', ['outlet_id'], ['id'], ondelete='SET NULL')

    # 3. Update existing roles in roles table
    connection = op.get_bind()

    # Ensure "super_admin" exists (rename superadmin -> super_admin)
    connection.execute(sa.text("UPDATE roles SET name = 'super_admin' WHERE name = 'superadmin'"))
    # Ensure "outlet_manager" exists (rename manager -> outlet_manager)
    connection.execute(sa.text("UPDATE roles SET name = 'outlet_manager' WHERE name = 'manager'"))

    # Insert "area_manager" role if not exists
    result = connection.execute(sa.text("SELECT id FROM roles WHERE name = 'area_manager'"))
    row = result.fetchone()
    if not row:
        connection.execute(sa.text(
            "INSERT INTO roles (name, description, is_system_role, is_active, created_at, updated_at) "
            "VALUES ('area_manager', 'Area Manager', false, true, NOW(), NOW())"
        ))

    # Get the role IDs
    role_ids = {}
    for rname in ['super_admin', 'area_manager', 'outlet_manager', 'analyst', 'staff']:
        res = connection.execute(sa.text(f"SELECT id FROM roles WHERE name = '{rname}'"))
        row = res.fetchone()
        if row:
            role_ids[rname] = row[0]

    # Map users with "analyst" or "staff" roles to "outlet_manager"
    outlet_manager_role_id = role_ids.get('outlet_manager')
    if outlet_manager_role_id:
        analyst_role_id = role_ids.get('analyst')
        staff_role_id = role_ids.get('staff')
        
        if analyst_role_id:
            connection.execute(sa.text(f"UPDATE users SET role_id = {outlet_manager_role_id} WHERE role_id = {analyst_role_id}"))
        if staff_role_id:
            connection.execute(sa.text(f"UPDATE users SET role_id = {outlet_manager_role_id} WHERE role_id = {staff_role_id}"))

    # 4. Migrate existing user outlets access from user_outlets to user_outlet_access
    # And populate the deprecated outlet_id field in users
    connection.execute(sa.text(
        "INSERT INTO user_outlet_access (user_id, outlet_id, created_at) "
        "SELECT user_id, outlet_id, NOW() FROM user_outlets"
    ))
    
    # Update users.outlet_id based on the migrated entries (select first outlet for each user)
    connection.execute(sa.text(
        "UPDATE users u SET outlet_id = ("
        "  SELECT outlet_id FROM user_outlet_access uoa "
        "  WHERE uoa.user_id = u.id "
        "  LIMIT 1"
        ") WHERE EXISTS ("
        "  SELECT 1 FROM user_outlet_access uoa "
        "  WHERE uoa.user_id = u.id"
        ")"
    ))

    # 5. Clean up old roles (delete staff and analyst roles)
    if role_ids.get('analyst'):
        connection.execute(sa.text(f"DELETE FROM roles WHERE id = {role_ids.get('analyst')}"))
    if role_ids.get('staff'):
        connection.execute(sa.text(f"DELETE FROM roles WHERE id = {role_ids.get('staff')}"))


def downgrade() -> None:
    # Recreate deleted roles and rollback changes if needed
    connection = op.get_bind()
    
    # Re-insert old roles if they do not exist
    for rname, desc in [('analyst', 'Data Analyst'), ('staff', 'Staff Member')]:
        res = connection.execute(sa.text(f"SELECT id FROM roles WHERE name = '{rname}'"))
        if not res.fetchone():
            connection.execute(sa.text(
                f"INSERT INTO roles (name, description, is_system_role, is_active, created_at, updated_at) "
                f"VALUES ('{rname}', '{desc}', false, true, NOW(), NOW())"
            ))

    # Rename super_admin -> superadmin, outlet_manager -> manager
    connection.execute(sa.text("UPDATE roles SET name = 'superadmin' WHERE name = 'super_admin'"))
    connection.execute(sa.text("UPDATE roles SET name = 'manager' WHERE name = 'outlet_manager'"))
    
    # Delete area_manager role
    connection.execute(sa.text("DELETE FROM roles WHERE name = 'area_manager'"))

    # Drop column and table
    op.drop_constraint('fk_users_outlet_id_outlets', 'users', type_='foreignkey')
    op.drop_column('users', 'outlet_id')
    op.drop_index('ix_user_outlet_access_id', table_name='user_outlet_access')
    op.drop_table('user_outlet_access')
