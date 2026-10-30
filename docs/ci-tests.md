# Complete automated CI test suites

This is the current CI contract for `.github/workflows/integration-tests.yml`.
It supersedes CI-specific descriptions of the previous two-job workflow in
`docs/testing.md`; that guide's general local/manual validation material remains
useful. This document describes configuration, not evidence of a passing run.

## Checks

Every configured push to `features/perplexity`, pull request and manual dispatch
runs four independent matrix jobs on Ubuntu 24.04, with fail-fast disabled and a
30-minute timeout per job:

| Check | Discovery/command | Runtime |
|---|---|---|
| Python / HTTP | `python/tests`, excluding browser and live_e2e | Python 3.14 |
| JavaScript regressions | every top-level `python/tests/test_*.js` | Node.js 24; Python report runner |
| Browser / mocked HTTP | `python/tests/browser` | Python 3.14, Playwright Chromium |
| Live Uvicorn | `python/tests/live_e2e`, with `LG_RUN_LIVE_E2E=1` | Python 3.14, Playwright Chromium |

The Python development/runtime requirements are installed and hard-import checked
in each job. Browser jobs additionally install Playwright and Chromium's system
dependencies, then run `python/tests/check_browser_environment.py` as a required
launch/navigation/DOM preflight. Its output records Playwright/Chromium and font
diagnostics. Browser fixture import-skips cannot produce a passing job because the
JUnit audit rejects skips. Conditionally inapplicable workflow steps are not
skipped test cases.

`python/tests/browser/test_upload_busy.py` adapts the existing standalone
`check_upload_busy_browser.py` into pytest discovery without changing its checks.
It exercises real Chromium against mocked responses, not a live campaign.
The original standalone command remains usable. The local runtests.sh browser
phase also discovers the adapter automatically.

## JavaScript reporting

Run `python tools/run_javascript_tests.py` from the repository root. It launches
all matching scripts in sorted order with the checkout root as working directory,
continues after script failures, and fails on empty discovery, a nonzero exit,
missing executable or timeout. Default timeout is 120 seconds per script;
`--timeout`, `--test-dir`, `--output-dir` and `--node` support focused validation.

`test-results/javascript-inventory.tsv` records every discovered script, exit
status, duration and log filename. Each script has a complete separate log.
`results.xml` reports one case per script, not each nested Node test/subtest.
A passing script means its Node process returned zero; nested skip/TODO semantics
are not parsed by this wrapper and must be inspected in its output when relevant.
There is no JavaScript package installation: scripts use Node built-in modules.
The local runtests.sh JavaScript loop remains unchanged; the reporting runner is
an additional entry point used by CI.

## Evidence and gates

Every job uploads `test-results/` even after a failed step, with names
`integration-python-<sha>`, `integration-javascript-<sha>`,
`integration-browser-<sha>` and `integration-live-<sha>` (14-day retention).
The directory is initialized before dependency installation so early failures
retain source/platform identity when checkout succeeds. Full setup output remains
in the Actions job logs. Each executed suite writes a JUnit report; a separate
audit rejects missing, empty, failed/error or skipped-case reports. Test exit
statuses are preserved through tee pipelines.

`getworkflow.sh` needs no update: it downloads all artifacts for the selected run,
records full run logs/metadata, generates reader chunks and prints the copyable
run/tested-SHA/evidence-SHA handoff after a successful publish. Older runs naturally
have fewer artifact groups. Artifact download remains run-scoped rather than
attempt-filtered; verify provenance after reruns.

Repository administrators must separately require all four named checks in branch
protection/rulesets if they are intended merge gates. This change does not alter
those settings or write to another branch. Existing `[skip ci]` evidence-only
commits still suppress push/PR workflows; consider required-check implications.

## Limits and validation

This runs the existing automated regression groups on one Linux/Python/Chromium
configuration. It does not automate the manual deployment checklist, add Windows,
Firefox or WebKit coverage, prove production behaviour, or automatically discover
arbitrarily named future standalone checks. Add future automated checks to an
existing discovery group or explicitly wire them into CI.

Local preparation validated workflow YAML parsing/matrix structure and five
isolated report-runner scenarios: success, continued execution after a failure,
timeout, empty discovery and missing executable. Runner fixtures used Python as
a stand-in executable, not actual JavaScript tests. The full project checkout,
Node regressions, Chromium adapter and hosted Actions workflow were not executed
by the assistant. The first four-suite CI run is acceptance evidence still needed.
