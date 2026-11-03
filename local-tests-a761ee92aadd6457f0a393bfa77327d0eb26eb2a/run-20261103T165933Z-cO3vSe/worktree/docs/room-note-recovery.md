# Retained room-note recovery UI and API

Bug 2 was accepted by the user on 2026-10-30 at 22:37 CET. Archive-aware recovery,
campaign ZIP backup/restore and clean duplication are implemented. Acceptance is
not evidence of a new test run or execution of the disposable schema-17 upgrade
exercise, which remains an outstanding validation item. It is not blanket
deployment approval. Keep stopped database/image backups before upgrades and
never test against the only copy of valuable data. See the current
[closure and evidence limits](handover/066-bug-2-accepted-closure-2026-10-30.md)
and the historical [coverage/checklist](handover/062-bug-2-coverage-acceptance-2026-10-30.md).

## Management workspace

On an admin map page, Retained notes in the top navigation opens a separate tab
at /maps/{map_id}/room-note-recovery. The original editor and its unsaved draft
are not replaced. Save or copy any existing draft before replacing saved notes;
recovery can make its old save context stale. The original tab is not silently
refreshed or rebased.

Choose a retained entry, inspect its full Markdown source and historical
provenance, then click an interior on the artwork or use the keyboard-accessible
X/Y coordinate form to inspect the current target. Preview text is rendered as
text, not trusted HTML. Load older notes for additional archive pages; Refresh
starts at the newest page without automatically selecting or recovering content.

Every recovery requires explicit confirmation. A nonempty target additionally
requires the replacement checkbox after reviewing its saved content. Target
content is archived first. The original source archive is retained.

Errors preserve selections/previews and require explicit target reinspection
before another attempt; there is no automatic retry or rebasing. If map
incarnation or boundaries changed since page load, reload the workspace. Pending
recovery warns before leaving the page. A transport error can have an uncertain
outcome: inspect the current target before another deliberate request.

Both API routes exist only on the admin application and require management
permission. Recovery additionally requires X-CSRF-Token. They do not activate
maps, reveal/hide fog or publish viewer updates.

## Retention and portability

Geometry reconciliation releases invalid room assignments only after retaining
their exact saved names and Markdown. Archives stay detached even if old geometry
returns. Imported library text remains separate from custom saved edits; releasing
an imported name does not replace those edits with the library's original text.

Archive map_id is current ownership. source_* fields, source_revision, timestamp
and origin_uuid describe historical provenance. Restore and duplication remap
current ownership/local IDs, not that history; repeated copies can share an
origin UUID. Clean copies start with fresh map identity and local note generation,
without automatic activation or recovered assignments. Explicit deletion of an
owning map/campaign cascades its archives; retention is not a substitute for backups.
See [archive backup/restore and clean duplication](room-note-backup.md).

## Listing

GET /api/maps/{map_id}/room-note-archives?limit=50

The no-store JSON response has ok, archives and next_before_id. Each archive
contains every stored column, including exact name/Markdown and provenance.
Records are newest-first by local archive ID. limit defaults to 50 and accepts
1-200. If next_before_id is non-null, pass it as before_id for the next page.
A page boundary is not a retention limit; nothing is automatically purged.
Refresh from the first page to see newly added archives while paging.

Listing follows existing admin read-time reconciliation: stale assignments may
be atomically archived/detached before listing. It does not automatically repair
associations or reattach retained notes.

## Explicit recovery

POST /api/maps/{map_id}/room-note-archives/{archive_id}/recover

```json
{
  "x": 100, "y": 50,
  "area_key": "<64-character current area key>",
  "revision": 0,
  "cache_token": "<current map incarnation>",
  "walls_version": 9,
  "room_notes_version": 4,
  "overwrite": false
}
```

Select a current room through POST /api/maps/{map_id}/room-at and retain that
response's context unchanged. All five validation fields are required. Counters
are strict nonnegative integers. overwrite is a strict boolean, default false.
Unknown fields, including client name/Markdown substitutions, are rejected.

For a nonempty target, inspect its current content and explicitly confirm
replacement with overwrite=true using that same target context. Its full content
is archived as recovery_replacement before replacement. Whitespace counts as
content. Recovery copies the chosen archive's exact name/Markdown without
trimming; the active association uses the selected current geometry and point.
The source archive and historical provenance are retained after recovery.

Success returns no-store JSON with ok and the refreshed ordinary room payload.
Missing/invalid fields use 422; stale context or unconfirmed replacement uses
400; a missing/wrong-map archive uses 404. Existing auth/CSRF errors remain.
API validation errors use the shared {ok:false,error:"field: message"} envelope,
not a detail array. Database failures roll back the request and are not reported
as success. A repeated request is stale after success. Do not automatically retry
with new stamps after a transport error; inspect current content first.

No archive edit/delete/consume/purge API is introduced. Explicit owning-map or
campaign deletion still follows migration 18's cascading ownership lifecycle.
See [backend record](handover/055-bug-2-explicit-recovery-2026-10-30.md) and
[UI record](handover/056-bug-2-recovery-ui-2026-10-30.md) for historical validation limits.
