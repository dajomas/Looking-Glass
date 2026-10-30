## Independent arrow visibility

Migration 9 adds `maps.viewer_door_arrows_enabled INTEGER NOT NULL DEFAULT 1 CHECK (... IN (0,1))`, then initializes it from existing `door_arrows_enabled`. The existing column becomes the admin flag; migration history 1-8 is unchanged. New maps default both on. Existing map preferences, colors, lock states and fog history remain intact.

`arrow_visibility.resolve_visibility` merges legacy shared and explicit per-screen partial updates with strict boolean handling. Management payload exposes both explicit aliases; the UI sends only the changed screen's field. Admin images and action hit geometry continue using `door_arrows_enabled`.

`MapSpec` includes viewer visibility in render identity. `viewer_image` uses a dataclass copy whose overlay flag is derived from the viewer preference; the caller's admin spec is never mutated. Its normalized viewer cache identity is independent of admin-only visibility. Old manually constructed specs without a viewer flag retain the former shared behavior; database specs always have the explicit viewer flag after migration.

Admin state/mask keys now include admin visibility, and polling compares both visibility fields. This permits admin-only updates without bumping fog version (and therefore without refreshing/recentering viewers). Viewer visibility/color changes still use the existing version/notification pipeline. Both color pickers remain usable while either display is enabled. Viewer JS/templates/API, wall rendering and lock-action code remain unchanged.


