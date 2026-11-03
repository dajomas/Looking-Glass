# Deployment

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

- [Introduction](deployment/001-introduction.md)
- [1. Native installation (RHEL / Rocky)](deployment/002-1-native-installation-rhel-rocky.md)
- [2. systemd service](deployment/003-2-systemd-service.md)
- [3. Networking](deployment/004-3-networking.md)
- [4. Podman deployment](deployment/005-4-podman-deployment.md)
- [5. Native-service operations](deployment/006-5-native-service-operations.md)
- [6. Backups and upgrades](deployment/007-6-backups-and-upgrades.md)
- [Door-arrow and clickable-arrow upgrade](deployment/008-door-arrow-and-clickable-arrow-upgrade.md)
- [Locked-door patch on e519068](deployment/009-locked-door-patch-on-e519068.md)
- [Independent arrow visibility upgrade](deployment/010-independent-arrow-visibility-upgrade.md)
- [Viewer room-zoom upgrade](deployment/011-viewer-room-zoom-upgrade.md)
- [Admin-controlled viewer zoom upgrade](deployment/012-admin-controlled-viewer-zoom-upgrade.md)
- [New-reveal overview reset upgrade](deployment/013-new-reveal-overview-reset-upgrade.md)
- [Passages upgrade (schema 10)](deployment/014-passages-upgrade-schema-10.md)
- [Movable portal dialogs, overview and route highlighting](deployment/015-movable-portal-dialogs-overview-and-route-highlighting.md)
- [Installing the viewer arrow exceptions patch](deployment/016-installing-the-viewer-arrow-exceptions-patch.md)
- [Installing cross-map passages (schema migration 12)](deployment/017-installing-cross-map-passages-schema-migration-12.md)
- [Passage modal and sidebar updates](deployment/018-passage-modal-and-sidebar-updates.md)
- [Portal Close, Travel return and Reset labels](deployment/019-portal-close-travel-return-and-reset-labels.md)
- [Upgrading for room notes](deployment/020-upgrading-for-room-notes.md)
- [Room-note import upgrade](deployment/021-room-note-import-upgrade.md)
- [Room metadata controls follow-up](deployment/022-room-metadata-controls-follow-up.md)
- [Replacement confirmation hotfix](deployment/023-replacement-confirmation-hotfix.md)
- [Imported-name availability follow-up](deployment/024-imported-name-availability-follow-up.md)
- [Edit highlight and library manager follow-up](deployment/025-edit-highlight-and-library-manager-follow-up.md)
- [Named / unnamed coverage follow-up](deployment/026-named-unnamed-coverage-follow-up.md)
- [Deploying imported-room list unassignment](deployment/027-deploying-imported-room-list-unassignment.md)
- [Campaign backup operations](deployment/028-campaign-backup-operations.md)
- [Readiness-check operations](deployment/029-readiness-check-operations.md)
- [Campaign search operations](deployment/030-campaign-search-operations.md)
- [Session checkpoint upgrade and operations](deployment/031-session-checkpoint-upgrade-and-operations.md)
- [Deploying viewer synchronization status (step 5)](deployment/032-deploying-viewer-synchronization-status-step-5.md)
- [HTTP access-log noise (item 8)](deployment/033-http-access-log-noise-item-8.md)
- [Upgrading for double-reveal rooms](deployment/034-upgrading-for-double-reveal-rooms.md)
- [Browser-test dependencies on Rocky Linux 10](deployment/035-browser-test-dependencies-on-rocky-linux-10.md)
- [Optional Scrying Glass lookup](deployment/036-optional-scrying-glass-lookup.md)

## Preservation and verification

The [manifest](deployment/manifest.json) records the original source commit/Git blob,
ordered source paths, byte counts and SHA-256 hashes. Concatenate its `files`
entries as bytes in order to reconstruct the exact 47889-byte UTF-8 original,
including line endings and final newline state. Indexes and manifests are excluded
from reconstruction. Every content file is below 10,000 bytes. The manifest
describes the split-time snapshot, not later semantic edits; use Git history
to retrieve that snapshot after future changes.

Links and fragments inside section files remain verbatim. Resolve relative links
against the former `docs/deployment.md` base until deliberately rebased. Relocation
can otherwise change their meaning. Legacy fragment links also need review.
Heading-like examples inside code fences were not treated as section boundaries.

## Campaign backup operations

This topic anchor retains the existing guide link. Read
[campaign backup operations](deployment/028-campaign-backup-operations.md).

