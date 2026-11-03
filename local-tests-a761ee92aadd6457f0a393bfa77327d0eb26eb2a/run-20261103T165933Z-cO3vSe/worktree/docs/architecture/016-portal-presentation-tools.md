## Portal presentation tools

services/portal_presentation.py joins already generated admin arrow polygons to
their authored opposite-element Exit references. It emits admin-only route IDs,
side/section/compass labels, effective Entry state and existing endpoint polygons.
It neither renders new server hints nor changes cache identity, fog topology,
hit resolution, runtime state or viewer payloads. Disabled/fogged sources have no
arrow object and hence no route item. Actual Exit geometry is required; shared
and Both endpoints are matched by wall ID and side.

static/js/floating_dialog.js moves native dialogs with captured pointer events or
keyboard arrows and clamps their positions on resize. portal_overview.js derives
a read-only grid from authored rows and optional popup links, using safe textContent
cells. portal_editor.js supplies pending versus current-draft snapshots.

portal_cycle.js separates a testable clock-driven Cycle from DOM rendering. The
admin editor holds it inactive until the matching raster arrow image has decoded;
new versions clear old highlights. The SVG overlay shares work coordinates and is
masked by the exact admin arrow alpha, with pointer-events:none. Viewport filtering,
busy/visibility changes, pause and page lifecycle events stop/restart the single
owned timer. Dwell is 1–15 s (default 5), pulse period one second. Reduced motion
uses steady polygons. Preferences are localStorage scoped by map, with validated
fallback defaults and graceful failure if storage is blocked. No schema migration
or new viewer capability is introduced.


