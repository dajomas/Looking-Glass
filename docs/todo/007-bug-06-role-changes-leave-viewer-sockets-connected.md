### 6. Role changes leave viewer sockets connected
- [x] Implementation delivered on `features/perplexity`; ASGI/deployment acceptance pending.
- Fix commit: `90fa8ba8b2a895d0a193b4aebfbe8f776f26a83e`.
- Documentation commit: `d1c6ee1ab9665611884d2d2028f724daf6e805c0`.
- Baseline: `aafa602fd1cae81f7157c57698f786e1b08c9ceb`. The user separately
  approved documentation-first, two-commit delivery for bug 6.
- Validation during preparation on Python 3.12.8 / pytest 8.3.5: baseline
  regressions produced 6 failures and 14 passes; candidate focused modules
  produced 20 passes and one skipped module containing four ASGI/WebSocket
  cases. FastAPI was unavailable. All three changed/new Python files compiled.
  The executed tests loaded the actual route function bodies through AST,
  with routing decorators removed and annotations postponed; SQLite transactions
  were real, while repository, role enum, redirect and hub boundaries were test
  doubles. An independent SQLite connection in the hub spy verified committed
  state before the kick. No HTTP, actual repository, dependency-injection,
  WebSocket transport, full-suite, browser, live-server or Python 3.14 acceptance
  checks were executed. No application tests were rerun during GitHub delivery
  or this documentation-only update. See HANDOVER.md for details.
- Problem: role changes revoke sessions, but only deactivation kicks sockets.
- Solution: `update_user()` now uses one `revoke_sessions` predicate for session
  deletion inside the transaction and the user socket kick after commit. All
  changed roles, including promotions, retain the existing session-revocation
  policy. Active unchanged-role/profile saves and existing reactivation behavior
  are preserved; deactivation still kicks. Rejected or rolled-back changes do
  not trigger a kick. Bug 5 access checks and safety guards are unchanged.
- Test: all nine active-role pairs, deactivation, reactivation, unknown users,
  self-revocation, last-superadmin protection and rollback/commit-boundary
  failures are covered by isolated tests. The four ASGI cases remain unexecuted.
- Limits: explicit kicks use the existing in-process hub; already in-flight
  network data cannot be recalled. Unit coverage is not ASGI/deployment acceptance.
- Remaining acceptance: run both new regression modules without skips using
  normal dependencies, then verify immediate role-change closure, loss of
  inherited access and unaffected viewer/profile-save behavior on the deployed
  Python 3.14 application. Bug 7 was implemented separately; see item 7.

