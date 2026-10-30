## Independent arrow visibility API

The management-only map payload adds `admin_door_arrows_enabled` and `viewer_door_arrows_enabled`. Existing `door_arrows_enabled` remains an alias for the admin flag and is still used to generate admin overlays/hit geometry.

`POST /api/maps/{map_id}/door-arrows` retains management authorization and CSRF, accepts strict optional booleans `admin_enabled` and `viewer_enabled`, and supports partial updates. Examples: `{"admin_enabled":false}` hides only admin arrows; `{"viewer_enabled":false}` hides only viewer arrows. Omitted/null fields preserve stored values. Existing `color` and `locked_color` behavior is unchanged.

For compatibility, legacy `enabled` still updates BOTH flags. Explicit per-screen fields take precedence over that legacy shared value if both are supplied. The write transaction preserves unrelated flags/colors, fog history, runtime locks and checkpoints. Viewer visibility or either shared color changing bumps fog version and publishes refresh; an admin-only visibility change does neither. The response always returns updated admin map state.

The admin PNG and arrow action endpoints honor admin visibility, never viewer visibility. Viewer images and exact image preview honor viewer visibility, never admin visibility. No viewer write endpoint or viewer-state schema change is needed. Hidden arrows cannot be used as admin click targets; direct wall-segment behavior is unchanged.


