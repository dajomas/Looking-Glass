## Hide already assigned imported names

Use imported room notes now lists only names not already saved on a room in this
map. This includes the room currently being edited: its saved name is omitted
from the dropdown, while its current name and notes remain in the editing fields.
Manual room names count too, even when their notes differ from the imported text.
Name matching ignores case and surrounding whitespace. All imported variants with
the same assigned name are hidden. Other maps have independent availability.

Save room commits the assignment and refreshes availability. Merely selecting an
entry, editing a draft, or cancelling does not reserve/release a name. Save a
rename or clear the name to make the previous name available again, provided no
other saved room still uses it. Clearing only the note does not release the name.
The library remains intact. If every imported name is assigned, the dropdown is
disabled and says “All imported room names are assigned”.

Availability refreshes on opening the editor, after saving, and after import.
Opening an editor again picks up another session's saved changes; this is dropdown
filtering, not a database uniqueness lock against simultaneous manual assignments.
When geometry reconciliation archives and releases an invalid assignment, its
name reservation is released too. Detached archives do not reserve imported
names. Explicitly recovering content onto a current room creates an active
assignment again. See [retained-note recovery](../room-note-recovery.md).

