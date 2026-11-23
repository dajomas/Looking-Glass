"""I1: a completed forced password change continues to the user's destination."""
import re
from urllib.parse import quote

import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from test_web import csrf_of, env, login
from looking_glass.repositories import users

ORIGIN = {"Origin": "http://testserver"}


@pytest.fixture
def forced(env):
    """A campaign with a newly created viewer who must change their password."""
    ctx, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    token = csrf_of(dm)
    cid = int(dm.post("/campaigns", data={"csrf_token": token, "name": "C"}, follow_redirects=False)
              .headers["location"].split("/")[2].split("?")[0])
    created = dm.post(f"/campaigns/{cid}/viewers/create",
                      data={"csrf_token": token, "username": "newbie", "password": "temp-pass-1"},
                      follow_redirects=False)
    assert "ok=" in created.headers["location"]
    with ctx.db.connect() as conn:
        assert users.get_with_hash(conn, "newbie")["must_change_password"]
    return ctx, viewer, cid


def change(client, path, **extra):
    data = {"csrf_token": csrf_of(client, path), "current_password": "temp-pass-1",
            "new_password": "brand-new-pw", "confirm_password": "brand-new-pw"}
    data.update(extra)
    return client.post("/account", data=data, follow_redirects=False)


def test_login_with_destination_carries_it_through_the_forced_change(forced):
    _, viewer, cid = forced
    client = TestClient(viewer)
    response = client.post("/login", data={"username": "newbie", "password": "temp-pass-1", "next": f"/c/{cid}"},
                           headers=ORIGIN, follow_redirects=False)
    account = f"/account?next={quote(f'/c/{cid}', safe='')}"
    assert response.headers["location"] == account
    page = client.get(account).text
    assert re.search(rf'<input type="hidden" name="next" value="/c/{cid}">', page)
    done = change(client, account, next=f"/c/{cid}")
    assert done.status_code == 303 and done.headers["location"] == f"/c/{cid}"
    assert client.get(f"/c/{cid}", follow_redirects=False).status_code == 200


def test_direct_link_while_forced_returns_to_it_after_the_change(forced):
    _, viewer, cid = forced
    client = TestClient(viewer)
    assert client.post("/login", data={"username": "newbie", "password": "temp-pass-1"},
                       headers=ORIGIN, follow_redirects=False).headers["location"] == "/account"
    redirect = client.get(f"/c/{cid}", follow_redirects=False)
    assert redirect.status_code == 303 and redirect.headers["location"] == f"/account?next=%2Fc%2F{cid}"
    done = change(client, redirect.headers["location"], next=f"/c/{cid}")
    assert done.headers["location"] == f"/c/{cid}"


def test_forced_change_without_destination_goes_to_the_start_page(forced):
    _, viewer, cid = forced
    client = TestClient(viewer)
    client.post("/login", data={"username": "newbie", "password": "temp-pass-1"}, headers=ORIGIN)
    page = client.get("/account").text
    assert 'name="next"' not in page
    done = change(client, "/account")
    assert done.status_code == 303 and done.headers["location"] == "/"
    # The viewer start page forwards the only campaign's player to its map.
    assert client.get("/").status_code == 200


@pytest.mark.parametrize("target", ["//evil.example/", "/\\evil.example", "https://evil.example/",
                                    "/%2F%2Fevil.example", "javascript:alert(1)"])
def test_unsafe_destinations_are_never_followed(forced, target):
    _, viewer, _ = forced
    client = TestClient(viewer)
    response = client.post("/login", data={"username": "newbie", "password": "temp-pass-1", "next": target},
                           headers=ORIGIN, follow_redirects=False)
    assert response.headers["location"] == "/account"
    assert 'name="next"' not in client.get(f"/account?next={quote(target, safe='')}").text
    assert change(client, "/account", next=target).headers["location"] == "/"


def test_failed_forced_change_keeps_the_destination(forced):
    _, viewer, cid = forced
    client = TestClient(viewer)
    client.post("/login", data={"username": "newbie", "password": "temp-pass-1", "next": f"/c/{cid}"},
                headers=ORIGIN)
    failed = change(client, f"/account?next=%2Fc%2F{cid}", next=f"/c/{cid}", confirm_password="different-pw")
    assert failed.status_code == 400
    assert f'<input type="hidden" name="next" value="/c/{cid}">' in failed.text


@pytest.mark.parametrize("portal", ["admin", "viewer"])
def test_voluntary_changes_still_stay_on_the_account_page(env, portal):
    ctx, admin, viewer = env
    username, password = ("dm", "dmpass123") if portal == "admin" else ("alice", "alicepass")
    client = login(admin if portal == "admin" else viewer, username, password)
    data = {"csrf_token": csrf_of(client, "/account"), "display_name": "Renamed", "current_password": password,
            "new_password": "another-pass-9", "confirm_password": "another-pass-9", "next": "/somewhere"}
    response = client.post("/account", data=data, follow_redirects=False)
    assert response.headers["location"] == "/account?ok=Account+updated"


def test_admin_portal_forced_change_continues_to_the_dashboard(env):
    ctx, admin, _ = env
    with ctx.db.connect() as conn:
        conn.execute("UPDATE users SET must_change_password=1 WHERE username='dm'")
    client = TestClient(admin)
    assert client.post("/login", data={"username": "dm", "password": "dmpass123"},
                       headers=ORIGIN, follow_redirects=False).headers["location"] == "/account"
    data = {"csrf_token": csrf_of(client, "/account"), "current_password": "dmpass123",
            "new_password": "dm-new-pass-1", "confirm_password": "dm-new-pass-1"}
    assert client.post("/account", data=data, follow_redirects=False).headers["location"] == "/"
    assert client.get("/", follow_redirects=False).status_code == 200
