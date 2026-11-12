"""Tables and queries for `offices` and `people`.

Imported only by `people.service` and the seed CLI (AD-1). The tables are created
by Alembic (AD-10); these definitions describe them for queries.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    Row,
    String,
    Table,
    insert,
    select,
    update,
)
from sqlalchemy.orm import Session

metadata = MetaData()

offices = Table(
    "offices",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
)

people = Table(
    "people",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, nullable=False, unique=True),
    Column("name", String, nullable=False),
    Column("home_office_id", Integer, ForeignKey("offices.id"), nullable=False),
    Column("is_office_manager", Boolean, nullable=False, default=False),
    Column("active", Boolean, nullable=False, default=True),
)

_person_columns = (
    people.c.id,
    people.c.email,
    people.c.name,
    people.c.home_office_id,
    offices.c.name.label("home_office_name"),
    people.c.is_office_manager,
    people.c.active,
)


def _person_select():
    return select(*_person_columns).join(offices, people.c.home_office_id == offices.c.id)


def search_active(session: Session, text: str, limit: int) -> Sequence[Row]:
    """Active people whose name contains `text`, ignoring case, sorted by name.

    Matched and sorted in Python with `casefold()`, because SQLite's `lower()` folds
    only ASCII (a few hundred rows, so this is cheap).
    """
    needle = text.casefold()
    rows = session.execute(_person_select().where(people.c.active.is_(True))).all()
    matches = [row for row in rows if needle in row.name.casefold()]
    matches.sort(key=lambda row: (row.name.casefold(), row.id))
    return matches[:limit]


def get_person(session: Session, person_id: int) -> Row | None:
    return session.execute(_person_select().where(people.c.id == person_id)).first()


def names(session: Session, person_ids: Iterable[int]) -> dict[int, str]:
    """Names of these people, active or not."""
    ids = set(person_ids)
    if not ids:
        return {}
    rows = session.execute(select(people.c.id, people.c.name).where(people.c.id.in_(ids)))
    return {row.id: row.name for row in rows}


def office_names(session: Session) -> dict[int, str]:
    return {row.id: row.name for row in session.execute(select(offices.c.id, offices.c.name))}


# --- writes, used only by the seed CLI (AD-3, AD-9) ---------------------------


@dataclass(frozen=True)
class PersonRecord:
    email: str
    name: str
    office: str
    is_office_manager: bool


@dataclass(frozen=True)
class LoadResult:
    offices_created: int
    offices_total: int
    added: int
    updated: int
    reactivated: int
    deactivated_ids: tuple[int, ...]


def ensure_offices(session: Session, names: Iterable[str]) -> tuple[dict[str, int], int]:
    """Create any missing offices by name. Returns name -> id and how many were created."""
    existing = {name: id_ for id_, name in session.execute(select(offices.c.id, offices.c.name))}
    created = 0
    for name in sorted(set(names) - existing.keys()):
        existing[name] = session.execute(insert(offices).values(name=name)).inserted_primary_key[0]
        created += 1
    return existing, created


def load_people(session: Session, records: Sequence[PersonRecord]) -> LoadResult:
    """Upsert people keyed on email; mark anyone missing inactive. Never deletes."""
    office_ids, offices_created = ensure_offices(session, (r.office for r in records))
    current = {
        row.email: row
        for row in session.execute(select(people.c.id, people.c.email, people.c.active))
    }
    added = updated = reactivated = 0
    for record in records:
        values = {
            "name": record.name,
            "home_office_id": office_ids[record.office],
            "is_office_manager": record.is_office_manager,
            "active": True,
        }
        row = current.get(record.email)
        if row is None:
            session.execute(insert(people).values(email=record.email, **values))
            added += 1
        else:
            session.execute(update(people).where(people.c.id == row.id).values(**values))
            updated += 1
            if not row.active:
                reactivated += 1

    seen = {r.email for r in records}
    deactivated = tuple(
        sorted(row.id for email, row in current.items() if row.active and email not in seen)
    )
    if deactivated:
        session.execute(update(people).where(people.c.id.in_(deactivated)).values(active=False))

    return LoadResult(
        offices_created=offices_created,
        offices_total=len(office_ids),
        added=added,
        updated=updated,
        reactivated=reactivated,
        deactivated_ids=deactivated,
    )
