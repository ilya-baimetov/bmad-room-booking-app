"""Rooms rules: listing, adding, editing, closing and reopening an office's rooms.

The only writer of `rooms` (AD-3). Every function takes the acting person and
raises `NotAllowed` unless they manage the room's office (AD-7, RULE-4).
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from roombooker.core.errors import DomainError, NotAllowed
from roombooker.people.service import Person, can_manage_office
from roombooker.rooms import store

log = logging.getLogger("roombooker.rooms")

NAME_MAX_LENGTH = 50
CAPACITY_MIN = 1
CAPACITY_MAX = 200
SQLITE_MAX_INTEGER = 2**63 - 1

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

    @property
    def status(self) -> str:
        return "Closed" if self.is_closed else "Open"


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


def _to_room(row: Row) -> Room:
    return Room(
        id=row.id,
        office_id=row.office_id,
        name=row.name,
        capacity=row.capacity,
        is_closed=row.is_closed,
    )


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
    rooms = [_to_room(row) for row in store.list_for_office(session, actor.home_office_id)]
    rooms.sort(key=lambda room: (room.name.casefold(), room.id))
    return rooms


def get_room(session: Session, actor: Person, room_id: int) -> Room:
    """One room the actor manages (for the edit form and the close confirmation)."""
    row = _get_row(session, room_id)
    _require_manager(actor, row.office_id, "view")
    return _to_room(row)


def all_rooms(session: Session) -> list[Room]:
    """Every room in every office, open or closed: read by `bookings.service` (AD-1)."""
    return [_to_room(row) for row in store.list_all(session)]


def find_room(session: Session, room_id: int) -> Room:
    """Any room, for anyone (booking needs no office-manager check); RoomNotFound if none."""
    return _to_room(_get_row(session, room_id))


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
    return Room(room_id, row.office_id, clean_name, clean_capacity, row.is_closed)


def _set_closed(session: Session, actor: Person, room_id: int, is_closed: bool) -> Room:
    action = "close" if is_closed else "reopen"
    row = _get_row(session, room_id)
    _require_manager(actor, row.office_id, action)
    store.set_closed(session, room_id, is_closed)
    session.commit()
    log.info("rooms: person_id=%d %s room_id=%d", actor.id, action, room_id)
    return Room(row.id, row.office_id, row.name, row.capacity, is_closed)


def close_room(session: Session, actor: Person, room_id: int) -> Room:
    """Close a room. A database trigger deletes its bookings that have not started yet
    in the same statement (docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md)."""
    return _set_closed(session, actor, room_id, is_closed=True)


def reopen_room(session: Session, actor: Person, room_id: int) -> Room:
    return _set_closed(session, actor, room_id, is_closed=False)
