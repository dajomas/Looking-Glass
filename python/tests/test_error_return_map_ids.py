"""Raw router IDs must be parsed before building an authorized editor return link."""
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from looking_glass.web import errors


@pytest.fixture
def return_request():
    @contextmanager
    def connection():
        yield object()

    def make(raw_id):
        return SimpleNamespace(
            method="POST", url=SimpleNamespace(path=f"/maps/{raw_id}/image"),
            path_params={"map_id": raw_id},
            state=SimpleNamespace(user={"must_change_password": False}),
            app=SimpleNamespace(state=SimpleNamespace(entry="admin",
                ctx=SimpleNamespace(db=SimpleNamespace(connect=connection)))))
    return make


@pytest.mark.parametrize("raw_id", ["7", 7, "007"])
def test_valid_raw_id_returns_canonical_authorized_map(monkeypatch, return_request, raw_id):
    access = Mock()
    monkeypatch.setattr(errors, "map_for_manage", access)
    request = return_request(raw_id)
    assert errors._replacement_return_map(request) == "/maps/7"
    access.assert_called_once()
    assert access.call_args.args[1] is request.state.user
    assert access.call_args.args[2] == 7
    assert type(access.call_args.args[2]) is int


@pytest.mark.parametrize("raw_id", [
    None, True, 7.0, "", "bad", "0", "-7", "https://untrusted.invalid",
    "７", "7/../8", "7\n", "9" * 5000, "9223372036854775808",
], ids=["missing", "boolean", "float", "empty", "letters", "zero", "negative",
        "external-url", "unicode-digits", "path", "whitespace", "oversized", "sqlite-overflow"])
def test_invalid_raw_id_has_no_link_or_permission_lookup(monkeypatch, return_request, raw_id):
    access = Mock()
    monkeypatch.setattr(errors, "map_for_manage", access)
    assert errors._replacement_return_map(return_request(raw_id)) is None
    access.assert_not_called()


@pytest.mark.parametrize("denied", [errors.Forbidden, errors.NotFound])
def test_string_route_id_still_requires_map_permission(monkeypatch, return_request, denied):
    access = Mock(side_effect=denied())
    monkeypatch.setattr(errors, "map_for_manage", access)
    assert errors._replacement_return_map(return_request("7")) is None
    access.assert_called_once()
    assert access.call_args.args[2] == 7
