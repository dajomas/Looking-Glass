"""Real loopback servers, not intercepted HTTP or mocked WebSockets."""
import asyncio
import copy
import importlib
import json
import queue
import socket
import threading
import time
from contextlib import ExitStack
from urllib.error import URLError
from urllib.request import urlopen

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    setattr(item, "rep_" + outcome.get_result().when, outcome.get_result())


def require(name):
    try:
        return importlib.import_module(name)
    except ImportError as error:
        pytest.fail(f"Live E2E requires {name}: {error}. Install requirements-dev.txt and Playwright.", pytrace=False)


@pytest.fixture(scope="session")
def live_browser():
    pw = require("playwright.sync_api")
    with pw.sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture
def live_servers(tmp_path):
    require("fastapi")
    uvicorn = require("uvicorn")
    from looking_glass.config import DEFAULTS, Settings
    from looking_glass.rbac import Role
    from looking_glass.repositories import users
    from looking_glass.server import _Server, BROWSER_BLOCKED_PORTS
    from looking_glass.services import images
    from looking_glass.web.app_factory import create_admin_app, create_viewer_app
    from looking_glass.web.context import AppContext

    # Never load config.yaml, LG_CONFIG, LG_DATA_DIR, bootstrap files or real users.
    raw = copy.deepcopy(DEFAULTS)
    raw["storage"].update(data_dir=str(tmp_path / "data"), database="live-test.db")
    raw["fog"].update(work_max_dim=400, feather_px=0)
    raw["viewer"]["image_format"] = "png"
    raw["security"]["secure_cookies"] = False
    settings = Settings(raw=raw)
    started = queue.Queue()
    servers, sockets, failures = [], [], []
    loop_holder = []

    async def run():
        loop_holder.append(asyncio.get_running_loop())
        images.configure(int(raw["storage"]["max_image_pixels"]))
        ctx = AppContext.build(settings)
        with ctx.db.connect() as conn:
            users.create(conn, "live-dm", "live-dm-password", Role.ADMIN)
            users.create(conn, "live-player", "live-player-password", Role.VIEWER)
            # Preserve existing IDs 1/2; revocation controls use viewer 3 and root 4.
            users.create(conn, "live-other-player", "live-other-player-password", Role.VIEWER)
            users.create(conn, "live-root", "live-root-password", Role.SUPERADMIN)
        urls = []
        for app in (create_admin_app(ctx), create_viewer_app(ctx)):
            while True:
                sock = socket.socket()
                sock.bind(("127.0.0.1", 0))
                if sock.getsockname()[1] not in BROWSER_BLOCKED_PORTS:
                    break
                sock.close()
            sock.listen(128)
            sockets.append(sock)
            urls.append(f"http://127.0.0.1:{sock.getsockname()[1]}")
            servers.append(_Server(uvicorn.Config(app, host="127.0.0.1", log_level="warning",
                                                  access_log=False, timeout_graceful_shutdown=3)))
        started.put(tuple(urls))
        await asyncio.gather(*(server.serve(sockets=[sock]) for server, sock in zip(servers, sockets)))

    def worker():
        try:
            asyncio.run(run())
        except BaseException as error:
            failures.append(repr(error))
            started.put(error)
        finally:
            for sock in sockets:
                sock.close()

    thread = threading.Thread(target=worker, daemon=True, name="looking-glass-live-e2e")
    thread.start()
    try:
        try:
            result = started.get(timeout=20)
        except queue.Empty:
            pytest.fail("Live servers did not initialize within 20 seconds")
        if isinstance(result, BaseException):
            pytest.fail(f"Live server startup failed: {result!r}")
        for url, entry in zip(result, ("admin", "viewer")):
            deadline = time.monotonic() + 15
            while True:
                if failures:
                    pytest.fail(f"Live server failed: {failures}")
                try:
                    with urlopen(url + "/healthz", timeout=1) as response:
                        payload = json.load(response)
                    if payload.get("ok") and payload.get("entry") == entry:
                        break
                except (URLError, OSError):
                    pass
                if time.monotonic() >= deadline:
                    pytest.fail(f"Live {entry} health check timed out: {url}")
                time.sleep(.05)
        yield result
    finally:
        def stop():
            for server in servers:
                server.should_exit = True
        if loop_holder and not loop_holder[0].is_closed():
            loop_holder[0].call_soon_threadsafe(stop)
        thread.join(timeout=10)
        assert not thread.is_alive(), "Live server thread failed to shut down"
        assert not failures, f"Live server errors: {failures}"


@pytest.fixture
def live_session(live_servers, live_browser, tmp_path, request):
    from .support import Session
    with ExitStack() as stack:
        dm_context = stack.enter_context(live_browser.new_context(viewport={"width":1280,"height":900}))
        player_context = stack.enter_context(live_browser.new_context(viewport={"width":1280,"height":900}))
        contexts = (dm_context, player_context)
        for context in contexts:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
        session = Session(dm_context.new_page(), player_context.new_page(), *live_servers)
        setup_or_teardown_failed = False
        try:
            session.setup()
            yield session
            assert not session.page_errors, session.page_errors
        except BaseException:
            setup_or_teardown_failed = True
            raise
        finally:
            failed = setup_or_teardown_failed or any(getattr(request.node, "rep_" + phase, None) and
                         getattr(request.node, "rep_" + phase).failed for phase in ("setup", "call"))
            for name, context in zip(("dm", "player"), contexts):
                if failed:
                    for i, page in enumerate(context.pages):
                        try:
                            page.screenshot(path=str(tmp_path / f"{name}-{i}.png"))
                        except Exception:
                            pass
                    context.tracing.stop(path=str(tmp_path / f"{name}-trace.zip"))
                else:
                    context.tracing.stop()
            (tmp_path / "page-errors.json").write_text(json.dumps(session.page_errors, indent=2))
