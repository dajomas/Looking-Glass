## Named / unnamed area overview API

GET /api/maps/{map_id}/room-name-overlay requires admin map-management access.
It returns `{ok,png,named,unnamed}` with a base64 RGBA PNG at fog work resolution
and named/unnamed current area counts. Response has Cache-Control: no-store.
It is read-only and does not update versions, checkpoints, notes or fog operations.
Only nonblank saved names with a valid current area_key/anchor make an area green;
other open areas are red, walls transparent. No viewer route is registered.

