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
