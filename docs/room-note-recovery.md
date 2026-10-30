# Retained room-note recovery API

Development-branch API: the recovery UI, archive portability and acceptance
are not complete. Do not deploy this intermediate branch against valuable
campaign data or rely on campaign ZIPs to preserve retained notes yet.

Both routes exist only on the admin application and require campaign-management
permission. Recovery additionally requires X-CSRF-Token. They do not activate
maps, reveal/hide fog or publish viewer updates.

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
Database failures roll back the request and are not reported as success.
A repeated request is stale after success. Do not automatically retry with new
stamps after a transport error; inspect current content first.

No archive edit/delete/consume/purge API is introduced. Explicit owning-map or
campaign deletion still follows migration 18's cascading ownership lifecycle.
See [handover](handover/055-bug-2-explicit-recovery-2026-10-30.md) for validation
limits and unfinished work.
