"""add auth fields to users

Revision ID: 20260408_0004
Revises: 20260330_0003
Create Date: 2026-04-08 01:40:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260408_0004"
down_revision = "20260330_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=False, server_default="!"),
    )
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="analyst"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
