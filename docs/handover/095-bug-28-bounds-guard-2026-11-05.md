# Bug 28: bounds guard; HTTP/CI validation pending (2026-11-05)

## Implementation and status

This increment adds the half-open image-coordinate check in _fog_op after
authorization and fog_inputs, before area_map/describe_click or any fog write:
0 <= x < spec.width and 0 <= y < spec.height. Model-valid outside points raise
BadRequest with Point is outside the map. The existing Point model, auth/CSRF,
no-op handling, FogEngine.label_at and historical replay are unchanged.
Reveal-all, reset and undo remain point-free. No schema migration is needed.
This does not add stale-context validation for valid ordinary fog coordinates.

Regression-first commit: f707eef73cd6fd251eab6ad8f51f81300e617f04. Its test file
is unchanged here. This record supersedes production-fix-pending statements in
record 094, preserving that preparation history. Bug 28 remains open pending
post-fix application evidence and acceptance; TODO.md and the audit are unchanged.

## User-supplied pre-fix HTTP baseline

The supplied paste.txt reports this command:

```bash
python -m pytest -q python/tests/test_fog_point_bounds_web.py
```

Result: 20 failed, 5 passed in 22.03s. Each invalid-point test reached line 78
and failed because response.status_code was 200 instead of 400, including
negative fractions, exact width/height and corners. There were no reported
fixture/setup errors. The five valid-point/wall/auth controls passed. These are
user-run results, not tests executed by the assistant. The paste does not show
a source SHA/workspace identity, so it is not independently commit-pinned.

Invalid tests stop at their first status assertion. Their subsequent unchanged
DB/pixel/notification checks were not reached; do not report those assertions
as passed or treat successful response payloads alone as independent DB proof.
No sensitive session/CSRF values from the log are copied into repository docs.

## Actual assistant validation and execution blocker

A fresh sandbox execution of the candidate extracted _fog_op body passed:
20 invalid cases rejected before area lookup, history/version/checkpoint writes
or notifications; six valid-point controls mutated; two point-free reveal-all/
reset controls retained their path. Dependencies/fog were test doubles and the
storage was minimal in-memory SQLite, not the full application schema. This is
28 extracted-function checks, not the 25 HTTP regression cases or a full suite.

The discovered GitHub connector exposes file reads/writes but no shell runner,
workflow-dispatch/run-status tool or CI-log reader. The sandbox has no repository
checkout or network access for dependency/source installation. Therefore the
assistant has not run post-fix HTTP/application/browser/live/full-suite tests,
and does not claim CI ran or passed. The proposed commit omits [skip ci] so the
existing push workflow remains eligible; this is not proof of a workflow run.

Live api.py is 24,763 bytes; the exact two-line guard adds 141 UTF-8 bytes for
24,904 bytes, below 25,000. Other changed documentation stays below the threshold.
No size split, unrelated refactor, file deletion, archive, Patch/ material, merge
or other branch is included. README.md was reviewed and remains accurate; no
cosmetic README change is needed. The API section documents the new contract,
and HANDOVER.md links this record while retaining record 094.

## Required post-fix validation

After the approved implementation commit is available, run in the normal
Python 3.14 development environment and retain the exact source SHA:

```bash
git rev-parse HEAD
python -m pytest -q python/tests/test_fog_point_bounds_web.py python/tests/test_fog.py
```

The focused HTTP target is all 25 cases passing, including downstream DB, pixel
and notification assertions on rejected points and the existing controls. Run
the normal CI suites too, inspect actual results and preserve any failures.
A green extracted check is not a substitute. Commit/push completion and the
actual SHA are reported only after the approved write succeeds.
