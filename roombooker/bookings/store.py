"""Tables and queries for `bookings` and `booking_attendees`.

Imported only by `bookings.service` (AD-1, AD-3). The tables and the AD-4 triggers are
created by Alembic (AD-10); these definitions describe them for queries. Times are UTC
text `YYYY-MM-DDTHH:MM:00Z`, so text order is time order (AD-5).
"""

from collections.abc import Iterable, Sequence

from sqlalchemy import Column, ForeignKey, Integer, MetaData, Row, String, Table, delete, select
from sqlalchemy import insert as sa_insert
from sqlalchemy.orm import Session

metadata = MetaData()

bookings = Table(
    "bookings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("room_id", Integer, nullable=False),  # FK to rooms.id in the database
    Column("organiser_id", Integer, nullable=False),  # FK to people.id in the database
    Column("title", String, nullable=False),
    Column("start_at", String, nullable=False),
    Column("end_at", String, nullable=False),
)

booking_attendees = Table(
    "booking_attendees",
    metadata,
    Column("booking_id", Integer, ForeignKey("bookings.id"), primary_key=True),
    Column("person_id", Integer, primary_key=True),  # FK to people.id in the database
)


def begin_immediate(session: Session) -> None:
    """Start a write transaction that holds SQLite's write lock from the start (AD-4).

    The driver opens no transaction for reads, so after ending the session's current
    one there is none open and an explicit BEGIN IMMEDIATE is allowed.
    """
    session.commit()
    session.connection().exec_driver_sql("BEGIN IMMEDIATE")


def overlapping(session: Session, start_at: str, end_at: str) -> Sequence[Row]:
    """Bookings in any room that overlap [start_at, end_at), in start order."""
    return session.execute(
        select(bookings)
        .where(bookings.c.start_at < end_at, bookings.c.end_at > start_at)
        .order_by(bookings.c.start_at, bookings.c.id)
    ).all()


def upcoming_for_organiser(
    session: Session, organiser_id: int, after: str, limit: int
) -> Sequence[Row]:
    """The organiser's bookings that end after `after`, soonest first."""
    return session.execute(
        select(bookings)
        .where(bookings.c.organiser_id == organiser_id, bookings.c.end_at > after)
        .order_by(bookings.c.start_at, bookings.c.id)
        .limit(limit)
    ).all()


def for_person(session: Session, person_id: int, start_at: str, end_at: str) -> Sequence[Row]:
    """Bookings overlapping [start_at, end_at) that the person organises or attends,
    in start order."""
    attending = select(booking_attendees.c.booking_id).where(
        booking_attendees.c.person_id == person_id
    )
    return session.execute(
        select(bookings)
        .where(
            bookings.c.start_at < end_at,
            bookings.c.end_at > start_at,
            (bookings.c.organiser_id == person_id) | bookings.c.id.in_(attending),
        )
        .order_by(bookings.c.start_at, bookings.c.id)
    ).all()


def get(session: Session, booking_id: int) -> Row | None:
    return session.execute(select(bookings).where(bookings.c.id == booking_id)).first()


def attendee_ids(session: Session, booking_id: int) -> list[int]:
    rows = session.execute(
        select(booking_attendees.c.person_id).where(booking_attendees.c.booking_id == booking_id)
    )
    return [row.person_id for row in rows]


def insert(
    session: Session,
    room_id: int,
    organiser_id: int,
    title: str,
    start_at: str,
    end_at: str,
    attendees: Iterable[int],
) -> int:
    booking_id = session.execute(
        sa_insert(bookings).values(
            room_id=room_id,
            organiser_id=organiser_id,
            title=title,
            start_at=start_at,
            end_at=end_at,
        )
    ).inserted_primary_key[0]
    rows = [{"booking_id": booking_id, "person_id": person_id} for person_id in attendees]
    if rows:
        session.execute(sa_insert(booking_attendees), rows)
    return booking_id


def delete_booking(session: Session, booking_id: int) -> None:
    """Delete a booking; its attendees go with it (ON DELETE CASCADE, AD-13)."""
    session.execute(delete(bookings).where(bookings.c.id == booking_id))
