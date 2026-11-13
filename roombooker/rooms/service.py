"""Rooms rules: listing, adding, editing, closing and reopening an office's rooms,
and setting up and removing their door tablets.

The only writer of `rooms` and `room_tablets` (AD-3). Every function that changes or
lists an office's rooms takes the acting person and raises `NotAllowed` unless they
manage the room's office (AD-7, RULE-4). A room has at most one active door tablet;
setting up a new one removes the old one at the same instant, so the room's tablet
periods stay contiguous. `bookings.service` reads those periods, never the table.
"""

import logging
import secrets
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from roombooker.core import time as clock
from roombooker.core.errors import DomainError, NotAllowed
from roombooker.people.service import Person, can_manage_office
from roombooker.rooms import store

log = logging.getLogger("roombooker.rooms")

NAME_MAX_LENGTH = 50
CAPACITY_MIN = 1
CAPACITY_MAX = 200
SQLITE_MAX_INTEGER = 2**63 - 1
TOKEN_MAX_LENGTH = 100

TabletPeriod = tuple[datetime, datetime | None]  # (set_up_at, removed_at or None if active)

NEEDS_NAME = "Give the room a name."
NAME_TOO_LONG = f"Room names can be up to {NAME_MAX_LENGTH} characters."
BAD_CAPACITY = f"Capacity must be a whole number from {CAPACITY_MIN} to {CAPACITY_MAX}."


@dataclass(frozen=True)
class Room:
    id: int
    office_id: int
    name: str
    capacity: int
    is_closed: bool
    tablet_since: datetime | None = None  # when its active door tablet was set up

    @property
    def status(self) -> str:
        return "Closed" if self.is_closed else "Open"

    @property
    def has_tablet(self) -> bool:
        return self.tablet_since is not None


class RoomNotFound(DomainError):
    status_code = 404
    default_message = "That room does not exist."


class InvalidRoom(DomainError):
    """The submitted name or capacity breaks a rule. Carries every reason and the typed values."""

    status_code = 422

    def __init__(self, errors: list[str], values: dict[str, str]):
        super().__init__(" ".join(errors))
        self.errors = errors
        self.values = values


def _to_room(row: Row, tablet_since: datetime | None = None) -> Room:
    return Room(
        id=row.id,
        office_id=row.office_id,
        name=row.name,
        capacity=row.capacity,
        is_closed=row.is_closed,
        tablet_since=tablet_since,
    )


def _tablets_since(
    session: Session, room_ids: Iterable[int] | None = None
) -> dict[int, datetime]:
    """When each room's active tablet was set up, for rooms that have one."""
    return {
        row.room_id: clock.from_text(row.set_up_at)
        for row in store.active_tablets(session, room_ids)
    }


def _rooms(session: Session, rows: Iterable[Row]) -> list[Room]:
    rows = list(rows)
    since = _tablets_since(session, [row.id for row in rows])
    return [_to_room(row, since.get(row.id)) for row in rows]


def _name_key(name: str) -> str:
    """Duplicate check key: SQLite's lower() folds only ASCII, so compare in Python."""
    return name.strip().casefold()


def _require_manager(actor: Person, office_id: int, action: str) -> None:
    if not can_manage_office(actor, office_id):
        log.info("rooms: person_id=%d refused %s for office_id=%d", actor.id, action, office_id)
        raise NotAllowed()


def _get_row(session: Session, room_id: int) -> Row:
    # Ids outside SQLite's INTEGER range cannot exist (and would fail to bind).
    row = store.get(session, room_id) if 0 < room_id <= SQLITE_MAX_INTEGER else None
    if row is None:
        raise RoomNotFound()
    return row


def _duplicate_of(
    session: Session, office_id: int, name: str, room_id: int | None
) -> Row | None:
    """Another room in the office with this name, ignoring case and surrounding spaces."""
    key = _name_key(name)
    for row in store.list_for_office(session, office_id):
        if row.id != room_id and _name_key(row.name) == key:
            return row
    return None


def _validate(
    session: Session, actor: Person, name: str, capacity: str, room_id: int | None
) -> tuple[str, int]:
    """Trimmed name and whole-number capacity, or InvalidRoom with every reason."""
    values = {"name": name, "capacity": capacity}
    errors: list[str] = []

    clean_name = name.strip()
    if not clean_name:
        errors.append(NEEDS_NAME)
    elif len(clean_name) > NAME_MAX_LENGTH:
        errors.append(NAME_TOO_LONG)
    else:
        duplicate = _duplicate_of(session, actor.home_office_id, clean_name, room_id)
        if duplicate is not None:
            errors.append(_duplicate_reason(actor, duplicate.name))

    raw_capacity = capacity.strip()
    clean_capacity = None
    if raw_capacity.isascii() and raw_capacity.isdigit() and len(raw_capacity) <= 4:
        clean_capacity = int(raw_capacity)
    if clean_capacity is None or not CAPACITY_MIN <= clean_capacity <= CAPACITY_MAX:
        errors.append(BAD_CAPACITY)

    if errors:
        raise InvalidRoom(errors, values)
    return clean_name, clean_capacity


def _duplicate_reason(actor: Person, existing_name: str) -> str:
    return f"{actor.home_office_name} already has a room called {existing_name}."


def _commit_details[T](
    session: Session, actor: Person, name: str, capacity: str, write: Callable[[], T]
) -> T:
    """Run `write` and commit, mapping the exact-match unique constraint (a backstop
    behind the case-insensitive check) to InvalidRoom."""
    try:
        result = write()
        session.commit()
        return result
    except IntegrityError:
        session.rollback()
        raise InvalidRoom(
            [_duplicate_reason(actor, name.strip())], {"name": name, "capacity": capacity}
        ) from None


def list_rooms(session: Session, actor: Person) -> list[Room]:
    """The actor's home-office rooms, sorted by name."""
    _require_manager(actor, actor.home_office_id, "list")
    rooms = _rooms(session, store.list_for_office(session, actor.home_office_id))
    rooms.sort(key=lambda room: (room.name.casefold(), room.id))
    return rooms


def get_room(session: Session, actor: Person, room_id: int) -> Room:
    """One room the actor manages (for the edit form and the close confirmation)."""
    row = _get_row(session, room_id)
    _require_manager(actor, row.office_id, "view")
    return _rooms(session, [row])[0]


def all_rooms(session: Session) -> list[Room]:
    """Every room in every office, open or closed: read by `bookings.service` (AD-1)."""
    rows = store.list_all(session)
    since = _tablets_since(session)
    return [_to_room(row, since.get(row.id)) for row in rows]


def find_room(session: Session, room_id: int) -> Room:
    """Any room, for anyone (booking needs no office-manager check); RoomNotFound if none."""
    return _rooms(session, [_get_row(session, room_id)])[0]


def add_room(session: Session, actor: Person, name: str, capacity: str) -> Room:
    """Create an Open room in the actor's home office."""
    _require_manager(actor, actor.home_office_id, "add")
    clean_name, clean_capacity = _validate(session, actor, name, capacity, room_id=None)
    room_id = _commit_details(
        session,
        actor,
        name,
        capacity,
        lambda: store.insert(session, actor.home_office_id, clean_name, clean_capacity),
    )
    log.info("rooms: person_id=%d add room_id=%d", actor.id, room_id)
    return Room(room_id, actor.home_office_id, clean_name, clean_capacity, is_closed=False)


def edit_room(session: Session, actor: Person, room_id: int, name: str, capacity: str) -> Room:
    """Change a room's name and capacity. Its status is unchanged."""
    row = _get_row(session, room_id)
    _require_manager(actor, row.office_id, "edit")
    clean_name, clean_capacity = _validate(session, actor, name, capacity, room_id=room_id)
    _commit_details(
        session,
        actor,
        name,
        capacity,
        lambda: store.update_details(session, room_id, clean_name, clean_capacity),
    )
    log.info("rooms: person_id=%d edit room_id=%d", actor.id, room_id)
    return find_room(session, room_id)


def _set_closed(session: Session, actor: Person, room_id: int, is_closed: bool) -> Room:
    action = "close" if is_closed else "reopen"
    row = _get_row(session, room_id)
    _require_manager(actor, row.office_id, action)
    store.set_closed(session, room_id, is_closed)
    session.commit()
    log.info("rooms: person_id=%d %s room_id=%d", actor.id, action, room_id)
    return find_room(session, room_id)


def close_room(session: Session, actor: Person, room_id: int) -> Room:
    """Close a room. A database trigger deletes its bookings that have not started yet
    in the same statement (docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md)."""
    return _set_closed(session, actor, room_id, is_closed=True)


def reopen_room(session: Session, actor: Person, room_id: int) -> Room:
    return _set_closed(session, actor, room_id, is_closed=False)


def set_up_tablet(session: Session, actor: Person, room_id: int) -> tuple[Room, str]:
    """Make a new door tablet the room's only active one, removing any previous one at
    the same instant (AD-8). Returns the room and the new tablet's secret token, which
    the caller puts in the browser's `door_tablet` cookie."""
    row = _get_row(session, room_id)
    _require_manager(actor, row.office_id, "set up tablet")
    token = secrets.token_urlsafe(32)
    store.begin_immediate(session)
    try:
        now = clock.to_text(clock.utc_now())
        replaced = store.remove_active_tablet(session, room_id, now)
        tablet_id = store.insert_tablet(session, room_id, token, actor.id, now)
        session.commit()
    except BaseException:
        session.rollback()
        raise
    if replaced is not None:
        log.info(
            "rooms: person_id=%d remove tablet_id=%d room_id=%d (replaced)",
            actor.id,
            replaced,
            room_id,
        )
    log.info("rooms: person_id=%d set up tablet_id=%d room_id=%d", actor.id, tablet_id, room_id)
    return find_room(session, room_id), token


def remove_tablet(session: Session, actor: Person, room_id: int) -> Room:
    """Remove the room's active door tablet; removing when there is none changes nothing.
    The removed tablet's browser then shows the not-set-up page."""
    row = _get_row(session, room_id)
    _require_manager(actor, row.office_id, "remove tablet")
    store.begin_immediate(session)
    try:
        removed = store.remove_active_tablet(session, room_id, clock.to_text(clock.utc_now()))
        session.commit()
    except BaseException:
        session.rollback()
        raise
    if removed is not None:
        log.info("rooms: person_id=%d remove tablet_id=%d room_id=%d", actor.id, removed, room_id)
    return find_room(session, room_id)


def tablet_room(session: Session, token: str | None) -> Room | None:
    """The room whose active door tablet holds `token`, or None (no, unknown or removed
    token). Read only by `core.identity.current_tablet`."""
    if not token or len(token) > TOKEN_MAX_LENGTH or not token.isascii():
        return None
    row = store.active_tablet_by_token(session, token)
    return find_room(session, row.room_id) if row is not None else None


def tablet_periods(session: Session, room_ids: Iterable[int]) -> dict[int, list[TabletPeriod]]:
    """Each room's door tablet periods, in setup order; an active tablet's period has no
    end. Rooms that never had a tablet are left out. Read by `bookings.service` (AD-6)."""
    periods: dict[int, list[TabletPeriod]] = {}
    for row in store.tablets_for_rooms(session, room_ids):
        removed = clock.from_text(row.removed_at) if row.removed_at is not None else None
        periods.setdefault(row.room_id, []).append((clock.from_text(row.set_up_at), removed))
    return periods
