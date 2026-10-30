## Viewer arrow category exceptions

`POST /api/maps/{map_id}/door-arrows` accepts two additional optional strict booleans:
`viewer_portal_enabled` and `viewer_secret_enabled`. Omitted/null fields preserve current values.
The admin map payload returns `viewer_portal_arrows_enabled` and `viewer_secret_arrows_enabled`.
Existing `enabled`, `admin_enabled`, `viewer_enabled` and color fields retain their meanings.
These settings require the existing map-management authorization and CSRF protection.
Actual changes bump the fog version and send the existing `appearance` notification.
No fog operations or passage runtime state are modified. Currently secret entries never render for viewers.


