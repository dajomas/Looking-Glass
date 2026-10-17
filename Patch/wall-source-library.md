# Reusable wall sources and explicit wall-set selection

## Target

- Repository: dajomas/Looking-Glass
- Branch: features/development
- Base commit: 3b485d96e44ed24c5593a2b8437255c02778a917
- Delivery: full changed/new files plus a unified patch; no remote commit made.

## Problem and behavior

The existing parser already understands multi-scene Foundry NeDB databases,
including the supplied maps.db. The previous HTML map-upload path always
applied scene index 0 and discarded the upload after import. The new library
retains validated source bytes in the application database, scoped to a campaign.
Each map can independently choose one of the file's non-empty scene wall sets.
The original upload is immutable and is never modified by applying a wall set.

Map creation with a single-set source continues to apply immediately and also
saves the source. With multiple sets, the source is saved but no walls are
applied until the DM selects a set in the editor. Image-only creation remains
supported. Existing one-off map-editor imports are unchanged and do not save
their upload automatically.

## Files and responsibilities

- python/looking_glass/db.py: append migration 2; preserve migration 1 byte for byte.
- python/looking_glass/repositories/wall_sources.py: save, list, scoped lookup,
  delete; SHA-256 deduplication and display-filename normalization.
- python/looking_glass/web/admin/wall_sources.py: source API routes, source/map
  authorization and explicit scene-index validation through existing import logic.
- python/looking_glass/web/admin/api.py: register source routes on the admin API.
- python/looking_glass/web/admin/campaigns.py: retain valid map-upload wall sources;
  defer multi-set application rather than silently choosing the first scene.
- web_html/admin/map_editor.html: accessible library controls, script inclusion.
- static/js/wall_source_library.js: save, select, inspect, apply, refresh, delete;
  explicit scene choice, request locking, safe text insertion and error status.
- python/tests/test_wall_sources_repository.py: migration/persistence regression tests.
- python/tests/test_wall_sources_web.py: full-app HTTP workflow regression test.
- README.md and docs/{usage,foundry-import,api,architecture}.md: existing documents
  updated with workflow, lifecycle, permissions, API and backup details.

## Data and lifecycle

Migration 2 creates wall_sources(id, campaign_id, filename, sha256, raw,
scene_count, created_at). The raw upload is a BLOB; campaign deletion cascades
source deletion. UNIQUE(campaign_id, sha256) deduplicates identical bytes while
preserving the first uploaded filename. Changed content creates another source.
AUTOINCREMENT prevents deleted source IDs from being reused in stale clients.

Source deletion cannot remove already-applied map walls: application copies
segments through the existing apply_walls path and computes map-specific
calibration. Sources are not shared across campaigns. A user managing two
campaigns must save the file separately in each. Raw source data is not served
by these endpoints; list/inspection responses contain metadata only.

Applying replaces only the target map's walls. Existing fog actions and the
per-map door setting are retained. Automatic alignment can be disabled to keep
the current map alignment. Fog is invalidated and viewers are notified after
the transaction. The editor reloads to show the new geometry.

## Safety and limitations

- Blank players before replacing walls during play. Existing fog actions replay
  against the replacement geometry and may reveal different areas.
- There is no live source-to-map relationship, source rename, or in-place update.
- New source IDs distinguish changed files with identical filenames.
- Empty scenes are filtered by the existing importer; indices refer to returned
  non-empty wall sets. Duplicate names remain distinct by index.
- Source persistence obeys the existing per-file upload limit but adds no total
  storage quota. Source deletion may not immediately shrink the SQLite file.
- Foundry LevelDB directories and SQLite .db inputs are not newly supported.
- Existing parser behavior is retained; unrelated import/parser edge cases are
  outside this patch. No new third-party dependency or config key is required.
- Source APIs use the existing campaign/map manage helpers and CSRF dependency,
  and are registered on the admin router only.

## Upgrade and rollback

Stop the service and back up the complete application data directory before
applying. Restart normally: Database.migrate() applies migration 2 once.
Retain the database, map images and configuration in backups. Test on a copy
before upgrading a live game. Restore the pre-upgrade database/data backup and
matching code for rollback; do not edit schema_version or remove migration rows.

See README.md in this Patch directory for application commands and test status.
