"""Bounded Chromium smoke test; no application server or live data required."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import PackageNotFoundError, version
import os
import platform
from pathlib import Path
import subprocess
import sys
from threading import Thread


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<!doctype html><title>Looking Glass browser preflight</title>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def probe():
    from playwright.sync_api import sync_playwright

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            print("Chromium executable:", p.chromium.executable_path, flush=True)
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"], timeout=15000)
            try:
                print("Chromium version:", browser.version, flush=True)
                page = browser.new_page()
                page.goto(f"http://127.0.0.1:{server.server_port}/", timeout=15000)
                assert page.title() == "Looking Glass browser preflight"
                page.set_content("<title>DOM check</title><button id='check'>Ready</button>")
                assert page.locator("#check").inner_text() == "Ready"
                print("PASS: launch, local HTTP navigation and DOM check", flush=True)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=float, default=45, help="overall smoke-test timeout in seconds")
    args = parser.parse_args(argv)
    if args.probe:
        probe()
        return 0
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    print("Python:", sys.version.split()[0], "Executable:", sys.executable, flush=True)
    print("Platform:", platform.platform(), flush=True)
    release = Path("/etc/os-release")
    if release.exists():
        print(release.read_text(), flush=True)
    try:
        print("Playwright:", version("playwright"), flush=True)
    except PackageNotFoundError:
        print("FAIL: install Playwright in this test environment: python -m pip install playwright")
        return 1
    env = dict(os.environ)
    env["DEBUG"] = ",".join(filter(None, [env.get("DEBUG"), "pw:browser"]))
    try:
        result = subprocess.run([sys.executable, "-u", str(Path(__file__).resolve()), "--probe"],
                                env=env, timeout=args.timeout, check=False)
    except subprocess.TimeoutExpired:
        print("FAIL: browser preflight timed out", flush=True)
        return 1
    if result.returncode:
        print("FAIL: browser preflight; inspect browser stderr above and docs/testing.md", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
