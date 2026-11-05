# Bug 29: accepted closure (2026-11-05)

The user accepted the fix for closure after review of green CI and completed
green local evidence. Bug 29 is accepted and closed on features/perplexity
within the scope and limits below. This is a repository backlog number, not a
GitHub issue number. Baseline for this documentation change:
27a8dee902f1cf2b1ded2b694b942310f20dc66c.

## Accepted implementation

Implementation: 2b121306e6a1edd7545d2fdcd08eae87880dbaac. Alternate-image
validation/encoding/storage runs before BEGIN IMMEDIATE. The final transaction
rechecks campaign-management permission, the original full stamp, campaign id
and current map dimensions before retirement and atomic reference installation.
No await occurs inside that transaction. Cancellation/result ownership
coordinates cleanup of late worker output. Failed installation discards the
new staged file; notification errors after commit do not delete installed
artwork. Superseded artwork remains subject to existing offline collection.

This closure supersedes acceptance-pending statements in record 087 without
rewriting its historical preparation evidence or failures. No production code,
migration or regression test changes are part of this closure commit.

## Reviewed evidence

CI run 42043238168, attempt 1, tested exactly
2b121306e6a1edd7545d2fdcd08eae87880dbaac on features/perplexity. Published
run metadata reports overall success, all five jobs successful, and successful
report-validation steps. Review covered run/job/step metadata, not an independent
recount of every JUnit case. Conditional skipped workflow steps are not skipped
test cases.
[CI evidence snapshot](https://github.com/dajomas/Looking-Glass/tree/27a8dee902f1cf2b1ded2b694b942310f20dc66c/ci-results-42043238168-attempt-1).

Local run local-tests-2b12130/run-20261105T141834Z-0lUugv confirms requested,
expected and actual workspace SHA all equal the same implementation commit.
Overall exit 0; all suite test and report-validation exits 0. Published validator
counts, not independently recounted JUnit totals:

| Suite | Reported cases | Failed/error | Skipped |
|---|---:|---:|---:|
| Python / HTTP | 1606 | 0 | 0 |
| JavaScript | 28 scripts | 0 | 0 |
| Browser / mocked HTTP | 172 | 0 | 0 |
| Live Uvicorn | 18 | 0 | 0 |
| Recovery | 6 | 0 | 0 |

WSL2 Linux, Python 3.14.7, Node 22.23.2; 2026-11-05 14:18:34 to
14:26:20 UTC. The detached sparse clone excludes uncommitted source changes.
[Local evidence snapshot](https://github.com/dajomas/Looking-Glass/tree/f73bf2e90bcb01e849b81a9678566935028ce093/local-tests-2b12130/run-20261105T141834Z-0lUugv).

The earlier focused command was user-reported as 15 passed in 17.25 seconds;
that pasted output did not identify its checkout SHA. The published complete
local run supplies separate commit-scoped evidence. Local case counts must not
be presented as CI totals; both runs name the same tested implementation but
their publication commits are evidence containers, not tested source revisions.

## Accepted limitations and documentation

A dedicated live same-admin-event-loop overlapping upload/mutation latency
measurement was not demonstrated. Passing the existing Live Uvicorn suite does
not establish that coverage. The user explicitly accepted closure with that
limitation. Broad filesystem/commit fault matrices and repeated cancellation
races are not established. Filesystem cleanup failures and process termination
can leave orphan files; this is not crash-atomic image storage. Other synchronous
SQLite transactions and external writers can still cause contention.

TODO.md closes only 29, leaving six second-hunt findings open: 22 and 24-28.
HANDOVER.md links this closure and retains implementation history. README.md
was reviewed; its user-facing behavior and existing documentation links remain
accurate, so no cosmetic change is needed. Historical audit files and split
manifests are unchanged. No tests were executed for this documentation-only
closure; no CI result for this closure commit is claimed. No evidence cleanup,
other branch, archive or Patch/ material is included.
