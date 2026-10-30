## Upload-busy adapter process isolation (2026-10-30)

The first expanded run 41016747640 against
`45b477a85f717aaea1d396ac7e7f29a7d0e9bf39` passed 1,125 Python tests plus
29 subtests, all 27 JavaScript scripts and four live tests. Browser results were
161 passed and one failure: the new adapter called asyncio.run while the parent
browser-test thread already had an active event loop. The unawaited-coroutine
warning followed that invocation failure; upload-busy assertions were not run.

`python/tests/browser/test_upload_busy.py` now invokes the unchanged standalone
check with the current Python executable in a separate process, using the
repository root as cwd. It captures stdout/stderr, reports both on nonzero exit,
and enforces a 120-second subprocess timeout. Timeouts propagate as test errors,
not skips or passes. The child owns its async Playwright/event-loop lifecycle
without importing or starting another asyncio loop in the parent test thread.
No application code, standalone regression assertions, workflow or collector
changes are needed. README.md was reviewed; its CI overview remains accurate.

Focused validation on Python 3.12.8 passed: a real subprocess using asyncio.run
completed while the parent's event loop was active; a real nonzero child exposed
both stdout/stderr in the assertion; a mocked TimeoutExpired propagated as an
error. Temporary stand-in scripts were used, not Chromium or the actual upload
check. Full browser/Python/JavaScript/live suites and Python 3.14 CI were not run
by the assistant for this correction. A new CI run is required for acceptance.

