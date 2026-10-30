## Campaign-wide quick navigation

Use **Search campaign** on campaign-context admin pages, or **Ctrl+K / ⌘+K** while
not typing in another input. This opens a native dialog scoped to the current campaign.
Type to search; a short debounce updates results. Choose a result type to narrow matches.
Use **Arrow Up/Down** to move between results and **Enter** to open the focused result
(or the first result from the query field). **Escape** or **Close** dismisses the dialog
and returns focus. Shortcuts do not replace text-editing shortcuts in other inputs or
interrupt an already-open dialog. Unsaved editor state stays in place while searching;
following a result leaves the current page, so save drafts before navigating.

Search includes map names; named rooms and saved room-note Markdown; passage names,
player labels and DM notes; and imported room-library names/Markdown. Room names and
note text share one result per saved area association. Unnamed notes are searchable.
Library entries have separate results and can be found even when not assigned to a room.

Matching uses literal case-insensitive Unicode text: every whitespace-separated query
word must occur in the result's title, parent map name or text. There is no wildcard,
regular-expression or fuzzy syntax. Markdown is searched as stored, not semantically
rendered. Exact/prefix title matches rank first, then other title matches, then body/map
matches; ties have stable ordering. Queries are limited to 200 characters and results
to the best 50. Refine the query if more results exist. Blank queries do not list content.

Results open **DM inspection** with the selected stored content shown as escaped plain
text. Room and passage targets highlight their stored position; library entries may not
have coordinates. Stale/deleted targets return not found: search again or run readiness.
Stored room associations are not reconciled or geometry-validated during search.

Search/inspection do not change the active player map, fog, doors, passage states or
room assignments and send no viewer notifications. Deliberately opening an editor from
inspection leaves the read-only view; existing editor behavior then applies. Player-facing
Show, Reveal and Travel remain explicit editor actions, not search-result actions.

The **Open full search page** button and normal Search campaign link provide a GET-form
fallback without dialog/JavaScript support. Search is available only with a current
campaign context, not as a global search across all campaigns from the dashboard.

