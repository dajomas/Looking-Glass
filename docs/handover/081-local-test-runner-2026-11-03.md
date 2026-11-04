# Commit-scoped local test runner (2026-11-03)

## Delivery and decisions

Added root `runlocaltests.sh`, invoked with bash, to collect local validation
under `local-tests-<full HEAD hash>/run-<UTC timestamp>-<unique suffix>/`.
The output parent is ignored by Git. Repeated runs retain separate evidence;
no prior output, configured application data or checkout test-results are deleted.

Default execution covers the five CI groups sequentially: Python / HTTP,
JavaScript, mocked browser, live Uvicorn and recovery/container tests. --suite
selects one group. The script reuses the JavaScript evidence runner and browser
preflight, sets the live/container opt-ins, emits JUnit and merged stdout/stderr
logs, and fails missing/empty/malformed/failed/skipped reports. A failed group
normally does not prevent later groups from running. Exit status 0 requires all
selected groups to pass. The EXIT trap records setup failures and interruptions
once an evidence directory exists; prerequisite failures before that point
cannot produce a run directory.

The script uses git archive of the captured commit, not dirty/untracked files,
and runs in an extracted source copy inside the evidence directory. Dependencies
come from the existing selected interpreter, not that copy. This avoids copying
local configuration/data/environments and preserves diagnostics hardcoded by
fixtures under worktree/test-results. Pytest temporary data is under run/tmp.
The archive does not contain its own .git directory; tests requiring a normal
Git checkout may need separate investigation. Git commands run inside that nested
archive can discover the enclosing original checkout.

## Usage and prerequisites

See [the testing guide](../testing.md#commit-scoped-local-test-output).
Use `bash runlocaltests.sh --suite python` for Python/HTTP without browser or
container prerequisites. All groups need an existing application test environment;
the full run also needs Node.js, Playwright/Chromium/system libraries and Docker
with suitable permissions. Dependencies are not installed automatically.
Use --python for an explicit interpreter. Automatic precedence is active virtual
environment, .venv-test, .venv, python3.14, then python3. The interpreter version
is recorded, not enforced; the supported application/CI target is Python 3.14.
No executable-bit change is claimed by GitHub delivery; invoke with bash.

## Validation and limits

Executed bash -n and a temporary Git-repository control-flow harness with a fake
interpreter producing stub JUnit reports. The harness verified success, nonzero
test exit despite a passing report, skipped-report rejection, browser preflight
failure with subsequent recovery execution, single-suite selection, separate
repeated-run directories and exit-code recording. This is orchestration testing,
not execution of the real Python, JavaScript, browser, live or recovery suites.
An initial harness implementation had incorrect argv handling for stdin scripts;
it was corrected before the successful checks. Full application runs, Docker,
other platforms, real dependency failures and signal handling remain unverified.

README.md and HANDOVER.md were read. README's test instructions remain valid;
current usage is added to docs/testing.md and this indexed record. Existing
runtests.sh, application code and historical manifests are unchanged. Every file
in this change is below 25,000 bytes. The requested commit includes [skip ci].

## Native scratch and recovery-engine integration follow-up (2026-11-03)

This section supersedes the original archive layout and Docker-only local
prerequisites above; those sections preserve the initial delivery history.
Local evidence committed at a31cb830dbc86a388607e61dead63c509b1bfd6b tested
a761ee92aadd6457f0a393bfa77327d0eb26eb2a under WSL2 on /mnt/d. It reports
three Python failures (recovery file permissions, tracked dependency audit,
FIFO packaging) and two container setup errors because Docker was not found.
The Python log exceeds connector limits, so the exact Python tracebacks were
not read; filesystem/Git mechanisms are addressed based on test-source review,
not claimed proven from those inaccessible tracebacks.

runlocaltests.sh now delegates workspace handling to tools/local_test_workspace.py.
It prepares an exact detached shared clone in native /tmp (or
LG_LOCAL_TEST_TMPDIR), probes POSIX permissions/FIFOs/symlinks, and has its own
Git root/index. Sparse-checkout excludes root ci-results-* and local-tests-*
evidence trees. Dirty files, local config/data and environments are not copied.
Dependencies remain in the original selected interpreter. Do not prune source
Git objects during the run. Results stay in the requested commit-scoped output.
An EXIT finalizer copies regular diagnostics and selected browser evidence,
records omitted links/special files, then removes only token-identified scratch.
Collection errors retain scratch and fail the run. SIGKILL remains outside this
cleanup guarantee. Full sources, synthetic DBs and Git objects are not copied
back to evidence. Short pytest tracebacks and per-case failures.txt excerpts
make future failures readable while preserving complete reports/logs.

Recovery's test_container.py now wires the existing native Engine adapter:
local auto prefers Podman then Docker, CI=true defaults Docker, and explicit
LG_CONTAINER_ENGINE overrides selection. Version/info and selection are logged.
Native pull flags, read-only configuration mounts and loopback-port validation
come from the adapter. Missing/unusable engines still fail; no skip or daemon
fallback is introduced. Non-root startup, persisted volume/session/fog checks
and scoped resource cleanup remain in place. If neither engine is installed,
the local environment still needs installation/configuration before acceptance.
No application or production security assertion is weakened.

Validation executed in an isolated Python 3.12 sandbox: 8 support pytest cases
passed using actual local Git clones/filesystem operations and AST-loaded
recovery wiring with fake engine boundaries. Four full runner smoke scenarios
with stub suite commands passed their expected status checks (success, nonzero
suite exit, skipped report, failed browser preflight), including continuation,
independent Git roots, diagnostic collection and scratch cleanup. bash -n passed.
These are harness checks, not real WSL, application, browser or container runs.
The original three Python failures and real Podman/Docker recovery have not yet
been rerun. No passing full-suite or bug 16 closure is claimed.

README.md and HANDOVER.md were reviewed and remain accurate at their level;
this existing record is already indexed. docs/testing.md documents current
behavior. All six changed files are below 25,000 bytes. This follow-up does not
request CI skipping and does not alter prior evidence or historical manifests.

## Full identity and finalized publication repair (2026-11-04)

The user changed the folder label to a seven-character SHA and added automatic
result commits/pushes. Passing that label into prepare caused its exact full-SHA
comparison to reject a successful checkout. The publication block also executed
inside the scratch clone before finished_utc, exit-code.txt and diagnostic
collection, so it could target the wrong repository and omit final evidence.

runlocaltests.sh now captures the full HEAD commit once for prepare, verification
and provenance, with a separately derived short label for local-tests-SHORT.
The helper's full-SHA contract is unchanged; no prefix-only verification is used.
User-added automatic publication is preserved and documented as the default;
--no-publish disables all Git writes. It occurs in the EXIT handler, from the
original checkout, only after selected suites finish and collection succeeds.
Only that invocation's finalized run directory is path-scoped committed with
[skip ci]. Publishing requires features/perplexity, unchanged HEAD and an empty
index, and explicitly pushes origin HEAD:refs/heads/features/perplexity without
force. Existing unrelated staged changes are refused rather than included.
Setup failures/interruption are not published; completed failed suites may be
published but retain failure. Publication status/logs stay outside the run,
which is not modified after its evidence commit. A failed push can leave a
local evidence commit; no destructive reset or automatic retry is performed.
exit-code.txt represents test/collection status, while publication failure also
makes the process exit nonzero. All diagnostics should be inspected before sharing.

Validation: bash -n passed. Seven regressions in a temporary checkout passed,
using real local Git repositories/bare remotes and stub helper/application test
commands. They verify full identity, short folders, no-publish, finalized contents
at remote, successful and failed-suite publication status, refusal of staged
changes/other branches, rejected push handling and setup-failure retention.
These are runner regressions, not real application/WSL/container or hosted GitHub
publication tests. The real suites need rerunning for this repair.

Separately, run 41723122486 attempt 1 reports success for all five CI jobs on
5232cc70fbc6816858f4d1b7eedf78a577976e2b; run.json was read from evidence commit
63c47bacb747af8d47b168fd95e3dd9661c167cc. Job metadata was checked, not individual
JUnit cases. That earlier run predates and does not validate this runner repair.
No unrelated bug status or application behavior is changed.

README.md/HANDOVER.md were reviewed; this existing record remains indexed and
current usage is in docs/testing.md. All four changed files are below 25,000 bytes.
The repair commit does not skip CI; only generated evidence commits do.
