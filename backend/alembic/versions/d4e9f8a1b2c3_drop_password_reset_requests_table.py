"""drop_password_reset_requests_table

Revision ID: d4e9f8a1b2c3
Revises: 26ee6594045c
Create Date: 2026-07-21 16:58:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e9f8a1b2c3"
down_revision: Union[str, Sequence[str], None] = "26ee6594045c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - drop password_reset_requests table."""
    op.execute("DROP TABLE IF EXISTS password_reset_requests CASCADE")


def downgrade() -> None:
    """Downgrade schema - recreate password_reset_requests table."""
    op.create_table(
        "password_reset_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("otp", sa.String(length=6), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column(
            "is_used", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_password_reset_requests_user_id"),
        "password_reset_requests",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_password_reset_requests_user_id_users",
        "password_reset_requests",
        "users",
        ["user_id"],
        ["id"],
    )
