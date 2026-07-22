"""add_entra_fields_to_users

Revision ID: e1a2b3c4d5e6
Revises: d4e9f8a1b2c3
Create Date: 2026-07-22 12:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "d4e9f8a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column("users", sa.Column("entra_oid", sa.String(length=255), nullable=True))
    op.add_column(
        "users", sa.Column("display_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "users", sa.Column("entra_tenant_id", sa.String(length=255), nullable=True)
    )
    op.add_column("users", sa.Column("last_login", sa.DateTime(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "roles", sa.String(length=255), nullable=False, server_default="HelpDesk"
        ),
    )

    # Create unique constraint for entra_oid
    op.create_unique_constraint("uq_users_entra_oid", "users", ["entra_oid"])

    # Alter existing columns to be nullable
    op.alter_column(
        "users", "username", existing_type=sa.String(length=100), nullable=True
    )
    op.alter_column(
        "users", "hashed_password", existing_type=sa.String(length=255), nullable=True
    )


def downgrade() -> None:
    # Revert columns to not null
    op.alter_column(
        "users", "hashed_password", existing_type=sa.String(length=255), nullable=False
    )
    op.alter_column(
        "users", "username", existing_type=sa.String(length=100), nullable=False
    )

    # Drop unique constraint
    op.drop_constraint("uq_users_entra_oid", "users", type_="unique")

    # Drop new columns
    op.drop_column("users", "roles")
    op.drop_column("users", "last_login")
    op.drop_column("users", "entra_tenant_id")
    op.drop_column("users", "display_name")
    op.drop_column("users", "entra_oid")
