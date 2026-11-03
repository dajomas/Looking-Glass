## Locked and unlocked doors

Migration 8 and its existing runtime door table remain intact. Migration 10 adds
`walls.passage` JSON and `passage_runtime_states(wall_id, side, kind)` with a
cascading wall foreign key. Side -1 stores shared secret-door state; sides 0/1
store independent portal Entry overrides. Authored secrets use `kind=secret` and
an optional `after` property; authored portal elements use `kind=portal` with pair,
end and two side definitions. Exact pair/route validation precedes replacement.

Repository `designed=True` reads omit runtime overrides for authoring/export.
Effective reads merge temporary kinds and retain designed_kind for boundary
filtering. Runtime changes bump wall/fog versions without changing topology or
fog history. Reset clears both runtime tables; fog hide_all triggers cover toolbar
Reset and explicit reset helpers cover map activation. Row replacement cascades
state deletion. Normal reveals use existing fog history/checkpoint/notifications.

`door_actions.perform` requires a current incarnation/version stamp and actual
raster hit. Double-click state changes require an arrow. Entry side IDs are checked
against server-resolved geometry, so the browser cannot choose another Entry.
The legacy arrow-reveal endpoint rejects locked and undiscovered-secret arrows.
Already revealed destinations are no-ops. Portal metadata is authored-only in
UVTT; runtime states never enter reusable sources.

