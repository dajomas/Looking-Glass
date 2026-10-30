## Portal phase helper and reviewed delayed-response CI (2026-10-30)

Run 41036469578 tested 33ccdbc4ed3b9c141ab7799fc53231ca0bd831fa; evidence was
reviewed at 101b7c83a177f1e0ad52afa935712727ad0a27ab. All seven delayed-response
viewer cases and the corrected wall-width test passed. Browser results were
168 passed and one failure in test_admin_highlight_phases_have_distinct_color_and_outline;
Python / HTTP, JavaScript, Live Uvicorn and Recovery jobs were green. Earlier
preparation-time pending statements above are historical. This run validates the
new client-side cases, but not the full workflow or unimplemented live scenarios.

The failing phase helper returned two polygons at 100 ms and none at 800 ms.
portal_cycle.render replaces overlay children, and readiness/busy changes clear
its route until arrows are ready. The admin fixture can yield before its scheduled
startup refresh finishes. This supplies a credible redraw window, not proof of
the precise original CI event sequence or a harmlessness guarantee.

The test-only helper now waits up to five seconds for two connected polygons,
a route ID, nonbusy rendering, decoded arrows and native portal animations. It
pauses/seeks and samples current nodes in one browser execution. Timeout diagnostics
record route, polygon count, status, busy flag and animation names. The phase API
still returns styles and all existing exact yellow/black, blue/white, opacity,
width and vector-effect assertions remain. No application JS/CSS is changed.

Screenshot sampling records polygon identities, route, mask and the current
triangle centroid/transform, then accepts a capture only if those identities and
paused animation time remain valid afterwards. A redraw invalidates that capture
and causes bounded resampling; incorrect colors do not trigger recapture and still
fail immediately against the unchanged +/-3 per-channel tolerance. Deriving the
interior point from the current polygon avoids obsolete route coordinates; the
original route rounds to the same point. Normal masking, pointer-event and no-POST
assertions remain. No fixed sleeps, whole-test retries, skips or color relaxation.

Focused actual Chromium 134.0.6998.35 validation passed: both native CSS phase
colors, recovery after an explicitly scheduled empty-overlay/redraw, one injected
replacement during screenshot capture (exactly two captures), the exact blue
interior pixel, and rejection of missing polygons or missing animations with
diagnostics. Helper syntax parsed. This used a minimal SVG/CSS fixture, not the
full application/admin fixture. The full repository phase test, other suites and
Python 3.14 hosted CI have not been executed for the candidate; acceptance remains
pending. README was reviewed and remains accurate. Workflow, fixtures, collector,
requirements and stored CI evidence are unchanged; broader application-test backlog
remains open as recorded above.

