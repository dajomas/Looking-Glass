# Second bug hunt: bugs 16–29

Date: 2026-10-31. Reviewed repository `dajomas/Looking-Glass`, working branch
`features/perplexity`, baseline `766780262bf44922bbd7c9fa2b3081e7e28e214f`.
The branch still resolved to this SHA at the final pre-approval read.

## Decisions and scope

Documentation-only review: no implementation, migrations, test changes, bug
closures, merges or archives. TODO.md remains an index; bugs 16–29 link to
numbered sections in [the focused audit](../todo/018-bugs-16-29-audit-2026-10-31.md).
Each includes source locations, impact, a proposed reproduction, minimal fix
approach and required regression. Preserve accepted status/evidence for bugs
1–15; do not infer current counts from the historical workflow section.
Original-image replacement findings 17/18 do not reopen bug 15's accepted scope.

Proposed order: 16, 17, 18, 19, 20, 21, 23, 29, 25, 26, 27, 28, 22, 24.
Coordinate original-image retirement 17/18 and state/mask sequencing 25/26.
README.md was read and needs no change for this backlog-only review; no new
implemented behavior is being advertised. Historical split manifests remain
unchanged. HANDOVER.md receives only this navigation link.

## Validation and unfinished work

Three extracted sandbox checks ran: copied CalibrationIn declarations under
Pydantic 2.11.4 accept an infinite offset and SQLite retains it; Node accepts
the slash/backslash redirect predicate and resolves it externally; Node shows
the poll inequality installing old fog version 8 over current version 10.
These are isolated behavioral checks, not repository regression tests.
All application-level reproductions and proposed regressions remain pending.
No application, HTTP, browser, live-server, full-suite or CI run was executed.
The source review was selective, not exhaustive. All 14 new findings stay open.

Database triggers were checked before recording findings: hide_all does reset
runtime door/passage states, and double-reveal writes do bump fog_version;
those apparent issues were excluded. Future fixes must inspect current branch
code, agree scope, reproduce, add regressions, implement and validate, then
obtain approval for the exact GitHub write. This record documents the proposed
review content, not an assertion that the pending commit already succeeded.

## Bugs 20/21: coordinated regression-first work (2026-11-05)

The user requested work on 20/21 together. Treat them as one narrow login-security
work package with independent acceptance criteria, not a general authentication
refactor. Earlier text above remains the historical audit record; current bug
status is in TODO.md. Neither bug is closed by this test-only step.

Reviewed live source at `c9c701ad530c7745277f39c7d05e8adf5a9f57c7`: shared
auth_routes.py, app_factory.py, login template, real-app test fixture and existing
login/reset tests. _safe_next still accepts slash/backslash and controls;
login_submit has no pre-authentication challenge or request-origin check.

Added python/tests/test_login_security_web.py: 12 parameterized HTTP cases using
the existing real-app/SQLite env fixture, across both portals. Contracts cover
unsafe next values after login and authenticated login-page visits, a valid local
query-string return path, and cross-site/opaque-Origin submissions without a
challenge establishing no session. Normal login first reads hidden form fields
so the tests do not preclude a future pre-login challenge. These are HTTP
contracts, not browser exploitability or supported-proxy validation.

Validation actually performed: Python 3.12.8 compiled the prepared test file.
An isolated execution of the current _safe_next excerpt accepted slash/backslash
and a literal tab (contrary to the proposed rejection contracts), preserved a
normal local query and rejected a literal double-slash target. This was not an
application HTTP run. FastAPI is absent from this sandbox; no HTTP regression,
browser, live, recovery, full-suite or CI execution was performed.

This is intentionally regression-first: production code is unchanged and some
new cases are expected to fail until the subsequent fix. Do not describe the
branch as fixed or these prepared cases as passing. Run the normal dependency
environment baseline, implement redirect validation and choose login-specific
CSRF protection after checking both portals and supported proxy behavior, then
expand coverage for normalization, expired sessions, retries and session identity.
Existing direct-POST login helpers must be reviewed if a challenge or required
origin policy changes their contract; do not weaken protection to satisfy tests.

README.md and HANDOVER.md were reviewed. Neither needs a cosmetic edit for this
test-only step: README advertises no new protection and HANDOVER already links
this focused record. TODO statuses and historical split manifests are unchanged.
No migrations, production changes, other branches, archives or Patch/ material
are included. GitHub delivery and subsequent CI results must be reported only
after they actually occur.

## Bug 20: redirect-validation candidate (2026-11-05)

The user requested bug 20 first, leaving bug 21 unchanged. Baseline branch head:
`7278d69a1e7982322af94d733ddafde2ccaa15fc`. The reconstructed auth_routes.py
matched live Git blob `f1e36a51bf3ac5ff01e210a81e1e962eba844005` before editing.

_safe_next now rejects raw backslashes, C0/DEL controls and non-root-relative
values. It inspects the path separately from query/fragment, repeatedly checks
percent-decoded paths for network-path references, backslashes, controls and
normalized /login prefixes, and returns accepted input byte-for-byte unchanged
as a Python string. Invalid UTF-8 escapes or encoding that does not stabilize
within eight checks fall back to /. This is conservative validation, not a new
canonical URL emitted to the browser. Ordinary local paths, encoded spaces,
UTF-8 path segments, query strings and fragments remain supported. Percent
escapes in queries are not recursively decoded; literal backslashes/controls
anywhere in the raw target are rejected. Authentication, roles, sessions,
password-change destination, response codes and both route call sites are unchanged.

Validation: 44 isolated pytest cases in test_login_redirects.py, executed against
the actual helper extracted from the reconstructed full candidate. Original
helper: 24 failures, 20 passes. Candidate: 44 passes. The complete candidate was
syntax-compiled under sandbox Python 3.12.8. No FastAPI app or HTTP/browser/live/
recovery/full-suite/CI execution occurred; FastAPI is unavailable here. These
checks do not establish application/browser acceptance or deployed security.

The existing 12 HTTP cases are retained without skips or weakened assertions.
The four bug-21 cross-site-submission cases are still expected to fail until its
separate fix; no clean full-suite result is claimed. Bug 20 remains acceptance
pending, not closed. Follow with real login/Location/browser validation on both
portals and review normal-runtime CI/local evidence. No bug-21 protection,
migration, unrelated change, archive or Patch/ material is included.

README.md and HANDOVER.md were reviewed again. README does not specify detailed
return-URL rules and needs no cosmetic edit; HANDOVER already indexes this focused
record, which now records the implementation decision and evidence limits. The
historical sections above and split manifests are preserved. Delivery is pending
the exact GitHub approval/write; report its SHA only after success.
