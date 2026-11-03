"""Read-only Scrying Glass catalog lookup; credentials and cookies never leave Python."""
import json
import math
import os
import re
import socket
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPCookieProcessor, HTTPRedirectHandler, ProxyHandler

MAX_RESPONSE = 2 * 1024 * 1024

class LookupError(Exception):
    """Safe error text suitable for the admin UI (never upstream bodies or secrets)."""

@dataclass(frozen=True)
class Options:
    base_url: str
    username: str
    password: str = field(repr=False)
    timeout: float = 5.0

def options(raw):
    if not isinstance(raw, dict) or type(raw.get("enabled", False)) is not bool:
        raise LookupError("Invalid Scrying Glass enabled setting.")
    if not raw.get("enabled", False):
        return None
    base = raw.get("base_url", "")
    if not isinstance(base, str):
        raise LookupError("Scrying Glass base_url must be an HTTP(S) origin.")
    try:
        parsed = urlsplit(base)
        port = parsed.port
    except ValueError:
        raise LookupError("Invalid Scrying Glass base_url.") from None
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
            or any(c.isspace() for c in base)):
        raise LookupError("Scrying Glass base_url must be an HTTP(S) origin without credentials, path, query or fragment.")
    username = raw.get("username", "")
    env = raw.get("password_env", "LG_SCRYING_GLASS_PASSWORD")
    if not isinstance(env, str):
        raise LookupError("Invalid Scrying Glass password_env setting.")
    password = os.environ.get(env, "") if env else ""
    password = password or raw.get("password", "")
    if not isinstance(username, str) or not username.strip() or not isinstance(password, str) or not password:
        raise LookupError("Configure the Scrying Glass account and password (or password environment variable).")
    try:
        timeout = float(raw.get("timeout_seconds", 5))
    except (TypeError, ValueError):
        raise LookupError("Scrying Glass timeout_seconds must be between 1 and 30.") from None
    if not math.isfinite(timeout) or not 1 <= timeout <= 30:
        raise LookupError("Scrying Glass timeout_seconds must be between 1 and 30.")
    return Options(base.rstrip("/"), username, password, timeout)

def setup_slug(name):
    return re.sub("[^a-z0-9]+", "-", name.strip().lower()).strip("-")[:80].rstrip("-")

def match_catalog(payload, campaign_name, room_name):
    if not isinstance(payload, dict) or not isinstance(payload.get("campaigns"), list):
        raise LookupError("Scrying Glass returned an invalid campaign catalog.")
    campaigns = payload["campaigns"]
    if any(not isinstance(c, dict) or not isinstance(c.get("name"), str) for c in campaigns):
        raise LookupError("Scrying Glass returned an invalid campaign catalog.")
    matches = [c for c in campaigns if c["name"].strip() == campaign_name.strip()]
    slug = setup_slug(room_name)
    result = {"campaign_name": campaign_name, "room_name": room_name, "setup_name": slug, "matched": False}
    if len(matches) > 1:
        return {**result, "status": "ambiguous_campaign", "message": "More than one accessible Scrying Glass campaign has this name."}
    if not matches:
        return {**result, "status": "campaign_not_accessible", "message": "No matching campaign is visible to the configured Scrying Glass account (it may be missing or unassigned)."}
    campaign = matches[0]
    if not isinstance(campaign.get("id"), (str, int)) or not isinstance(campaign.get("setups"), list) or any(not isinstance(s, str) for s in campaign["setups"]):
        raise LookupError("Scrying Glass returned an invalid campaign catalog.")
    result["campaign_id"] = str(campaign["id"])
    if not slug:
        return {**result, "status": "invalid_room_name", "message": "The saved room name does not produce a valid Scrying Glass setup name."}
    found = slug in campaign["setups"]
    return {**result, "matched": found, "status": "matched" if found else "setup_not_found",
            "message": f"Matching battle setup found: {slug}." if found else f"No battle setup named {slug} in the matching campaign."}

class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def fetch_catalog(config, opener_factory=build_opener):
    jar = CookieJar()
    # No environment proxies, redirects, credential persistence, or TLS bypass.
    opener = opener_factory(ProxyHandler({}), HTTPCookieProcessor(jar), NoRedirects())
    body = urlencode({"username": config.username, "password": config.password}).encode()
    request = Request(config.base_url + "/login", data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        try:
            with opener.open(request, timeout=config.timeout) as response:
                # Valid Scrying Glass logins redirect; a 200 login page is failure.
                raise LookupError("Scrying Glass sign-in failed. Check the configured account and role.")
        except HTTPError as exc:
            code = exc.code
            location = exc.headers.get("Location", "")
            exc.close()
            if code != 303 or location not in {"/", "/users"} or not list(jar):
                raise LookupError("Scrying Glass sign-in failed. Check the configured account and role.") from None
        with opener.open(Request(config.base_url + "/api/campaigns", headers={"Accept": "application/json"}), timeout=config.timeout) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise LookupError("Scrying Glass campaign catalog exceeds the 2 MiB safety limit.")
            try:
                return json.loads(raw)
            except (ValueError, UnicodeError):
                raise LookupError("Scrying Glass returned an invalid campaign catalog.") from None
    except HTTPError as exc:
        code = exc.code
        exc.close()
        if code in {401, 403}:
            raise LookupError("Scrying Glass denied catalog access. Check the account and campaign assignment.") from None
        raise LookupError("Scrying Glass returned an HTTP error.") from None
    except (URLError, TimeoutError, socket.timeout, OSError):
        raise LookupError("Cannot reach Scrying Glass. Check the admin address, port, TLS and timeout.") from None
    finally:
        jar.clear()

def lookup(raw, campaign_name, room_name):
    config = options(raw)
    if config is None:
        return {"matched": False, "status": "disabled", "message": "Scrying Glass lookup is disabled in config.yaml."}
    if not room_name.strip():
        return {"matched": False, "status": "unnamed_room", "message": "Save a room name before checking Scrying Glass."}
    return match_catalog(fetch_catalog(config), campaign_name, room_name)
