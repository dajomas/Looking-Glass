"""Bugs 20/21: HTTP contracts; intentionally red before the login fixes.

Use real apps/SQLite. These are not browser exploitability tests.
"""
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from test_web import env


class HiddenFields(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("type") == "hidden" and attrs.get("name"):
            self.values[attrs["name"]] = attrs.get("value", "")


def form_data(client, target="/"):
    response = client.get("/login", params={"next": target}, follow_redirects=False)
    assert response.status_code == 200
    parser = HiddenFields()
    parser.feed(response.text)
    return {**parser.values, "username": "root", "password": "rootpass1"}


@pytest.mark.parametrize("portal", [1, 2], ids=["admin", "viewer"])
@pytest.mark.parametrize("target", ["/\\example.invalid", "//example.invalid", "/\texample.invalid"])
def test_unsafe_next_is_local_after_login_and_authenticated_visit(env, portal, target):
    with TestClient(env[portal], base_url="http://testserver") as client:
        data = form_data(client)
        data["next"] = target
        response = client.post("/login", data=data, headers={"Origin": "http://testserver"},
                               follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/"
        response = client.get("/login", params={"next": target}, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/"


@pytest.mark.parametrize("portal", [1, 2], ids=["admin", "viewer"])
def test_same_origin_login_preserves_local_query(env, portal):
    with TestClient(env[portal], base_url="http://testserver") as client:
        data = form_data(client, "/account?ok=hello%20world")
        response = client.post("/login", data=data, headers={"Origin": "http://testserver"},
                               follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/account?ok=hello%20world"
        assert client.get("/account", follow_redirects=False).status_code == 200


@pytest.mark.parametrize("portal,cookie", [(1, "lg_admin_session"), (2, "lg_viewer_session")],
                         ids=["admin", "viewer"])
@pytest.mark.parametrize("origin", ["https://example.invalid", "null"])
def test_cross_site_login_without_challenge_cannot_establish_session(env, portal, cookie, origin):
    with TestClient(env[portal], base_url="http://testserver") as client:
        response = client.post("/login", data={"username": "root", "password": "rootpass1"},
                               headers={"Origin": origin, "Sec-Fetch-Site": "cross-site"},
                               follow_redirects=False)
        assert response.status_code == 403
        assert cookie not in client.cookies
        assert not any(value.startswith(cookie + "=") for value in response.headers.get_list("set-cookie"))
        denied = client.get("/account", follow_redirects=False)
        assert denied.status_code == 303
        assert denied.headers["location"].startswith("/login")
