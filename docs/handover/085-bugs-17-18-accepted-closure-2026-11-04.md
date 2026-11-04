# Bugs 17 and 18: accepted closure and evidence limits

## Accepted status and scope

The user requested closure on 2026-11-04 after the successful full local run
and GitHub Actions results were reviewed. Bugs 17 and 18 are accepted and closed
on features/perplexity within the scope below. This record supersedes pending
statements in the historical [regression-first record](083-bugs-17-18-regression-first-2026-11-04.md)
and [implementation/harness record](084-bugs-17-18-original-retirement-2026-11-04.md).
The original audit remains a historical snapshot; TODO.md is authoritative for
current status. No other bug's status changes.

The combined production fix was delivered in
`2b9f83ce3c6dcff2fd80c825aeafb6fd9062a8ae`. Original-image replacement registers
the superseded original through image_retirement.retire_paths inside the existing
BEGIN IMMEDIATE transaction, after the locked compatibility recheck and before
replacing the reference. Registration, replacement and room-note reconciliation
commit or roll back together. The post-commit old-original unlink is removed.

For bug 17, replacement no longer deletes the original path still selected by
in-flight readers. For bug 18, old-original unlink failure is no longer between
the database commit and fog invalidation/viewer notification. This does not claim
notification cannot fail for other reasons. Failed-new-image cleanup and
original/alternate compatibility checks retain their existing contracts.
Superseded originals are retained until explicit coordinated offline collection;
there is no new migration or historical orphan-file backfill.

The AST test harness was corrected in
`d0375c3cf72058268f79b9fc9fcae28ce8a51818` to replace the reconciliation import
at nested depths with its dependency double. This is the source tested by both
successful full runs below, not an additional production behavior change.

## GitHub Actions evidence

Run 41906927331, attempt 1, event push, branch features/perplexity, tested
headSha `d0375c3cf72058268f79b9fc9fcae28ce8a51818`. The published run.json at
evidence commit `240c557b8e77eeabf37128fcd02f4558c08857f0`, directory
`ci-results-41906927331-attempt-1/`, reports status completed, conclusion success.
All five jobs completed successfully: Python / HTTP, JavaScript regressions,
Browser / mocked HTTP, Live Uvicorn and Recovery. Each job's Reject skipped tests
or empty results validation step also succeeded. Conditionally skipped workflow
steps in the job matrix are not skipped test cases.

Review covered run/job metadata and validation-step outcomes, not a recount of
every CI JUnit case or an audit of every retained diagnostic artifact. The
[evidence snapshot](https://github.com/dajomas/Looking-Glass/tree/240c557b8e77eeabf37128fcd02f4558c08857f0/ci-results-41906927331-attempt-1)
is distinct from the tested source commit.

## Full local evidence

Tested source `d0375c3cf72058268f79b9fc9fcae28ce8a51818`; evidence commit
`432264823456a9cded97cc633c271765343db1fb`; directory
`local-tests-d0375c3/run-20261104T202943Z-oiZv8X/`. The workspace identity record
confirms requested, expected and actual source IDs all match that full hash.
The overall runner exit code is 0. Summary.tsv gives test_exit=0 and report_exit=0
for every suite. Per-suite report-validation logs show:

| Suite | Reported cases | Failed/error | Skipped |
|---|---:|---:|---:|
| Python / HTTP | 1476 | 0 | 0 |
| JavaScript regressions | 28 scripts | 0 | 0 |
| Browser / mocked HTTP | 172 | 0 | 0 |
| Live Uvicorn | 18 | 0 | 0 |
| Recovery | 6 | 0 | 0 |

JavaScript counts scripts, not nested assertions. These are local report counts,
not independently recounted CI totals. See the
[local evidence snapshot](https://github.com/dajomas/Looking-Glass/tree/432264823456a9cded97cc633c271765343db1fb/local-tests-d0375c3/run-20261104T202943Z-oiZv8X).

The earlier full local run on 2b9f83c failed three standalone harness cases with
KeyError for the nested reconciliation import. That failure is not omitted or
reclassified as a clean run. The corrected tested source above resolves it;
record 084 preserves the cause and the isolated rerun details.

## Limits and documentation-only delivery

Acceptance is based on the implemented retention design, the corrected isolated
checks and the supplied successful integration suites. It is not proof of every
possible reader interleaving, a new dedicated deferred-ASGI-FileResponse or cold
fog-worker barrier test, or exhaustive original-replacement collector fault
injection. External deletion, uncoordinated readers, shared-storage multi-process
operation, power-loss durability and failed-new-file process-termination windows
are not redesigned. Deployment and other-platform validation are not claimed.
Disk growth until maintenance remains an operational obligation; stop all readers
and use the installation configuration before collection as documented in
[retired artwork maintenance](../image-retirement.md).

This closure was prepared from live branch head
`2e0958fef0cc054fc235093f61119157adc3edaa`. TODO.md closes both backlog items;
HANDOVER.md indexes this acceptance record; release notes describe the accepted
fix, offline-collection requirement and evidence. README.md was reviewed and its
existing summary and maintenance link remain valid; the maintenance guide already
explicitly documents original replacement, so neither needs a cosmetic edit.
Historical audit/implementation records, manifests and evidence snapshots remain
unchanged. No application code, tests, migrations, GitHub issue state or other
branches are changed. These numbers are repository backlog IDs, not GitHub issue
numbers. No new tests were executed for this documentation-only closure and no
new CI result for the eventual documentation commit is claimed. No archive or
Patch/ delivery material is added.
