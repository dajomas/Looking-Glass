# Bug 28: accepted closure and validation limits (2026-11-06)

## Acceptance and delivered scope

The user requested finishing and closing bug 28 after review of successful
focused, local all-suite and CI evidence, with [skip ci] on this closure commit.
Backlog bug 28 is accepted and closed on features/perplexity. This is a repository
backlog number, not GitHub issue number 28; no GitHub issue mutation is included.
This record supersedes open/pending-validation statements in records 094-096
without rewriting their preparation, failures or evidence limits.

Regression-first commit f707eef73cd6fd251eab6ad8f51f81300e617f04 added the
25-case HTTP regression file. Production fix
a54f6346ff6fa2b89b94c719f9bc5e89b0483559 adds the half-open image-coordinate
guard in _fog_op after authorization/fog_inputs and before area interpretation:
0 <= x < spec.width and 0 <= y < spec.height. Model-valid outside points return
400 with Point is outside the map. Rejection precedes fog writes, version bumps,
active-map checkpoints and map-change notifications. Point-model validation,
authentication, CSRF, permissions, valid in-map wall snapping, no-op handling,
point-free reveal-all/reset/undo and historical fog replay are unchanged.
No schema migration, new user control or historical-data repair is required.
The existing API section 002 documents this contract and remains accurate.

## Browser measurement follow-ups

The CI browser failure exposed a separate wall screenshot-oracle problem.
Commit 25a09e65f2ce3019df24ea1e85092b8edb79838d introduced coherent current-path
measurement, positive-baseline checks and failure artifacts.
6a17cfe7e9f1e85791ada5d0fc69cff20087c674 retained completed measurements and
their matching PNGs separately from later failures and bounded attempt history.
27b2eebf21954dbef3338e667824acfd9e897c7a replaced near-solid colour counting
with background-aware, three-row coverage estimation for the controlled vertical
magenta-wall fixture. The existing +/-1 zoom comparison and native-drag growth
assertion remain; coverage has an absolute +/-0.5 check and CSS width +/-0.01.
Application rendering code was not changed for these test-harness corrections.
See record 096 for exact algorithm, rejection conditions and diagnostic limits.

## Focused user-run red-to-green evidence

The pre-fix paste reported 20 failed/5 passed in 22.03s: each invalid point
returned 200 instead of 400, not a fixture failure. The paste lacked source
identity and stopped at the first status assertion; later unchanged-state
assertions were not reached. A subsequent run explicitly pinned a54f6346...
and passed test_fog_point_bounds_web.py plus test_fog.py: 35 passed in 17.77s.
Thus the 25 HTTP cases reached their downstream DB/pixel/notification checks
and existing fog controls passed. This is user-run evidence, not assistant
execution. The earlier extracted sandbox checks are not substituted for HTTP.

After measurement corrections, the user pinned 27b2eebf... and reported all
65 helper/coverage cases passed in 2.32s, plus all five browser follow-up cases
in 9.36s. These include both battle/wall native-drag and keyboard/zoom/reload
variants and independent sidebar controls. Earlier local browser failures on
25a09e65... and 6a17cfe7... remain failures, preserved in record 096.

## Reviewed successful CI evidence

Run/databaseId 42173223083, attempt 1, workflow Looking Glass integration tests,
event push, branch features/perplexity, headSha
27b2eebf21954dbef3338e667824acfd9e897c7a. The collected run.json records
completed/success, all five jobs successful (Python / HTTP, JavaScript
regressions, Browser / mocked HTTP, Live Uvicorn, Recovery), and each Reject
skipped tests or empty results validation step successful. Conditional skipped
workflow steps are distinct from skipped test cases. The review verified
run/job metadata and artifact inventory, not every JUnit case; no individual
CI test totals are asserted in this record.

Evidence: ci-results-42173223083-attempt-1/ at repository snapshot
5badfd2b26ef6787b75013f5684cc2658034e39a. This evidence-storage revision is
not the CI-tested source. The earlier run 42113616342 attempt 1 on a54f6346...
remains failed: browser 171 passed/1 failed, other four jobs passed. Later
success does not retroactively turn that failed run green.

## Reviewed full local evidence

Published run local-tests-5badfd2/run-20261106T063012Z-WrRDF6/, evidence commit
dddf6b7e2571e945a9d7877c4a75d0c55c061c65. workspace-identity.json records
requested, expected and actual source as exactly
5badfd2b26ef6787b75013f5684cc2658034e39a. environment.txt identifies a detached
sparse clone excluding uncommitted changes, Python 3.14.7 and Node v22.23.2
on WSL2. The run finished 2026-11-06T06:38:03Z with overall exit 0 and every
summary.tsv test_exit/report_exit pair 0. Reviewed report-validation logs:

| Local suite | Reported tests/scripts | Failed/error | Skipped |
|---|---:|---:|---:|
| Python / HTTP | 1,697 | 0 | 0 |
| JavaScript | 35 scripts | 0 | 0 |
| Browser | 172 | 0 | 0 |
| Live | 18 | 0 | 0 |
| Recovery | 6 | 0 | 0 |

Counts are validation-log totals, not an independent recount of all XML cases;
JavaScript counts scripts, not nested cases. The local tested SHA differs from
the CI tested SHA. Neither is the publication commit or this closure commit.
Earlier full local evidence on a54f6346... was also green (publication
a433145f09081268080dfd602ae269fe0ec6d881); it did not erase the same-source
failed CI browser job. Keep each result tied to its own revision and run.

## Accepted limitations and completion scope

The bounds check does not provide stale-context protection for otherwise valid
ordinary coordinate actions, change engine label clamping or repair stored
operations. Browser coverage is not exhaustive across engines/deployments. The
coverage estimator is deliberately fixture-specific: uniform background, known
magenta foreground and vertical wall. It is not a general image detector or
a guarantee for arbitrary textures, compression, colour spaces or rasterizers.
Coherent before/after probes cannot make screenshots/DOM sampling literally
atomic. Failures still need their retained diagnostics, not tolerance widening.

TODO.md newly closes only 28; the remaining second-hunt findings are 22 and 24,
in order 22 -> 24. HANDOVER.md links this closure and relabels 094-096 as
history rather than current blockers. Historical audits, manifests, records
and published evidence are unchanged. README.md and the API bounds guide were
reviewed and remain accurate, so no cosmetic edits are made to those files.

This commit changes documentation/status only: no application, test, workflow,
migration, file deletion, archive, Patch/ material, merge or other branch change.
No tests were executed for this closure preparation, and no new CI success is
claimed for it. [skip ci] is included as requested, not proof that a workflow
was actually skipped. Report the actual closure SHA only after the approved
GitHub write succeeds.
