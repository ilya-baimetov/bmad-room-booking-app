"""Load or reload offices and people from a CSV (R8, AD-9).

    python -m roombooker.seed <file.csv> [--demo-bookings]

Columns: email, name, office, office_manager. People are matched on email; anyone
missing from the file is marked inactive and keeps their id. Offices are created by
name and never deleted. The whole file loads in one transaction, or nothing does.

`--demo-bookings` then adds demo rooms and this week's and next week's bookings
(`roombooker.demo`). It needs the build seed's people; never use it with HR's list.
"""

import argparse
import csv
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy.orm import Session

from roombooker import demo
from roombooker.core.db import get_engine
from roombooker.people import store

log = logging.getLogger("roombooker.seed")

COLUMNS = ("email", "name", "office", "office_manager")
TRUE_VALUES = {"true", "yes", "1"}
FALSE_VALUES = {"false", "no", "0", ""}


class SeedError(Exception):
    """The file cannot be loaded. Each problem names its line."""

    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def parse(path: Path) -> list[store.PersonRecord]:
    """Read and validate the whole file. Raises SeedError listing every problem."""
    try:
        handle = path.open(newline="", encoding="utf-8-sig")
    except OSError as exc:
        raise SeedError([f"{path}: cannot open ({exc.strerror})"]) from exc

    with handle:
        reader = csv.DictReader(handle)
        header = [(name or "").strip().lower() for name in reader.fieldnames or []]
        missing = [c for c in COLUMNS if c not in header]
        if missing:
            names = ", ".join(missing)
            raise SeedError([f"line 1: missing column{'s' if len(missing) > 1 else ''} {names}"])
        reader.fieldnames = header

        problems: list[str] = []
        records: list[store.PersonRecord] = []
        first_line_for_email: dict[str, int] = {}
        for row in reader:
            line = reader.line_num
            email = (row.get("email") or "").strip().lower()
            name = (row.get("name") or "").strip()
            office = (row.get("office") or "").strip()
            flag = (row.get("office_manager") or "").strip().lower()

            row_problems = []
            if not email:
                row_problems.append("empty email")
            if not name:
                row_problems.append("empty name")
            if not office:
                row_problems.append("empty office")
            if flag not in TRUE_VALUES | FALSE_VALUES:
                row_problems.append(
                    f"unknown office_manager value {row.get('office_manager', '').strip()!r} "
                    "(use true/yes/1, false/no/0 or leave blank)"
                )
            if email and email in first_line_for_email:
                row_problems.append(
                    f"duplicate email {email} (first on line {first_line_for_email[email]})"
                )
            elif email:
                first_line_for_email[email] = line

            if row_problems:
                problems.extend(f"line {line}: {p}" for p in row_problems)
            else:
                records.append(store.PersonRecord(email, name, office, flag in TRUE_VALUES))

    if problems:
        raise SeedError(problems)
    if not records:
        raise SeedError([f"{path}: no people in the file; refusing to mark everyone inactive"])
    return records


def load(path: Path) -> store.LoadResult:
    """Validate `path`, then load it in one transaction."""
    records = parse(path)
    with Session(get_engine()) as session, session.begin():
        return store.load_people(session, records)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m roombooker.seed", description=__doc__.split("\n")[0])
    parser.add_argument("csv_file", type=Path, help="CSV with columns " + ", ".join(COLUMNS))
    parser.add_argument(
        "--demo-bookings",
        action="store_true",
        help="then add demo rooms and bookings for this week and next (build seed only)",
    )
    args = parser.parse_args(argv)

    try:
        result = load(args.csv_file)
    except SeedError as exc:
        log.error("seed: %s not loaded, nothing written", args.csv_file)
        for problem in exc.problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1

    log.info(
        "seed: loaded %s: %d offices (%d new), people %d added, %d updated (%d reactivated), "
        "%d marked inactive",
        args.csv_file,
        result.offices_total,
        result.offices_created,
        result.added,
        result.updated,
        result.reactivated,
        len(result.deactivated_ids),
    )
    for person_id in result.deactivated_ids:
        log.info("seed: marked inactive person_id=%d", person_id)
    if args.demo_bookings:
        return _load_demo()
    return 0


def _load_demo() -> int:
    try:
        with Session(get_engine()) as session:
            result = demo.load_demo(session)
    except demo.DemoError as exc:
        log.error("seed: people loaded, but no demo rooms or bookings written")
        print(f"error: {exc}", file=sys.stderr)
        return 1
    log.info(
        "seed: demo rooms %d added, %d already there; demo bookings %d added, "
        "%d skipped (slot already taken)",
        result.rooms_added,
        result.rooms_kept,
        result.bookings_added,
        result.bookings_skipped,
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s", stream=sys.stdout
    )
    sys.exit(main())
