"""Manage rooms through the app (one test per I/O matrix row, plus the landing redirect)."""

import html
import logging
import re
import sqlite3

import pytest

from roombooker.rooms import service

HX = {"HX-Request": "true"}
REFUSED = "Only office managers can manage rooms."
ROOM_NAMES = re.compile(r'class="room-name">([^<]*)<')
ROOM_STATUSES = re.compile(r'class="room-status">([^<]*)<')
ANNOUNCE = re.compile(r'<div id="announce"[^>]*>(.*?)</div>', re.S)

PEOPLE = (
    "anna@example.com,Anna Kowalski,London,true",
    "hannah@example.com,Hannah Okafor,London,",
    "joanne@example.com,Joanne Price,Manchester,true",
)


@pytest.fixture
def ids(load_csv, people):
    assert load_csv(*PEOPLE) == 0
    return {email.split("@")[0]: row["id"] for email, row in people().items()}


@pytest.fixture
def act(client, ids):
    """Act as someone: set the `person_id` cookie on `client`."""

    def _act(who: str) -> None:
        client.cookies.set("person_id", str(ids[who]))

    return _act


@pytest.fixture
def rooms(db_path):
    """The rooms table as {name: row dict}, straight from the file."""

    def _rooms() -> dict[str, dict]:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT r.id, o.name AS office, r.name, r.capacity, r.is_closed "
                "FROM rooms r JOIN offices o ON o.id = r.office_id"
            ).fetchall()
        return {row["name"]: dict(row) for row in rows}

    return _rooms


@pytest.fixture
def add(client, act, rooms):
    """Add a room as Anna through the app; returns its id."""

    def _add(name: str, capacity: str = "8") -> int:
        act("anna")
        response = client.post("/manage-rooms", data={"name": name, "capacity": capacity})
        assert response.status_code == 303
        return rooms()[name.strip()]["id"]

    return _add


def announced(text: str) -> str:
    return ANNOUNCE.search(text).group(1)


def test_landing_sends_office_managers_to_manage_rooms(client, act):
    act("anna")
    response = client.get("/")
    assert response.status_code == 303
    assert response.headers["location"] == "/manage-rooms"
    assert client.head("/manage-rooms").status_code == 200

    act("hannah")
    response = client.get("/")
    assert response.status_code == 303
    assert response.headers["location"] == "/rooms"
    page = client.get("/rooms")
    assert '<a class="tab" href="/rooms" aria-current="page">Rooms</a>' in page.text
    assert ">Manage rooms</a>" not in page.text


def test_list_and_add(client, act, add, rooms, ids, caplog):
    act("joanne")
    client.post("/manage-rooms", data={"name": "Manchester Hub", "capacity": "6"})
    manchester_room = rooms()["Manchester Hub"]["id"]

    act("anna")
    page = client.get("/manage-rooms")
    assert "No rooms in London yet." in page.text
    assert '<a class="tab" href="/manage-rooms" aria-current="page">Manage rooms</a>' in page.text
    assert '<a class="current-person" href="/pick-name?next=/">' in page.text  # switch via landing

    caplog.set_level(logging.INFO, logger="roombooker.rooms")
    response = client.post("/manage-rooms", data={"name": "  Snug ", "capacity": "1"})
    snug = rooms()["Snug"]
    assert response.status_code == 303
    assert response.headers["location"] == f"/manage-rooms?notice=added&room={snug['id']}"
    assert f"rooms: person_id={ids['anna']} add room_id={snug['id']}" in caplog.text
    assert announced(client.get(response.headers["location"]).text) == '<p class="notice">Added Snug.</p>'

    fragment = client.post(
        "/manage-rooms", data={"name": "board room", "capacity": "200"}, headers=HX
    )
    assert fragment.status_code == 200
    assert "<html" not in fragment.text
    assert re.search(r'id="add-room-name"[^>]*value=""', fragment.text)  # a fresh form
    assert 'id="rooms-table" class="rooms" hx-swap-oob="true"' in fragment.text
    assert ROOM_NAMES.findall(fragment.text) == ["board room", "Snug"]  # by name, ignoring case
    assert '<p class="notice">Added board room.</p>' in fragment.text

    page = client.get("/manage-rooms")
    assert ROOM_NAMES.findall(page.text) == ["board room", "Snug"]  # not Manchester's room
    assert ROOM_STATUSES.findall(page.text) == ["Open", "Open"]
    london = [row for row in rooms().values() if row["office"] == "London"]
    assert {(row["capacity"], row["is_closed"]) for row in london} == {(1, 0), (200, 0)}
    # A notice only ever names a room in the actor's own office.
    assert announced(client.get(f"/manage-rooms?notice=added&room={manchester_room}").text) == ""


def test_edit_changes_name_and_capacity_only(client, add, rooms):
    other_id = add("Mezzanine", "6")
    room_id = add("Snug", "4")
    client.post(f"/manage-rooms/{room_id}/close")

    form = client.get(f"/manage-rooms/{room_id}/edit", headers=HX)
    assert form.text.startswith(f'\n<tr id="room-{room_id}" class="room-row is-editing">')
    assert 'value="Snug"' in form.text and 'value="4"' in form.text
    page = client.get(f"/manage-rooms/{room_id}/edit")  # without JavaScript: the page, row as a form
    assert "<html" in page.text and 'class="room-row is-editing"' in page.text

    long_name = "L" * 50
    table = client.post(
        f"/manage-rooms/{room_id}",
        data={"name": f" {long_name} ", "capacity": "20", "is_closed": "0"},
        headers=HX,
    )
    assert table.status_code == 200
    assert table.headers["hx-retarget"] == "#rooms-table"
    assert table.headers["hx-reswap"] == "outerHTML"
    assert table.text.lstrip().startswith('<div id="rooms-table" class="rooms">')
    assert ROOM_NAMES.findall(table.text) == [long_name, "Mezzanine"]  # re-sorted by the rename
    assert ROOM_STATUSES.findall(table.text) == ["Closed", "Open"]
    assert f'<p class="notice">Saved {long_name}.</p>' in table.text

    response = client.post(f"/manage-rooms/{room_id}", data={"name": "snug", "capacity": "5"})
    assert response.status_code == 303
    assert response.headers["location"] == f"/manage-rooms?notice=saved&room={room_id}"
    assert rooms() == {
        "Mezzanine": {
            "id": other_id, "office": "London", "name": "Mezzanine", "capacity": 6, "is_closed": 0
        },
        "snug": {"id": room_id, "office": "London", "name": "snug", "capacity": 5, "is_closed": 1},
    }


def test_close_after_confirmation_then_reopen(client, add, rooms):
    room_id = add("Snug")

    page = client.get(f"/manage-rooms/{room_id}/close")
    assert "<html" in page.text
    assert (
        "Close Snug? No one can book it until you reopen it, "
        "and its future bookings are cancelled."
    ) in page.text
    assert '>Close room</button>' in page.text
    assert 'href="/manage-rooms"' in page.text and ">Keep open</a>" in page.text  # cancelling is a GET
    fragment = client.get(f"/manage-rooms/{room_id}/close", headers=HX)
    assert fragment.text.startswith(f'<tr id="room-{room_id}" class="room-row is-confirming">')
    assert rooms()["Snug"]["is_closed"] == 0  # asking changes nothing

    response = client.post(f"/manage-rooms/{room_id}/close")
    assert response.status_code == 303
    assert response.headers["location"] == f"/manage-rooms?notice=closed&room={room_id}"
    page = client.get(response.headers["location"])
    assert announced(page.text) == '<p class="notice">Closed Snug.</p>'
    assert f'<tr id="room-{room_id}" class="room-row is-closed">' in page.text
    assert ROOM_STATUSES.findall(page.text) == ["Closed"]

    row = client.post(f"/manage-rooms/{room_id}/reopen", headers=HX)
    assert ROOM_STATUSES.findall(row.text) == ["Open"]
    assert '<p class="notice">Reopened Snug.</p>' in row.text
    assert rooms()["Snug"]["is_closed"] == 0


@pytest.mark.parametrize(
    ("name", "capacity", "reason"),
    [
        ("", "4", service.NEEDS_NAME),
        ("   ", "4", service.NEEDS_NAME),
        ("N" * 51, "4", service.NAME_TOO_LONG),
        ("Pod", "", service.BAD_CAPACITY),
        ("Pod", "four", service.BAD_CAPACITY),
        ("Pod", "1.5", service.BAD_CAPACITY),
        ("Pod", "0", service.BAD_CAPACITY),
        ("Pod", "201", service.BAD_CAPACITY),
        (" SNUG  ", "4", "London already has a room called Snug."),
    ],
    ids=["empty", "blank", "long", "no-capacity", "word", "fraction", "zero", "over", "duplicate"],
)
def test_add_refuses_invalid_room(client, add, rooms, name, capacity, reason):
    add("Snug")
    before = rooms()

    page = client.post("/manage-rooms", data={"name": name, "capacity": capacity})

    assert page.status_code == 422
    text = html.unescape(page.text)
    assert text.index(reason) < text.index(">Add room</button>")
    assert f'value="{name}"' in text and f'value="{capacity}"' in text
    assert rooms() == before


def test_rename_refuses_a_name_used_in_the_office(client, add, rooms):
    add("Snug")
    room_id = add("Board")
    before = rooms()

    row = client.post(f"/manage-rooms/{room_id}", data={"name": "snug ", "capacity": "9"}, headers=HX)
    assert row.status_code == 422
    assert row.text.lstrip().startswith(f'<tr id="room-{room_id}" class="room-row is-editing">')
    assert row.text.index("London already has a room called Snug.") < row.text.index(">Save</button>")
    assert 'value="snug "' in row.text and 'value="9"' in row.text

    page = client.post(f"/manage-rooms/{room_id}", data={"name": "SNUG", "capacity": "9"})
    assert page.status_code == 422
    assert "<html" in page.text and "London already has a room called Snug." in page.text
    assert rooms() == before


def test_unique_constraint_backstop_maps_to_invalid(client, add, rooms, monkeypatch):
    add("Snug")
    monkeypatch.setattr(service, "_duplicate_of", lambda *args: None)

    page = client.post("/manage-rooms", data={"name": "Snug", "capacity": "3"})

    assert page.status_code == 422
    assert "London already has a room called Snug." in page.text
    assert list(rooms()) == ["Snug"]


REQUESTS = [
    ("GET", "/manage-rooms"),
    ("POST", "/manage-rooms"),
    ("GET", "/manage-rooms/{id}/edit"),
    ("POST", "/manage-rooms/{id}"),
    ("GET", "/manage-rooms/{id}/close"),
    ("POST", "/manage-rooms/{id}/close"),
    ("POST", "/manage-rooms/{id}/reopen"),
]


# Joanne manages Manchester, so `/manage-rooms` (list and add) is her own office's and allowed.
REFUSALS = [("hannah", m, p) for m, p in REQUESTS] + [
    ("joanne", m, p) for m, p in REQUESTS if "{id}" in p
]


def _send(client, method: str, path: str):
    form = {"name": "Taken", "capacity": "3"} if method == "POST" else None
    return client.request(method, path, data=form)


@pytest.mark.parametrize(
    ("who", "method", "path"), REFUSALS, ids=[f"{w} {m} {p}" for w, m, p in REFUSALS]
)
def test_refused_unless_managing_the_office(client, act, add, rooms, who, method, path):
    room_id = add("Snug")
    before = rooms()
    act(who)

    response = _send(client, method, path.format(id=room_id))

    assert response.status_code == 403
    assert announced(response.text) == f'<p class="error-message">{REFUSED}</p>'
    if who == "hannah":
        assert ">Manage rooms</a>" not in response.text
    assert rooms() == before


def test_refusal_for_htmx_goes_to_announce(client, act, add, rooms):
    room_id = add("Snug")
    act("joanne")

    response = client.post(f"/manage-rooms/{room_id}/close", headers=HX)

    assert response.status_code == 403
    assert response.headers["hx-retarget"] == "#announce"
    assert response.headers["hx-reswap"] == "innerHTML"
    assert response.headers["hx-reselect"] == ".error-message"
    assert response.text.strip() == f'<p class="error-message">{REFUSED}</p>'
    assert rooms()["Snug"]["is_closed"] == 0


@pytest.mark.parametrize(
    ("method", "path"), REQUESTS[2:], ids=[f"{m} {p}" for m, p in REQUESTS[2:]]
)
@pytest.mark.parametrize("room_id", [9999, 2**63], ids=["unknown", "out-of-range"])
def test_unknown_room_is_not_found(client, add, rooms, method, path, room_id):
    add("Snug")
    before = rooms()

    response = _send(client, method, path.format(id=room_id))

    assert response.status_code == 404
    assert rooms() == before
