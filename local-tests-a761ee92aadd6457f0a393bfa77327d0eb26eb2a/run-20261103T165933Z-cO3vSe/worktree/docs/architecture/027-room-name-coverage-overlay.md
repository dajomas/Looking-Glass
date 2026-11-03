## Room name coverage overlay

room_name_overlay.js owns a one-button name coverage overlay. It listens to the
selection-mode checkbox, shows its button only when checked, and clears/reset state
when unchecked. Template inserts it directly below the checkbox; those controls
remain accessible while editing. A separate stage image (z-index 2) paints green
and red below the amber room-edit marker (z-index 3), with a viewport text legend.
No map state is changed and pointer events pass through.

The GET service labels each current connected area using saved nonblank names
whose anchor resolves to the same geometry fingerprint. It builds a label palette
and renders one PNG, rather than hashing every unnamed area. Wall pixels are
transparent; empty/whitespace names and detached geometry records do not produce
false green regions. The client invalidates stale responses on hide, geometry
change and refresh. Successful note saves refresh enabled coverage; draft edits,
Cancel and import management do not change classification. Other sessions' note
changes are picked up by explicitly hiding/showing; no new polling loop is added.

