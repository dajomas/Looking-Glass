# Immediate Apply, selection retention and display policy

Apply actions take effect without confirmation. Deletion and toolbar Reset
confirmations remain. Every Show or editor map-switch selection uses uncached
GET /api/maps/{id}/display-options. Effective saved reveals cause the existing
Restore/Reset/Cancel dialog; empty/fully hidden histories use explicit reset
without a dialog. Failed checks do not activate a map. This behavior is unchanged.
Direct editor URLs remain editing actions, while the editor map-switch publishes
its selected target after the policy check. Multiple tabs can still race between
the availability check and activation; no optimistic-concurrency token is added.

Valid dropdown choices now remain visible through Apply, refresh and reload.
Preferences are browser-local, page/map scoped and source-dependent for wall
sets. Invalid/missing options are never silently selected. The current map switch
is determined by the URL/server, not a stored selection for a different map.

Wall legend Show controls are local overlay visibility. Enabled controls are
persistent server-side room-boundary participation, applied without confirmation.
GET /api/maps/{id} now reports disabled_wall_types and image_version; POST
/api/maps/{id}/wall-types accepts {"disabled_wall_types":["window"]}. Campaign
management and CSRF checks apply. Invalid types fail validation. Raw wall segments
are preserved; fog inputs mark disabled categories non-blocking for all callers.
Wall/fog versions increment and existing cache invalidation/notifications run.

The viewer state response adds revealed_bounds (x/y/width/height in original
image coordinates), or null for fully hidden maps. Only revealed pixels are used
to compute it. The browser scales these coordinates to the composited image and
centers/fits the union with a margin. It receives no raw geometry or unmasked image.

Migration 4 adds map_wall_type_settings with per-map cascade deletion. Existing
legacy maps.disabled_wall_types settings are used until a map is explicitly saved,
and are kept in sync when that column exists. No old migration is rewritten.
Back up before migration and retain the previous checkpoint/token schema repair.
