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
