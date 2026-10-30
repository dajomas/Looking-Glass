## Wall legend: Show and Enabled

Each type has two independent controls:

- **Show** immediately shows/hides that category in the DM overlay only. It is
  remembered in this browser per map. Hiding it does not remove its boundaries.
- **Enabled** controls whether the type participates in area calculations after
  **Apply wall types**. These settings are saved per map on the server, survive
  reload/reimport and affect both DM area detection and player composites.

Disabled segments remain stored and are displayed passively unless hidden.
They can be re-enabled without reimport. Ethereal walls never block even when
Enabled is checked. Door and secret-door boundaries also require Doors split
areas. The overall Show walls toggle still controls the entire DM overlay.
Changing boundaries can merge rooms and expand previous reveals. Blank the
viewer before applying boundary changes during play. Apply is immediate.

The legend colours are magenta normal walls, blue doors, purple dashed secret
doors, green windows/terrain, yellow dashed invisible walls and grey passive/
ethereal walls. Alignment uses image=(wall-offset)*scale. Apply alignment after
adjusting scale, offset or nudges; no confirmation is shown.

