### 5. Viewer sockets outlive session expiry/logout
- [x] Implementation delivered on `features/perplexity`; ASGI/deployment acceptance pending.
- Fix commit: `88c705eb98d42bbd39fef536b0515666ee298696`.
- Documentation commit: `cbcf2b5bd2a8af87ec303b66388df338357ab0ea`.
- Baseline: `10c5d4af419b08d7639d2e3867e49fe518798b47`. The user approved
  documentation-first, two-commit delivery for this item only.
- Validation during preparation on Python 3.12.8: baseline regressions produced
  9 failures and 2 passes; candidate regressions produced 11 passes and one
  skipped module containing seven ASGI/WebSocket cases. FastAPI/Starlette were
  unavailable. Baseline's WebSocket annotation import alone was shimmed; hub
  and repository logic was unchanged. All six changed/new Python files compiled.
  Unit coverage used real SQLite and mocked sockets. No ASGI transport, actual
  live-loop timer, full-suite, browser, live-server or Python 3.14 deployment
  checks were executed. No application tests were rerun during GitHub delivery
  or this documentation-only update. See HANDOVER.md for details.
- Problem: admission-only authentication leaves stale event subscriptions.
- Solution: sockets now use hashed session identities; logout disconnects that
  session after committed deletion. Session/user/campaign access is rechecked
  before event/pong delivery, before status reports and on a 15-second idle
  timer. A post-subscription check covers logout during admission. Per-socket
  locks serialize delivery with explicit kicks; other valid sessions stay connected.
- Limits: immediate logout kicks are in-process; other processes observe DB
  revocation through their checks. The idle interval excludes scheduling, DB
  and transport delays. Already in-flight frames cannot be recalled. Raw tokens
  are not added to socket indexes or authorization-check closures.
- Test: no new events are authorized after revocation is observed; idle sockets
  close and other valid sessions remain connected. Integration cases remain
  unexecuted, not passed.
- Remaining acceptance: run both new regression modules with normal dependencies,
  then verify expiry/logout, idle closure and session isolation on the deployed
  Python 3.14 application. Bug 7 was implemented separately; see item 7.

