"""Table and queries for `rooms`.

Imported only by `rooms.service` (AD-1, AD-3). The table is created by Alembic
(AD-10); this definition describes it for queries.
"""

from collections.abc import Sequence

from sqlalchemy import Boolean, Column, Integer, MetaData, Row, String, Table, select, update
from sqlalchemy import insert as sa_insert
from sqlalchemy.orm import Session

metadata = MetaData()

rooms = Table(
    "rooms",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("office_id", Integer, nullable=False),  # FK to offices.id in the database
    Column("name", String, nullable=False),
    Column("capacity", Integer, nullable=False),
    Column("is_closed", Boolean, nullable=False, default=False),
)


def list_for_office(session: Session, office_id: int) -> Sequence[Row]:
    return session.execute(select(rooms).where(rooms.c.office_id == office_id)).all()


def list_all(session: Session) -> Sequence[Row]:
    return session.execute(select(rooms)).all()


def get(session: Session, room_id: int) -> Row | None:
    return session.execute(select(rooms).where(rooms.c.id == room_id)).first()


def insert(session: Session, office_id: int, name: str, capacity: int) -> int:
    result = session.execute(
        sa_insert(rooms).values(office_id=office_id, name=name, capacity=capacity, is_closed=False)
    )
    return result.inserted_primary_key[0]


def update_details(session: Session, room_id: int, name: str, capacity: int) -> None:
    session.execute(update(rooms).where(rooms.c.id == room_id).values(name=name, capacity=capacity))


def set_closed(session: Session, room_id: int, is_closed: bool) -> None:
    session.execute(update(rooms).where(rooms.c.id == room_id).values(is_closed=is_closed))
