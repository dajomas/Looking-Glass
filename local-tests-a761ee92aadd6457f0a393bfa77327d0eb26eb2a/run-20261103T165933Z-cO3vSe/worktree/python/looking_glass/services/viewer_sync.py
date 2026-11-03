"""Ephemeral, per-socket display diagnostics; no persistent play-state writes."""
import time
import uuid


def display_version(m):
    return "blank" if m is None else f"{m['id']}:{m['cache_token']}-{m['walls_version']}-{m['fog_version']}"


class ViewerSync:
    STALE_SECONDS = 65
    RETAIN_SECONDS = 90

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.records = {}

    def _prune(self):
        now = self.clock()
        for key, row in list(self.records.items()):
            if row["closed"] is not None and now-row["closed"] > self.RETAIN_SECONDS:
                del self.records[key]
        closed = sorted((r["closed"], k) for k,r in self.records.items() if r["closed"] is not None)
        for _, key in closed[:-1024]:
            del self.records[key]

    def connect(self, campaign_id, user_id, username):
        self._prune()
        key = uuid.uuid4().hex
        self.records[key] = {"campaign_id":campaign_id, "user_id":user_id,
                             "username":str(username)[:120], "seen":self.clock(), "closed":None,
                             "state":"connected", "version":None}
        return key

    def disconnect(self, key):
        row = self.records.get(key)
        if row and row["closed"] is None:
            row["closed"] = self.clock()
        self._prune()

    def touch(self, key):
        row = self.records.get(key)
        if row and row["closed"] is None:
            row["seen"] = self.clock()

    def report(self, key, message):
        row = self.records.get(key)
        if not row or row["closed"] is not None or not isinstance(message,dict):
            return False
        state, version = message.get("state"), message.get("version")
        if message.get("type") != "viewer-status" or state not in ("loading","ready","failed"):
            return False
        if not isinstance(version,str) or not 1 <= len(version) <= 200:
            return False
        row.update(state=state, version=version, seen=self.clock())
        return True

    def snapshot(self, campaign_id, expected):
        self._prune()
        now = self.clock()
        rows = []
        for key,row in self.records.items():
            if row["campaign_id"] != campaign_id:
                continue
            age = max(0,int(now-row["seen"]))
            if row["closed"] is not None or now-row["seen"] > self.STALE_SECONDS:
                status = "reconnecting"
            elif row["state"] == "connected":
                status = "connected"
            elif row["state"] == "failed":
                status = "failed"
            elif row["version"] != expected:
                status = "loading"
            elif row["state"] == "ready":
                status = "up-to-date"
            else:
                status = row["state"]
            rows.append({"id":key[:12], "username":row["username"], "status":status,
                         "last_report_seconds":age, "connected":row["closed"] is None})
        return {"viewers":rows, "counts":{s:sum(r["status"]==s for r in rows)
                for s in ("connected","loading","up-to-date","failed","reconnecting")},
                "blank":expected=="blank", "stale_after_seconds":self.STALE_SECONDS,
                "retained_for_seconds":self.RETAIN_SECONDS}
