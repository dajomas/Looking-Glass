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
