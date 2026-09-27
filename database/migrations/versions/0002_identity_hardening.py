"""Add verification, recovery, and refresh-family security state.

Revision ID: 0002_identity_hardening
Revises: 0001_identity
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_identity_hardening"
down_revision: str | None = "0001_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email_verified_at", sa.DateTime(timezone=True)))
        batch_op.add_column(sa.Column("password_changed_at", sa.DateTime(timezone=True)))
        batch_op.add_column(
            sa.Column("auth_version", sa.Integer(), nullable=False, server_default="1")
        )
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("auth_version", existing_type=sa.Integer(), server_default=None)

    with op.batch_alter_table("refresh_sessions") as batch_op:
        batch_op.add_column(sa.Column("family_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("parent_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("replaced_by_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("reuse_detected_at", sa.DateTime(timezone=True)))

    op.execute(sa.text("UPDATE refresh_sessions SET family_id = id WHERE family_id IS NULL"))
    with op.batch_alter_table("refresh_sessions") as batch_op:
        batch_op.alter_column("family_id", existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index("ix_refresh_sessions_family_id", ["family_id"])
        batch_op.create_index("ix_refresh_sessions_family_active", ["family_id", "revoked_at"])

    op.create_table(
        "one_time_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "purpose IN ('email_verification', 'password_reset')",
            name="ck_one_time_tokens_purpose",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_one_time_tokens_user_purpose",
        "one_time_tokens",
        ["user_id", "purpose", "used_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_one_time_tokens_user_purpose", table_name="one_time_tokens")
    op.drop_table("one_time_tokens")

    with op.batch_alter_table("refresh_sessions") as batch_op:
        batch_op.drop_index("ix_refresh_sessions_family_active")
        batch_op.drop_index("ix_refresh_sessions_family_id")
        batch_op.drop_column("reuse_detected_at")
        batch_op.drop_column("replaced_by_id")
        batch_op.drop_column("parent_id")
        batch_op.drop_column("family_id")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("auth_version")
        batch_op.drop_column("password_changed_at")
        batch_op.drop_column("email_verified_at")
