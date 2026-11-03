## Imported room list: fixed header and unassigning

Open Room notes → Import room notes → List imported notes. The title, Close,
Refresh list, instructions and status stay fixed above the scrollable entries.
The list accepts keyboard focus for scrolling; individual Markdown blocks retain
their existing independent scrolling for long notes.

Assigned entries provide **Unassign from rooms**. Confirm to clear both the saved
name and Markdown from all matching rooms on this map. Matching trims surrounding
whitespace and ignores case, exactly like library availability. The operation
also clears custom room-note edits; the original imported text remains unchanged.
If multiple imported entries share the same normalized name, they all become
available once the matching room assignments are cleared. Other maps are untouched.

This is immediate, not a draft edit, and has no Undo. Cancel at confirmation to
leave data unchanged. Save or cancel any pending room draft first. During a
request, actions and Close/Escape are disabled to prevent duplicate operations.
After success the imported picker, dialog status, selected room (if affected),
and named/unnamed overlay refresh. An unassigned selected room returns to read
mode; use Edit room to assign another entry. Fog, walls and player images do not
change. Delete imported entry remains available only for unassigned entries.

Existing geometry-change reconciliation continues to remove invalid assignments
when walls change; this manual action releases an assignment without editing walls.

