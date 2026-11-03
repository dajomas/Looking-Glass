# HTTP API

This index replaces the former monolithic guide. Its complete text is
preserved, in original order, in the numbered files below. This split changes
no implementation, acceptance status, API behavior or validation evidence.

## Contents

- [Introduction](api/001-introduction.md)
- [Admin port (5000)](api/002-admin-port-5000.md)
- [Reusable wall sources (admin port only)](api/003-reusable-wall-sources-admin-port-only.md)
- [Viewer port (5100)](api/004-viewer-port-5100.md)
- [Explicit map-display reveal policy](api/005-explicit-map-display-reveal-policy.md)
- [Dedicated wall editor and UVTT export (admin only)](api/006-dedicated-wall-editor-and-uvtt-export-admin-only.md)
- [Door arrow settings and actions](api/007-door-arrow-settings-and-actions.md)
- [Locked and unlocked doors](api/008-locked-and-unlocked-doors.md)
- [Independent arrow visibility API](api/009-independent-arrow-visibility-api.md)
- [Viewer revealed-area framing lookup](api/010-viewer-revealed-area-framing-lookup.md)
- [Admin viewer-zoom command](api/011-admin-viewer-zoom-command.md)
- [Revealed-area change metadata](api/012-revealed-area-change-metadata.md)
- [Authored passage schema](api/013-authored-passage-schema.md)
- [Portal compass labels and selectable None targets](api/014-portal-compass-labels-and-selectable-none-targets.md)
- [Admin-only visible portal route associations](api/015-admin-only-visible-portal-route-associations.md)
- [Viewer arrow category exceptions](api/016-viewer-arrow-category-exceptions.md)
- [Cross-map passage API (admin portal only)](api/017-cross-map-passage-api-admin-portal-only.md)
- [Admin room notes API](api/018-admin-room-notes-api.md)
- [Imported room-note library (admin only)](api/019-imported-room-note-library-admin-only.md)
- [Imported-name availability](api/020-imported-name-availability.md)
- [Room edit decoration and imported-entry deletion](api/021-room-edit-decoration-and-imported-entry-deletion.md)
- [Named / unnamed area overview API](api/022-named-unnamed-area-overview-api.md)
- [Unassign imported room metadata (admin only)](api/023-unassign-imported-room-metadata-admin-only.md)
- [Campaign backup and restore form routes](api/024-campaign-backup-and-restore-form-routes.md)
- [Campaign readiness HTML routes](api/025-campaign-readiness-html-routes.md)
- [Campaign search and generic inspection](api/026-campaign-search-and-generic-inspection.md)
- [Named session checkpoint routes](api/027-named-session-checkpoint-routes.md)
- [Viewer synchronization diagnostics (step 5)](api/028-viewer-synchronization-diagnostics-step-5.md)
- [Clean duplication form endpoints](api/029-clean-duplication-form-endpoints.md)
- [Double-reveal API](api/030-double-reveal-api.md)
- [Admin map artwork URL contract](api/031-admin-map-artwork-url-contract.md)
- [Wall-type boundary request contract](api/032-wall-type-boundary-request-contract.md)
- [Fog-mode Double Reveal API reuse](api/033-fog-mode-double-reveal-api-reuse.md)

## Preservation and future edits

[The manifest](api/manifest.json) records the source commit/blob, byte counts,
SHA-256 hashes and ordered files. Concatenating those file bytes reconstructs
the original UTF-8 guide exactly, including line endings and final newline.
This index is not part of that reconstruction. Each content file is at most
10,000 bytes. Read adjacent parts if a future section spans numbered parts.

Wording, examples and original relative links/fragments are preserved verbatim.
Moving prose changes the base for relative links: resolve such links relative
to the original docs/api.md, not the new section directory, until reviewed.
External links to docs/api.md#... also need review against the section files.
Edit the individual sections for future corrections; the manifest describes
this original split snapshot, not later edits. Git history preserves it.

For the current retained-note recovery contract, including complete save/recovery
context and the shared validation-error envelope, see
[retained room-note recovery](room-note-recovery.md). Original section wording
may predate that implementation; semantic documentation reconciliation remains
separate from this lossless extraction. The user's Bug 2 acceptance is unchanged.
See [the staged split record](handover/065-usage-api-lossless-split-2026-10-30.md).
