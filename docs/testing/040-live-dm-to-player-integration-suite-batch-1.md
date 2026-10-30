## Live DM-to-player integration suite: batch 1

Location: `python/tests/live_e2e/`. Run with `bash runlive.sh`, or directly:

```bash
python -m pytest -v -ra python/tests/live_e2e
python -m pytest -v python/tests/live_e2e -k offline
LG_RUN_LIVE_E2E=1 bash runtests.sh
```

The four tests add a distinct coverage layer, not a replacement for fast service,
HTTP TestClient, JavaScript, or mocked browser tests. The regular Python runner
now excludes both `browser/` and `live_e2e/`. For manual Python-only runs use:

```bash
python -m pytest -v python/tests --ignore=python/tests/browser --ignore=python/tests/live_e2e
```

### Harness and isolation

Each test builds Settings from a deep copy of DEFAULTS, not load_settings, so
config.yaml, LG_CONFIG and LG_DATA_DIR cannot redirect it to production storage.
SQLite, uploaded maps and generated cache live below pytest's tmp_path. Test-only
DM/player accounts are seeded. Images and campaign membership are created through
real authenticated HTTP; logins use the actual pages. Two real loopback servers
share one AppContext and asyncio event loop, matching production EventHub design.
Sockets bind port zero and stay reserved, avoiding a find-free-port race. Both
health endpoints must become ready; server errors/timeouts fail setup.

Playwright uses independent browser contexts for DM and player. No page.route,
response fixtures, stub templates or mocked sockets are installed. Fog reveal,
hide and undo use real UI controls; campaign setup/uploads use the authenticated
browser request context. Map activation uses authenticated fetch in the DM page,
not the map-display dialog. Thus this is not coverage of every display-dialog UX.

### Assertions

1. Reveal one red room; adjacent room remains black in the installed viewer image.
2. Hide that room and undo; viewer image follows both actions without a reload.
3. Prepare green map's opposite room, switch to it and back; final artwork, name
   and visible/hidden room pixels match each map's own saved state.
4. Prepare an inactive map; authoritative viewer state/version and installed image
   stay unchanged, then activation exposes only the newly prepared room.

The player must have a connected WebSocket before actions. Conditions wait at
most ten seconds, below the viewer's forty-second fallback refresh interval.
Image checks draw the actual viewer img element to a canvas; they do not fetch a
replacement test image. These verify delivered image pixels and DOM identity,
not every transient compositor frame, arrow rendering, or visual typography.
Offline stability is observed after confirmed request completion, not an unlimited
absence-of-events guarantee. No retry-until-pass wrapper or arbitrary action sleep
is used. Startup health polling alone has a bounded short retry interval.

### Prerequisites and diagnostics

Use the existing project development/runtime requirements, Playwright, installed
Chromium and its OS libraries. Dependencies missing from an explicitly requested
live run are failures, not silent skips. The fixture launches headless Chromium
with the same --no-sandbox flag as existing tests; this is a test-only setting.
Run solely against synthetic data on your development host.

Contexts and server sockets are closed in finally blocks. Server shutdown is
bounded; a surviving thread fails teardown. On test/setup failures the fixture
attempts screenshots and saves traces under the test tmp_path. Open a trace with
`python -m playwright show-trace /path/to/dm-trace.zip`. Pytest prints tmp paths;
use `--basetemp` to choose a dedicated disposable directory if needed. Page script
errors are collected and fail otherwise passing scenarios. Logs remain in pytest
capture and `test-results/live-e2e.log` when using the runner.

Live execution has not been completed in the assistant environment: FastAPI and
Uvicorn are absent. Collection and static checks are reported separately under
Patch/. Do not add these four cases to successful-test totals until they run.


