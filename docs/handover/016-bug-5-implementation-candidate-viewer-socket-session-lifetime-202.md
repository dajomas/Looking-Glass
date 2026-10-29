## Bug 5 implementation candidate: viewer socket session lifetime (2026-10-29)

Baseline: features/perplexity at 10c5d4af419b08d7639d2e3867e49fe518798b47.
Reconstructed existing code replacements and HANDOVER were verified against live
Git blob hashes. The supplied README matched live blob
9b08f1618d55ba27a9c5fb303c9376e1fd8e26c4 after CRLF-to-LF normalization;
its complete previous contents and this handover are preserved as exact prefixes.
No earlier uploaded application snapshot is used for code replacements.

Scope: sessions.lookup_hash resolves the existing DB identity without retaining
raw tokens in socket indexes/checker closures. Viewer sockets record that hash
and an access checker for session expiry/deletion, active user, viewer portal and
current campaign access. The hub validates before each event/pong, the live loop
validates before reports and on an idle timeout of 15 seconds, and a post-subscribe
check covers logout during admission. Logout becomes async and, after committed
session deletion, kicks only that hashed session's sockets across campaigns.
Per-socket delivery locks serialize sends with explicit session/user kicks;
existing kick_user behavior is retained. Failed checks fail closed. Empty hub
subscription sets are removed, and sync records are disconnected on retirement.

No fog rendering, JS, templates, schema, settings, dependencies or other backlog
implementations change. Bug 6's explicit role-update kick and bug 7's forced
password-change restriction are deliberately not implemented here. Session checks
can observe role-related session deletions, but this is not bug 6's completion.

Validation executed on Python 3.12.8 with installed pytest 8.3.5, plugin autoload
disabled, and a focused source tree containing verified live support modules:
- New unit regressions against baseline: 9 failed, 2 passed. Baseline's FastAPI
  WebSocket annotation import alone was shimmed with object because FastAPI is
  unavailable; no baseline hub/repository logic was changed. One failure directly
  reproduces all three events being sent despite access being revoked.
- Candidate focused modules: 11 passed, 1 module skipped (0.04 seconds). The
  skipped module contains seven ASGI/WebSocket tests; FastAPI/Starlette are absent.
- All six changed/new Python files compiled successfully.

Unit coverage uses real SQLite for hash/raw lookup equivalence, portal separation,
expiry boundary and deletion, plus mocked sockets for session/campaign isolation,
event/pong/idle guard behavior, failed authorization/transport cleanup, existing
user kicks, idempotent removal and serialization with an in-flight send. This does
not execute routing, middleware, ASGI transport or the actual live-loop timer.
The seven included integration cases cover logout isolation/tabs, expiry before
broadcast, timer-driven idle closure, assignment removal, rejected status reports,
admission/logout races and unauthenticated admission; they remain unexecuted.

Run from a normal repository checkout with development/runtime dependencies:
`PYTHONPATH=python python -m pytest -q python/tests/test_viewer_session_lifetime.py python/tests/test_viewer_session_web.py`
No full suite, browser or live-server test was run. Python 3.14 deployment acceptance
also remains pending; do not describe the skipped integration module as passing.

Limits: hub/kicks are in-process; revocations from another process are observed by
DB checks rather than direct cross-process notification. Short synchronous DB
checks run on the application loop, consistent with existing access checks. The
15-second idle interval excludes scheduling/DB/transport delays. An already
in-flight frame cannot be recalled; after closure no new sends are authorized.
No files are deleted/renamed and no Patch/ material is added to the repository.
Implementation is prepared, not delivered at preparation. TODO item 5 remains
open until approved GitHub delivery; record the delivered SHA and distinguish
implementation delivery from pending ASGI/deployment acceptance then.

