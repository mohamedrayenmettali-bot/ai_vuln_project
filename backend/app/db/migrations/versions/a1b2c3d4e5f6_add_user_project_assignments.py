"""Add user_project_assignments table

Revision ID: a1b2c3d4e5f6
Revises: f0c8b9f3912d
Create Date: 2026-05-06 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f0c8b9f3912d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_project_assignments",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "project_id"),
    )
    op.create_index("ix_user_project_assignments_user_id", "user_project_assignments", ["user_id"], unique=False)
    op.create_index("ix_user_project_assignments_project_id", "user_project_assignments", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_project_assignments_project_id", table_name="user_project_assignments")
    op.drop_index("ix_user_project_assignments_user_id", table_name="user_project_assignments")
    op.drop_table("user_project_assignments")
