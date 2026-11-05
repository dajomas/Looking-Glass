"""Fail-closed origin policy for pre-authentication login submissions."""
from urllib.parse import urlsplit


def _origin(value: str, *, referer: bool = False) -> tuple[str, str, int] | None:
    if not value or any(ord(c) <= 32 or ord(c) == 127 or c in "\\," for c in value):
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.fragment or "%" in parsed.hostname or parsed.netloc.endswith(":")):
            return None
        if not referer and (parsed.path or parsed.query):
            return None
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80
        if not 0 < port <= 65535:
            return None
        return parsed.scheme, parsed.hostname.lower(), port
    except ValueError:
        return None


def login_request_allowed(target: str, origins: list[str], referers: list[str]) -> bool:
    """Origin takes precedence; Referer is a fallback only when Origin is absent.

    Target comes from the ASGI request, not untrusted forwarding headers. Missing,
    opaque, malformed or duplicate source headers never authorize a login.
    """
    expected = _origin(target, referer=True)
    if expected is None or len(origins) > 1 or len(referers) > 1:
        return False
    if origins:
        return _origin(origins[0]) == expected
    if referers:
        return _origin(referers[0], referer=True) == expected
    return False
