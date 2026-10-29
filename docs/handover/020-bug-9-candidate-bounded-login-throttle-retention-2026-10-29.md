## Bug 9 candidate: bounded login-throttle retention (2026-10-29)

Baseline: features/perplexity at 978a16333d40137045b0480931cab45d8709da88.
Bug 8 is delivered in 35f749192272bdc3028b08a5f9493ba90160438f, documented in
704419d7a669fc55ae407090b4b7b79105b7a7d0, with TODO status at this baseline.
Earlier candidate/open wording records historical preparation, not delivery status.
Bug 8 HTTP/deployment acceptance remains pending. TODO's workflow summary and
remaining order still omit bug 8 delivery; those stale lines are not repaired here.

The user approved bounded, fail-closed capacity handling for bug 9. Live security.py
matched blob f5402c281b894921b4cfcfbb1f50b934d979eeb6. Complete uploaded README
and HANDOVER, after CRLF-to-LF normalization, matched current live blobs
cb0f241d53a8b83953a3219a448e6ae8e89e3b67 and
e06be3269ebef7e0a4064c10029f8f4a6de900f7. Preserve those exact normalized
contents as prefixes; do not substitute an older application snapshot.

Scope: only LoginThrottle in python/looking_glass/security.py changes runtime
behavior. MAX_KEYS=4096 limits retained IP/username entries; fail retains at most
max_failures newest timestamps per key. blocked never creates an entry. Checks
and failures prune all expired histories and delete empty keys under the existing
thread lock, sampling monotonic time after acquiring it. At capacity, blocked
rejects untracked keys without evicting active histories. Existing tracked keys
still follow the configured rolling window and threshold, and successful reset
releases its key. Lowercasing and existing key encoding remain unchanged. For
nonpositive thresholds, admission stays blocked without retaining failures; for
nonpositive windows and positive thresholds, failures are not retained and no
lockout is introduced. No constructor-validation/configuration-policy change.
Password hashing, session logic, account atomicity, roles, fog and bugs 1-8 are
not replaced. No schema, route, dependency, setting, file deletion or rename.

Validation actually executed on Python 3.12.8 using stdlib unittest in a temporary
focused package, with the real complete security.py module and an empty package
initializer. Only time.monotonic is replaced by a deterministic clock in unit
cases; no AST rewriting or throttle-body doubles. The test imports
looking_glass.security, matching normal repository package imports.
- Verified baseline: 17 tests ran; 15 failed and 2 passed.
- Candidate: all 17 passed (0.049 seconds), none skipped.
- Changed runtime and new regression file both compiled successfully.
- Additional real-default-cap probe: 4,200 distinct fail calls retained exactly
  4,096 keys/timestamps and blocked an overflow key. This is a bound assertion,
  not a performance/load acceptance benchmark.

Coverage includes check-only allocation, exact expiry, rolling-window behavior,
bounded newest histories, cleanup of abandoned keys, fail-closed saturation,
locked-history preservation, expiry/reset capacity recovery, case/IP isolation,
threaded failures and mixed reset/check/failure operations, nonpositive settings,
a deterministic capacity race and 1,000 seeded reference-model operations below
capacity. Thread tests exercise real threads, not all possible schedules.
The earlier 13-test preliminary standalone run is superseded by these final results.

Run without repository conftest/framework dependencies from the repository root:
PYTHONPATH=python python -m unittest discover -s python/tests -p test_login_throttle.py
Or use the normal development environment:
PYTHONPATH=python python -m pytest -q python/tests/test_login_throttle.py
The pytest invocation and project conftest were not executed in this preparation.
No full suite, HTTP application/DI, browser, live-server, multi-process or Python
3.14 deployment checks ran. Verify normal login failure/429/reset behavior and
capacity recovery on both portals with normal dependencies before calling this
HTTP/deployment accepted. No HTTP regression module is added in this scoped draft.

Limits/decisions: saturation intentionally trades availability for protecting
active histories; one failure each across 4,096 keys can deny new-key login until
capacity recovers. Existing tracked subthreshold keys can still authenticate.
blocked and fail remain separate calls: in-flight authentication is not cancelled
or rechecked if capacity fills in between. fail then drops a new-key record rather
than exceeding the bound/evicting another key; subsequent checks see saturation.
This does not provide atomic attempt reservation or a strict concurrent-attempt
limit. State is per instance/process and disappears on restart. Key strings keep
their existing encoding and arbitrary input lengths; the cap bounds entry and
timestamp counts, not a fixed byte budget. Cleanup is lazy/request-driven, not
time-driven release, and scans the bounded table while holding its lock. No
cross-process throttle, global rate limit or background maintenance is added.

Delivery exception explicitly approved by the user for bug 9 only: three separate
commits, documentation first (README, HANDOVER), then implementation plus tests.
README step 1 is delivered in dcd93fcee0d62508c541a13042e5874f5f50e28d; this
HANDOVER update is step 2. Runtime implementation and tests remain pending step 3
and their own exact-write approval. No tests were rerun during documentation delivery.
TODO item 9 remains open until approved implementation delivery; then record the
actual SHA and distinguish delivery from pending HTTP/deployment acceptance.
No archive or Patch/ material is part of the proposed repository writes.

