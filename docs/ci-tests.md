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
| Recovery | `python/tests/recovery`, with `LG_RUN_CONTAINER_TESTS=1` | Python 3.14, real CLI processes, migration children, HTTP and Docker |

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

## Reliability batch 2, increment 2: controlled migration interruption

`python/tests/recovery/test_migration_interruption.py` adds two parameterized
cases against a temporary database built with the real first two migration
scripts. It seeds committed synthetic campaign/map/fog history, captures the
legacy schema and rows, then starts a separate Python child running the real
Database.migrate method. Only that child replaces the existing migration-3
initialization hook with a barrier wrapper; production code and SQL are untouched.

The child pauses either before ordered initialization or after initialization
but before recording version 3/committing. An atomically published JSON marker
must identify the exact child/phase, an open transaction and recorded version 2.
The after-initialization marker must contain correctly ordered snapshot arrays.
The child blocks on a private stdin pipe; it is never released to finish normally.
The parent waits for this handshake (15-second bound), confirms a separate
connection still sees exactly the committed version-2 schema/data, kills only
that child and requires termination within five seconds. No timed random kill
is used to choose the transaction boundary.

After termination, reopening must show the same legacy schema and original rows,
recorded version 2, and passing integrity/foreign-key checks. A new unmodified
Python process retries all pending migrations with a 20-second bound. The final
version must match the live migration list, original legacy-column values must
remain, snapshots must preserve per-map operation order, and maps without history
must remain without snapshots. A further migration call must leave cache tokens
and saved snapshots unchanged. Missing handshake, early child exit, partial
commit, damaged data, incorrect order or failed retry all fail the test.

The test does not start the web server, render images or read production config.
It needs no Docker opt-in when run by itself:

```sh
PYTHONPATH=python python -m pytest -v python/tests/recovery/test_migration_interruption.py
```

This proves only the selected migration-3 boundaries under process termination
when the tests actually pass. It does not simulate power loss, interruption at
every SQL statement, all historical migrations, filesystem/database atomicity,
or interruption during restore/duplication. No production failure hook exists.

## Reliability batch 2, increment 3: storage-failure safety

Eleven new Python / HTTP cases use temporary data and scoped injected errors,
not real disk exhaustion or permission changes. `test_storage_failures.py` covers
image-create permission denial, partial PNG encoding failure with ENOSPC, UUID
collision preservation, recovery-ZIP create denial/partial write/file-fsync/
directory-fsync errors, and real SQLite contention between two connections.
The contender's busy timeout is shortened on that connection only. Tests verify
prior file contents and committed rows remain intact, failed recovery ZIPs are
removed, and retry succeeds after the injected fault/lock is removed. Directory
fsync injection targets the Linux CI durability path; it is not Windows coverage.

`test_storage_failure_web.py` adds EACCES, ENOSPC and EIO restore-gate cases.
A valid preview is prepared first; recovery storage then fails before live
replacement. Tests distinguish trial imports into inspection clones from writes
to the real test database, require the restore-blocked response, preserve every
DB row and map/recovery file, and require no success notification. This checks
the HTTP/service gate, not delivery to a real connected browser (increment 4).

The image fault reproduced a real partial-file leak in the prior store helper.
`images.store_map_image` now exclusively creates its destination before encoding.
Only after creation succeeds does it own that path. Encoding/close failures close
the stream and attempt to remove the partial file; a collision cannot overwrite
or delete another file. If unlink itself fails, a warning is logged and the
original error is retained. This is best-effort failure cleanup, not crash-safe
atomic publication or fsync durability. Empty directories may remain. Storage
errors are not newly translated into friendly upload/replace HTTP responses.

Failures after a fully successful image store but a subsequent upload/replace DB
write failure remain a separate orphan-cleanup gap: this increment does not
claim coverage or a fix for that transaction boundary. No upload/replace route
transaction logic or backup implementation changes are made here.

Run the new cases locally with installed development requirements:

```sh
PYTHONPATH=python python -m pytest -v python/tests/test_storage_failures.py python/tests/test_storage_failure_web.py
```

Existing top-level discovery collects all 11 cases without workflow/collector
changes. Failed-case tracebacks and values reach the existing Python job log
and JUnit artifact. No real account or campaign data is used.

## Local commands

```sh
PYTHONPATH=python python -m pytest -v python/tests/test_ci_evidence_chunks.py
PYTHONPATH=python python -m pytest -v python/tests/test_storage_failures.py python/tests/test_storage_failure_web.py
PYTHONPATH=python python -m pytest -v python/tests/recovery/test_restart.py
PYTHONPATH=python python -m pytest -v python/tests/recovery/test_migration_interruption.py
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
Actions logs. One pytest invocation covers all Recovery tests, so reports do not
overwrite one another. Missing/empty/failed/error or reported-skipped results
fail the common audit. Pipelines preserve test exits. Existing discovery already
includes increments 2/3; neither workflow nor collector needs changing for them.

Live uses ci-live-tmp and copies generated traces, DM/player screenshots and
page-errors.json to test-results/live-diagnostics. Extra viewer contexts do not
yet have individual traces. Recovery server logs are under test-results/recovery;
Docker version/build logs under test-results/container-build; container case
commands/inspect/server output under test-results/container. Inspect output has
synthetic test credentials, not real account data; review before publishing.
Migration logs, barrier marker and successful result summary are under
`test-results/migration-interruption/<phase>/`. Temporary databases are not
uploaded. Failure may prevent a successful result summary, but earlier logs and
the handshake (if reached) remain available to the always-uploaded artifact.

getworkflow.sh downloads/chunks all suite evidence and prints the handoff after
successful publish. Download is run-scoped, not attempt-filtered. Its confirmed
cleanup targets recognized old collection directories in a clean working branch;
publication stages tracked deletions with new evidence, while local-only removal
stays unstaged. Failures do not automatically restore files, recoverable from
the printed starting commit. No history rewrite or Actions artifact removal occurs.
Administrators must require all five checks separately in merge rules if desired;
protection settings and skip-ci evidence-commit implications are unchanged.

## Validation and remaining work

Increment 2 was reviewed green in run 41025509410 at
183a4787001597095a4ba26303ca57b04557b3ed: 1,134 Python tests, 29 subtests,
27 JS scripts, 162 browser, seven live and six Recovery cases. Both interruption
summaries recorded killed child exit -9, retry exit 0 and final schema version 17.
Those results do not validate this new storage-failure increment.

For increment 3, the assistant verified the live images.py blob before preparing
its change, reproduced the pre-fix partial-PNG leak, and passed focused candidate
checks for partial cleanup, permission failure, collision preservation, valid
retry and real SQLite contention/retry on Python 3.12.8 / SQLite 3.46.1. Candidate
source and new test modules parsed. The full committed pytest/HTTP/recovery-ZIP
cases and Python 3.14 CI were not executed; acceptance is pending CI.

Batch 2 still needs live access revocation (increment 4). Post-image-store DB
failure cleanup also remains an explicitly identified gap. Later work includes
property-based state machines, delayed-response/restore live cases, broader
interruption coverage and collector/runner regressions. General power-loss,
cross-file atomicity and other platform/browser claims remain out of scope.
