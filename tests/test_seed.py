"""Seed CLI: first load, reload, bad CSV (I/O matrix rows 1-3)."""

import logging
import sqlite3

import pytest


def test_first_load_creates_offices_and_active_people(load_csv, people, db_path, caplog):
    caplog.set_level(logging.INFO, logger="roombooker.seed")

    exit_code = load_csv(
        "a@example.com,Amy True,London,true",
        "b@example.com,Ben Yes,London,YES",
        "c@example.com,Cal One,Leeds,1",
        "d@example.com,Dee False,Leeds,False",
        "e@example.com,Eve No,Manchester,no",
        "f@example.com,Fay Zero,Manchester,0",
        "g@example.com,Gus Blank,Manchester,",
    )

    assert exit_code == 0
    with sqlite3.connect(db_path) as conn:
        assert sorted(n for (n,) in conn.execute("SELECT name FROM offices")) == [
            "Leeds",
            "London",
            "Manchester",
        ]
    rows = people()
    assert {email: (r["name"], r["office"]) for email, r in rows.items()} == {
        "a@example.com": ("Amy True", "London"),
        "b@example.com": ("Ben Yes", "London"),
        "c@example.com": ("Cal One", "Leeds"),
        "d@example.com": ("Dee False", "Leeds"),
        "e@example.com": ("Eve No", "Manchester"),
        "f@example.com": ("Fay Zero", "Manchester"),
        "g@example.com": ("Gus Blank", "Manchester"),
    }
    assert all(r["active"] for r in rows.values())
    managers = {email for email, r in rows.items() if r["is_office_manager"]}
    assert managers == {"a@example.com", "b@example.com", "c@example.com"}
    assert "3 offices (3 new), people 7 added" in caplog.text


def test_reload_updates_by_email_and_never_deletes(load_csv, people, db_path):
    assert load_csv(
        "a@example.com,Amy,Leeds,",
        "b@example.com,Ben,London,",
        "c@example.com,Cal,London,",
    ) == 0
    assert load_csv("a@example.com,Amy,Leeds,", "b@example.com,Ben,London,") == 0
    before = people()
    assert before["c@example.com"]["active"] == 0

    # A dropped, B renamed, C back.
    assert load_csv("b@example.com,Benjamin,London,", "c@example.com,Cal,London,true") == 0

    after = people()
    assert {email: r["id"] for email, r in after.items()} == {
        email: r["id"] for email, r in before.items()
    }
    assert after["a@example.com"]["active"] == 0
    assert after["b@example.com"]["name"] == "Benjamin"
    assert after["b@example.com"]["active"] == 1
    assert after["c@example.com"]["active"] == 1
    assert after["c@example.com"]["is_office_manager"] == 1
    with sqlite3.connect(db_path) as conn:
        offices = sorted(n for (n,) in conn.execute("SELECT name FROM offices"))
    assert offices == ["Leeds", "London"]  # Leeds kept although no active person is in it


@pytest.mark.parametrize(
    ("header", "lines", "message"),
    [
        (
            "email,name,office_manager",
            ["x@example.com,Xan,"],
            "line 1: missing column office",
        ),
        (
            None,
            ["x@example.com,Xan,London,", "X@example.com,Xan Again,Leeds,"],
            "line 3: duplicate email x@example.com (first on line 2)",
        ),
        (
            None,
            ["x@example.com,Xan,London,maybe"],
            "line 2: unknown office_manager value 'maybe'",
        ),
        (None, ["x@example.com,,London,"], "line 2: empty name"),
        (None, ["x@example.com,Xan,London,", ",Nobody,Leeds,"], "line 3: empty email"),
    ],
    ids=["missing-column", "duplicate-email", "unknown-flag", "empty-name", "empty-email"],
)
def test_bad_csv_writes_nothing(load_csv, people, db_path, capsys, header, lines, message):
    assert load_csv("a@example.com,Amy,London,true") == 0
    before = people()
    capsys.readouterr()

    kwargs = {"header": header} if header else {}
    exit_code = load_csv(*lines, **kwargs)

    assert exit_code != 0
    assert message in capsys.readouterr().err
    assert people() == before
    with sqlite3.connect(db_path) as conn:
        assert [n for (n,) in conn.execute("SELECT name FROM offices")] == ["London"]
