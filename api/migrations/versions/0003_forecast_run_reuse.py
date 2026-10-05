"""Fast answers on small servers: reusable forecast results and a response cache for analytics pages.

Forecast runs keep a compact copy of their result so the same forecast can be served again without refitting;
response_cache stores analytics answers per user, request and data version.

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("forecast_runs") as batch:
        # date-free result (model choice, back-test, forecast values) + fingerprint of the input series
        batch.add_column(sa.Column("core", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("fingerprint", sa.String(64), nullable=True))
    op.create_index("ix_forecast_runs_lookup", "forecast_runs", ["scope", "target", "data_end", "fingerprint"])
    op.create_table(
        "response_cache",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("version", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("response_cache")
    op.drop_index("ix_forecast_runs_lookup", table_name="forecast_runs")
    with op.batch_alter_table("forecast_runs") as batch:
        batch.drop_column("fingerprint")
        batch.drop_column("core")
