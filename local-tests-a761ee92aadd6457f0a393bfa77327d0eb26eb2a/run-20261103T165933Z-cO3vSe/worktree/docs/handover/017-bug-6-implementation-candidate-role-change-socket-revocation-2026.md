## Bug 6 implementation candidate: role-change socket revocation (2026-10-29)

Baseline: features/perplexity at aafa602fd1cae81f7157c57698f786e1b08c9ceb.
At this baseline bug 5 is delivered in 88c705eb98d42bbd39fef536b0515666ee298696,
with documentation in cbcf2b5bd2a8af87ec303b66388df338357ab0ea and TODO status in
aafa602fd1cae81f7157c57698f786e1b08c9ceb. Its earlier candidate/open wording above
is historical, not current TODO status. Bug 5 ASGI/deployment acceptance remains pending.

Re-read the live admin user routes, user repository, README and HANDOVER.
The unchanged users.py source matched Git blob
55b26049d1307aa73439dc48cee0d5450096e70e. Complete README/HANDOVER baselines were
recovered from the supplied bug 5 draft plus the existing final blank line,
then verified against current live blobs 7e4e92372428fb516965a716eafe86a1519f7285
and 5f59536dda1812c65f4e8d14b32ca30c6442f978 respectively. Preserve these exact
baselines as prefixes; do not substitute an older application snapshot.

Root cause: update_user already deleted all target sessions when the role changed
or active was false, but the post-transaction kick checked only active=false.
The sole runtime change computes revoke_sessions before updating the user and
uses that same predicate for transactional deletion and the post-commit kick.
All changed roles are covered, including promotions: this preserves the existing
session policy, rather than introducing a demotion-only policy. Unchanged-role,
active profile edits and existing reactivation behavior remain unchanged.
Self-revocation and last-superadmin guards, CSRF dependencies, password reset,
user deletion, the event hub, viewer routes and bug 5 are not modified. Bug 7
is not implemented. No migration, setting, dependency or new API is introduced.

Validation actually executed with Python 3.12.8 / pytest 8.3.5, plugin autoload off:
- New isolated route-body regressions against the verified baseline: 6 failed,
  14 passed. Every changed active-role pair missed its kick on the baseline.
- Candidate focused modules: 20 passed, 1 module skipped (0.19 seconds).
  The skipped module contains four ASGI/WebSocket cases; FastAPI is unavailable.
- The changed runtime file and both new test files compiled successfully.

The executable unit module loads update_user and _guard_last_superadmin from the
actual source via AST, strips routing decorators, and postpones annotations.
It does not rewrite their function bodies. Real temporary SQLite transactions
are used; role enum, repository facades, redirect and hub are test doubles.
Tests cover all nine active-role pairs, three deactivations, same-role reactivation,
unknown targets, self-revocation, last-superadmin protection, rollback after failed
session deletion and an injected commit-boundary failure. A fresh independent
SQLite connection inside the hub spy verifies the kick observes committed state;
unrelated actor/other-user sessions remain intact. These are isolated route-body
tests, not HTTP, real repository, dependency-injection or WebSocket execution.

The included ASGI module mounts the real admin/viewer apps on one TestClient loop.
Its four unexecuted cases cover two inherited-access demotions, unaffected viewer
isolation, unchanged-role profile saves and missing CSRF. The demotion cases
expect closure before another viewer event or idle timeout; a new valid session
also cannot recover the lost inherited campaign access. A three-second receive
bound prevents missing-frame regressions from hanging indefinitely.

Run in a normal checkout with runtime/development dependencies:
`PYTHONPATH=python python -m pytest -q python/tests/test_user_role_socket_revocation.py python/tests/test_user_role_socket_web.py`
No full suite, browser, live-server or Python 3.14 acceptance was executed. Run
both new modules without skips and verify role-change disconnection on the target
deployment before declaring the fix integration-validated. Existing in-process
hub/transport limitations still apply; already in-flight data cannot be recalled.

Implementation and documentation are prepared only; no bug 6 GitHub write has
occurred at preparation. TODO item 6 stays open until approved delivery, when
its actual SHA and pending integration acceptance must be recorded. The bug 5
two-commit exception applied only to bug 5 and is not reused for this candidate.
No archive or Patch/ material is included in the proposed repository write.

