"""Short-lived, bounded verification/catalog cache for automatic room lookups."""
import hashlib
import json
import math
import threading
import time
from . import scrying_glass as sg

SUCCESS_TTL = 60
FAILURE_TTL = 30
MAX_ENTRIES = 8

class CatalogCache:
    def __init__(self, clock=time.monotonic, fetcher=None):
        self.clock = clock
        self.fetcher = fetcher
        self.lock = threading.Lock()
        self.entries = {}

    def catalog(self, raw):
        config = sg.options(raw)
        if config is None:
            return None, SUCCESS_TTL
        key = hashlib.sha256(json.dumps([config.base_url, config.username, config.password, config.timeout]).encode()).hexdigest()
        # One bounded network refresh at a time, including concurrent browser tabs.
        with self.lock:
            now = self.clock()
            self.entries = {k: v for k, v in self.entries.items() if v[0] > now}
            entry = self.entries.get(key)
            if entry is None:
                try:
                    payload = (self.fetcher or sg.fetch_catalog)(config)
                    sg.match_catalog(payload, "", "")  # Validate catalog shape before caching.
                    entry = (self.clock() + SUCCESS_TTL, payload, None)
                except sg.LookupError as exc:
                    entry = (self.clock() + FAILURE_TTL, None, str(exc))
                if len(self.entries) >= MAX_ENTRIES:
                    del self.entries[next(iter(self.entries))]
                self.entries[key] = entry
            if entry[2] is not None:
                raise sg.LookupError(entry[2])
            return entry[1], max(1, math.ceil(entry[0] - self.clock()))

cache = CatalogCache()

def _gate(payload, campaign_name, ttl):
    if payload is None:
        return {"enabled": False, "verified": False, "status": "disabled", "retry_after_seconds": ttl, "message": ""}
    result = sg.match_catalog(payload, campaign_name, "")
    verified = result["status"] == "invalid_room_name"
    return {"enabled": True, "verified": verified, "status": "verified" if verified else result["status"],
            "retry_after_seconds": ttl, "message": "" if verified else result["message"]}

def access(raw, campaign_name):
    payload, ttl = cache.catalog(raw)
    return _gate(payload, campaign_name, ttl)

def lookup(raw, campaign_name, room_name):
    # Even a direct API request cannot initiate room matching for an unnamed area.
    if not room_name.strip():
        if sg.options(raw) is None:
            return {"enabled": False, "verified": False, "matched": False, "status": "disabled", "message": ""}
        return {"matched": False, "status": "unnamed_room", "message": "Save a room name before checking Scrying Glass."}
    payload, ttl = cache.catalog(raw)
    gate = _gate(payload, campaign_name, ttl)
    if not gate["verified"]:
        return {**gate, "matched": False}
    return {**sg.match_catalog(payload, campaign_name, room_name), "enabled": True, "verified": True, "retry_after_seconds": ttl}
