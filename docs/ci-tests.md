# Complete automated CI test suites

This is the current CI contract for `.github/workflows/integration-tests.yml`.
It supersedes CI-specific descriptions of earlier workflows in `docs/testing.md`;
that guide's general local/manual validation material remains useful.
Configuration and test definitions are not evidence of a passing run.

## Checks

Configured pushes to `features/perplexity`, pull requests and manual dispatches
run five independent matrix jobs on Ubuntu 24.04, with fail-fast disabled and a
30-minute timeout per job:

| Check | Discovery/command | Runtime |
|---|---|---|
| Python / HTTP | `python/tests`, excluding browser, live_e2e and recovery | Python 3.14 |
| JavaScript regressions | every top-level `python/tests/test_*.js` | Node.js 24; Python report runner |
| Browser / mocked HTTP | `python/tests/browser` | Python 3.14, Playwright Chromium |
| Live Uvicorn | `python/tests/live_e2e`, with `LG_RUN_LIVE_E2E=1` | Python 3.14, Playwright Chromium |
| Recovery | `python/tests/recovery` | Python 3.14, real CLI child processes and HTTP |

All jobs install development/runtime requirements and hard-import check the web
stack. Browser/live jobs install Playwright, Chromium and system dependencies,
then require `check_browser_environment.py`. Its diagnostics include browser and
font information. A reported pytest skip fails the JUnit audit. Conditionally
inapplicable workflow steps are not skipped test cases.

The mocked-browser suite includes the standalone upload-busy check through a
separate-process pytest adapter, isolating async and synchronous Playwright loops.
The original standalone command and local runtests.sh discovery remain available.

## Reliability batch 1

Recovery tests launch `python/main.py --config <temporary-config> serve` as a real
subprocess with isolated data and loopback ports. Inherited LG_* overrides are
removed and an explicit test-only bootstrap password is supplied. They exercise
normal shutdown/restart and forced termination after acknowledged committed
writes. After restart they check both listener health, existing viewer session
access, persisted snapshot and map version, revealed/hidden pixels in the real
viewer image response, SQLite integrity/foreign keys and anonymous denial.
This is HTTP/image persistence validation, not browser reconnection across a
server restart, in-flight transaction interruption, power-loss simulation or
cross-file crash atomicity. Port reservation must be released for the real CLI;
a port-allocation race fails startup rather than retrying silently.

Live tests additionally cover offline disconnect/reconnect convergence and two
viewer tabs sharing a session or using independent sessions for the same viewer
account. Both receive fog changes, and the surviving tab continues through hide
and undo after the other closes. These do not add distinct-account isolation,
access-revocation, delayed-response or checkpoint-restore live scenarios yet.

Nine Python tooling cases cover Unicode/CRLF, single-line XML, binary and empty
chunk reconstruction, per-file size bounds, damage/source-change detection,
no-overwrite policy and complete paginated-index reconstruction. No production
evidence or real GitHub account is used by those tests.

Run the new groups locally from the repository root:

```sh
PYTHONPATH=python python -m pytest -v python/tests/test_ci_evidence_chunks.py
PYTHONPATH=python python -m pytest -v python/tests/recovery
LG_RUN_LIVE_E2E=1 PYTHONPATH=python python -m pytest -v python/tests/live_e2e
```

A broad local pytest invocation also discovers recovery tests; the CI Python job
excludes them explicitly so they execute only in their own CI matrix job.

## JavaScript reporting

`python tools/run_javascript_tests.py` runs matching scripts in sorted order,
continues after failures and rejects empty discovery, a missing executable,
nonzero exits or a 120-second per-script timeout. Options include `--timeout`,
`--test-dir`, `--output-dir` and `--node`. The inventory TSV records filename,
exit status, duration and log path. Each script has a full separate log and one
JUnit case; nested Node case/skip/TODO semantics are not parsed. No npm packages
are required by the existing built-in-module regression scripts.

## Evidence and gates

Each job uploads `test-results/` even after failure, as
`integration-<suite>-<sha>` with 14-day retention. The five suite identifiers are
python, javascript, browser, live and recovery. Evidence identity is initialized
before dependency installation. Full setup output remains in Actions logs.
Reports must exist, contain cases and contain no failures/errors/reported skips;
test command exit statuses remain visible through tee pipelines.

The live job uses `--basetemp=ci-live-tmp` (pytest replaces that dedicated test
temporary directory). Its always-run diagnostic collection copies generated
`*-trace.zip`, `dm-*.png`, `player-*.png` and `page-errors.json` files into
`test-results/live-diagnostics/`, preserving relative paths. The existing live
fixture produces traces/screenshots on failures; a passing run need not contain
them. Extra viewer contexts in the new multi-session test do not have their own
trace capture. Recovery retains each child's server log under
`test-results/recovery/`; temporary databases/configuration are not uploaded.
All these artifacts contain synthetic test data; review logs before publishing.

The existing getworkflow.sh handles every artifact group without modification,
including binary traces through base64 reader chunks. It prints the copyable
run/tested-SHA/evidence-SHA handoff only after a successful publish.
Download remains run-scoped, not attempt-filtered; verify provenance after reruns.

Before downloading a new run, the collector requires a clean features/perplexity
checkout and valid completed run. It refuses an existing new output path, lists
old root directories named exactly ci-results-<digits> or its attempt-suffixed
form and requires typing remove before local deletion. Dirty/ignored contents
and symlinks block cleanup. With --publish, a separate confirmation stages old
tracked deletions with new evidence. Local-only runs leave deletions unstaged.
Cancellation/failure after cleanup does not automatically restore files; tracked
contents remain recoverable from the printed starting commit. No history rewrite
or Actions artifact deletion occurs.

Repository administrators must require all five named checks separately in merge
rules if desired. This change does not alter protection settings or other branches.
Evidence-only [skip ci] commits retain their existing required-check implications.

## Validation and follow-up work

Batch 1 adds 14 cases: two recovery, three live and nine chunking cases. The three
new Python test modules passed local syntax parsing. Full checkout tests, real
application subprocesses, browser tests, hosted Actions and actionlint were not
executed by the assistant for this batch. First five-suite acceptance is pending.
The previous four-suite run 41017872020 was reviewed green at
e6f932b688682328177dc7ef0063400bb75514be; those results do not transfer to this batch.

Remaining planned work: built-container health/volume persistence, controlled
in-flight migration/restore interruption, disk/permission/locking fault injection,
bounded property-based fog/import state machines, delayed-response and revocation/
restore live cases, and committed collector-cleanup/JavaScript-runner regressions.
These are explicitly not implemented in batch 1. One Linux/Python/Chromium
configuration does not replace manual deployment checks or other platform/browser
coverage. Future standalone checks still need a discovery group or explicit wiring.
