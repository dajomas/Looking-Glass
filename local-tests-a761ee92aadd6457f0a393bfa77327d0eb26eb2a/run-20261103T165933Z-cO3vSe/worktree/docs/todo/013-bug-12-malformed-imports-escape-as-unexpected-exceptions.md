### 12. Malformed imports escape as unexpected exceptions
- [x] Implementation delivered on `features/perplexity`; HTTP/DB, full-suite
  and deployment acceptance pending.
- Fix/parser regression/guide/index commit: `0b8b3189487d373b5fd3613c16c6fa7f694b1136`.
- Policy and HTTP regression commit: `8c4094a9356274f17e4cb02398c64210de658508`.
- Final delivery-status documentation: this containing commit; report its actual
  returned SHA after a successful write. The user authorized three commits for
  bug 12 specifically, without a signature guarantee.
- Baseline: `69376ea3ed6fe53a487f3b14529dd6db41e1ee63`. The handover split,
  historical sections, reconstruction manifest and existing CI are preserved.
- Problem: expected Foundry door conversion and malformed container/UVTT endpoint
  failures escaped as raw exceptions. NeDB identity/replay was already handled
  by bug 10; finite numeric geometry/calibration was already handled by bug 11.
- Solution: local conversion handling and explicit shape checks raise
  WallImportError before unsafe operations. No blanket parser catch is added.
  Existing falsy defaults, iterable filtering, coordinate omission and UVTT
  point/short-bounds behavior remain. Routes and ZIP helpers are unchanged.
- Policies: ZIP skips invalid entries while accepting usable companions; an
  invalid-only pack rejects. Map-upload partial success and already-saved source
  retention after a later target rejection remain intentional. No automatic
  repair of stored sources or copied map walls is included.
- Actual earlier combined service validation on Python 3.12.8: baseline 48 failed
  and 268 passed; exact candidate 316 passed in 0.31 seconds, no errors/skips.
  Counts: new shapes 90, numeric/parser 154, Foundry 8, NeDB 24, UVTT 30,
  pack-image 10. Complete modules/tests were hash-verified; empty initializers
  and minimal conftest bypassed application initialization. No tests were rerun
  during the GitHub writes or final documentation preparation.
- Separate earlier policy run: 30 isolated cases passed (20 route-body, 10 ZIP).
  Parser/DB/auth/image boundaries were doubles; campaign/API local execution
  used pinned excerpts. Do not add that run to the 316-case service result or
  treat it as real parser-to-route, persistent rollback or HTTP/DB acceptance.
- HTTP/DB module: 29 intended cases, compiled only; not collected/executed in
  this environment. Both step-2 files were hash-verified and compiled again
  before their write. Post-write reads verified both regression blobs.
- Remaining acceptance: normal-checkout service/policy execution, real HTTP/DB
  inspection/import/saved-source rejection and persistent geometry/calibration,
  map-upload/source-retention checks, application imports, authentication/CSRF,
  migrated DB, full suite and target Python 3.14 deployment. Browser/live-server
  checks remain pending. No exact-SHA Actions result has been verified; workflow
  existence, compilation and commit delivery are not integration acceptance.
- Other backlog implementations are not bundled; bugs 2 and 13-15 remain open.
  See `docs/handover/026-bug-12-malformed-import-normalization-2026-10-29.md`
  for delivery records, commands and validation limits.

