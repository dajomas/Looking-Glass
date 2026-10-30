## Read-only viewer room zoom

`services/viewer_area.revealed_area_bounds` maps a displayed source-image point to the work mask using actual dimensions (including ceil-rounding). It requires currently visible mask pixels and a currently revealed component label, permits boundary snapping only to revealed labels, expands that component by the existing wall thickness, intersects it with the current revealed mask and returns its source-space bounding box. Hidden labels never produce bounds. Computation runs in a worker thread; only a bounding box for the clicked revealed region is returned.

The authorized read-only viewer endpoint binds requests to the active map's existing version, reads one database snapshot and checks the current map/version/permission again after computation. No schema or fog/lock mutation is introduced. The client continues to receive server-composited imagery, not raw maps or wall topology.

`viewer_area_zoom.js` provides pure source-to-viewer-image fitting, pose comparison (1 screen-pixel position tolerance and small relative scale tolerance) and filtered double-tap pairing. Fitting uses the same 90% viewport margin and existing PanZoom scale limits. `viewer_display.js` receives stationary tap coordinates from PanZoom, resolves a double tap via the read-only endpoint, and compares the actual camera with the returned room pose. Matching poses toggle to the existing all-revealed overview; nonmatching poses fit the selected room.

Request generations, displayed versions and visibility checks prevent late results from affecting newer navigation, switched/blanked maps or refreshed images. After live image updates, newly visible component signatures clear focus and return to overview. Without new areas, focus is revalidated and cleared if hidden. Viewer resize is owned by the display code, replacing that instance's unconditional PanZoom resize fit so it can refit a focused room. Fit/F clears focus and restores overview. Wheel/drag clears focus tracking; admin PanZoom code is untouched.

No Center/Fit admin preferences, arrow visibility changes, lock changes, migrations or new dependencies are part of this feature. Camera changes are tab-local; the new endpoint has no viewer write permission.


