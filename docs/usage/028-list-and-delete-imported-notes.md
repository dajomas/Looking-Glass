## List and delete imported notes

Expand Import room notes and click List imported notes. A dialog shows every
imported name and its Markdown source, including assigned entries hidden from the
assignment dropdown. Notes sections start expanded and can be collapsed. Names
have import IDs to distinguish variants. Refresh list reloads assignment status.

Status is Unassigned, Assigned · name and notes match, or Assigned · saved notes
differ from this import. Assignment follows the existing trimmed/case-insensitive
room-name matching within this map, including manually entered names and preserved
inactive geometry records. Notes-match means at least one matching-name saved room
has the same Markdown (normalized CRLF); modified assigned notes remain protected.

Only unassigned entries have Delete imported entry. Confirm to permanently remove
that one library record. Deletion does not remove map rooms, room notes, walls or
fog. The server rechecks assignment under a write transaction, so an entry assigned
by another session since opening the dialog cannot be deleted. The list and picker
refresh after deletion; errors are shown with refreshed status where possible.
Unsaved drafts do not count as assignments. A deleted entry can be imported again.
Close or Escape exits the dialog. The browser list shows note source as text rather
than executing or rendering uploaded HTML. Back up SQLite before deleting records
if you need recovery; there is no undo for library deletion.

