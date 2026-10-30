## Imported-note manager and guarded deletion

room_library_manager.js provides a native dialog, all-entry list, expanded Markdown
source details, assignment badges, Refresh and confirmed delete actions. Content
is placed via textContent, never unsanitized innerHTML. It uses the existing library
GET and a new DELETE route. Successful deletion replaces the owner's cached
library and rebuilds the assignment picker; errors refresh status without removing
protected entries. Request generations ignore results from closed dialogs.

The deletion service requires a caller-held IMMEDIATE transaction. The route holds
it across map permission, same-map entry lookup, current name-based assignment
validation and deletion, serializing against room-note saves. No schema change.
notes_match distinguishes exact source-note matches from assigned names with
modified notes; assignment protection still applies to both. Drafts do not reserve
entries. Simultaneous manual room assignment after deletion is still possible
because room notes are copied text rather than import-ID foreign keys.

