"""Bookings and attendees, with the AD-4 triggers and closing a room's cascade.

- `bookings_no_overlap_insert` / `_update`: refuse a booking that overlaps another in the
  same room (half-open intervals) or is in a closed room (AD-4).
- `rooms_close_cancels_future_bookings`: closing a room deletes its bookings that have not
  started yet (docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_GUARD = """
    SELECT RAISE(ABORT, 'room_closed')
    WHERE (SELECT is_closed FROM rooms WHERE id = NEW.room_id);
    SELECT RAISE(ABORT, 'booking_conflict')
    WHERE EXISTS (
        SELECT 1 FROM bookings other
        WHERE other.room_id = NEW.room_id
          AND other.id IS NOT NEW.id
          AND other.start_at < NEW.end_at
          AND NEW.start_at < other.end_at
    );
"""


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("rooms.id", name="fk_bookings_room_id_rooms"),
            nullable=False,
        ),
        sa.Column(
            "organiser_id",
            sa.Integer(),
            sa.ForeignKey("people.id", name="fk_bookings_organiser_id_people"),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("start_at", sa.String(), nullable=False),  # UTC 'YYYY-MM-DDTHH:MM:00Z' (AD-5)
        sa.Column("end_at", sa.String(), nullable=False),
        sa.CheckConstraint("end_at > start_at", name="ck_bookings_end_after_start"),
    )
    op.create_index("ix_bookings_room_id_start_at", "bookings", ["room_id", "start_at"])
    op.create_index("ix_bookings_organiser_id", "bookings", ["organiser_id"])
    op.create_table(
        "booking_attendees",
        sa.Column(
            "booking_id",
            sa.Integer(),
            sa.ForeignKey(
                "bookings.id", name="fk_booking_attendees_booking_id_bookings", ondelete="CASCADE"
            ),
            primary_key=True,
        ),
        sa.Column(
            "person_id",
            sa.Integer(),
            sa.ForeignKey("people.id", name="fk_booking_attendees_person_id_people"),
            primary_key=True,
        ),
    )
    op.execute(
        f"CREATE TRIGGER bookings_no_overlap_insert BEFORE INSERT ON bookings BEGIN {_GUARD} END"
    )
    op.execute(
        "CREATE TRIGGER bookings_no_overlap_update "
        f"BEFORE UPDATE OF room_id, start_at, end_at ON bookings BEGIN {_GUARD} END"
    )
    op.execute(
        """
        CREATE TRIGGER rooms_close_cancels_future_bookings
        AFTER UPDATE OF is_closed ON rooms
        WHEN NEW.is_closed AND NOT OLD.is_closed
        BEGIN
            DELETE FROM bookings
            WHERE room_id = NEW.id
              AND start_at > strftime('%Y-%m-%dT%H:%M:%SZ', 'now');
        END
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER rooms_close_cancels_future_bookings")
    op.execute("DROP TRIGGER bookings_no_overlap_update")
    op.execute("DROP TRIGGER bookings_no_overlap_insert")
    op.drop_table("booking_attendees")
    op.drop_table("bookings")
