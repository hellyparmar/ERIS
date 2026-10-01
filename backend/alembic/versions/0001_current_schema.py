"""Current ERIS schema baseline.

Revision ID: 0001_current_schema
Revises: None

The prototype migration history was consolidated before the portfolio release.
Existing prototype databases must be recreated or stamped only after their schema
has been reconciled with this baseline.
"""

from alembic import op

from app.models import Base


revision = "0001_current_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
