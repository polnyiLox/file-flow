"""Create files table."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "files",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("original_name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("original_key", sa.String(), nullable=False),
        sa.Column("thumbnail_key", sa.String(), nullable=True),
        sa.Column("status", sa.Enum("UPLOADED", "PROCESSING", "READY", "FAILED", name="filestatuses"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("files")
    sa.Enum(name="filestatuses").drop(op.get_bind())
