"""add playbook fields to incidents

Revision ID: 20260330_0002
Revises: 20260330_0001
Create Date: 2026-03-30 00:30:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260330_0002"
down_revision = "20260330_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("playbook_status", sa.String(length=50), nullable=False, server_default="pending"),
    )
    op.add_column("incidents", sa.Column("playbook_result", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("playbook_last_run_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("incidents", "playbook_last_run_at")
    op.drop_column("incidents", "playbook_result")
    op.drop_column("incidents", "playbook_status")
