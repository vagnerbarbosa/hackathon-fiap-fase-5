"""Cria tabela de jobs

Revision ID: 001
Revises:
Create Date: 2026-07-09 20:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("input_image_path", sa.String(500), nullable=False),
        sa.Column("output_report_path", sa.String(500), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Cria índice no status para queries mais rápidas
    op.create_index("ix_jobs_status", "jobs", ["status"])

    # Cria índice no created_at para ordenação
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_jobs_created_at", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_table("jobs")
