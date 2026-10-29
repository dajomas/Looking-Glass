# Bug-fix TODO

Created: 2026-10-28. Audited baseline: `3d34a4f8d2c5f184d5e667aa4e47de2a22ee3c10`.
Target: `dajomas/Looking-Glass`, branch `features/perplexity`.

## Workflow

Bugs 1, 3, 4, 5, 6 and 7 have delivered implementations; the other 9 items remain open.
Bugs 4, 5, 6 and 7 integration/deployment acceptance remains pending; see their validation limits below.
The earlier combined draft was not committed; do not apply it wholesale.
Re-read live code and reproduce each remaining finding before fixing.
For each item: agree a minimal solution, add a regression, implement, validate,
update relevant docs and HANDOVER.md, then approve the exact GitHub write.
Check off only after delivery; record commit SHA, actual test results and limits.
Proposed solutions/migrations are not installed or pre-approved changes.

Suggested remaining order: 8, 9, 10, 11, 12, 2, 13, 14, 15.
Coordinate session items 5-7, parser items 10-12 and image-lifetime items 4/14/15,
while keeping changes individually reviewable. Package paths below refer to
`python/looking_glass/`; static findings still need application-level reproduction.

## Findings and proposed solutions

### 1. Feathered fog exposes hidden artwork
- [x] Complete; delivered on `features/perplexity`.
- Fix commit: `253b33ddae49d403a3985bf99135ce07226e95e4`.
- Validation: 15 new regression cases and 246 related service tests passed on
  Python 3.14.4. HTTP/browser/live-viewer/JPEG/WebP visual checks remain
  outstanding; the broader non-HTTP suite was not fully green (see HANDOVER.md).
- Problem: `services/fog.py` blurs the reveal mask into hidden-room artwork.
- Solution: feather inward, clip permitted coverage, prevent dilation into hidden
  interiors, and invalidate unsafe old composites through a new cache identity.
- Test: adjacent-room pixels remain hidden with default feathering and scaling;
  revealed rooms and bounding walls still render.

### 2. Geometry reconciliation discards custom room notes
- [ ] Open; data-retention risk. Imported-name release itself is intentional.
- Problem: `services/room_notes.py` reconciliation, including during admin reads,
  can delete custom names/Markdown when geometry changes.
- Solution: retain recoverable orphan/archive content while releasing assignments.
  Define read behavior and management-only, revision-safe recovery; preserve
  retained notes in backup/restore and duplication.
- Test: split/merge/alignment changes retain edits and map isolation, release
  names correctly, and allow recovery without changing fog.

### 3. Viewer stays blank after a transient state error
- [x] Complete; delivered on `features/perplexity`.
- Fix commit: `b162dfca0e502f07a2d20ef7b654b7f9e19f3ee4`.
- Location: `static/js/viewer_display.js`, refresh().
- Validation: all 10 viewer-refresh tests and all 27 top-level JavaScript
  regression scripts passed with Node v20.20.1. Transport and DOM behavior were
  mocked; real HTTP/WebSocket, browser and live multi-viewer acceptance remain
  unexecuted. No application tests were rerun for this documentation update.
- Problem: failure hides the stage; a same-version retry returns early as ready.
- Solution: the same-version fast path now requires a visible stage; otherwise
  reload, decode and install the current image before reporting ready.
- Test: loaded map -> HTTP 500 -> same-version success restores image/status
  without a DM mutation; stale-response protection remains.

### 4. Cache cleanup races with image responses
- [x] Implementation delivered on `features/perplexity`; HTTP/deployment acceptance pending.
- Fix commit: `0b0f8f7089d064c9060b15165fbe52aa88d46222`.
- Baseline: `54cae125d996ceccff6cc61d3942edea88209c4e`; bug 1 privacy rendering
  and bug 3 recovery/documentation are preserved. The earlier stale-baseline
  archive and `edd5c121f3ee292a6cf3d75dfa8f991c464595c8` are superseded.
- Validation during corrected archive preparation: 73 passed, 1 skipped on
  Python 3.14.4, including existing bug 1 privacy regressions. The skipped
  module contains five HTTP cases; FastAPI was unavailable. No ASGI integration,
  full-suite, browser or live-server checks were run. No application tests were
  rerun for this documentation-only update. See HANDOVER.md for details.
- Problem: cleanup can delete a path before FileResponse opens it.
- Solution: `FogEngine.viewer_bytes()` captures encoded bytes under the existing
  per-map RLock; viewer image and admin preview routes return byte Responses
  via `asyncio.to_thread`, retaining authorization/version checks and no-store.
- Limits: coordinates one FogEngine instance, not external deletion or shared-cache
  multi-process access; each in-flight response holds encoded bytes in memory.
- Test: concurrent rendering, invalidation and delivery cause neither missing
  files nor wrong-version images; cache cleanup remains bounded.
- Remaining acceptance: execute the included HTTP tests with normal dependencies
  and verify viewer/admin preview during reveal/hide/map changes before declaring
  the fix fully integration-validated.

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

### 7. Forced password change is bypassed by WebSockets
- [x] Implementation delivered on `features/perplexity`; ASGI/deployment acceptance pending.
- Fix commit: `07c5e8b9debad7c2fa7a3362e804c76d2cc30746`.
- Documentation commit: `3c770fd4b90f375e5dac4c177cb85e674f7ce58a`.
- Baseline: `b95ac2123e5c11ee2e13d4d642c6986cc0340d65`. The user separately
  approved documentation-first, two-commit delivery for bug 7.
- Validation during preparation on Python 3.12.8 / pytest 8.3.5: new baseline
  regressions produced 12 failures and 7 passes; all 19 new unit cases passed
  on the candidate. The focused run produced 50 passes and one skipped module:
  19 new cases, bug 5's 11 existing unit cases and bug 6's 20 isolated route cases.
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

### 8. Failed account forms partially save display names
- [ ] Open; route ordering/transaction semantics verified in isolation.
- Problem: `web/auth_routes.py` updates display_name before password validation;
  a normal error return commits the earlier update.
- Solution: validate before writes or roll back the complete failed update.
- Test: wrong current/short/mismatched/unchanged new passwords leave all fields
  untouched; valid/profile-only updates and session revocation still work.

### 9. Login throttle retains unlimited keys
- [ ] Open; isolated retention reproduction in `security.py`, LoginThrottle.
- Problem: checks allocate empty entries without global eviction.
- Solution: avoid check-only allocation, bound keys/histories, expire inactive
  entries and retain thread safety and normal lockout behavior.
- Test: many usernames cannot exceed the bound; expiry/reset/case handling and
  concurrent failures behave deterministically.

### 10. NeDB imports resurrect deleted walls/scenes
- [ ] Open; isolated tombstone reproduction in importer `_parse_ndjson()`.
- Problem: tombstones are discarded before latest-record resolution.
- Solution: replay validated identities in order, applying deletions to current
  state while preserving intended anonymous-document handling.
- Test: update/delete/recreate sequences resolve correctly; deleted-only input
  reports no walls instead of resurrecting geometry.

### 11. Wall imports accept non-finite coordinates
- [ ] Open; isolated NaN acceptance in wall-import coordinate validation.
- Problem: float conversion accepts NaN/infinity; failures occur later.
- Solution: require finite coordinates/origins and positive finite dimensions
  and grid scales where required, before persistent writes.
- Test: invalid values yield controlled errors and unchanged geometry; valid
  supported formats still import and round-trip.

### 12. Malformed imports escape as unexpected exceptions
- [ ] Open; invalid identity reproduced; other paths need route coverage.
- Problem: invalid identity/door types or UVTT shapes escape WallImportError handling.
- Solution: validate external shapes/types and normalize expected input failures
  at the parser boundary, without swallowing unrelated programming errors.
- Test: malformed direct/packed imports yield client errors, not HTTP 500 or
  partial writes; valid inputs remain compatible.

### 13. Replacement leaves incompatible alternate artwork
- [ ] Open; defensive compatibility fix. The originally alleged rendering crash
  was not established: dimension changes also invalidate room geometry keys.
- Problem: original-image dimension changes leave alternate artwork/configuration stale.
- Solution: reject dimension changes while alternate artwork exists, or agree
  explicit reconfiguration; never silently discard artwork or play state.
- Test: rejection preserves DB/original/alternate state and removes failed uploads;
  same-size replacement remains supported.

### 14. Failed map uploads leave orphan artwork
- [ ] Open; static rollback finding in `web/admin/campaigns.py`, upload_map().
- Problem: later upload/DB failures lack cleanup after storing artwork; oversized
  accompanying walls are one trigger.
- Solution: track created files, clean failure/cancellation and recheck permission
  at commit; preserve documented partial-wall-import behavior.
- Test: oversized walls/injected DB failures leave neither map rows nor orphan
  files; successful imports retain their artwork.

### 15. Deletion/restore leaks alternate-image files
- [ ] Open; static lifecycle finding; coordinate with items 4 and 14.
- Problem: map/campaign deletion, replacement and restore remove alternate DB
  references but clean only originals; immediate deletion can break readers.
- Solution: collect both paths transactionally and use reference-checked retirement.
  Startup-only collection is an option, not CLI/context construction under a
  serving process. Never blindly delete existing untracked files.
- Test: both images are covered, rollback preserves files, and collection is
  idempotent/path-contained and respects active references and supported readers.

## Validation caveats

Uncommitted candidate results are not evidence of branch fixes. Re-run relevant
tests per delivered item; skipped HTTP/browser checks are not acceptance.
The stale scrying-auto-2 template assertion was reproduced on the untouched
baseline; track it separately rather than silently skipping it or bundling an
unrelated repair merely to make these tests green.
