# Testing and upgrade validation

This index replaces the original monolithic guide. Its original text is preserved
in order in the source sections below. This is a structural preservation snapshot,
not a semantic correction or a new test/deployment result.

Historical commands, dependency names, schema descriptions and test results retain
their original context. For current CI suite definitions, see [CI details](ci-tests.md).
For current retained-note behavior and accepted Bug 2 status, see
[recovery](room-note-recovery.md), [portability](room-note-backup.md) and
[closure/evidence limits](handover/066-bug-2-accepted-closure-2026-10-30.md).
These current contracts take precedence over obsolete descriptions in the snapshot.

## Contents

- [Introduction](testing/001-introduction.md)
- [Environment](testing/002-environment.md)
- [Python service and HTTP tests](testing/003-python-service-and-http-tests.md)
- [JavaScript regression scripts](testing/004-javascript-regression-scripts.md)
- [Browser tests](testing/005-browser-tests.md)
- [Manual pre-deployment checklist](testing/006-manual-pre-deployment-checklist.md)
- [Scope and limitations](testing/007-scope-and-limitations.md)
- [Passage modal/sidebar regressions](testing/008-passage-modal-sidebar-regressions.md)
- [Passage save-scope isolation](testing/009-passage-save-scope-isolation.md)
- [Portal Close, Reset and Travel-return regressions](testing/010-portal-close-reset-and-travel-return-regressions.md)
- [Collapsible sidebar help](testing/011-collapsible-sidebar-help.md)
- [Help surface styling](testing/012-help-surface-styling.md)
- [Room-note regression checks](testing/013-room-note-regression-checks.md)
- [Markdown room-note import regression checks](testing/014-markdown-room-note-import-regression-checks.md)
- [Room controls follow-up coverage](testing/015-room-controls-follow-up-coverage.md)
- [Replacement confirmation regression tests](testing/016-replacement-confirmation-regression-tests.md)
- [Edit-only imported-note picker](testing/017-edit-only-imported-note-picker.md)
- [Unnamed room auto-edit regression cases](testing/018-unnamed-room-auto-edit-regression-cases.md)
- [Imported-name availability tests](testing/019-imported-name-availability-tests.md)
- [Edit marker and imported-note manager coverage](testing/020-edit-marker-and-imported-note-manager-coverage.md)
- [Name coverage overlay regression tests](testing/021-name-coverage-overlay-regression-tests.md)
- [Imported-room list fixed header and unassign regression](testing/022-imported-room-list-fixed-header-and-unassign-regression.md)
- [Campaign backup and restore validation](testing/023-campaign-backup-and-restore-validation.md)
- [Campaign readiness validation](testing/024-campaign-readiness-validation.md)
- [Campaign quick-navigation validation](testing/025-campaign-quick-navigation-validation.md)
- [Named session checkpoint validation](testing/026-named-session-checkpoint-validation.md)
- [Step 4 backup inspection and recovery](testing/027-step-4-backup-inspection-and-recovery.md)
- [Step 5 viewer synchronization status](testing/028-step-5-viewer-synchronization-status.md)
- [Step 6: duplication](testing/029-step-6-duplication.md)
- [Items 7 and 8: import busy feedback / access logging](testing/030-items-7-and-8-import-busy-feedback-access-logging.md)
- [Double-reveal regression checks](testing/031-double-reveal-regression-checks.md)
- [Admin artwork response regression](testing/032-admin-artwork-response-regression.md)
- [Rocky Linux 10 / WSL browser preflight](testing/033-rocky-linux-10-wsl-browser-preflight.md)
- [Browser harness follow-up (a24b7d0)](testing/034-browser-harness-follow-up-a24b7d0.md)
- [Confirmation spy initialization](testing/035-confirmation-spy-initialization.md)
- [Fixture repair and UI follow-up for 9f3be8f](testing/036-fixture-repair-and-ui-follow-up-for-9f3be8f.md)
- [Viewer diagnostics and disclosure-state fixture contracts](testing/037-viewer-diagnostics-and-disclosure-state-fixture-contracts.md)
- [Arrow-image and new-window inspection mock contracts](testing/038-arrow-image-and-new-window-inspection-mock-contracts.md)
- [Browser regressions and isolated label paint checks (f4d60c3)](testing/039-browser-regressions-and-isolated-label-paint-checks-f4d60c3.md)
- [Live DM-to-player integration suite: batch 1](testing/040-live-dm-to-player-integration-suite-batch-1.md)
- [Double Reveal fog-mode regressions](testing/041-double-reveal-fog-mode-regressions.md)
- [GitHub Actions integration validation](testing/042-github-actions-integration-validation.md)

## Preservation and verification

The [manifest](testing/manifest.json) records the original source commit/Git blob,
ordered source paths, byte counts and SHA-256 hashes. Concatenate its `files`
entries as bytes in order to reconstruct the exact 63257-byte UTF-8 original,
including line endings and final newline state. Indexes and manifests are excluded
from reconstruction. Every content file is below 10,000 bytes. The manifest
describes the split-time snapshot, not later semantic edits; use Git history
to retrieve that snapshot after future changes.

Links and fragments inside section files remain verbatim. Resolve relative links
against the former `docs/testing.md` base until deliberately rebased. Relocation
can otherwise change their meaning. Legacy fragment links also need review.
Heading-like examples inside code fences were not treated as section boundaries.

## Existing topic links

These anchors retain the cross-guide links identified during finalization;
follow the section link for the complete original text. Other legacy fragment
links are not assumed to redirect automatically.

### Campaign backup and restore validation

Read [backup validation](testing/023-campaign-backup-and-restore-validation.md).

### Step 5 viewer synchronization status

Read [viewer synchronization](testing/028-step-5-viewer-synchronization-status.md).

### Fontconfig and rendered-text failures

Read [browser preflight and font diagnostics](testing/033-rocky-linux-10-wsl-browser-preflight.md#fontconfig-and-rendered-text-failures).

