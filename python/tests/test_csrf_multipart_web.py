"""Bug 22: malformed multipart CSRF tokens must not reach account writes."""

import pytest

from looking_glass.repositories import users as users_repo
from test_web import csrf_of, env, login


CASES = [
    ("missing", 403),
    ("empty", 403),
    ("wrong", 403),
    ("file", 403),
    ("file_matching_token", 403),
    ("valid_form", 303),
    ("valid_header", 303),
    ("header_over_file", 303),
    ("wrong_header_over_valid_form", 403),
    ("empty_header_fallback", 303),
]


def user_snapshot(ctx, username):
    with ctx.db.connect() as conn:
        return dict(users_repo.get_with_hash(conn, username))


@pytest.mark.parametrize("portal,username,password", [
    (1, "dm", "dmpass123"),
    (2, "alice", "alicepass"),
], ids=["admin", "viewer"])
@pytest.mark.parametrize("case,expected_status", CASES, ids=[case for case, _ in CASES])
def test_account_multipart_csrf(env, portal, username, password, case, expected_status):
    ctx = env[0]
    with login(env[portal], username, password) as client:
        token = csrf_of(client, "/account")
        before = user_snapshot(ctx, username)
        changed_name = "Bug 22 profile update"
        # A harmless file forces real multipart parsing even when the token is absent.
        parts = [("display_name", (None, changed_name)),
                 ("unused_upload", ("unused.txt", b"unused", "text/plain"))]
        headers = {}
        if case == "empty":
            parts.append(("csrf_token", (None, "")))
        elif case == "wrong":
            parts.append(("csrf_token", (None, "definitely-not-the-token")))
        elif case in ("file", "file_matching_token", "header_over_file"):
            content = token.encode() if case == "file_matching_token" else b"not-a-text-field"
            parts.append(("csrf_token", ("token.txt", content, "text/plain")))
        elif case in ("valid_form", "wrong_header_over_valid_form", "empty_header_fallback"):
            parts.append(("csrf_token", (None, token)))

        if case in ("valid_header", "header_over_file"):
            headers["X-CSRF-Token"] = token
        elif case == "wrong_header_over_valid_form":
            headers["X-CSRF-Token"] = "definitely-not-the-token"
        elif case == "empty_header_fallback":
            headers["X-CSRF-Token"] = ""

        # Keep TestClient's default exception propagation: a server exception fails the test.
        response = client.post("/account", files=parts, headers=headers, follow_redirects=False)
        assert response.status_code == expected_status, response.text
        after = user_snapshot(ctx, username)
        if expected_status == 403:
            assert "Invalid or missing CSRF token." in response.text
            assert after == before
        else:
            assert response.headers["location"] == "/account?ok=Account+updated"
            assert after["display_name"] == changed_name
            assert {k: v for k, v in after.items() if k != "display_name"} == {
                k: v for k, v in before.items() if k != "display_name"
            }
        assert client.get("/account", follow_redirects=False).status_code == 200
