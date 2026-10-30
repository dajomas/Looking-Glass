# Looking Glass - Project Handover

This index replaces the previous monolithic handover. Its complete text is
preserved, in original order, in the linked files below. Read the introduction
and authority/workflow sections before preparing repository changes.

Historical candidate and validation statements retain their original wording;
they are not new claims about the current implementation or test results.
No application code or test results are changed by this documentation split.

## Handover contents

- [Introduction](docs/handover/001-introduction.md)
- [Purpose and authority](docs/handover/002-purpose-and-authority.md)
- [Repository and agreed working branch](docs/handover/003-repository-and-agreed-working-branch.md)
- [Project purpose](docs/handover/004-project-purpose.md)
- [Current live README highlights](docs/handover/005-current-live-readme-highlights.md)
- [Architecture orientation](docs/handover/006-architecture-orientation.md)
- [Resume locally](docs/handover/007-resume-locally.md)
- [Data protection and recovery](docs/handover/008-data-protection-and-recovery.md)
- [Assistant workflow and user preferences](docs/handover/009-assistant-workflow-and-user-preferences.md)
- [Status at preparation](docs/handover/010-status-at-preparation.md)
- [Suggested first message in a replacement assistant session](docs/handover/011-suggested-first-message-in-a-replacement-assistant-session.md)
- [Bug-hunt backlog and one-at-a-time workflow (2026-10-28)](docs/handover/012-bug-hunt-backlog-and-one-at-a-time-workflow-2026-10-28.md)
- [Bug 1 implementation candidate: inward fog feathering (2026-10-28)](docs/handover/013-bug-1-implementation-candidate-inward-fog-feathering-2026-10-28.md)
- [Bug 3 implementation candidate: same-version viewer recovery (2026-10-29)](docs/handover/014-bug-3-implementation-candidate-same-version-viewer-recovery-2026-.md)
- [Bug 4 corrected archive candidate (2026-10-29)](docs/handover/015-bug-4-corrected-archive-candidate-2026-10-29.md)
- [Bug 5 implementation candidate: viewer socket session lifetime (2026-10-29)](docs/handover/016-bug-5-implementation-candidate-viewer-socket-session-lifetime-202.md)
- [Bug 6 implementation candidate: role-change socket revocation (2026-10-29)](docs/handover/017-bug-6-implementation-candidate-role-change-socket-revocation-2026.md)
- [Bug 7 implementation candidate: forced-password-change viewer gate (2026-10-29)](docs/handover/018-bug-7-implementation-candidate-forced-password-change-viewer-gate.md)
- [Bug 8 implementation candidate: atomic account form validation (2026-10-29)](docs/handover/019-bug-8-implementation-candidate-atomic-account-form-validation-202.md)
- [Bug 9 candidate: bounded login-throttle retention (2026-10-29)](docs/handover/020-bug-9-candidate-bounded-login-throttle-retention-2026-29.md)
- [Bug 10 implementation candidate: ordered NeDB deletion replay (2026-10-29)](docs/handover/021-bug-10-implementation-candidate-ordered-nedb-deletion-replay-2026.md)
- [Bug 11 implementation candidate: finite numeric imports and target transforms (2026-10-29)](docs/handover/022-bug-11-implementation-candidate-finite-numeric-imports-and-target.md)
- [Bug 11 delivery completed; acceptance pending (2026-10-29)](docs/handover/023-bug-11-delivery-completed-acceptance-pending-2026-10-29.md)
- [GitHub Actions integration setup (2026-10-29)](docs/handover/024-github-actions-integration-setup-2026-10-29.md)
- [CI fix 1: live login URL predicate (2026-10-29)](docs/handover/025-ci-live-login-url-fix-2026-10-29.md)
- [Bug 12: malformed import normalization (2026-10-29)](docs/handover/026-bug-12-malformed-import-normalization-2026-10-29.md)

- [Lossless TODO split (2026-10-30)](docs/handover/027-lossless-todo-split-2026-10-30.md)

## Preservation and verification

The ordered source files, byte counts and SHA-256 hashes are recorded in
[the split manifest](docs/handover/manifest.json). Concatenating its `files`
entries in order reconstructs the exact original UTF-8 file, including its
line endings and final newline state. The index is navigational material
and is not part of that reconstruction.

Original relative links and fragment links are preserved verbatim. Moving
text can change their meaning: review links relative to the old repository
root and external links to `HANDOVER.md#...` after applying the split.
Oversized sections may be continued across files, including code fences or
long lines; consult adjacent parts if a standalone fragment renders poorly.

## CI evidence collector (2026-10-30)

`bash getworkflow.sh [RUN_ID] [--publish]` collects the latest completed
integration workflow run, or an explicit run, from `features/perplexity`.
It preserves metadata, tested SHA, attempt-specific logs, run-scoped artifacts,
download diagnostics and a collection report in a new run/attempt directory.
Missing logs/artifacts are recorded as warnings, not proof of successful tests.
Default operation is local collection only. Publishing requires a clean,
up-to-date working branch, the expected origin push URL and typed confirmation;
only the evidence directory is staged. Evidence commits use `[skip ci]` to
avoid push-triggered runs; skipped required checks can affect PR merge gates.
Review evidence for secrets before publishing. Failed pushes leave the local
commit intact; there is no automatic rebase or force-push. Alternate origin URL
forms are rejected conservatively. Artifact downloads are not attempt-filtered;
verify contained environment SHAs and provenance after reruns. Existing output
directories are never overwritten. Runtime, GitHub CLI integration and shell
syntax validation have not been executed by the assistant for this change.
README.md was reviewed; its existing CI overview remains accurate and unchanged.

## Bounded CI evidence reading copies (2026-10-30)

The collector now requires Python 3 and invokes `tools/chunk_ci_evidence.py`
before publishing. Original evidence is unchanged. A separate `reader-chunks/`
contains copies in parts of at most 4,000 bytes, an ordered paginated index,
per-source metadata and SHA-256 checksums for originals and parts. UTF-8 code
points are preserved; long lines and XML elements may span parts. Binary or
non-UTF-8 inputs use base64, decoded after concatenating their parts. Concatenate
parts without inserting newlines. Metadata and all reading-copy files are
bounded; oversized metadata fails explicitly. The exact connector threshold is
unknown, so this size is conservative rather than a guaranteed connector limit.
The helper verifies reconstruction against originals before exposing the reading
copy, and the collector verifies it again before staging. Files are read into
memory, so this is intended for CI evidence rather than arbitrarily large data.
Do not modify source evidence after chunking. Existing reading copies are not
overwritten. No existing published evidence is automatically rewritten.

For the already published run, execute:

```bash
python3 tools/chunk_ci_evidence.py ci-results-41011195909-attempt-1
python3 tools/chunk_ci_evidence.py --verify ci-results-41011195909-attempt-1
```

Review and publish only the generated reading copy on `features/perplexity`:

```bash
git add -- ci-results-41011195909-attempt-1/reader-chunks
git commit -m "Add readable chunks for CI run 41011195909 [skip ci]"
git push origin HEAD:refs/heads/features/perplexity
```

The existing run collector still refuses to reuse an output directory; use the
helper directly for already collected runs. No helper tests, shell syntax checks
or live GitHub integration tests were executed by the assistant for this change.
README.md was reviewed; its existing workflow overview remains accurate.

## Ordered fog snapshot initialization (2026-10-30)

CI run 41011195909 against fe357602aa918ecc7dfa25b02178fd9775a237d9
reported reversed snapshot operation order during a version-2 upgrade.
Historical migration SQL and schema version count remain unchanged. The runner
now delegates pending migrations to `migration_hooks.apply_migration`. Only
while applying version 3, it leaves the script transaction open, initializes
its newly created snapshots from `fog_ops ORDER BY map_id,id` using Python JSON,
and records version 3 before committing. Any failure rolls back this migration's
schema, snapshot data and version record. Other migration execution is unchanged.
This avoids dependence on aggregate ORDER BY syntax or JSON subtype behavior.
Maps with no history still have no snapshot. Raw history and cache-token behavior
are retained. The hook only runs for a pending version 3; already migrated
snapshots are not rebuilt, including ones that differ from offline edit history.
No automatic repair of previously misordered snapshots is attempted: recovering
those requires an explicit, backed-up decision rather than overwriting saved
last-displayed state from potentially different current history.

Seven isolated candidate-hook SQLite checks passed in the assistant environment
(Python 3.12.8, SQLite 3.46.1): ordering/coordinates across interleaved maps,
empty maps, committed version, initialization rollback/retry, version-insert
rollback, later-migration preservation, and in-transaction hook execution.
These used a focused schema and migration-3 fixture, not the full checkout.
New repository tests in `python/tests/test_fog_snapshot_migration.py` cover real
migration integration, idempotency, saved-state preservation and rollback.
Those tests, the existing `test_map_display.py` suite and full Python/live suites
have not been executed by the assistant; Python 3.14 CI acceptance is pending.
The original migration regression is unchanged. The separate Scrying Glass asset
token assertion failure is out of scope and remains unresolved.
README.md was reviewed; existing upgrade/backup and test guidance stays accurate.

## Scrying Glass template assertion alignment (2026-10-30)

The remaining failure in CI run 41014231894 against
`e13c1e7fbe220dad53391d8122a7cb409e037584` was the stale
`scrying-auto-2` assertion. The live admin map template references both
Scrying Glass assets with `scrying-prefix-3`. The test now checks the exact CSS
href and JavaScript src rather than searching for an obsolete generic token.
Script ordering, removed manual-check control, status markup, admin-only router
registration, viewer exclusion, CSRF and ownership assertions are unchanged.
No application template, script, stylesheet or runtime behavior changes.
Future intentional asset-version bumps must update these explicit expectations.
The live README and HANDOVER were reviewed; README needs no change for this
test-only correction. Tests have not been executed by the assistant for this
change; CI must validate both tests and assertions beyond the previous failure.
Historical validation statements above describe their preparation-time status;
subsequent reviewed CI run 41014231894 passed the original migration regression
and all five new migration tests, with four live tests passing. That prior run
does not establish that this new template assertion change passes.

## Copyable CI evidence handoff (2026-10-30)

After a successful `getworkflow.sh --publish` push, the script prints the
user-requested message with the selected run's databaseId, its tested headSha,
and the current evidence commit SHA from `git rev-parse HEAD`. The output has a
blank line between the run/tested-commit sentence and current-commit sentence.
It is terminal output only: no self-referential commit hash is written into the
evidence. Local-only collection, cancelled publication and failed pushes do not
print this published-evidence handoff. Existing collection and publishing logic
is unchanged. README.md was reviewed; its workflow overview remains accurate.
No script execution, shell syntax check or live publication test was performed
by the assistant for this output-only change.

## Four-suite automated workflow (2026-10-30)

The existing integration workflow now includes Python / HTTP, JavaScript
regressions, Browser / mocked HTTP and Live Uvicorn as independent matrix jobs.
The existing two check names are retained. All jobs use Python 3.14, and the
JavaScript job additionally configures Node.js 24. Browser/live jobs install
Playwright Chromium with system dependencies and require the existing bounded
browser environment check. Strict nonempty/no-failure/no-reported-skip JUnit
validation and always-uploaded per-suite artifacts remain enabled. Evidence
identity is initialized before dependency installation. No branch protection
settings were changed: administrators must require all four checks separately.

The new `tools/run_javascript_tests.py` discovers every top-level test_*.js,
continues after script failure, logs each script, records status/duration inventory
and emits one JUnit case per script. It fails on empty discovery, missing Node,
nonzero exits or a default 120-second per-script timeout. Nested Node case/skip
semantics are not parsed; script exit status is the contract. Existing tests
and local JavaScript loop are unchanged. A small pytest adapter includes the
existing standalone upload-busy Chromium check in browser discovery without
changing its assertions; local browser-suite execution also discovers it.

The live getworkflow.sh was reviewed and left unchanged: it already downloads
all artifacts for the selected run and prepares reading chunks for all files.
No extra evidence upload/download action, new archive or runtime change is needed.
README's CI overview now links to `docs/ci-tests.md`, the current four-suite
contract. That focused guide supersedes old CI-specific descriptions in the
oversized docs/testing.md while leaving historical/general/manual content intact.
Discovery covers existing automated groups, not arbitrary future standalone
filenames, manual acceptance, other operating systems or other browser engines.

Validation performed locally: workflow YAML parsing/matrix structure checks and
five isolated JavaScript-runner smoke scenarios (success, continuation after
failure, timeout, empty discovery, missing executable). Runner fixtures used
Python as the stand-in subprocess, not Node or project JavaScript tests.
No full checkout test run, actual Node suite, Chromium test, hosted Actions run,
or actionlint validation was performed. First four-suite CI acceptance is pending.
The prior two-suite run 41014901375 against 977f65a390586e8b7262380e0ba3acd678cb4bf4
was reviewed as successful (1,125 Python tests, 29 subtests, four live tests);
that result does not establish the newly included suites pass.

## Replace prior CI collections (2026-10-30)

The collector now cleans prior root collection directories before downloading a
new run, after validating run metadata and refusing an existing new output path.
Names must exactly match `ci-results-<digits>` or the attempt-suffixed form.
Every invocation requires a clean working tree/index on features/perplexity;
publishing additionally retains the up-to-date-origin safeguards. The script
lists exact cleanup targets and starting HEAD and requires typing `remove`.
Symlink/non-directory matches and ignored files inside a collection block
cleanup. A second safety check runs after confirmation. Unrelated names and
noncollection files are not cleanup targets. The removed directory list is
recorded in the new collection report before reader chunks are generated.

Local-only collection leaves old tracked deletions unstaged and does not change
GitHub. With --publish, a separate publish prompt explicitly includes prior
removals; a guard permits only those expected tracked deletions before staging.
`git add -A` is limited to the new evidence path and the listed old paths, so
old tracked files are deleted in the same commit that adds the new collection.
The existing copyable run/tested-SHA/current-SHA handoff remains unchanged.
No force push, history rewrite, Actions artifact removal or automatic rollback
is performed. Failure/cancellation after cleanup leaves local deletions for
review; recover tracked old contents from the printed starting commit as needed.
A partial run is dirty and must be reviewed before retrying. Current-branch
cleanup does not shrink historical Git storage or erase old evidence commits.

Five isolated temporary-Git scenarios passed: clean matching removal plus staged
and committed deletion/history recovery, dirty-tree refusal, symlink refusal,
ignored-file refusal and no matching collections; nonmatching similarly named
data was preserved. These checks exercised the cleanup/staging logic rather
than the complete collector. Full collector execution, network download,
chunking integration, interactive prompts and remote publishing were not tested
by the assistant. README.md was reviewed and remains accurate; docs/ci-tests.md
now documents retention, destructive prompts, local-only effects and recovery.
This implementation commit itself removes no existing evidence files; deletion
occurs only when the updated script is run and its cleanup is confirmed.

## Upload-busy adapter process isolation (2026-10-30)

The first expanded run 41016747640 against
`45b477a85f717aaea1d396ac7e7f29a7d0e9bf39` passed 1,125 Python tests plus
29 subtests, all 27 JavaScript scripts and four live tests. Browser results were
161 passed and one failure: the new adapter called asyncio.run while the parent
browser-test thread already had an active event loop. The unawaited-coroutine
warning followed that invocation failure; upload-busy assertions were not run.

`python/tests/browser/test_upload_busy.py` now invokes the unchanged standalone
check with the current Python executable in a separate process, using the
repository root as cwd. It captures stdout/stderr, reports both on nonzero exit,
and enforces a 120-second subprocess timeout. Timeouts propagate as test errors,
not skips or passes. The child owns its async Playwright/event-loop lifecycle
without importing or starting another asyncio loop in the parent test thread.
No application code, standalone regression assertions, workflow or collector
changes are needed. README.md was reviewed; its CI overview remains accurate.

Focused validation on Python 3.12.8 passed: a real subprocess using asyncio.run
completed while the parent's event loop was active; a real nonzero child exposed
both stdout/stderr in the assertion; a mocked TimeoutExpired propagated as an
error. Temporary stand-in scripts were used, not Chromium or the actual upload
check. Full browser/Python/JavaScript/live suites and Python 3.14 CI were not run
by the assistant for this correction. A new CI run is required for acceptance.

## Reliability batch 1 and fifth Recovery check (2026-10-30)

Added 14 regression cases: nine CI-evidence chunking cases in Python / HTTP,
three live reconnect/tab/session cases, and two real CLI subprocess restart
cases in a new Recovery matrix job. The workflow excludes recovery from the
Python job to avoid duplicate CI execution. Existing check names and strict
JUnit audit/artifact retention remain; the fifth artifact is integration-recovery.
The collector already handles every artifact for a run and needs no modification.

Recovery uses explicit temporary configuration/data, sanitized LG_* environment,
test-only credentials, ephemeral loopback ports and bounded startup/shutdown.
Normal restart and forced termination after committed requests must preserve
existing viewer access, active map version, saved fog snapshot and fogged image
pixels; both listeners, integrity/foreign-key checks and anonymous refusal are
checked. This is not an in-flight write interruption or power-failure guarantee.
Port reservation is released for the CLI listener, so a race fails startup.
Child-server logs are retained under test-results/recovery, not temporary DBs.

Live additions cover offline reconnect after a missed reveal and continued hide/
undo delivery when one of two tabs closes, both with a shared session and with
independent sessions for the same account. The new secondary context has page
error reporting but no separate trace capture. Distinct-account permissions,
revocation and delayed responses remain separate follow-up scenarios.

The live job now uses a dedicated ci-live-tmp basetemp and always copies existing
fixture traces, DM/player screenshots and page-errors.json into uploaded
 test-results/live-diagnostics paths while preserving test-relative locations.
No fixture or runtime application code changes are needed. Binary trace copies
remain available through the collector's lossless base64 chunk format.

Chunk tests cover Unicode/CRLF, single-line XML, binary/empty files, exact
reconstruction and size bounds, altered/missing parts, changed originals,
no-overwrite and complete paginated inventory. They use only temporary data.
The three new Python modules passed local syntax parsing; no full checkout,
actual application process, Chromium, hosted workflow or actionlint run was
performed by the assistant for this batch. All new-case execution remains pending
CI. The prior four-suite run 41017872020 was reviewed green at e6f932b688682328177dc7ef0063400bb75514be;
that result does not establish this first five-suite batch passes.

Explicit remaining backlog: built-container startup/health/volume persistence;
controlled interruption during migration, restore and duplication; disk-full,
permission and locking fault injection; bounded Hypothesis state-machine checks;
live delayed-response, revocation and checkpoint/backup-restore propagation;
committed collector-cleanup and JavaScript-runner harness regressions. These
were proposed but are not implemented in batch 1. README and docs/ci-tests.md
now document five-suite scope, commands, evidence and these limitations.

## Reduced-motion portal test synchronization (2026-10-30)

Run 41019420067 against 5f33869a133c4a601e9d66e9f3e84c2e93d1366f
passed all 14 new reliability cases (1,134 Python tests plus 29 subtests,
27 JavaScript scripts, seven live cases, two recovery cases) but the browser
suite reported 161 passed and one failure in the existing reduced-motion portal
style check. That test sampled computed CSS immediately after media emulation;
the assertion did not record which actual property differed. A synchronization
race is plausible, not a proven product defect or a proven harmless flake.

Only `test_admin_reduced_motion_is_bright_and_steady` changes: wait up to five
seconds for matchMedia to report reduced motion, require exactly two polygons,
then use Playwright locator CSS assertions on each polygon to wait for exact
animation-name none, yellow fill, black stroke and full opacity. The original
expected values and no-posts check are retained. Assertion diagnostics now
identify the property and observed CSS value. No fixed sleeps, whole-test
retries, skips, looser colors, stylesheet or runtime changes were introduced.
Other tests in the file are unchanged. README.md was reviewed and its CI overview
remains accurate. Workflow and getworkflow.sh need no changes.

The browser test and full suites were not executed by the assistant for this
correction; a new CI run must establish whether bounded CSS synchronization
resolves the intermittent failure. A persistent style mismatch must still fail
and be investigated using the richer assertion diagnostics.

## Reliability batch 2 increment 1: container deployment (2026-10-30)

The first batch-2 increment adds two Docker-backed tests inside Recovery, not a
sixth check. CI explicitly sets LG_RUN_CONTAINER_TESTS=1 for the Recovery pytest
step. That same invocation reports both existing CLI cases and new container
cases in one JUnit file, so the common strict audit covers all of them. Local
container cases are opt-in and skipped otherwise; missing Docker after opting
in fails setup rather than skipping. Full local Recovery equivalence requires
the flag and a disposable Docker daemon/context with local bind-mount support.

The real Containerfile is built once per test session. Unique test-owned image,
container and named-volume names scope creation/removal; no shared-resource prune
is used. The first case checks non-root PID 1 uid 1001, both listener health
responses, both login templates and CSS/JS serving. The second seeds synthetic
accounts through non-root application code, creates campaign/map/walls/viewer
assignment/reveal via HTTP, validates exact revealed/hidden PNG pixels, then
stops/removes the first container and starts a new one with the same named volume.
The existing viewer cookie and map display version must still work; anonymous
access remains denied. Each case has isolated volume data and bounded clean
shutdown (zero exit required). A read-only temporary config provides small PNG
rendering; it invokes the real CLI with explicit config rather than testing the
default image CMD verbatim. Containerfile and runtime application are unchanged.

Docker version/build/command/inspect output and application logs are written
under test-results/container-build and test-results/container. Inspect logs have
synthetic test credentials only; review before publishing. getworkflow.sh already
collects every artifact and requires no update. Cleanup finalizers may not finish
if a workflow is forcibly cancelled or a daemon is unresponsive; manual cleanup
must target only the uniquely recorded resources. Image removal is best effort;
volume removal is checked. Docker-client timeouts do not guarantee daemon build
cancellation. This is Linux Docker coverage, not Podman/SELinux deployment proof.

Validation performed: new module passed Python syntax parsing; a synthetic Docker
port-binding structure produced the expected loopback URLs. No Docker engine,
image build, running container, actual deployment HTTP or full suite execution
was performed by the assistant. Acceptance of these two new cases is pending CI.
The preceding five-suite run 41020692166 at 6315be869139ee17536222795f4ae07e3d014c44
was reviewed green; that does not validate this increment.

Batch 2 remains incomplete: controlled migration interruption, file/database
failure injection and live access revocation are still planned next. Later
property/state-machine, delayed-response/restore and collector/runner harness
work also remains. README and docs/ci-tests.md now reflect the container scope,
local opt-in command, cleanup/evidence rules and validation limits.
