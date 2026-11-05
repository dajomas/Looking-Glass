# Bugs 20 and 21: accepted closure (2026-11-05)

The user requested closure after green CI and completed green local evidence.
Bugs 20 and 21 are accepted and closed on features/perplexity within the scope
below. This supersedes acceptance-pending statements in records 075/076; their
historical failures, preparation evidence and limits remain preserved. Baseline
for this documentation change: ca93d96f6ecfda0683fc816631def211d2929d13.
These are repository backlog numbers, not GitHub issue numbers.

## Accepted implementation

Bug 20: 29e19a121c503bdd0e3e9a54a382f32ccc0320de hardened _safe_next for both
login paths. Raw backslashes/controls and unsafe decoded path forms fall back
to /. Accepted URLs retain their original query/fragment representation.
Decoding is bounded and conservative; this is not a general URL sanitizer.

Bug 21: 1f31285bafb73b6dad7ee009ea4dab52de8342a7 added the strict login-origin
policy. Origin takes precedence; Referer is a fallback only when Origin is absent.
Scheme, hostname and effective port must match the ASGI request. Missing, opaque,
malformed, duplicate or cross-origin sources are denied before the login handler
accesses credentials/session creation. Automation must supply a matching source.
Existing authenticated-mutation CSRF protection is not replaced or broadened.
Helper alignment landed in dd882a5cbdf228b61aca443b731155d07ec8a0fb and
c734226657ee556ff86f42883decc15c8499f389 without weakening security assertions.

## Evidence and limits

CI run 42003087572 attempt 1 tested c734226657ee556ff86f42883decc15c8499f389.
The published run metadata reports success for all five jobs and their report
validation steps. Metadata was reviewed, not every CI JUnit case recounted.
[CI snapshot](https://github.com/dajomas/Looking-Glass/tree/733aaa91f0da57ec6a236034d17d9b5d3d715f51/ci-results-42003087572-attempt-1).

Local run local-tests-e17fbae/run-20261105T102507Z-5rCE68 tested exactly
e17fbae2696eda27bed26daebc29a8a8f06747ce, as confirmed by requested/expected/
actual workspace identity. Overall exit 0; all test/report exits 0. Reports show:

| Suite | Reported cases | Failed/error | Skipped |
|---|---:|---:|---:|
| Python / HTTP | 1593 | 0 | 0 |
| JavaScript | 28 scripts | 0 | 0 |
| Browser / mocked HTTP | 172 | 0 | 0 |
| Live Uvicorn | 18 | 0 | 0 |
| Recovery | 6 | 0 | 0 |

Python 3.14.8, Node 22.23.2; 2026-11-05 10:25:07 to 10:36:53 UTC.
[Local snapshot](https://github.com/dajomas/Looking-Glass/tree/ca93d96f6ecfda0683fc816631def211d2929d13/local-tests-e17fbae/run-20261105T102507Z-5rCE68).
These local report counts are not independently recounted CI totals. CI and local
source IDs are distinct and must not be presented as the same tested revision.
The earlier local run on 733aaa9 failed because Node/Playwright were absent;
that failure is preserved in e17fbae2696eda27bed26daebc29a8a8f06747ce under
local-tests-733aaa9/run-20261105T100229Z-umk8zN and is not reclassified as passing.

Acceptance is bounded by these suites and the supplied policy regressions, not
proof of every browser engine, encoded URL interpretation, proxy topology or
privacy configuration. No real nginx/TLS deployment acceptance was performed.
The networking guide now documents the external-authority, trusted-scheme and
source-header contract and a deployment checklist; that checklist is not a test
result. No application tests were executed for this documentation-only change.

## Documentation and evidence cleanup

TODO.md closes only 20/21; seven second-hunt findings remain open: 22, 24–29.
HANDOVER.md indexes this record; release notes and the existing networking guide
record the accepted behavior and upgrade requirements. README.md was reviewed;
its deployment link and existing descriptions remain accurate, so no cosmetic
edit is needed. Existing audit/history files and split manifests are unchanged.
No production code, migrations, regression tests or other branches change.
The commit uses [skip ci] as requested; no CI result for that commit is claimed.

Requested cleanup scope is limited to generated root directories:
ci-results-42003087572-attempt-1, local-tests-733aaa9 and local-tests-e17fbae.
Deletion is NOT included or claimed complete: the available connector deletes
only one file per commit and its multi-file writer cannot delete directories.
A bulk Git cleanup remains pending. Preserve the commit-specific evidence links
above so later removal from HEAD does not erase the evidence references. Do not
remove source tests, runners, documentation, manifests or installation data.
No downloadable archive or Patch/ material is produced.
