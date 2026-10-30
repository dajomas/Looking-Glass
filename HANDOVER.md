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
- [Bug 9 candidate: bounded login-throttle retention (2026-10-29)](docs/handover/020-bug-9-candidate-bounded-login-throttle-retention-2026-10-29.md)
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


## Additional archived records (2026-10-30)

- [CI evidence collector (2026-10-30)](docs/handover/028-ci-evidence-collector-2026-10-30.md)
- [Bounded CI evidence reading copies (2026-10-30)](docs/handover/029-bounded-ci-evidence-reading-copies-2026-10-30.md)
- [Ordered fog snapshot initialization (2026-10-30)](docs/handover/030-ordered-fog-snapshot-initialization-2026-10-30.md)
- [Scrying Glass template assertion alignment (2026-10-30)](docs/handover/031-scrying-glass-template-assertion-alignment-2026-10-30.md)
- [Copyable CI evidence handoff (2026-10-30)](docs/handover/032-copyable-ci-evidence-handoff-2026-10-30.md)
- [Four-suite automated workflow (2026-10-30)](docs/handover/033-four-suite-automated-workflow-2026-10-30.md)
- [Replace prior CI collections (2026-10-30)](docs/handover/034-replace-prior-ci-collections-2026-10-30.md)
- [Upload-busy adapter process isolation (2026-10-30)](docs/handover/035-upload-busy-adapter-process-isolation-2026-10-30.md)
- [Reliability batch 1 and fifth Recovery check (2026-10-30)](docs/handover/036-reliability-batch-1-and-fifth-recovery-check-2026-10-30.md)
- [Reduced-motion portal test synchronization (2026-10-30)](docs/handover/037-reduced-motion-portal-test-synchronization-2026-10-30.md)
- [Reliability batch 2 increment 1: container deployment (2026-10-30)](docs/handover/038-reliability-batch-2-increment-1-container-deployment-2026-10-30.md)
- [Reliability batch 2 increment 2: migration interruption (2026-10-30)](docs/handover/039-reliability-batch-2-increment-2-migration-interruption-2026-10-30.md)
- [Reliability batch 2 increment 3: storage-failure safety (2026-10-30)](docs/handover/040-reliability-batch-2-increment-3-storage-failure-safety-2026-10-30.md)
- [Live revocation delivery and reviewed CI (2026-10-30)](docs/handover/041-live-revocation-delivery-and-reviewed-ci-2026-10-30.md)
- [Wall-width browser measurement race correction (2026-10-30)](docs/handover/042-wall-width-browser-measurement-race-correction-2026-10-30.md)
- [Reliability batch 3 increment 1: JavaScript runner harness (2026-10-30)](docs/handover/043-reliability-batch-3-increment-1-javascript-runner-harness-2026-10-30.md)
- [Reliability batch 3 increment 2: delayed viewer responses (2026-10-30)](docs/handover/044-reliability-batch-3-increment-2-delayed-viewer-responses-2026-10-30.md)
- [Portal phase helper and reviewed delayed-response CI (2026-10-30)](docs/handover/045-portal-phase-helper-and-reviewed-delayed-response-ci-2026-10-30.md)
- [Reliability batch 3 increment 3: connected checkpoint restore (2026-10-30)](docs/handover/046-reliability-batch-3-increment-3-connected-checkpoint-restore-2026-10-30.md)
- [Reliability batch 3 increment 4: live campaign ZIP restore (2026-10-30)](docs/handover/047-reliability-batch-3-increment-4-live-campaign-zip-restore-2026-10-30.md)
- [Regression-first image/database cleanup cases (2026-10-30)](docs/handover/048-regression-first-image-database-cleanup-cases-2026-10-30.md)

## Archive extraction and future updates (2026-10-30)

The 21 additional records above preserve the remaining dated sections verbatim,
in their original order. They are historical records, not new implementation or
validation claims. Keep future detailed decisions, delivery notes, validation
results, limitations and unfinished work in focused files under docs/handover/;
add only short descriptive links here. Do not append detailed history to this index.

The original manifest.json remains unchanged and covers only its original split.
[The additional extraction manifest](docs/handover/remaining-sections-manifest.json)
records the source Git blob, full-source and retained-prefix hashes, and ordered
archive hashes. Concatenating the original retained prefix with these archive
files reconstructs the exact pre-extraction HANDOVER.md. The prefix is the bytes
before this index's Additional archived records heading (excluding the extra
separator newline immediately before that heading), with the two link corrections
listed in the extraction manifest reversed. Archive text, including
commands and historical pending statements, has not been rewritten. Review
historical instructions against current guides before using them.

Validation: the supplied source matched the live HANDOVER Git blob; all 21
extracted sections reconstructed the source byte-for-byte with the retained
prefix. README.md was reviewed and needs no change for this documentation-only
extraction. No application tests were run. Existing archive files and the
original manifest are unchanged. Pre-existing index links for records 020 and
021 were corrected to the actual existing filenames; no files were renamed.

## Current work

- [Bug 2: regression-first integration contracts (2026-10-30)](docs/handover/049-bug-2-integration-contract-tests-2026-10-30.md)
- [Bug 2: migration 18 intermediate; do not deploy (2026-10-30)](docs/handover/050-bug-2-migration-18-2026-10-30.md)
- [Bug 2: archive-before-detach reconciliation; acceptance pending (2026-10-30)](docs/handover/051-bug-2-archive-reconciliation-2026-10-30.md)
- [Bug 2: ordinary-save payload context prerequisite (2026-10-30)](docs/handover/052-bug-2-room-save-context-2026-10-30.md)
- [Bug 2: editor save context and delayed-response protection (2026-10-30)](docs/handover/053-bug-2-editor-save-context-2026-10-30.md)
- [Bug 2: strict ordinary-save validation; acceptance pending (2026-10-30)](docs/handover/054-bug-2-strict-save-validation-2026-10-30.md)
- [Bug 2: explicit archive listing and recovery; acceptance pending (2026-10-30)](docs/handover/055-bug-2-explicit-recovery-2026-10-30.md)
- [Bug 2: dedicated recovery UI; acceptance pending (2026-10-30)](docs/handover/056-bug-2-recovery-ui-2026-10-30.md)
- [Bug 2: archive-aware backup and restore; acceptance pending (2026-10-30)](docs/handover/057-bug-2-archive-backup-restore-2026-10-30.md)
