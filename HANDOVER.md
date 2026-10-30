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
