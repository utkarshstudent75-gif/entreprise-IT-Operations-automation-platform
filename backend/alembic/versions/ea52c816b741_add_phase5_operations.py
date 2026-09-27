"""Add Phase 5 operations request data.

Revision ID: ea52c816b741
Revises: d4e9f8a1b2c3
Create Date: 2026-09-27 14:45:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "ea52c816b741"
down_revision: Union[str, Sequence[str], None] = "d4e9f8a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "software_requests",
        sa.Column("requester_email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "software_requests",
        sa.Column("decided_by_email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "software_requests",
        sa.Column("decision_note", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "software_requests", sa.Column("decided_at", sa.DateTime(), nullable=True)
    )
    op.create_index(
        op.f("ix_software_requests_requester_email"),
        "software_requests",
        ["requester_email"],
        unique=False,
    )
    op.create_table(
        "account_unlock_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("requester_email", sa.String(length=255), nullable=False),
        sa.Column("justification", sa.String(length=1000), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["requested_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_account_unlock_requests_id"),
        "account_unlock_requests",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_account_unlock_requests_requested_by"),
        "account_unlock_requests",
        ["requested_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_account_unlock_requests_requester_email"),
        "account_unlock_requests",
        ["requester_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_account_unlock_requests_status"),
        "account_unlock_requests",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_account_unlock_requests_status"),
        table_name="account_unlock_requests",
    )
    op.drop_index(
        op.f("ix_account_unlock_requests_requester_email"),
        table_name="account_unlock_requests",
    )
    op.drop_index(
        op.f("ix_account_unlock_requests_requested_by"),
        table_name="account_unlock_requests",
    )
    op.drop_index(
        op.f("ix_account_unlock_requests_id"), table_name="account_unlock_requests"
    )
    op.drop_table("account_unlock_requests")
    op.drop_index(
        op.f("ix_software_requests_requester_email"), table_name="software_requests"
    )
    op.drop_column("software_requests", "decided_at")
    op.drop_column("software_requests", "decision_note")
    op.drop_column("software_requests", "decided_by_email")
    op.drop_column("software_requests", "requester_email")
