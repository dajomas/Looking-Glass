## Viewer double-click room zoom

Double-click a revealed area on the viewer screen to zoom to that individual room/area and center it with a small margin. If that area's fitted camera position and zoom already match the current view, another double-click returns to the overview bounding all currently revealed areas and centers the visible battle map. Double-clicking a different revealed area switches focus to that area. If you have manually moved away from a room's fitted view, double-click first refits/recenters it rather than toggling out. With only one revealed room, room and overview framing can be identical.

The viewer Fit button and F shortcut always leave room focus and show the revealed-area overview. Dragging, wheel zoom and pinch still work normally. On touch screens, two stationary taps also work; taps must be within 400 ms and 12 screen pixels. Pan/Space-drag, pinch/multitouch, non-primary clicks, wheel zoom, pointer cancellation and window blur cannot complete an old tap pair. No admin fog/door gesture is changed.

Hidden/fogged areas and out-of-map clicks do nothing; the viewer cannot use zoom to reveal rooms or control locks. Eligible areas are the same calibrated raster rooms/components used by fog reveal, so incomplete walls or disabled door boundaries may make multiple rooms one zoom area. Click visible interior pixels for the most predictable selection; hidden open pixels near a dilated wall are still rejected.

A focused room is refitted on viewer resize. When a newly revealed area appears in a live update, room focus is cleared and the viewer fits/centers all visible areas. For other updates the focus point is revalidated: focus is retained if still visible, otherwise the viewer returns to the remaining revealed-area overview. Switching/blanking maps clears focus. A late lookup cannot override newer navigation or map state. Manual wheel/drag clears room-focus tracking; existing overview fitting on subsequent live refresh remains available. Camera state is local to this viewer tab, not a saved campaign preference or a change to other viewers.

This feature does not add the previously rolled-back Center/Fit admin toggles. Split admin/viewer arrow visibility and locked-door behavior remain unchanged.


