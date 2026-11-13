"""Tables and queries for `rooms` and `room_tablets`.

Imported only by `rooms.service` (AD-1, AD-3). The tables are created by Alembic
(AD-10); these definitions describe them for queries.
"""

from collections.abc import Iterable, Sequence

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    MetaData,
    Row,
    String,
    Table,
    select,
    update,
)
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

room_tablets = Table(
    "room_tablets",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("room_id", Integer, nullable=False),  # FK to rooms.id in the database
    Column("token", String, nullable=False),
    Column("set_up_by", Integer, nullable=False),  # FK to people.id in the database
    Column("set_up_at", String, nullable=False),
    Column("removed_at", String, nullable=True),
)


def begin_immediate(session: Session) -> None:
    """Start a write transaction holding SQLite's write lock from the start, so two
    tablet setups for one room take turns instead of failing on the unique index."""
    session.commit()
    session.connection().exec_driver_sql("BEGIN IMMEDIATE")


def active_tablets(session: Session, room_ids: Iterable[int] | None = None) -> Sequence[Row]:
    """The active (not removed) tablet of each room, for all rooms or only `room_ids`."""
    query = select(room_tablets).where(room_tablets.c.removed_at.is_(None))
    if room_ids is not None:
        query = query.where(room_tablets.c.room_id.in_(list(room_ids)))
    return session.execute(query).all()


def active_tablet_by_token(session: Session, token: str) -> Row | None:
    return session.execute(
        select(room_tablets).where(
            room_tablets.c.token == token, room_tablets.c.removed_at.is_(None)
        )
    ).first()


def tablets_for_rooms(session: Session, room_ids: Iterable[int]) -> Sequence[Row]:
    """Every tablet, active or removed, of the rooms, in setup order."""
    return session.execute(
        select(room_tablets)
        .where(room_tablets.c.room_id.in_(list(room_ids)))
        .order_by(room_tablets.c.set_up_at, room_tablets.c.id)
    ).all()


def insert_tablet(session: Session, room_id: int, token: str, set_up_by: int, at: str) -> int:
    return session.execute(
        sa_insert(room_tablets).values(
            room_id=room_id, token=token, set_up_by=set_up_by, set_up_at=at, removed_at=None
        )
    ).inserted_primary_key[0]


def remove_active_tablet(session: Session, room_id: int, at: str) -> int | None:
    """Mark the room's active tablet removed at `at`; its id, or None if it had none."""
    row = session.execute(
        select(room_tablets.c.id).where(
            room_tablets.c.room_id == room_id, room_tablets.c.removed_at.is_(None)
        )
    ).first()
    if row is None:
        return None
    session.execute(update(room_tablets).where(room_tablets.c.id == row.id).values(removed_at=at))
    return row.id


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
