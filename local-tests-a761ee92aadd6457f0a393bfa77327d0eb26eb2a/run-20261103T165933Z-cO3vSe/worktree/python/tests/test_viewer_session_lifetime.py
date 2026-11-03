"""Session repository and hub regressions; transport is deliberately mocked."""
import asyncio
import sqlite3
from types import SimpleNamespace


from looking_glass.repositories import sessions
from looking_glass.security import token_hash
from looking_glass.services.events import EventHub


class Socket:
    def __init__(self, token="one", user_id=7, allowed=lambda: True):
        self.state = SimpleNamespace(user_id=user_id, username="Viewer",
                                     session_hash=token_hash(token), access_check=allowed)
        self.sent = []
        self.closed = []

    async def send_text(self, payload):
        self.sent.append(payload)

    async def close(self, code):
        self.closed.append(code)


def test_lookup_hash_matches_raw_lookup_and_portal(monkeypatch):
    monkeypatch.setattr(sessions.time, "time", lambda: 100)
    with sqlite3.connect(":memory:") as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE users (id INTEGER, username TEXT, display_name TEXT,
                                role TEXT, active INTEGER, must_change_password INTEGER);
            CREATE TABLE sessions (token_hash TEXT, user_id INTEGER, entry TEXT,
                                   csrf_token TEXT, expires_at INTEGER);
            INSERT INTO users VALUES (7, 'viewer', 'Viewer', 'viewer', 1, 0);
        """)
        token, _ = sessions.create(conn, 7, "viewer", 10)
        identity = token_hash(token)
        assert dict(sessions.lookup_hash(conn, identity, "viewer")) == dict(sessions.lookup(conn, token, "viewer"))
        assert sessions.lookup_hash(conn, identity, "admin") is None
        assert sessions.lookup_hash(conn, token, "viewer") is None
        monkeypatch.setattr(sessions.time, "time", lambda: 110)
        assert sessions.lookup_hash(conn, identity, "viewer") is None
        monkeypatch.setattr(sessions.time, "time", lambda: 100)
        sessions.delete(conn, token)
        assert sessions.lookup_hash(conn, identity, "viewer") is None


def test_session_kick_isolates_sessions_and_covers_campaigns():
    async def run():
        hub = EventHub()
        a, b, c, other = Socket(), Socket(), Socket("two"), Socket("other", 8)
        for cid, ws in [(1, a), (2, b), (1, c), (1, other)]:
            await hub.subscribe(cid, ws)
        await hub.kick_session(token_hash("one"))
        await hub.publish(1, {"type": "refresh"})
        assert a.closed == b.closed == [4403]
        assert a.sent == b.sent == []
        assert c.closed == other.closed == []
        assert len(c.sent) == len(other.sent) == 1
        assert hub.viewer_count(1) == 2 and hub.viewer_count(2) == 0
        assert not hub.sync.snapshot(2, "blank")["viewers"][0]["connected"]
        assert "one" not in vars(a.state).values()
    asyncio.run(run())


def test_publish_rechecks_access_before_every_event():
    async def run():
        allowed = [True]
        hub, ws = EventHub(), Socket(allowed=lambda: allowed[0])
        await hub.subscribe(1, ws)
        await hub.publish(1, {"type": "refresh"})
        allowed[0] = False
        await hub.publish(1, {"type": "focus"})
        await hub.publish(1, {"type": "refresh"})
        assert len(ws.sent) == 1 and ws.closed == [4403]
        assert hub.viewer_count(1) == 0
    asyncio.run(run())


def test_idle_access_check_closes_without_an_event():
    async def run():
        hub, ws = EventHub(), Socket(allowed=lambda: False)
        await hub.subscribe(1, ws)
        assert not await hub.check_access(1, ws)
        assert ws.closed == [4403] and ws.sent == []
        assert not await hub.check_access(1, ws)
        assert ws.closed == [4403]
    asyncio.run(run())


def test_pong_uses_same_guard():
    async def run():
        hub, ws = EventHub(), Socket(allowed=lambda: False)
        await hub.subscribe(1, ws)
        assert not await hub.send_text(1, ws, '{"type":"pong"}')
        assert ws.sent == [] and ws.closed == [4403]
    asyncio.run(run())


def test_access_check_exception_fails_closed():
    def broken():
        raise sqlite3.OperationalError("database unavailable")
    async def run():
        hub, ws = EventHub(), Socket(allowed=broken)
        await hub.subscribe(1, ws)
        await hub.publish(1, {"type": "refresh"})
        assert ws.sent == [] and ws.closed == [4403]
    asyncio.run(run())


def test_close_failure_still_detaches_socket():
    async def broken_close(code):
        raise RuntimeError("gone")
    async def run():
        hub, ws = EventHub(), Socket()
        ws.close = broken_close
        await hub.subscribe(1, ws)
        await hub.kick_session(ws.state.session_hash)
        assert hub.viewer_count(1) == 0
        assert not hub.sync.records[ws.state.sync_id]["closed"] is None
    asyncio.run(run())


def test_send_failure_does_not_break_other_viewers():
    async def broken_send(payload):
        raise RuntimeError("gone")
    async def run():
        hub, bad, good = EventHub(), Socket(), Socket("two")
        bad.send_text = broken_send
        await hub.subscribe(1, bad)
        await hub.subscribe(1, good)
        await hub.publish(1, {"type": "refresh"})
        assert len(good.sent) == 1 and hub.viewer_count(1) == 1
    asyncio.run(run())


def test_kick_user_preserves_existing_scope():
    async def run():
        hub, a, b, other = EventHub(), Socket(), Socket("two"), Socket("other", 8)
        for ws in (a, b, other):
            await hub.subscribe(1, ws)
        await hub.kick_user(7)
        assert a.closed == b.closed == [4403] and other.closed == []
        assert hub.viewer_count(1) == 1
    asyncio.run(run())


def test_unsubscribe_and_unknown_kicks_are_idempotent():
    async def run():
        hub, ws = EventHub(), Socket()
        await hub.subscribe(1, ws)
        await hub.unsubscribe(1, ws)
        await hub.unsubscribe(1, ws)
        await hub.kick_session(token_hash("missing"))
        await hub.publish(1, {"type": "refresh"})
        assert ws.sent == ws.closed == [] and not hub._subs
    asyncio.run(run())


def test_kick_waits_for_inflight_send_and_prevents_later_sends():
    async def run():
        hub, ws = EventHub(), Socket()
        entered, release = asyncio.Event(), asyncio.Event()
        async def slow_send(payload):
            entered.set()
            await release.wait()
            ws.sent.append(payload)
        ws.send_text = slow_send
        await hub.subscribe(1, ws)
        sending = asyncio.create_task(hub.publish(1, {"type": "refresh"}))
        await entered.wait()
        kicking = asyncio.create_task(hub.kick_session(ws.state.session_hash))
        await asyncio.sleep(0)
        assert not kicking.done()
        release.set()
        await asyncio.gather(sending, kicking)
        await hub.publish(1, {"type": "focus"})
        assert len(ws.sent) == 1 and ws.closed == [4403]
    asyncio.run(run())
