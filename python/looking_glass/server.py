"""Runs the admin and viewer apps as two uvicorn servers in one event loop."""

import asyncio
import contextlib
import logging
import signal

import uvicorn

from .access_logging import configure_access_logging
from .bootstrap import ensure_superadmin
from .config import Settings
from .services import images
from .web.app_factory import create_admin_app, create_viewer_app
from .web.context import AppContext

log = logging.getLogger("looking_glass")

# Ports Chrome / Firefox refuse to open (ERR_UNSAFE_PORT). See https://www.chromium.org/developers/design-documents/network-stack/unsafely-blocked-ports
BROWSER_BLOCKED_PORTS = frozenset({
    1, 7, 9, 11, 13, 15, 17, 19, 20, 21, 22, 23, 25, 37, 42, 43, 53, 69, 77, 79, 87, 95, 101, 102, 103, 104,
    109, 110, 111, 113, 115, 117, 119, 123, 135, 137, 139, 143, 161, 179, 389, 427, 465, 512, 513, 514, 515,
    526, 530, 531, 532, 540, 548, 554, 556, 563, 587, 601, 636, 989, 990, 993, 995, 1719, 1720, 1723, 2049,
    3659, 4045, 4190, 5060, 5061, 6000, 6566, 6665, 6666, 6667, 6668, 6669, 6679, 6697, 10080,
})


class _Server(uvicorn.Server):
    """uvicorn server that leaves signal handling to us (two servers, one loop)."""

    @contextlib.contextmanager
    def capture_signals(self):
        yield

    def install_signal_handlers(self) -> None:  # older uvicorn versions
        pass


def build(settings: Settings) -> tuple[AppContext, list[_Server]]:
    configure_access_logging(settings.section("server").get("access_log_success", False))
    images.configure(int(settings.section("storage")["max_image_pixels"]))
    ctx = AppContext.build(settings)
    ensure_superadmin(ctx)
    level = settings.section("server")["log_level"]
    common = dict(host=settings.host, log_level=level, proxy_headers=True, ws_ping_interval=20, log_config=None)
    servers = [
        _Server(uvicorn.Config(create_admin_app(ctx), port=settings.admin_port, **common)),
        _Server(uvicorn.Config(create_viewer_app(ctx), port=settings.viewer_port, **common)),
    ]
    return ctx, servers


async def serve(settings: Settings) -> None:
    _, servers = build(settings)
    loop = asyncio.get_running_loop()

    def stop(*_):
        log.info("Shutting down...")
        for s in servers:
            s.should_exit = True

    previous_handlers = {}
    loop_handlers = []

    def handle_signal(signum, frame):
        loop.call_soon_threadsafe(stop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[sig] = signal.getsignal(sig)
        try:
            loop.add_signal_handler(sig, stop)
        except NotImplementedError:
            # Windows does not support asyncio signal handlers.
            signal.signal(sig, handle_signal)
        else:
            loop_handlers.append(sig)

    for name, port in (("admin", settings.admin_port), ("viewer", settings.viewer_port)):
        if port in BROWSER_BLOCKED_PORTS:
            log.warning("The %s port %d is on the browser 'unsafe port' list (Chrome/Firefox show "
                        "ERR_UNSAFE_PORT). Put a reverse proxy in front, pick another port, or allow it in the "
                        "browser - see docs/deployment.md.", name, port)
    log.info("Admin  portal: http://%s:%d", settings.host, settings.admin_port)
    log.info("Viewer portal: http://%s:%d", settings.host, settings.viewer_port)
    try:
        await asyncio.gather(*(s.serve() for s in servers))
    finally:
        for sig in loop_handlers:
            loop.remove_signal_handler(sig)

        for sig, previous_handler in previous_handlers.items():
            signal.signal(sig, previous_handler)
