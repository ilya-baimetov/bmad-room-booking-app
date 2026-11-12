"""Pick your name and the current person (I/O matrix rows 4-6)."""

import logging
import re
from http.cookies import SimpleCookie

import pytest

PERSON_NAME = re.compile(r'class="person-name">([^<]*)<')
PERSON_OFFICE = re.compile(r'class="person-office">([^<]*)<')
ACTIVE = "a@example.com,Amy Active,London,"
GONE = "g@example.com,Gail Gone,Leeds,"


def set_cookie(response) -> SimpleCookie:
    cookie = SimpleCookie()
    for header in response.headers.get_list("set-cookie"):
        cookie.load(header)
    return cookie


@pytest.fixture
def ids(load_csv, people):
    """Amy is active, Gail was dropped by a reload."""
    assert load_csv(ACTIVE, GONE) == 0
    assert load_csv(ACTIVE) == 0
    rows = people()
    return {"active": rows["a@example.com"]["id"], "inactive": rows["g@example.com"]["id"]}


def test_search(client, load_csv):
    # 21 matches: the 20th by name is HANNAH (match inside the name, other case), Joanne is cut.
    matches = [f"Ann Person {i:02d}" for i in range(19)] + ["HANNAH Okafor", "Joanne Price"]
    lines = [f"p{i}@example.com,{name},Leeds," for i, name in enumerate(matches)]
    lines += ["z@example.com,Zara Annex,London,", "bob@example.com,Bob Smith,London,"]
    assert load_csv(*lines) == 0
    assert load_csv(*lines[:-2], "bob@example.com,Bob Smith,London,") == 0  # Zara inactive

    page = client.get("/pick-name", params={"q": "ann"})
    names = PERSON_NAME.findall(page.text)
    assert names == sorted(matches, key=str.lower)[:20]
    assert names[-1] == "HANNAH Okafor"
    assert set(PERSON_OFFICE.findall(page.text)) == {"Leeds"}
    assert "<html" in page.text

    fragment = client.get("/pick-name", params={"q": "ANN"}, headers={"HX-Request": "true"})
    assert PERSON_NAME.findall(fragment.text) == names
    assert "<html" not in fragment.text

    assert "Start typing your name." in client.get("/pick-name", params={"q": "  "}).text
    assert "No one called “Zara”." in client.get("/pick-name", params={"q": "Zara"}).text

    # Case folding beyond ASCII (SQLite's lower() would miss this).
    assert load_csv("o@example.com,Órla Ó Briain,Leeds,") == 0
    assert PERSON_NAME.findall(
        client.get("/pick-name", params={"q": "ó BRIAIN"}).text
    ) == ["Órla Ó Briain"]


@pytest.mark.parametrize(
    ("next_url", "location"),
    [
        ("/?view=today", "/?view=today"),
        (None, "/"),
        ("//evil.example", "/"),
        ("http://evil.example/", "/"),
    ],
    ids=["local-next", "no-next", "protocol-relative", "absolute"],
)
def test_pick_sets_cookie_and_redirects(client, ids, caplog, next_url, location):
    caplog.set_level(logging.INFO, logger="roombooker.people")
    form = {"person_id": str(ids["active"])}
    if next_url is not None:
        form["next"] = next_url

    response = client.post("/pick-name", data=form)

    assert response.status_code == 303
    assert response.headers["location"] == location
    morsel = set_cookie(response)["person_id"]
    assert morsel.value == str(ids["active"])
    assert morsel["max-age"] == str(400 * 24 * 60 * 60)
    assert morsel["httponly"] is True
    assert morsel["samesite"].lower() == "lax"
    assert not morsel["secure"]
    assert f"person_id={ids['active']}" in caplog.text


def test_pick_cookie_is_secure_in_production(client, ids, monkeypatch):
    monkeypatch.setenv("ROOMBOOKER_ENV", "production")
    response = client.post("/pick-name", data={"person_id": str(ids["active"])})
    assert set_cookie(response)["person_id"]["secure"] is True


@pytest.mark.parametrize("who", ["inactive", "unknown", "junk", "oversized"])
def test_pick_refuses_inactive_or_unknown(client, ids, who):
    person_id = {
        "inactive": str(ids["inactive"]),
        "unknown": "9999",
        "junk": "abc",
        "oversized": "9" * 25,
    }[who]

    response = client.post("/pick-name", data={"person_id": person_id, "next": "/?view=today"})

    assert response.status_code == 303
    assert response.headers["location"] == "/pick-name?next=/%3Fview%3Dtoday&gone=1"
    assert "person_id" not in set_cookie(response)
    assert "no longer in the list" in client.get(response.headers["location"]).text


@pytest.mark.parametrize("cookie", [None, "junk", "9999", "99999999999999999999", "inactive"])
@pytest.mark.parametrize("htmx", [False, True], ids=["page", "htmx"])
def test_guarded_page_sends_to_pick_your_name(client, ids, cookie, htmx):
    if cookie == "inactive":
        cookie = str(ids["inactive"])
    if cookie is not None:
        client.cookies.set("person_id", cookie)
    headers = {"HX-Request": "true"} if htmx else {}

    response = client.get("/?view=today", headers=headers)

    target = "/pick-name?next=/%3Fview%3Dtoday"
    if htmx:
        assert response.status_code == 200
        assert response.headers["hx-redirect"] == target
    else:
        assert response.status_code == 303
        assert response.headers["location"] == target
    cleared = set_cookie(response).get("person_id")
    if cookie is None:
        assert cleared is None
    else:
        assert cleared is not None and cleared.value == "" and cleared["max-age"] == "0"
