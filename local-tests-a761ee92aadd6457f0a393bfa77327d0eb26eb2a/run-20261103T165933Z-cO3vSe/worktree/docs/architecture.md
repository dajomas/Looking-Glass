# Architecture

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

- [Introduction](architecture/001-introduction.md)
- [Process model](architecture/002-process-model.md)
- [Package layout (`python/looking_glass/`)](architecture/003-package-layout-python-looking-glass.md)
- [How area reveal works](architecture/004-how-area-reveal-works.md)
- [Templates](architecture/005-templates.md)
- [Database schema (v1)](architecture/006-database-schema-v1.md)
- [Reusable wall source library (schema v2)](architecture/007-reusable-wall-source-library-schema-v2.md)
- [Map incarnation identity and display checkpoints (schema v3)](architecture/008-map-incarnation-identity-and-display-checkpoints-schema-v3.md)
- [Shared clickable door arrows](architecture/009-shared-clickable-door-arrows.md)
- [Locked and unlocked doors](architecture/010-locked-and-unlocked-doors.md)
- [Independent arrow visibility](architecture/011-independent-arrow-visibility.md)
- [Read-only viewer room zoom](architecture/012-read-only-viewer-room-zoom.md)
- [Admin-origin viewer camera commands](architecture/013-admin-origin-viewer-camera-commands.md)
- [Newly revealed area -> viewer overview](architecture/014-newly-revealed-area-viewer-overview.md)
- [Passage UI and interchange](architecture/015-passage-ui-and-interchange.md)
- [Portal presentation tools](architecture/016-portal-presentation-tools.md)
- [Viewer arrow category filtering](architecture/017-viewer-arrow-category-filtering.md)
- [Cross-map endpoints and atomic travel (schema 12)](architecture/018-cross-map-endpoints-and-atomic-travel-schema-12.md)
- [Sidebar help presentation](architecture/019-sidebar-help-presentation.md)
- [Room-note persistence and rendering](architecture/020-room-note-persistence-and-rendering.md)
- [Imported room-note library](architecture/021-imported-room-note-library.md)
- [One-shot room-import action and actual draft comparison](architecture/022-one-shot-room-import-action-and-actual-draft-comparison.md)
- [Automatic editor entry for unnamed rooms](architecture/023-automatic-editor-entry-for-unnamed-rooms.md)
- [Imported names already assigned to rooms](architecture/024-imported-names-already-assigned-to-rooms.md)
- [Admin-only room editing overlay](architecture/025-admin-only-room-editing-overlay.md)
- [Imported-note manager and guarded deletion](architecture/026-imported-note-manager-and-guarded-deletion.md)
- [Room name coverage overlay](architecture/027-room-name-coverage-overlay.md)
- [Imported library unassignment and dialog scrolling](architecture/028-imported-library-unassignment-and-dialog-scrolling.md)
- [Campaign backup and restore](architecture/029-campaign-backup-and-restore.md)
- [Read-only campaign readiness](architecture/030-read-only-campaign-readiness.md)
- [Campaign search and navigation targets](architecture/031-campaign-search-and-navigation-targets.md)
- [Named campaign session checkpoints](architecture/032-named-campaign-session-checkpoints.md)
- [Viewer synchronization diagnostics (step 5)](architecture/033-viewer-synchronization-diagnostics-step-5.md)
- [Clean map/campaign duplication (step 6)](architecture/034-clean-map-campaign-duplication-step-6.md)
- [HTTP access-log noise (item 8)](architecture/035-http-access-log-noise-item-8.md)
- [Fog editor flash-message placement](architecture/036-fog-editor-flash-message-placement.md)
- [Double-reveal architecture (schema 17)](architecture/037-double-reveal-architecture-schema-17.md)
- [Browser harness follow-up (a24b7d0)](architecture/038-browser-harness-follow-up-a24b7d0.md)
- [Test template/dependency boundaries and dialog reflow](architecture/039-test-template-dependency-boundaries-and-dialog-reflow.md)
- [Read-only viewer diagnostics in browser mocks](architecture/040-read-only-viewer-diagnostics-in-browser-mocks.md)
- [Image and popup boundaries in the browser harness](architecture/041-image-and-popup-boundaries-in-the-browser-harness.md)
- [Editor paint policy and background-test isolation](architecture/042-editor-paint-policy-and-background-test-isolation.md)
- [Live integration-test boundary (batch 1)](architecture/043-live-integration-test-boundary-batch-1.md)
- [Double Reveal fog shortcuts and badges](architecture/044-double-reveal-fog-shortcuts-and-badges.md)

## Preservation and verification

The [manifest](architecture/manifest.json) records the original source commit/Git blob,
ordered source paths, byte counts and SHA-256 hashes. Concatenate its `files`
entries as bytes in order to reconstruct the exact 65461-byte UTF-8 original,
including line endings and final newline state. Indexes and manifests are excluded
from reconstruction. Every content file is below 10,000 bytes. The manifest
describes the split-time snapshot, not later semantic edits; use Git history
to retrieve that snapshot after future changes.

Links and fragments inside section files remain verbatim. Resolve relative links
against the former `docs/architecture.md` base until deliberately rebased. Relocation
can otherwise change their meaning. Legacy fragment links also need review.
Heading-like examples inside code fences were not treated as section boundaries.

