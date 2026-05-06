"""Add password reset tokens and finding sync metadata

Revision ID: f0c8b9f3912d
Revises: 9b7f4c2e1a8d
Create Date: 2026-05-05 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f0c8b9f3912d"
down_revision: Union[str, Sequence[str], None] = "9b7f4c2e1a8d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"], unique=False)
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)

    op.add_column("findings", sa.Column("dedupe_key", sa.String(length=128), nullable=True))
    op.add_column("findings", sa.Column("external_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("findings", sa.Column("external_payload_hash", sa.String(length=64), nullable=True))
    op.add_column("findings", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("findings", sa.Column("local_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("findings", sa.Column("sync_conflict", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_index("ix_findings_dedupe_key", "findings", ["dedupe_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_findings_dedupe_key", table_name="findings")
    op.drop_column("findings", "sync_conflict")
    op.drop_column("findings", "local_updated_at")
    op.drop_column("findings", "last_synced_at")
    op.drop_column("findings", "external_payload_hash")
    op.drop_column("findings", "external_updated_at")
    op.drop_column("findings", "dedupe_key")

    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
