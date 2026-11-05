# Bug 27: accepted closure with acceptance gap (2026-11-05)

## Acceptance and scope

The user explicitly requested closing bug 27 while noting the acceptance gap,
updating documentation and committing with [skip ci]. Backlog bug 27 is accepted
and closed on features/perplexity within the delivered scope and limitations
below. This is a repository backlog number, not GitHub issue number 27; no
GitHub issue mutation is included. This record supersedes open/pending/delivery
statements in record 092 without rewriting its historical evidence.

This closure is documentation-only. Application code, tests, workflows, migrations,
permissions and the historical audit are unchanged. TODO.md marks only bug 27
newly closed and leaves 22, 24 and 28 open, in remaining order 28 -> 22 -> 24.

## Delivered implementation

The completed implementation is 7770c2212dd3e23c2b0496d0bf6f4d632a981cd2.
Earlier increments exposed room_notes_version in the admin map payload, taught
room-notes refresh to reload clean selected content and library assignment
availability while preserving dirty drafts, connected polling and unchanged-state
retries, and invalidated named/unnamed-room coverage on notes revisions.
The final increment shares library read generations between the dialog and
picker and refreshes an open manager from accepted entries, preserving scroll
and busy controls. Obsolete read errors/results cannot replace newer accepted
library state. Existing server stale-save checks remain unchanged.

The notes revision does not change fog-mask identity. This fixes notes-only
convergence without requiring a fog edit, schema migration or new user control.
Details and intermediate failures remain in
[implementation history](092-bug-27-regression-first-2026-11-05.md).

## Reviewed local evidence

Published run: local-tests-7770c22/run-20261105T205713Z-HLJZpI,
evidence commit b05abe9110f191f1bc3f104d6ff4420567df237e.
workspace-identity.json records requested, expected and actual source as exactly
7770c2212dd3e23c2b0496d0bf6f4d632a981cd2. environment.txt identifies a detached
sparse clone, excludes uncommitted changes, and records Python 3.14.7 and Node
v22.23.2 on WSL2. All five summary.tsv test_exit/report_exit pairs are 0.

| Local suite | Reviewed reported count | Failures/errors | Skipped |
|---|---:|---:|---:|
| Python / HTTP | 1,607 tests from report-validation.log | 0 | 0 |
| JavaScript | 35 scripts from JUnit inventory | 0 | 0 |
| Browser | 172 tests from JUnit | 0 | 0 |
| Live | 18 tests from JUnit | 0 | 0 |
| Recovery | 6 tests from JUnit | 0 | 0 |

JavaScript counts whole scripts, not nested cases. The inventory includes the
notes polling, room-notes sync, library sync, overlay sync and save-context
regressions. The assistant reviewed published evidence, not a new execution.
Python's count is the validation-log total, not a full reread of its large XML.
Earlier user-supplied focused runs also passed after implementation, including
all five library-sync cases, the existing manager and notes UI scripts, six
save-context cases and five polling cases. Preserve the earlier 4-failure/1-pass
library baseline as failed evidence, not retroactively green.

## Reviewed GitHub Actions evidence

Run/databaseId 42107960644, attempt 1, workflow Looking Glass integration tests,
event push, branch features/perplexity, headSha
7770c2212dd3e23c2b0496d0bf6f4d632a981cd2. Collected run.json records completed/
success, all five jobs successful (Python / HTTP, JavaScript regressions, Browser /
mocked HTTP, Live Uvicorn, Recovery), and each Reject skipped tests or empty
results validation step successful. Conditional skipped workflow steps are not
skipped test cases. No individual CI test totals are asserted here: the review
verified run/job metadata and artifact inventory, not every CI report.

Evidence folder: ci-results-42107960644-attempt-1, stored in repository snapshot
2f264ba97cf822c2c0a1d401d28e0471744ed443. That publication/current snapshot and
the local publication commit are not the tested implementation revision. The
successful run does not automatically validate every later repository change
or this documentation closure.

## Explicitly accepted acceptance gap and residual limits

No dedicated two-DM-editor browser/live acceptance scenario for bug 27 was
demonstrated. The reviewed browser/live inventories do not establish the complete
notes-only save/clear/unassign flow across two running editors, including clean
content/overlay/manager convergence, dirty-draft preservation and stale-save
rejection in one end-to-end scenario. Passing the existing browser/live suites
must not be relabeled as that missing acceptance test. The user accepts closure
with this gap recorded; it is not a claim the scenario passed.

Additional mutation/close/import/failure-retry interleavings and every browser/
deployment topology have not been exhaustively validated. The shared library
generation orders client request starts/acceptance, not server snapshots by a
returned library revision. Superseded requests are ignored, not network-aborted.
Polling is periodic and can be delayed while busy or after network failures.
Dirty drafts are preserved, not automatically merged or rebased.

Follow-up validation may add the dedicated two-editor scenario and broaden the
ordering matrix. These remain accepted validation follow-ups, not delivered
coverage or blockers to this user-authorized backlog closure. No other bug is
closed or reopened by this decision.

## Documentation and delivery

HANDOVER.md links this current closure and retains record 092. The room-notes
usage section now explains notes-only refresh, timing, draft/stale-save behavior
and limits. README.md and release notes were reviewed: their existing descriptions
remain accurate and do not require cosmetic edits for this closure. The original
audit and split manifests, prior history and published test evidence are untouched.
All proposed files remain below 25,000 bytes; no size split is needed.

No tests were executed during this documentation-only preparation. [skip ci] is
in the proposed commit message at the user's request; it is not evidence that
GitHub actually skipped a run. No archive, Patch/ material, merge, file deletion
or other branch is included. Report the closure commit SHA only after the exact
approved GitHub write succeeds.
