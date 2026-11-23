# Improvement I2: wall endpoint drag (2026-11-23)

Requested 2026-11-22; the user answered the design questions on 2026-11-23:
joined corners move together (Alt detaches one wall), dragging works in every
tool, and paired portals can be dragged and keep their pairing. Delivered on
`features/claude`; acceptance pending.

## Implementation

- `static/js/pan_zoom.js`: optional `onDragStart(imageX, imageY, event)`. It is
  asked on a single-pointer press that would not already pan (not middle button,
  Space or multi-touch). A returned handler gets `move` once the pointer leaves
  the 5 px tap tolerance, then `end` on release; a stationary press is cancelled
  and still taps. `pointercancel`, a second pointer and `cancelDrag()` cancel it.
  The fog editor and viewer pass no hook, so their behaviour is unchanged.
- `static/js/admin_wall_editor.js`: a left mouse/pen press (no Ctrl/Meta, not
  touch) within 10 screen px of an endpoint claims the drag. Every wall with an
  end within 0.5 image px of the hit (at most one end per wall) moves together;
  Alt takes only the nearest end. While dragging, ends snap to other endpoints
  (never to the dragged ones) and clamp to the image. Release records one batch
  undo step; no movement records nothing; a zero-length wall is refused and the
  draft restored. Escape cancels; Ctrl/Cmd+Z is ignored during a drag. A pending
  Add start survives the move. Only coordinates change, so kinds, the passive
  flag and portal configuration (including `pair`) are preserved.
- Hovering an endpoint shows a grab cursor; dragging shows grabbing
  (`static/css/admin.css`). Cache-busting tags for the three changed assets in
  `web_html/admin/wall_editor.html` were bumped; the in-page help and
  `docs/usage/009-separate-wall-editor-and-uvtt-saving.md` describe the gesture.
- Not included: touch long-press dragging (one-finger touch keeps panning; the
  edit dialog remains the touch route).

## Tests

- `python/tests/test_pan_zoom_drag.js` (Node, 7 cases): no hook still pans;
  claimed press drags without panning or tapping; stationary press taps;
  unclaimed press pans; pointercancel and `cancelDrag()`; second pointer;
  middle button. All passed locally, and every existing JS test still passed.
- `python/tests/browser/test_wall_endpoint_drag.py` (Playwright): joined corner
  move and save, Alt detach, single-step undo/redo, Escape mid-drag, every tool,
  pan away from endpoints and click-on-endpoint keeps the Add tool, snap and
  clamp on release, zero-length refusal, hover cursor, paired portal keeps its
  pair. Not runnable in this workspace (no Playwright browsers); CI is the
  evidence.

## CI evidence

- Run 45135322868 (`9b2c2b6`) failed only in the new browser module: the 8 tests
  that turned snapping off timed out on `page.uncheck("#snap-ends")`, because the
  checkbox sits in a collapsed sidebar panel. The 4 tests that kept snapping on
  passed, as did every other suite. Fixed in `7049495` by setting the option
  directly; no product code changed.
- Run 45137161559 (`7049495`) succeeded with no failures, errors or skips;
  evidence published in `6ed80da`: Python/HTTP 1,993, browser 184 (previously
  172; all 12 endpoint-drag tests passed), JavaScript 36 (including
  `test_pan_zoom_drag.js`), live 18, recovery 6. Manual acceptance is pending.

## Manual acceptance and Alt fix (2026-11-23)

The user ran Runbook E (Claude doc): nine checks passed; E3 was partial because
Alt always detached the same wall wherever the pointer was. Cause: joined ends
share one point, so the "nearest endpoint" tie always resolved to the same
wall. Fix: with Alt, the joined wall whose line is nearest the pointer is
detached, so pressing slightly along a wall picks it. The browser test now
covers both walls of a corner. Help text, usage doc and the script's cache tag
(`endpoint-drag-2`) were updated. E3 needs to be re-checked.
CI run 45142306112 tested `1b6012d` and succeeded with no failures, errors or
skips (published in `b8da3a1`, without reader chunks): Python/HTTP 1,993,
browser 185 (both Alt cases passed), JavaScript 36, live 18, recovery 6.
