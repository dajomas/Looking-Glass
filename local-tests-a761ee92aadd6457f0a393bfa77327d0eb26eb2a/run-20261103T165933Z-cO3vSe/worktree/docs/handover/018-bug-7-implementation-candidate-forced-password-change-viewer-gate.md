## Bug 7 implementation candidate: forced-password-change viewer gate (2026-10-29)

Baseline: features/perplexity at b95ac2123e5c11ee2e13d4d642c6986cc0340d65.
Bugs 5 and 6 are delivered; their earlier candidate/open wording above is historical.
Bug 6 implementation: 90fa8ba8b2a895d0a193b4aebfbe8f776f26a83e; documentation:
d1c6ee1ab9665611884d2d2028f724daf6e805c0; status: b95ac2123e5c11ee2e13d4d642c6986cc0340d65.
ASGI/deployment acceptance for both remains pending.

Re-read live viewer/api.py, deps.py, README and HANDOVER before preparing changes.
The unchanged viewer API matched blob a396f2714b34722f727d54e7e6f105c45e482ad8.
Full documentation recovered from the supplied bug 6 draft matched current live
blobs ff5cc083eb18693b6b887f189302f0f6165f5766 (README) and
659982bf5c47595fdbb21ab00e7822c0103f7304 (HANDOVER); retain those exact prefixes.
No old uploaded application snapshot substitutes for these live baselines.

Root cause: live() resolves a session without require_user()'s password-change
restriction, and bug 5's hashed-session checker also omitted the flag.
The sole runtime file changed is web/viewer/api.py: live() closes with 4403 before
accept/subscribe when its resolved user must change password; _session_allowed()
also rejects the flag on every subsequent check. Existing post-subscribe checks
cover flag changes during admission. Existing event/pong/report guards and idle
checks therefore inherit the restriction without changing the hub or timer.
All roles are covered. Missing/expired/inactive sessions and denied campaigns
retain their existing admission behavior. HTTP dependencies, auth/account/logout,
role-update routes, repositories, session revocation and bugs 5/6 are unchanged.
Account and logout remain available through their existing HTTP exceptions;
clearing the flag through successful password change permits normal reconnection.
No viewer mutation API, migration, configuration, dependency or JS change is added.

Validation actually executed on Python 3.12.8 / pytest 8.3.5, plugin autoload off:
- Final new regressions on verified baseline: 12 failed, 7 passed.
- Final new unit module on candidate: all 19 passed.
- Focused candidate run: 50 passed, 1 module skipped (0.30 seconds), comprising
  19 new cases, bug 5's existing 11 unit cases and bug 6's 20 isolated route cases.
  The skipped new module contains seven ASGI/WebSocket cases; FastAPI is absent.
- All three changed/new Python files compiled successfully.

The new unit loader extracts actual _session_allowed/live function bodies by AST,
removes decorators and postpones annotations; it does not rewrite their bodies.
Most sockets, repository/RBAC boundaries and hub operations are test doubles;
an additional case uses the real, unchanged EventHub to reject event delivery
through the new checker after the flag changes. New cases cover all three roles,
admission/recheck, valid ping/status, prior denial behavior, flag changes during
accept/receive, the timeout control path and reconnection after clearing the flag.
The timeout case injects TimeoutError, not a measured wall-clock timer. The new
unit module does not exercise real DB sessions, account password hashing, HTTP,
dependency injection or ASGI transport. Bug 5's retained unit tests use real SQLite.
Support security.py and viewer_sync.py matched their live blob hashes, and the
unchanged EventHub matched f5016149515921345c37d657485ad88862f59098. Previously
supplied bug 5/6 files were used only as focused test-tree support, not replacement
implementation files. No support files are included in the proposed commit.

The seven included ASGI cases remain unexecuted: admission denial for three roles,
a new flag blocking broadcast while another user stays connected, actual idle
closure, real account/password-change followed by reconnection, and logout while
a password change is required. These use normal application fixtures and bounded
three-second receive helpers; they are not browser or live-listener tests.

Run in a normal checkout with runtime/development dependencies:
`PYTHONPATH=python python -m pytest -q python/tests/test_viewer_password_gate.py python/tests/test_viewer_password_gate_web.py python/tests/test_viewer_session_lifetime.py python/tests/test_user_role_socket_revocation.py`
No full suite, browser, live-server or Python 3.14 acceptance was executed. Run the
new ASGI module without skips and verify required-change admission, password-change
recovery and existing-socket restriction on the deployment before declaring the
fix integration-validated. Idle checks retain the existing 15-second interval,
subject to scheduling/DB/transport delays; this adds no immediate flag-change kick.
Already in-flight data cannot be recalled and existing in-process hub limits apply.

Implementation/documentation are prepared only; no bug 7 repository write has
occurred at preparation. TODO item 7 stays open until approved delivery. Record
the delivered SHA and pending integration acceptance after delivery. Earlier
bug 5/6 split-delivery exceptions do not authorize splitting this candidate.
No archive or Patch/ material is included in the proposed repository write.

