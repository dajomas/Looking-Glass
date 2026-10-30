## Reliability batch 3 increment 3: connected checkpoint restore (2026-10-30)

The user reported a green workflow after the portal helper correction; no new
run ID, tested SHA or passing counts were supplied for independent review.
Do not infer that the new checkpoint cases below were included in that run.

Added `python/tests/live_e2e/test_live_checkpoints.py` with three real-listener
Chromium cases: restoring same-map fog, restoring the saved active map and
campaign-wide exploration, and rejecting an incorrect campaign-name confirmation.
Helpers save checkpoints, discover their IDs from the real list page, obtain a
real compatibility preview token and submit authenticated CSRF-protected forms.
They explicitly distinguish ok and err redirect parameters. Save/preview must
leave authoritative viewer state unchanged; successful restore adds one automatic
safety checkpoint, while rejected confirmation preserves the checkpoint inventory.
No repository-level database writes or fake token/restore responses are used.

A test-only native WebSocket subclass records refresh notices and successfully
sent viewer-status reports without replacing transport. After one setup reload,
the document ID and exactly one open/no closes must persist through operations.
Successful restore requires a session-checkpoint notification, installed image
pixels, the authoritative image URL, a current ready report and monotonic display
version change. The same-map case compares restored bounds/region signatures;
the map-switch case also activates the other map to check that added exploration
was removed. Rejection preserves state/version/image and is followed by a real
hide/undo delivery check. These reports prove client emission, not manager-side
acknowledgment; the tests do not claim to inspect the entire synchronization panel.

The existing isolated live fixture supplies synthetic users, maps, temporary data
and both real listeners. Shared fixture page-error/failure-trace handling remains.
The tests perform no player navigation/reload after setup, intercept no responses,
and use bounded readiness/message waits rather than race-selecting sleeps.
The real routes, preview/list templates, checkpoint restore implementation, viewer
state format and stable revealed-region signatures were inspected during drafting.

Validation: Python syntax parsing passed for the three-case candidate. None of
the live cases, full application suites or hosted Python 3.14 CI was executed by
the assistant. Execution and possible harness corrections remain pending; this
is not a passing-run or runtime-defect claim. Existing Live Uvicorn discovery
collects this module with LG_RUN_LIVE_E2E=1; no workflow/requirements changes.
Focused command: LG_RUN_LIVE_E2E=1 python -m pytest -q python/tests/live_e2e/test_live_checkpoints.py.
README was reviewed and remains accurate. No runtime code, shared fixtures,
collector, stored evidence or other branch changes are included. Campaign ZIP
restore propagation, stale preview-token cases, multi-viewer restore, broad
runtime-state coverage, restore interruption and the remaining application backlog
are separate follow-up work.

