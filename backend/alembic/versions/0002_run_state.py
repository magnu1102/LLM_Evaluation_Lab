"""add evaluation_runs.state

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-07
"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing rows are by definition complete (POST /runs used to block until done),
    # so backfill them as "completed". New rows are inserted as "pending".
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "state",
            sa.String(length=16),
            nullable=False,
            server_default="completed",
        ),
    )


def downgrade() -> None:
    op.drop_column("evaluation_runs", "state")
