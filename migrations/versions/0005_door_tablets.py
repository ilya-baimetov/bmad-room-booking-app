"""Door tablets (`room_tablets`) and a booking's check-in and freed times.

- `room_tablets`: one row per tablet ever set up; rows are never deleted. The partial
  unique index allows one active (not removed) tablet per room.
- `bookings.checked_in_at` and `bookings.freed_at`: nullable UTC text, at most one of
  them set. Added with plain `ALTER TABLE ... ADD COLUMN`: a batch rebuild of `bookings`
  would drop the overlap triggers and cascade-delete attendees. Neither column is in the
  overlap triggers' `UPDATE OF` list, so writing them does not fire the guard.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "room_tablets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("rooms.id", name="fk_room_tablets_room_id_rooms"),
            nullable=False,
        ),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column(
            "set_up_by",
            sa.Integer(),
            sa.ForeignKey("people.id", name="fk_room_tablets_set_up_by_people"),
            nullable=False,
        ),
        sa.Column("set_up_at", sa.String(), nullable=False),  # UTC 'YYYY-MM-DDTHH:MM:00Z'
        sa.Column("removed_at", sa.String(), nullable=True),
    )
    op.create_index("uq_room_tablets_token", "room_tablets", ["token"], unique=True)
    op.create_index(
        "uq_room_tablets_active_room",
        "room_tablets",
        ["room_id"],
        unique=True,
        sqlite_where=sa.text("removed_at IS NULL"),
    )
    op.add_column("bookings", sa.Column("checked_in_at", sa.String(), nullable=True))
    op.execute(
        "ALTER TABLE bookings ADD COLUMN freed_at VARCHAR "
        "CHECK (checked_in_at IS NULL OR freed_at IS NULL)"
    )


def downgrade() -> None:
    # Plain DROP COLUMN (SQLite 3.35+), freed_at first: its CHECK names checked_in_at.
    op.execute("ALTER TABLE bookings DROP COLUMN freed_at")
    op.execute("ALTER TABLE bookings DROP COLUMN checked_in_at")
    op.execute("DROP INDEX uq_room_tablets_active_room")
    op.execute("DROP INDEX uq_room_tablets_token")
    op.execute("DROP TABLE room_tablets")
