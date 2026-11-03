## When imported-room replacement asks for confirmation

“Replace unsaved room name and notes with the imported entry?” is only appropriate
when there are unsaved name/note differences AND the chosen imported entry differs
from that draft. It is not a warning about replacing already saved metadata:
opening Edit room and selecting a replacement before changing any fields does not prompt. Save room
still controls whether it is persisted; Cancel restores the saved content.

The check compares actual field contents with the selected room's saved values.
Editing and then undoing/reverting to the saved content is clean again. Room names
are compared trimmed (matching server save behavior); Markdown preserves whitespace
other than normalized newline encoding. Choosing an entry identical to the draft
is a no-op and does not prompt. Clearing an already empty room stays clean.

OK replaces the draft once. Cancel leaves it unchanged. Neither choice should
redisplay the modal by itself. The imported-room dropdown always resets to its
placeholder and is never automatically remembered/restored between refreshes or
rooms. Other persistent dropdowns retain their existing behavior. Deploy the fix
and refresh the page; old cached dropdown choices are ignored without requiring
all browser storage to be cleared.

### Imported notes picker location

Select a room, then click Edit room. Use imported room notes appears at the top
of the edit form, above Room name, and stays available while editing. It is hidden
in read mode and when no room is selected. The separate Import room notes upload
section remains outside the editor and starts collapsed as before.

Selecting an entry updates the draft only. Save room persists it; Cancel restores
the saved content. The dropdown prompts once only if a different unsaved draft
would be discarded; choosing an identical entry is a no-op. The picker is disabled
with the other form controls while a save is pending.

