"""Restaurant model: menu items and ingredients, recipes, covers and dine-in / takeaway / delivery channels.

products.kind separates menu items (sold) from ingredients (stocked); recipes link them. sales.covers records the
guests on a dine-in bill. The old "in_store" channel becomes "dine_in". An index on sales.sold_at keeps the bill
list fast.

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.add_column(sa.Column("kind", sa.String(12), nullable=False, server_default="menu"))
    op.create_index("ix_products_kind", "products", ["kind"])
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("menu_item_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.UniqueConstraint("menu_item_id", "ingredient_id"),
    )
    op.create_index("ix_recipes_menu_item_id", "recipes", ["menu_item_id"])
    op.create_index("ix_recipes_ingredient_id", "recipes", ["ingredient_id"])
    with op.batch_alter_table("sales") as batch:
        batch.add_column(sa.Column("covers", sa.Integer(), nullable=True))
    op.create_index("ix_sales_sold_at", "sales", ["sold_at", "id"])
    op.execute("UPDATE sales SET channel = 'dine_in' WHERE channel = 'in_store'")


def downgrade() -> None:
    op.execute("UPDATE sales SET channel = 'in_store' WHERE channel IN ('dine_in', 'takeaway')")
    op.drop_index("ix_sales_sold_at", table_name="sales")
    with op.batch_alter_table("sales") as batch:
        batch.drop_column("covers")
    op.drop_table("recipes")
    op.drop_index("ix_products_kind", table_name="products")
    with op.batch_alter_table("products") as batch:
        batch.drop_column("kind")
