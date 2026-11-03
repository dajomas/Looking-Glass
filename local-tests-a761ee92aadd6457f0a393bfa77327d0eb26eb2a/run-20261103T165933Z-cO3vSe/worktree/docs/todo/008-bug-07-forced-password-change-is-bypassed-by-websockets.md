### 7. Forced password change is bypassed by WebSockets
- [x] Implementation delivered on `features/perplexity`; ASGI/deployment acceptance pending.
- Fix commit: `07c5e8b9debad7c2fa7a3362e804c76d2cc30746`.
- Documentation commit: `3c770fd4b90f375e5dac4c177cb85e674f7ce58a`.
- Baseline: `b95ac2123e5c11ee2e13d4d642c6986cc0340d65`. The user separately
  approved documentation-first, two-commit delivery for bug 7.
- Validation during preparation on Python 3.12.8 / pytest 8.3.5: new baseline
  regressions produced 12 failures and 7 passes; all 19 new unit cases passed
  on the candidate. The focused run produced 50 passes and one skipped module:
  19 new cases, bug 5's 11 unit cases and bug 6's 20 isolated route cases.
  The skipped new module contains seven ASGI/WebSocket cases; FastAPI was absent.
  All three changed/new Python files compiled successfully. Actual route function
  bodies were exercised through an AST loader with decorators removed and
  annotations postponed. Most socket, repository/RBAC and hub boundaries were
  doubles; one case used the real unchanged EventHub to block event delivery
  after the flag changed. The timeout control-path case injected TimeoutError,
  not a measured wall-clock timer. No real account/password-change recovery,
  HTTP, dependency-injection, ASGI transport, full-suite, browser, live-server
  or Python 3.14 acceptance checks ran. No application tests were rerun during
  GitHub delivery or this documentation-only update. See HANDOVER.md for details.
- Problem: resolve_user() bypasses require_user()'s password-change restriction.
- Solution: viewer live() now rejects required-change users with code 4403 before
  accept/subscribe, and `_session_allowed()` rejects the flag in ongoing access
  checks. Existing post-subscribe, event/pong/report and idle checks inherit the
  restriction. All roles are covered; HTTP account/logout exceptions remain
  unchanged so password-change recovery and logout stay available. No viewer
  mutation API was introduced; bugs 5 and 6 remain otherwise unchanged.
- Test: unit cases cover admission/recheck for all three roles, valid ping/status,
  existing denial behavior, flag changes during accept/receive, the timeout path,
  reconnection after clearing the flag and real-hub event rejection. The seven
  ASGI cases remain unexecuted, not passed.
- Limits: idle checks retain the existing 15-second interval, subject to
  scheduling/DB/transport delays; no immediate flag-change kick was added.
  Already in-flight data cannot be recalled; existing in-process hub limits apply.
- Remaining acceptance: execute the new ASGI module without skips with normal
  dependencies, then verify required-change admission, real password-change
  recovery, logout and existing-socket restriction on the Python 3.14 deployment.

