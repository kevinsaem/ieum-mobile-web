"""add simple numeric login id

Revision ID: 20260715_02
Revises: 20260715_01
Create Date: 2026-07-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260715_02"
down_revision: str | None = "20260715_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("login_id", sa.String(length=32), nullable=True))
    op.create_index("ix_users_login_id", "users", ["login_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_login_id", table_name="users")
    op.drop_column("users", "login_id")
