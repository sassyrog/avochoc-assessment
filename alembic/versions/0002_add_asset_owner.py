from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"


def upgrade():
    op.add_column("assets", sa.Column("owner_id", sa.Integer, nullable=False))
    op.create_foreign_key(
        "fk_assets_users",
        "assets",
        "users",
        ["owner_id"],
        ["id"],
    )
    op.create_index("ix_assets_owner_id", "assets", ["owner_id"])


def downgrade():
    op.drop_index("ix_assets_owner_id", table_name="assets")
    op.drop_constraint("fk_assets_users", "assets", type_="foreignkey")
    op.drop_column("assets", "owner_id")
