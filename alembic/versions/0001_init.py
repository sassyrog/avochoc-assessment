from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, unique=True),
        sa.Column("hashed_password", sa.String),
    )
    op.create_table(
        "assets",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String),
        sa.Column("type", sa.String),
        sa.Column("description", sa.Text),
    )


def downgrade():
    op.drop_table("assets")
    op.drop_table("users")
