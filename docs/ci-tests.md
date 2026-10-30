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
| Recovery | `python/tests/recovery`, with `LG_RUN_CONTAINER_TESTS=1` | Python 3.14, real CLI processes, HTTP and Docker |

All jobs install development/runtime requirements and hard-import check the web
stack. Browser/live jobs install Playwright, Chromium and system dependencies,
then require `check_browser_environment.py`. Its diagnostics include browser and
font information. A reported pytest skip fails the JUnit audit. Conditionally
inapplicable workflow steps are not skipped test cases.

The mocked-browser suite includes the standalone upload-busy check through a
separate-process pytest adapter, isolating async and synchronous Playwright loops.
The original standalone command and local runtests.sh discovery remain available.

## Reliability batch 1

Recovery process tests launch `python/main.py --config <temporary-config> serve`
with isolated data and loopback ports. Inherited LG_* overrides are removed and
an explicit test-only bootstrap password is supplied. They exercise normal
shutdown/restart and forced termination after acknowledged committed writes.
They check both listeners, existing viewer access, persisted snapshot/version,
fogged image pixels, database integrity/foreign keys and anonymous denial.
This is HTTP/image validation, not browser reconnection across server restart,
in-flight interruption, power-loss simulation or cross-file crash atomicity.
Port reservation is released for the CLI; a port race fails startup.

Live cases cover offline reconnect and two tabs sharing a session or using
independent sessions for the same account, including hide/undo after one closes.
Nine tooling cases cover Unicode/CRLF, single-line XML, binary/empty chunking,
size bounds, damage detection, no-overwrite and complete paginated inventory.

## Reliability batch 2, increment 1: built container

Two tests in `python/tests/recovery/test_container.py` build the real Containerfile
once per test session, then use separate disposable named volumes and containers.
The Recovery CI step explicitly enables them; missing Docker CLI/daemon, build
failure or container startup failure is an error rather than a passing skip.
Default local runs skip these opt-in Docker cases. Use a disposable local Docker
environment and explicitly enable them to claim full Recovery coverage:

```sh
LG_RUN_CONTAINER_TESTS=1 PYTHONPATH=python python -m pytest -v python/tests/recovery
```

Tests use the active Docker context and require a local daemon that can bind-mount
the test configuration file. Each image/container/volume has a UUID-based
looking-glass-test name. Only those resources are removed; no global prune is
used. Container volumes hold synthetic campaign data only. An interrupted CI job
or unresponsive daemon can prevent finalizers from completing; inspect test logs
and remove only recorded test-owned resources if manual cleanup is necessary.
Image cleanup is best effort, while named-volume removal is checked.

The first test verifies application PID 1 has uid 1001, both published health
endpoints become ready, both login templates render, and CSS/JavaScript assets
are served. Container ports remain 5000/5100 and host ports are assigned by Docker
on 127.0.0.1. The second creates a campaign, image/walls, viewer assignment and
reveal via authenticated HTTP. It verifies revealed/hidden PNG pixels, stops and
removes the first container, starts a new instance with the same named volume,
and checks those pixels and the display version using the existing viewer cookie.
Anonymous access remains denied. Synthetic users are seeded through a non-root
Docker exec using the application's repository/password-hashing code.

A read-only test config selects small PNG output and zero feathering for exact
pixel assertions. The image runs its real CLI with explicit --config arguments;
this does not test the image's default CMD verbatim. The production Containerfile
and runtime code are unchanged. Bounded docker stop must yield a stopped
container with zero exit status; a forced-shutdown exit does not pass. Build has
a 600-second command timeout; health readiness is bounded to 30 seconds and stop
to a 20-second client timeout with a 10-second daemon grace period. Client timeout
does not itself guarantee daemon-side build cancellation.

## Local commands

```sh
PYTHONPATH=python python -m pytest -v python/tests/test_ci_evidence_chunks.py
PYTHONPATH=python python -m pytest -v python/tests/recovery/test_restart.py
LG_RUN_CONTAINER_TESTS=1 PYTHONPATH=python python -m pytest -v python/tests/recovery
LG_RUN_LIVE_E2E=1 PYTHONPATH=python python -m pytest -v python/tests/live_e2e
```

Broad local pytest discovery also finds recovery; CI excludes that directory
from Python / HTTP to avoid duplicate execution. Without the container opt-in,
a local Recovery result is partial coverage, not equivalent to CI.

## JavaScript reporting

`python tools/run_javascript_tests.py` runs matching scripts in sorted order,
continues after failures and rejects empty discovery, missing executable,
nonzero exits or a 120-second per-script timeout. Options include --timeout,
--test-dir, --output-dir and --node. The TSV records filename, exit, duration and
log path; JUnit counts scripts, not nested Node cases. Nested skip/TODO semantics
are not parsed. Existing scripts require no npm package installation.

## Evidence and gates

Each job always uploads test-results as integration-<suite>-<sha>, retaining it
14 days. Identifiers are python, javascript, browser, live and recovery.
Identity is initialized before dependency setup; full setup output remains in
Actions logs. One pytest invocation covers process and container Recovery tests,
so neither overwrites the other's JUnit report. Missing/empty/failed/error or
reported-skipped results fail the common audit. Pipelines preserve test exits.

Live uses the dedicated ci-live-tmp basetemp and copies generated traces,
DM/player screenshots and page-errors.json to test-results/live-diagnostics.
Extra viewer contexts do not yet have individual trace capture. Recovery child
logs are under test-results/recovery, Docker version/build output under
 test-results/container-build, and per-case commands/inspect/server output under
 test-results/container. Inspect output contains synthetic test credentials;
review artifacts before publishing. Temporary databases are not uploaded.

getworkflow.sh already downloads/chunks all suite artifacts and prints the
copyable handoff after successful publish. Download remains run-scoped rather
than attempt-filtered. Its confirmed cleanup targets only recognized old root
collection directories in a clean features/perplexity checkout. Publishing
stages their tracked deletions with new evidence; local-only deletion stays
unstaged. Failures do not automatically restore files, which remain recoverable
from the printed starting commit. No history rewrite or Actions artifact removal
occurs. No collector changes are needed for container evidence.

Administrators must separately require all five checks in merge rules if desired;
workflow changes do not modify branch protection. Existing evidence-only skip-ci
commits retain their required-check implications.

## Validation and remaining work

Batch 1 and the reduced-motion synchronization fix were reviewed green in run
41020692166 at 6315be869139ee17536222795f4ae07e3d014c44: 1,134 Python tests,
29 subtests, 27 JS scripts, 162 browser, seven live and two recovery tests.
Those results do not establish the newly added container cases pass.

This container increment passed Python syntax parsing and a synthetic Docker
port-binding shape check only. No Docker daemon, image build, container, actual
HTTP deployment or full test suite was executed by the assistant. CI acceptance
of the new container increment remains pending. Linux Docker is tested, not
Podman/SELinux bind mounts or other operating systems/browser engines.

Batch 2 still needs controlled migration interruption, permission/disk/lock
failure injection and live access-revocation coverage. Later backlog includes
property-based state machines, delayed-response/restore live scenarios,
interruption during restore/duplication, and collector/runner harness tests.
These are not implemented by this container increment.
