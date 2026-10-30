## Double-reveal architecture (schema 17)

`services/double_reveal.py` owns room identity validation, artwork compositing, appearance
history and state-preserving navigation. `web/admin/double_reveal.py` exposes the DM-only
routes; `static/js/double_reveal.js` controls the new panel. The partial is included in the
fog editor and its selection handler intercepts clicks before fog, notes and doors.

Migration 17 appends three tables without changing existing migration scripts:

- `double_reveal_maps`: one alternate image file and revision per map.
- `double_reveal_rooms`: geometry digest, image-space interior anchor, optional same-campaign
  destination map, true/initial runtime flag and optimistic revision.
- `double_reveal_history`: ordered before/after appearance states, cascading with room removal.

Geometry keys use the existing room-notes region hashing. Anchors on wall pixels are not
snapped to another room. A changed region is ignored at render/navigation time rather than
silently reassociated. SQL triggers reject cross-campaign destinations and advance
`maps.fog_version` on image/room mutations, including destination removal. Operations execute
inside `BEGIN IMMEDIATE`; the API checks cache incarnation, walls/fog versions, image revision,
and (where relevant) room revision before writes.

`web/access.fog_inputs` adds immutable alternate path/room tuples to `MapSpec`. The renderer
composites selected true-room interiors into the original artwork before applying the existing
fog and viewer overlays. Alternate path and room states participate in cache identity. Existing
positional MapSpec arguments are preserved by appending optional fields. Ordinary fog actions
never mutate appearance tables. Raw alternate artwork and selection masks are admin-only;
viewer routes continue returning only server-composited fogged images.

Cross-map links are not map-transition endpoints: they are explicit DM navigation attached
to a double-reveal room. They require a true, revealed, geometry-matched source on the active
map. Navigation snapshots current source/destination fog and changes only the active map and
campaign generation; it does not replay/reset fog or reveal arrival areas.

Backup export includes the three tables and alternate assets. Restore remaps destination map
IDs, validates dimensions and references, and preserves appearance history. Duplication copies
authored assets/configuration but starts in initial appearance with empty history; full campaign
copies remap links and single-map copies detach links outside the copied map set.
Named checkpoints fingerprint alternate image content and authored room links, capture runtime
appearance/history, and restore only against matching authored content. Older checkpoints remain
compatible when no double-reveal authored configuration has been added.


