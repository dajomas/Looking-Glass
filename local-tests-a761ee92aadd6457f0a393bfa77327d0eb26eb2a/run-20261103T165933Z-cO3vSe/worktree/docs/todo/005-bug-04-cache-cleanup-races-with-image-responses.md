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

