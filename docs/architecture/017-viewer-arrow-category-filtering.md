## Viewer arrow category filtering

Schema migration 11 adds `maps.viewer_portal_arrows_enabled` and
`maps.viewer_secret_arrows_enabled` as checked boolean integers, default zero.
MapSpec loads both with backward-compatible defaults and includes them in cache identity.
The viewer compositor retains the main viewer flag as the primary visibility switch.
When that switch is off, door_arrows.arrows permits generation for category exceptions,
then filters entries by portal/secret-origin union. Current-secret checks and admin-only
exit-hint restrictions precede filtering. Admin rendering and validated hit testing remain
controlled only by the admin switch. API updates preserve omitted fields, invalidate via
fog-version changes, and notify connected viewers through the appearance event.


