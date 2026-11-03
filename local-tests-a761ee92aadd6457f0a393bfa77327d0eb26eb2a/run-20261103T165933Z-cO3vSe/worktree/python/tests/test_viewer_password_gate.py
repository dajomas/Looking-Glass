"""Isolated viewer route-body tests; routing, repositories and hub are doubles.

AST loading preserves the actual function bodies but removes decorators and
postpones annotations, allowing execution without installed FastAPI.
"""
import ast
import asyncio
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest


class WebSocketDisconnect(Exception):
    pass


def load_logic():
    path = Path(__file__).resolve().parents[1] / "looking_glass/web/viewer/api.py"
    tree = ast.parse(path.read_text())
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name in ("_session_allowed", "live")]
    assert len(functions) == 2
    for function in functions:
        function.decorator_list = []
    module = ast.Module(body=[ast.ImportFrom(module="__future__",
                        names=[ast.alias(name="annotations")], level=0), *functions], type_ignores=[])
    def resolve(ctx, entry, token):
        return dict(ctx.current) if ctx.valid and ctx.current["active"] and token == "valid" else None
    namespace = dict(asyncio=asyncio, json=json, WebSocketDisconnect=WebSocketDisconnect,
                     SESSION_RECHECK_SECONDS=15, resolve_user=resolve,
                     cookie_name=lambda ws: "lg_viewer_session",
                     token_hash=lambda token: hashlib.sha256(token.encode()).hexdigest(),
                     sessions_repo=SimpleNamespace(lookup_hash=lambda conn, identity, entry:
                         dict(conn.current) if conn.valid and identity == hashlib.sha256(b"valid").hexdigest()
                         and entry == "viewer" else None),
                     campaigns_repo=SimpleNamespace(get=lambda conn, cid: {"id": cid} if conn.exists else None),
                     rbac=SimpleNamespace(can_use_viewer_portal=lambda user: bool(user["active"]),
                                          can_view_campaign=lambda conn, user, campaign: conn.assigned))
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace


class Hub:
    def __init__(self):
        self.subs, self.reports, self.touches = set(), [], []
        self.sync = SimpleNamespace(touch=self.touches.append,
                                    report=lambda key, value: self.reports.append(value))

    async def subscribe(self, cid, ws):
        self.subs.add(ws)
        ws.state.sync_id = "sync"

    async def unsubscribe(self, cid, ws):
        self.subs.discard(ws)

    async def check_access(self, cid, ws):
        if ws not in self.subs:
            return False
        if not ws.state.access_check():
            await ws.close(code=4403)
            self.subs.discard(ws)
            return False
        return True

    async def send_text(self, cid, ws, payload):
        if not await self.check_access(cid, ws):
            return False
        await ws.send_text(payload)
        return True


class Socket:
    def __init__(self, ctx, messages=(), on_accept=None):
        self.app = SimpleNamespace(state=SimpleNamespace(ctx=ctx))
        self.cookies = {"lg_viewer_session": "valid"}
        self.state = SimpleNamespace()
        self.accepted, self.closed, self.sent = False, [], []
        self.messages, self.on_accept = list(messages), on_accept

    async def close(self, code):
        self.closed.append(code)

    async def accept(self):
        self.accepted = True
        if self.on_accept:
            self.on_accept()

    async def receive_text(self):
        if not self.messages:
            raise WebSocketDisconnect()
        message = self.messages.pop(0)
        return message() if callable(message) else message

    async def send_text(self, payload):
        self.sent.append(payload)


@pytest.fixture
def setup():
    ctx = SimpleNamespace(current=dict(id=4, username="viewer", role="viewer", active=1,
                                       must_change_password=0), valid=True, exists=True, assigned=True)
    @contextmanager
    def connect():
        yield ctx
    ctx.db, ctx.hub = SimpleNamespace(connect=connect), Hub()
    return load_logic(), ctx


@pytest.mark.parametrize("role", ["viewer", "admin", "superadmin"])
def test_required_password_change_denies_admission_before_accept_or_subscribe(setup, role):
    logic, ctx = setup
    ctx.current.update(role=role, must_change_password=1)
    ws = Socket(ctx)
    asyncio.run(logic["live"](ws, 1))
    assert not ws.accepted and not ctx.hub.subs
    assert ws.closed == [4403] and ws.sent == [] and ctx.hub.reports == []


@pytest.mark.parametrize("role", ["viewer", "admin", "superadmin"])
def test_session_recheck_observes_password_change_flag(setup, role):
    logic, ctx = setup
    ctx.current["role"] = role
    identity = logic["token_hash"]("valid")
    assert logic["_session_allowed"](ctx, identity, 1)
    ctx.current["must_change_password"] = 1
    assert not logic["_session_allowed"](ctx, identity, 1)
    ctx.current["must_change_password"] = 0
    assert logic["_session_allowed"](ctx, identity, 1)


@pytest.mark.parametrize("role", ["viewer", "admin", "superadmin"])
def test_normal_viewer_ping_and_status_are_unchanged(setup, role):
    logic, ctx = setup
    ctx.current["role"] = role
    report = {"type": "viewer-status", "state": "ready", "version": "blank"}
    ws = Socket(ctx, ["ping", json.dumps(report)])
    asyncio.run(logic["live"](ws, 1))
    assert ws.accepted and ws.closed == []
    assert ws.sent == ['{"type":"pong"}'] and ctx.hub.reports == [report]
    assert not ctx.hub.subs


@pytest.mark.parametrize("attribute", ["valid", "assigned", "exists"])
def test_existing_session_and_campaign_denials_remain(setup, attribute):
    logic, ctx = setup
    setattr(ctx, attribute, False)
    assert not logic["_session_allowed"](ctx, logic["token_hash"]("valid"), 1)
    ws = Socket(ctx)
    asyncio.run(logic["live"](ws, 1))
    assert not ws.accepted and ws.closed == ([4401] if attribute == "valid" else [4404])


def test_inactive_user_still_denied(setup):
    logic, ctx = setup
    ctx.current["active"] = 0
    assert not logic["_session_allowed"](ctx, logic["token_hash"]("valid"), 1)
    ws = Socket(ctx)
    asyncio.run(logic["live"](ws, 1))
    assert not ws.accepted and ws.closed == [4401]


def test_flag_set_during_accept_is_caught_after_subscribe(setup):
    logic, ctx = setup
    ws = Socket(ctx, on_accept=lambda: ctx.current.update(must_change_password=1))
    asyncio.run(logic["live"](ws, 1))
    assert ws.accepted and ws.closed == [4403] and not ctx.hub.subs
    assert ws.sent == [] and ctx.hub.reports == []


@pytest.mark.parametrize("message", ["ping", '{"type":"viewer-status","state":"ready","version":"blank"}'])
def test_flag_set_while_receiving_blocks_pong_and_status(setup, message):
    logic, ctx = setup
    def receive_after_flag():
        ctx.current["must_change_password"] = 1
        return message
    ws = Socket(ctx, [receive_after_flag])
    asyncio.run(logic["live"](ws, 1))
    assert ws.closed == [4403] and not ctx.hub.subs
    assert ws.sent == [] and ctx.hub.reports == [] and ctx.hub.touches == []


def test_idle_timeout_path_rechecks_new_flag(setup):
    logic, ctx = setup
    def flag_and_timeout():
        ctx.current["must_change_password"] = 1
        raise TimeoutError()
    ws = Socket(ctx, [flag_and_timeout])
    asyncio.run(logic["live"](ws, 1))
    assert ws.closed == [4403] and ws.sent == [] and not ctx.hub.subs


def test_reconnect_after_flag_cleared(setup):
    logic, ctx = setup
    ctx.current["must_change_password"] = 1
    first = Socket(ctx)
    asyncio.run(logic["live"](first, 1))
    assert not first.accepted and first.closed == [4403]
    ctx.current["must_change_password"] = 0
    second = Socket(ctx, ["ping"])
    asyncio.run(logic["live"](second, 1))
    assert second.accepted and second.closed == [] and second.sent == ['{"type":"pong"}']


def test_real_hub_blocks_event_when_password_gate_becomes_required(setup):
    from looking_glass.services.events import EventHub
    logic, ctx = setup
    async def run():
        hub = EventHub()
        ws = Socket(ctx)
        ws.state.access_check = lambda: logic["_session_allowed"](ctx, logic["token_hash"]("valid"), 1)
        await hub.subscribe(1, ws)
        await hub.publish(1, {"type": "refresh"})
        assert len(ws.sent) == 1
        ctx.current["must_change_password"] = 1
        await hub.publish(1, {"type": "focus"})
        assert len(ws.sent) == 1 and ws.closed == [4403] and hub.viewer_count(1) == 0
    asyncio.run(run())
