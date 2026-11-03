## Door arrow settings and actions

Admin map payloads include `door_arrow_color` (`#RRGGBB`), `door_arrows_enabled` (boolean, default true) and `work_scale` (work pixels per source image pixel).

- `POST /api/maps/{map_id}/door-arrows`: authenticated campaign manager plus CSRF. Accepts partial JSON updates `{"enabled":false}`, `{"color":"#46c0ff"}`, or both. Omitted/null fields preserve current values. Enabled must be a strict JSON boolean; color is a six-digit hexadecimal string, normalized lower-case. Saves preferences, bumps fog version, broadcasts refresh and returns map state without adding a fog action/checkpoint.
- `GET /api/maps/{map_id}/door-arrows.png`: management-only, no-store RGBA overlay at work resolution; transparent when disabled.
- `POST /api/maps/{map_id}/door-arrows/reveal`: authenticated campaign manager plus CSRF. Body: `{"x":175.5,"y":100.5,"cache_token":"<map incarnation>","walls_version":1,"fog_version":1}`. Coordinates identify the clicked visible arrow pixel in image space, not a client-selected target room. The server recomputes the enabled arrow and resolves a verified open pixel in the opposite hidden area. A successful request appends one ordinary reveal operation, bumps fog version, checkpoints if active, broadcasts normal refresh and returns the updated map payload with `area_fraction` and `leak_warning`.

The click endpoint holds a SQLite write transaction across stamp validation and mutation. Stale incarnation/version stamps or a point with no enabled visible arrow return 400 without a fog write. Repeating the same click stamp is rejected after the first reveal. Management authorization is checked before topology use. Viewer endpoints remain unchanged and read-only: only composited imagery is delivered, never hidden target coordinates or wall geometry.


