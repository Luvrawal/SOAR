"""create playbook executions table

Revision ID: 20260330_0003
Revises: 20260330_0002
Create Date: 2026-03-30 01:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260330_0003"
down_revision = "20260330_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playbook_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("playbook_name", sa.String(length=100), nullable=False, server_default="default_triage"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="running"),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name=op.f("fk_playbook_executions_incident_id_incidents")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_playbook_executions")),
    )
    op.create_index(op.f("ix_playbook_executions_id"), "playbook_executions", ["id"], unique=False)
    op.create_index(op.f("ix_playbook_executions_incident_id"), "playbook_executions", ["incident_id"], unique=False)
    op.create_index(op.f("ix_playbook_executions_task_id"), "playbook_executions", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_playbook_executions_task_id"), table_name="playbook_executions")
    op.drop_index(op.f("ix_playbook_executions_incident_id"), table_name="playbook_executions")
    op.drop_index(op.f("ix_playbook_executions_id"), table_name="playbook_executions")
    op.drop_table("playbook_executions")
