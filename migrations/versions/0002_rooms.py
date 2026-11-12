"""Rooms (AD-10; `is_closed` for AD-4).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "office_id",
            sa.Integer(),
            sa.ForeignKey("offices.id", name="fk_rooms_office_id_offices"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("capacity >= 1", name="ck_rooms_capacity_positive"),
        sa.UniqueConstraint("office_id", "name", name="uq_rooms_office_id_name"),
    )


def downgrade() -> None:
    op.drop_table("rooms")
