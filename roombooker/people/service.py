"""People rules: who is active, finding people by name, and who manages an office.

Must never import `core.identity` (it imports this module).
"""

from dataclasses import dataclass

from sqlalchemy import Row
from sqlalchemy.orm import Session

from roombooker.people import store

SEARCH_LIMIT = 20


@dataclass(frozen=True)
class Person:
    id: int
    email: str
    name: str
    home_office_id: int
    home_office_name: str
    is_office_manager: bool


def _to_person(row: Row) -> Person:
    return Person(
        id=row.id,
        email=row.email,
        name=row.name,
        home_office_id=row.home_office_id,
        home_office_name=row.home_office_name,
        is_office_manager=row.is_office_manager,
    )


def search_active_people(session: Session, text: str) -> list[Person]:
    """Active people whose name contains `text` (case-insensitive), sorted by name, at most 20.

    Blank text matches no one.
    """
    text = text.strip()
    if not text:
        return []
    return [_to_person(row) for row in store.search_active(session, text, SEARCH_LIMIT)]


def can_manage_office(person: Person, office_id: int) -> bool:
    """RULE-4 (AD-7): only an office manager of their own home office manages it.

    The one predicate for services and templates alike.
    """
    return person.is_office_manager and person.home_office_id == office_id


def get_active_person(session: Session, person_id: int) -> Person | None:
    """The person with this id, or None when unknown or inactive."""
    row = store.get_person(session, person_id)
    if row is None or not row.active:
        return None
    return _to_person(row)


def names(session: Session, person_ids) -> dict[int, str]:
    """{id: name} for these people, including inactive ones (who keep their bookings)."""
    return store.names(session, person_ids)


def office_names(session: Session) -> dict[int, str]:
    """{office id: office name}."""
    return store.office_names(session)
