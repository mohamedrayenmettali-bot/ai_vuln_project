"""Add persistent auth, notifications, and dashboard state

Revision ID: 9b7f4c2e1a8d
Revises: 4ef91d35fda0
Create Date: 2026-05-04 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b7f4c2e1a8d"
down_revision: Union[str, Sequence[str], None] = "4ef91d35fda0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("finding_id", sa.String(length=36), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_read_at", "notifications", ["read_at"], unique=False)
    op.create_index("ix_notifications_type", "notifications", ["type"], unique=False)

    op.create_table(
        "project_integration_settings",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("jira_url", sa.Text(), nullable=False),
        sa.Column("project_key", sa.String(length=64), nullable=False),
        sa.Column("api_token", sa.Text(), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("default_issue_type", sa.String(length=64), nullable=False),
        sa.Column("auto_critical", sa.Boolean(), nullable=False),
        sa.Column("auto_high_ai", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id"),
    )

    op.create_table(
        "finding_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("finding_id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finding_events_finding_id", "finding_events", ["finding_id"], unique=False)
    op.create_index("ix_finding_events_created_at", "finding_events", ["created_at"], unique=False)

    op.add_column("findings", sa.Column("epss_score", sa.Float(), nullable=True))
    op.add_column("findings", sa.Column("epss_percentile", sa.Float(), nullable=True))
    op.add_column("findings", sa.Column("scanner", sa.String(length=100), nullable=True))
    op.add_column("findings", sa.Column("source", sa.String(length=100), nullable=True, server_default=sa.text("'manual'")))
    op.add_column("findings", sa.Column("external_id", sa.String(length=100), nullable=True))
    op.create_index("ix_findings_external_id", "findings", ["external_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_findings_external_id", table_name="findings")
    op.drop_column("findings", "external_id")
    op.drop_column("findings", "source")
    op.drop_column("findings", "scanner")
    op.drop_column("findings", "epss_percentile")
    op.drop_column("findings", "epss_score")

    op.drop_index("ix_finding_events_created_at", table_name="finding_events")
    op.drop_index("ix_finding_events_finding_id", table_name="finding_events")
    op.drop_table("finding_events")

    op.drop_table("project_integration_settings")

    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_read_at", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_token_hash", table_name="auth_sessions")
    op.drop_table("auth_sessions")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
