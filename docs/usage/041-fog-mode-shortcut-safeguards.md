## Fog-mode shortcut safeguards

Badges appear only in normal admin fog mode, not Double Reveal or room-note selection.
Invalid geometry has no badge. Hidden rooms may still show a DM badge: their artwork can
be prepared without revealing fog. Travel requires the source room to be visible and its
map to be shown to players; destination fog and appearance are preserved. Cancelling the
confirmation makes no map change. Plain left/right clicks, drag/pinch and unmodified
double-click viewer zoom keep their existing behavior.

Ctrl-primary in fog mode is reserved and never falls through to fog, doors, transitions
or viewer zoom, even on invalid rooms or failed requests. Fresh room state is read before
acting; changed state refreshes markers and requires another click. Restore initial
appearance and Undo appearance change remain available in Double reveal.
