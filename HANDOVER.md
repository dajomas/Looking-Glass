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
- [Bug 10 implementation candidate: ordered NeDB deletion replay (2026-10-29)](docs/handover/021-bug-10-nedb-imports-resurrect-deleted-walls-scenes.md)
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

## Reliability batch 2 increment 2: migration interruption (2026-10-30)

Added `python/tests/recovery/test_migration_interruption.py` with two cases at
known migration-3 boundaries: before ordered initialization, and after it but
before version recording/commit. Only a temporary child process monkeypatches
the existing initialization hook. It asserts an active transaction and recorded
version 2, atomically writes a phase/PID/snapshot handshake, then blocks on its
private stdin pipe. The parent validates the handshake and independent-reader
visibility before killing precisely that child. Random sleeps do not select the
interruption boundary; polling merely waits for the explicit barrier marker.

The fixture uses actual migration 1/2 scripts and committed synthetic data only.
After the child is killed, version, schema and every legacy table's data must
match the committed baseline; integrity and foreign keys must pass. A fresh
unmodified child retries all pending migrations. It must preserve legacy column
values, reach the current version and create correctly ordered per-map snapshots
without an empty-map snapshot. Repeated migration must preserve tokens and full
snapshot rows. Handshake/kill/retry waits are bounded, and child cleanup runs on
failures. Logs, marker and success summary are written to
 test-results/migration-interruption/<phase> for existing artifact collection.
Temporary database files/configuration are not uploaded or taken from real data.

No workflow or collector edits are necessary: Recovery already discovers these
files and uploads all test-results. Production migration SQL, hooks and runtime
behaviour remain unchanged. README was reviewed and left unchanged: these two
selected process-kill boundaries do not introduce a general in-flight crash,
power-loss or cross-filesystem atomicity guarantee. Detailed scope and a focused
local command are in docs/ci-tests.md.

Preparation validation: new module parsed successfully and two isolated synthetic
SQLite child-process handshake/kill/rollback/retry experiments passed on Python
3.12.8 / SQLite 3.46.1. Those experiments tested the process/barrier method, not
the full application migration scripts. The new repository cases/full suites and
Python 3.14 CI were not executed by the assistant; CI acceptance remains pending.
Increment 1 was subsequently reviewed green in run 41022509451 at
9397eaf499235c98cad271b5e4b9e91f67e3714a, with four Recovery cases including
both Docker tests. That prior result does not validate increment 2.

Remaining batch-2 work: permission/disk/locking fault injection and live access
revocation. Broader migration-statement coverage, restore/duplication interruption,
property-based state machines, delayed-response/restore propagation and collector/
runner harnesses remain follow-up work. These tests do not simulate power loss
or prove atomicity across database and image files.

## Reliability batch 2 increment 3: storage-failure safety (2026-10-30)

Added 11 top-level Python / HTTP cases: eight service cases (two image-write
faults, collision preservation, four recovery-ZIP write/durability faults, real
SQLite contention/retry) and three HTTP recovery-gate failures (EACCES, ENOSPC,
EIO). They compare prior bytes and committed rows, require the injected boundary
to be reached, reject premature live restoration/success notification, and test
successful retry after service-level faults/locking are removed. Test-local
faults avoid actual disk exhaustion or permission changes. The directory-fsync
case targets Linux CI, not Windows. Existing workflow discovery and artifact
collection already include all cases; no workflow/getworkflow.sh changes needed.

A focused image experiment reproduced a real defect in the live store helper:
partial PNG bytes remained when encoding raised ENOSPC. The helper now creates
its destination exclusively, then closes and attempts unlink on encoding/close
failure. A preexisting UUID collision raises without overwriting or deleting its
file. Cleanup failures log a warning while retaining the original exception.
This is the only runtime code change, limited to images.py. It is best effort,
not crash-safe/atomic/fsync-backed publication; empty directories can remain.
Existing storage exception types/HTTP upload error mapping are not redesigned.

The HTTP cases prepare valid preview tokens, distinguish inspection-clone work
from live-database replacement and verify an error redirect with no changes to
any main DB rows/map files/recovery files and no awaited success notification.
The SQLite case uses a real competing write lock and a short busy timeout only
on the contender connection, then verifies retry after release. These are not
real-browser delivery or broad concurrent-load tests; those remain separate.

Validation: the live images.py blob matched 243817c79253daa7cb478f20f2630ec86cb5ce5e
before modification. The original partial-file leak was reproduced. Candidate
partial-write cleanup, denied-open preservation, collision preservation, valid
image retry and actual SQLite contention/retry checks passed on Python 3.12.8 /
SQLite 3.46.1. Candidate source/new test modules parsed. Full repository pytest,
HTTP/recovery-backup checks and Python 3.14 CI were not executed for this change;
CI acceptance is pending. Prior increment 2 was reviewed green in run 41025509410
at 183a4787001597095a4ba26303ca57b04557b3ed; that does not validate this increment.

Explicit remaining gap: upload/replace can fail at a database boundary after a
fully successful image store; post-store transaction/orphan cleanup is not
covered or fixed here. Sudden termination, unlink failure, genuine exhausted
filesystems and other operating systems also remain outside these guarantees.
Increment 4 (live access revocation), broader property/race/fault coverage and
collector/runner regressions remain follow-up work. README was reviewed and its
high-level scope stays unchanged; docs/ci-tests.md documents the precise cases,
minimal image fix, local command and limits.

## Live revocation delivery and reviewed CI (2026-10-30)

Increment 4 was delivered at ac8a77f5396531e6cf7a7b1db48ec39baf848344.
It adds four real Chromium/live-server cases for shared-session logout, campaign
assignment removal, deactivation and role change. Affected sockets must close
4403; independent old-cookie state/image requests must receive 401 or 404, while
an unaffected session/account receives pixel-verified hide/undo updates. Extra
synthetic accounts preserve existing fixture IDs, and extra revocation contexts
collect errors/failure traces/screenshots plus token-free status observations.
No runtime authorization, workflow or collector changes were made. The original
approved write omitted HANDOVER despite its summary; this section records that
previously missing handover rather than claiming it was included at delivery.

Run 41029015169 tested that implementation commit; evidence was reviewed at
97e5a628f136b2ff1102f074009bbc6f530f0c3c. All 11 live cases, including the four new
revocation cases, passed. Python / HTTP, JavaScript and Recovery jobs were green;
Browser / mocked HTTP reported 161 passed and one wall-width NaN failure. This
validates the specified live scenarios, not the whole workflow, idle/multi-worker
revocation or every race. Previously delivered pixels cannot be recalled and no
new blank-screen product requirement was introduced. The post-image-store DB
failure/orphan gap and broader backlog remain open. Earlier preparation-time
pending statements above are historical and do not override these reviewed results.

## Wall-width browser measurement race correction (2026-10-30)

The failure in run 41029015169 occurred at the first four-pixel assertion in
`test_wall_width_is_screen_constant_and_survives_reload`, before zoom/reload.
The editor replaces wall paths using svg.innerHTML on state refresh, including
its scheduled post-artwork startup refresh. Chromium 134.0.6998.35 experiments
showed that an old detached path returns empty computed strokeWidth and CTM.a=1,
so parseFloat produces NaN despite a valid four-pixel replacement. Under rapid
path replacement, 150 locator-based samples returned NaN and 150 same-turn DOM
query/measurement samples did not. This establishes a reproducible failure
mechanism, not retrospective proof of the original CI sample's connectivity.

The test now queries the current path and measures CSS/CTM in one JavaScript
execution, using bounded five-second polling with the unchanged four-pixel
+/-0.01 tolerance at initial, zoomed and reloaded checkpoints. Missing paths,
nonfinite measurements and invalid scale cannot pass. Timeout diagnostics include
connectivity, raw CSS stroke width, CTM scale, calculated width and slider value.
Preference persistence and no-POST/page-error assertions remain; those checks
also run after reload. No application rendering code, fixed sleeps, test-level
retries, skips, tolerance relaxation, workflow or collector changes are included.
README.md was reviewed and remains accurate; no cosmetic README edit is needed.

The candidate helper passed actual Chromium 134 focused checks: static four-pixel
measurement, 100 samples during repeated SVG replacement, rejection of a 4.02px
stroke and rejection of a missing path with useful diagnostics. Helper syntax
parsed. These checks used a minimal SVG fixture, not the full checkout/editor.
The full modified repository browser test/suites and Python 3.14 CI have not been
executed by the assistant for this candidate; new CI acceptance remains required.

## Reliability batch 3 increment 1: JavaScript runner harness (2026-10-30)

Added `python/tests/test_javascript_runner.py` with nine cases (eight functions,
including two nonpositive-timeout parameters). Each invokes the actual runner CLI
in a separate subprocess. Synthetic Python scripts use .js names and the current
Python executable is supplied through --node, so this tests orchestration without
requiring Node or pretending to validate JavaScript language/runtime behaviour.
All inputs and reports use temporary directories, including paths with spaces;
runner child cwd must still be the repository root. No real project JS scripts,
accounts, application config, database or existing evidence are modified.

Cases cover sorted top-level discovery and exclusion, stdout/stderr capture,
nonzero exit with continuation, timeout with retained partial output/continuation,
missing executable across multiple scripts, failing empty discovery, zero and
negative timeout rejection, and XML special-character round trips. Shared report
checks compare JUnit counts/failures and inventory exit codes, case identity,
finite nonnegative durations and log paths. A timed-out case must be 124, missing
execution 127, and argument rejection 2. An outer 20-second timeout bounds each
runner subprocess; the slow fixture sleeps without spawning descendants.

The unchanged live runner blob was verified as
b21ab142dbf545cfb370b5aa7db1ea90d8026d78. All nine tests passed in 1.52 seconds in
an isolated temporary repository layout using that exact runner and candidate
module. This executed real subprocess/timeouts and XML/TSV parsing, not mocked
subprocess returns. It did not load the real checkout's conftest or run the full
application suites, Node scripts or Python 3.14 CI. Hosted acceptance remains
pending, as does any unreviewed CI acceptance of the preceding wall-width fix.

README.md was reviewed and left unchanged; its test overview and the CI guide's
runner invocation remain valid. This module docstring provides the focused local
command: python -m pytest -q python/tests/test_javascript_runner.py. Existing
Python / HTTP top-level discovery includes the new module; workflow, collector,
runner implementation and requirements are unchanged. Nested Node skip semantics,
process-tree cancellation, arbitrary/nonfinite timeout values, damaged-output/
permission failures and unusual tab/newline filenames are not newly covered.
Collector cleanup/publication harnesses and broader property/live/fault coverage
remain separate backlog items; this does not mark all tooling work complete.

## Reliability batch 3 increment 2: delayed viewer responses (2026-10-30)

The user subsequently ran the committed JavaScript-runner module in their real
checkout with .venv-test: nine cases passed in 3.41 seconds. This adds local
checkout validation, not a reviewed full-CI result. The user then excluded further
collector harness work from workflow testing and requested application tests.
No collector tests, prompt changes or collector documentation changes are part
of this increment.

Added seven cases in `python/tests/browser/test_viewer_delayed_responses.py`:
old state headers, old JSON consumption, late images after a same-map update,
a map switch or a blank scene, readiness while the current image is delayed,
and failed delayed-image retry without changing the requested version or reloading.
The standalone page loads the real viewer_display.js, pan_zoom.js and
viewer_area_zoom.js. Route-held HTTP payloads and a test WebSocket driver select
response order. Native fetch/body parsing/image requests/decoding remain in
Chromium; test wrappers only gate JSON delivery or record completion/status.
Synthetic PNG fixtures contain an exact colored left region and black right
region, not server-rendered fog or real campaign artwork.

Bounded waits synchronize startup and barriers. Post-release completion markers
allow stale continuations to run before assertions. Tests check installed image
URLs, map titles, stage/waiting visibility, image pixel samples and emitted ready
versions, including blank. The loading case rejects premature readiness; the
failure case requires Display failed followed by recovery without page reload.
Unexpected HTTP writes/requests and uncaught page errors fail the fixture.
Pending HTTP routes are aborted during teardown and each browser context closes.
There are no fixed sleeps used to select a race, runtime viewer changes, new
requirements, workflow or collector changes. Existing Browser / mocked HTTP
suite discovery includes the module, not the Live Uvicorn job.

Validation remains intentionally limited: the draft passed Python syntax parsing,
and the live browser fixture was reviewed for integration. None of these seven
Chromium cases, the full browser/application suites or hosted Python 3.14 CI has
been executed by the assistant. This is a test candidate requiring execution and
possible harness corrections, not a passing-run claim. No new runtime defect is
asserted from an unexecuted draft. Prior test results do not validate these cases.
README.md was reviewed and remains accurate; the focused command is
python -m pytest -q python/tests/browser/test_viewer_delayed_responses.py.

Coverage is client-side response ordering/readiness with synthetic HTTP/WS input,
not live-server delivery, server authorization, actual fog generation, all timing
races or a mutation-sensitivity proof. Live delayed-response and restore/checkpoint
propagation, post-image-store transaction cleanup, controlled restore/duplication
interruption and broader property/security/fault coverage remain separate work.

## Portal phase helper and reviewed delayed-response CI (2026-10-30)

Run 41036469578 tested 33ccdbc4ed3b9c141ab7799fc53231ca0bd831fa; evidence was
reviewed at 101b7c83a177f1e0ad52afa935712727ad0a27ab. All seven delayed-response
viewer cases and the corrected wall-width test passed. Browser results were
168 passed and one failure in test_admin_highlight_phases_have_distinct_color_and_outline;
Python / HTTP, JavaScript, Live Uvicorn and Recovery jobs were green. Earlier
preparation-time pending statements above are historical. This run validates the
new client-side cases, but not the full workflow or unimplemented live scenarios.

The failing phase helper returned two polygons at 100 ms and none at 800 ms.
portal_cycle.render replaces overlay children, and readiness/busy changes clear
its route until arrows are ready. The admin fixture can yield before its scheduled
startup refresh finishes. This supplies a credible redraw window, not proof of
the precise original CI event sequence or a harmlessness guarantee.

The test-only helper now waits up to five seconds for two connected polygons,
a route ID, nonbusy rendering, decoded arrows and native portal animations. It
pauses/seeks and samples current nodes in one browser execution. Timeout diagnostics
record route, polygon count, status, busy flag and animation names. The phase API
still returns styles and all existing exact yellow/black, blue/white, opacity,
width and vector-effect assertions remain. No application JS/CSS is changed.

Screenshot sampling records polygon identities, route, mask and the current
triangle centroid/transform, then accepts a capture only if those identities and
paused animation time remain valid afterwards. A redraw invalidates that capture
and causes bounded resampling; incorrect colors do not trigger recapture and still
fail immediately against the unchanged +/-3 per-channel tolerance. Deriving the
interior point from the current polygon avoids obsolete route coordinates; the
original route rounds to the same point. Normal masking, pointer-event and no-POST
assertions remain. No fixed sleeps, whole-test retries, skips or color relaxation.

Focused actual Chromium 134.0.6998.35 validation passed: both native CSS phase
colors, recovery after an explicitly scheduled empty-overlay/redraw, one injected
replacement during screenshot capture (exactly two captures), the exact blue
interior pixel, and rejection of missing polygons or missing animations with
diagnostics. Helper syntax parsed. This used a minimal SVG/CSS fixture, not the
full application/admin fixture. The full repository phase test, other suites and
Python 3.14 hosted CI have not been executed for the candidate; acceptance remains
pending. README was reviewed and remains accurate. Workflow, fixtures, collector,
requirements and stored CI evidence are unchanged; broader application-test backlog
remains open as recorded above.

## Reliability batch 3 increment 3: connected checkpoint restore (2026-10-30)

The user reported a green workflow after the portal helper correction; no new
run ID, tested SHA or passing counts were supplied for independent review.
Do not infer that the new checkpoint cases below were included in that run.

Added `python/tests/live_e2e/test_live_checkpoints.py` with three real-listener
Chromium cases: restoring same-map fog, restoring the saved active map and
campaign-wide exploration, and rejecting an incorrect campaign-name confirmation.
Helpers save checkpoints, discover their IDs from the real list page, obtain a
real compatibility preview token and submit authenticated CSRF-protected forms.
They explicitly distinguish ok and err redirect parameters. Save/preview must
leave authoritative viewer state unchanged; successful restore adds one automatic
safety checkpoint, while rejected confirmation preserves the checkpoint inventory.
No repository-level database writes or fake token/restore responses are used.

A test-only native WebSocket subclass records refresh notices and successfully
sent viewer-status reports without replacing transport. After one setup reload,
the document ID and exactly one open/no closes must persist through operations.
Successful restore requires a session-checkpoint notification, installed image
pixels, the authoritative image URL, a current ready report and monotonic display
version change. The same-map case compares restored bounds/region signatures;
the map-switch case also activates the other map to check that added exploration
was removed. Rejection preserves state/version/image and is followed by a real
hide/undo delivery check. These reports prove client emission, not manager-side
acknowledgment; the tests do not claim to inspect the entire synchronization panel.

The existing isolated live fixture supplies synthetic users, maps, temporary data
and both real listeners. Shared fixture page-error/failure-trace handling remains.
The tests perform no player navigation/reload after setup, intercept no responses,
and use bounded readiness/message waits rather than race-selecting sleeps.
The real routes, preview/list templates, checkpoint restore implementation, viewer
state format and stable revealed-region signatures were inspected during drafting.

Validation: Python syntax parsing passed for the three-case candidate. None of
the live cases, full application suites or hosted Python 3.14 CI was executed by
the assistant. Execution and possible harness corrections remain pending; this
is not a passing-run or runtime-defect claim. Existing Live Uvicorn discovery
collects this module with LG_RUN_LIVE_E2E=1; no workflow/requirements changes.
Focused command: LG_RUN_LIVE_E2E=1 python -m pytest -q python/tests/live_e2e/test_live_checkpoints.py.
README was reviewed and remains accurate. No runtime code, shared fixtures,
collector, stored evidence or other branch changes are included. Campaign ZIP
restore propagation, stale preview-token cases, multi-viewer restore, broad
runtime-state coverage, restore interruption and the remaining application backlog
are separate follow-up work.

## Reliability batch 3 increment 4: live campaign ZIP restore (2026-10-30)

The user ran the checkpoint module in .venv-test: three cases passed in 31.11s,
and reported a green GitHub workflow. This validates those local checkpoint
scenarios and supplies a user-confirmed workflow result; no independent run ID,
tested SHA or complete suite counts were supplied. It does not validate the new
ZIP cases below.

Added `python/tests/live_e2e/test_live_zip_restore.py` with four cases: an actual
campaign backup/restore/downloaded-recovery round trip and three rejected restores
(wrong campaign confirmation, different uploaded ZIP, stale target preview).
Authenticated exports and multipart inspection/restore use the actual application
routes. The success case changes the active map and revealed region, restores the
saved red-map scene, downloads the automatic pre-restore recovery ZIP, compares
its manifest/member contents to a pre-restore backup, then inspects and restores
that recovery ZIP to reinstall the changed green-map scene. It checks normal
hide/undo delivery afterward. Imported map IDs are rediscovered from current
exports rather than assumed to survive restore; new display tokens must replace
old installed image versions.

The module subclasses the existing Checkpoints observer/helper from
.test_live_checkpoints instead of duplicating native WS recording. It preserves
the player document, single native connection and existing viewer cookie; it
checks actual campaign refresh messages, current ready reports and installed
server-rendered image pixels/URLs. Successful real owner operations and continued
viewer access exercise the original authenticated identities, not a full account/
permission audit. Export and inspection must not change viewer state. Negative
cases preserve current viewer state, installed image and exported campaign member
content, observe no additional campaign-restore notice at the assertion boundary,
and prove subsequent fog/undo delivery still works.

ZIP checks verify CRCs, unique member names, expected format/version and absence
of account/session/assignment/checkpoint tables and campaign owner_id. Comparing
member bytes avoids timestamp/compression-container differences; it is not general
ZIP-bomb or malicious-archive coverage. Small synthetic archives stay in memory.
A standard HTMLParser extracts the real escaped preview token and recovery link;
no fake tokens, direct database writes, HTTP interception or synthetic WS transport.
Rejection checks do not inventory the recovery directory or every private database
row; existing storage-gate tests cover separate lower-level failure boundaries.

Candidate validation: Python syntax parsing and a focused escaped preview-token
HTML round trip passed. None of the four live cases, full suites or Python 3.14
hosted CI was executed by the assistant. Execution and possible harness corrections
remain pending; this candidate supplies no new runtime-defect or passing-run claim.
The existing isolated Live Uvicorn fixture and discovery collect these cases;
shared fixtures, workflow, requirements, collector and application are unchanged.
README was reviewed and remains accurate. Focused command:
LG_RUN_LIVE_E2E=1 python -m pytest -q python/tests/live_e2e/test_live_zip_restore.py.
Broader artwork/runtime-state/permission and multi-viewer restore, interruption,
fault injection, property-based coverage and the post-image-store transaction gap
remain follow-up work. No existing CI evidence or other branches are modified.
