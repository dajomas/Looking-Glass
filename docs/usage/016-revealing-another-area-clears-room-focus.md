## Revealing another area clears room focus

If a viewer is focused on one room, revealing another area returns it to the overview of all currently revealed areas and centers that visible portion of the battle map. It works for focus created by either a viewer-local double-click or an admin remote double-click. Reveal all, an arrow revealing a destination, re-revealing a hidden room and Undo of a hide also reset focus when they make an additional area visible.

The new area need not expand the outer visible bounding box. Replacing one visible area with another between displayed states is also detected, even when the visible area count stays equal. Repeating Reveal on an already revealed room does not reset focus. Arrow visibility, color and lock/unlock-only changes keep room focus when area geometry/visibility is unchanged. Hiding another room alone also preserves focus; hiding the focused room still falls back to overview through existing validation.

After the overview reset, a fresh explicit admin/viewer zoom can focus a room again. Old in-flight area lookups cannot restore the discarded focus. The viewer applies the reset with the newly decoded map image; a newly visible area inside unchanged overview bounds still triggers it. Detection compares the last displayed state with the next displayed state, rather than replaying transient states that never reached the viewer.

Areas follow the fog engine's raster room components. Changing wall geometry/calibration or boundary settings can change those components' footprints and may reset focus as newly represented visible areas. Routine lock/unlock keeps those footprints unchanged. Existing manual pan/zoom, overview behavior, Fit/F and both double-click paths are otherwise unchanged. Reload viewer tabs after the upgrade.

