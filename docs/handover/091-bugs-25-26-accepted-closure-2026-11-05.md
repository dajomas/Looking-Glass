# Bugs 25/26: accepted closure (2026-11-05)

## Acceptance and scope

The user requested finishing and closing bugs 25 and 26 after review of the green
commit-scoped CI evidence. Both backlog findings are accepted and closed on
features/perplexity within the scope and limitations recorded here. These are
repository backlog numbers, not GitHub issue numbers.

This record supersedes acceptance-pending and fixture-follow-up statements in
records 089 and 090 without rewriting their historical preparation, test or
failure evidence. The closure is documentation-only: no application, test,
workflow or migration changes are included.

## Delivered implementation

- Regression-first tests: 6e84c4fca37d62abfdacd872af5bbe65a32866bc.
- Bug 25 state ordering: 69ac6f81da23ef3c999657cbbef7c9254bec3317.
- Behavior-preserving wall-renderer extraction: dbfa42fceaa0b6f9b56dc00112858578b76d0701.
- Bug 26 mask identity/generation and guarded errors: d11f58d74c1b3b10b6324ff78fa9df63a1d35a31.
- Extracted door-arrow fixture alignment: 2a4a9f9175936b3a01002c84732ba31716a0c2df.

Bug 25 centralizes editor map-state GET installation through request generations.
Starting an action fences prior reads; installed state also fences outstanding
reads; background polling does not start while busy. Cache-token identity is
included even when numeric fog/wall versions are equal, without ordering random
tokens. Valid later external changes still converge through polling.

Bug 26 invalidates pending mask work before the cache-hit return. Both fog and
arrow decodes must complete and match the current request generation and state
identity before synchronous installation. Obsolete decode errors are ignored;
current failures retain actionable loading feedback. The corrected door-arrow
fixture retains its original assertions and additionally checks one refresh GET,
one state installation and preservation of the original stale-action error.

## Reviewed CI evidence

GitHub Actions run 42055860962, attempt 1, tested exactly
2a4a9f9175936b3a01002c84732ba31716a0c2df on features/perplexity. Collected run.json
records completed/success, all five jobs successful and each report-validation
step successful. Reviewed JUnit suite attributes report:

| Suite | Reported results | Failures | Errors | Skipped tests |
|---|---:|---:|---:|---:|
| Python / HTTP | 1635 tests | 0 | 0 | 0 |
| JavaScript regressions | 31 scripts | 0 | 0 | 0 |
| Browser / mocked HTTP | 172 tests | 0 | 0 | 0 |
| Live Uvicorn | 18 tests | 0 | 0 | 0 |
| Recovery | 6 tests | 0 | 0 | 0 |

Counts are report totals, not a new independent execution or a recount of every
assertion. JavaScript JUnit counts whole scripts rather than their nested cases.
Python totals were read from the first bounded results.xml reading chunk.
Conditional skipped workflow steps are not skipped test cases. Browser reports
include editor startup/retry and wall-control/width checks; those integration
checks do not prove every admin mask/state race in a real browser.

Evidence snapshot: repository commit 8b0a747dc79af96c04f103246817bd5bd35433ae,
folder ci-results-42055860962-attempt-1/. This publication/storage commit is not
the tested source revision. The closure commit itself has not been tested by
this CI run.

## Local evidence and preserved failures

The user supplied 18/18 focused Node cases passing after the mask implementation.
The subsequent JavaScript-only local run tested
2a4a9f9175936b3a01002c84732ba31716a0c2df: all 31 scripts exited 0, with both
test_exit and report_exit 0. Run directory:
local-tests-2a4a9f9/run-20261105T153158Z-u6U6HT; publication commit:
2c087ae133ab722ef01d8faf1b61455b955c50ea. This is not an all-suite local run.

Earlier all-suite local evidence tested d11f58d74c1b3b10b6324ff78fa9df63a1d35a31,
not the fixture-fix revision: run local-tests-d11f58d/run-20261105T151520Z-rd7W75,
publication abc99914bd6df193f151d5149d2570c4f960b6c8. It remained overall exit 1
with the door-arrow fixture as its sole failing JavaScript script. Other suite
test/report exits were 0. That failed run is retained as failed evidence; it is
not retroactively relabeled green or combined with the later JavaScript rerun
into an all-suite local result for 2a4a9f9. The green CI run supplies the same-SHA
five-suite validation for acceptance.

## Accepted limitations and documentation

Ordinary coordinate fog actions still lack server-side stale-context validation.
This closure covers client response/mask sequencing, not all stale-coordinate
mutations or every multi-client/network ordering. Background read generations
prefer the newer-issued request; if that request fails, convergence waits for a
later successful refresh. Obsolete requests are ignored, not network-aborted.
An already installed overlay may remain while another loads; existing tap gating
still requires its key to match current state. No real-browser exhaustive race
matrix, every browser engine or every deployment topology is claimed.

TODO.md closes only 25/26 and leaves four second-hunt findings open: 22, 24, 27,
28 (remaining audit order 27 -> 28 -> 22 -> 24). HANDOVER.md links this closure
and keeps implementation history. Release notes describe the accepted behavior
and evidence limits. README.md was reviewed and remains accurate: no new user
controls, setup commands or migration are needed, so it is not cosmetically edited.
Historical audits, split manifests, implementation history and published evidence
are unchanged. Evidence-directory bulk cleanup remains separate unfinished
housekeeping; no files are deleted or renamed here.

No tests were executed for this documentation-only closure preparation and no
new CI success is claimed for it. No archive, Patch material, merge or other
branch is included. Commit/push completion is reported only after the approved
GitHub write succeeds.
