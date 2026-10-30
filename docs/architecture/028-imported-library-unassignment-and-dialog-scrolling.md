## Imported library unassignment and dialog scrolling

The native imported-room dialog uses a flex column only while `[open]`, preserving
closed-dialog behavior. The header is nonshrinking; the list alone uses
`min-height:0; overflow-y:auto`. Modal height is bounded by viewport/dynamic viewport.

`room_library_manager.js` renders unassign controls for assigned entries and delete
controls for unassigned entries. Text continues to use textContent. Mutations are
confirmed, serialized, and guarded against stale async responses and unsaved drafts.
Successful unassignment updates library availability, re-fetches an affected selected
room, and refreshes the named/unnamed overlay without changing player state.

`room_note_import.unassign` matches the existing Python `strip().casefold()` name
policy and clears saved name/Markdown in place, incrementing revisions. The API
holds BEGIN IMMEDIATE around permission checks, geometry reconciliation and mutation.
Imported entries remain immutable; no migration, cache format or dependency change.

