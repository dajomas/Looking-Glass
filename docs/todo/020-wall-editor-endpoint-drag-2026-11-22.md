# I2. Wall editor: move endpoints by left-button drag (2026-11-22)

- [x] Accepted and closed on 2026-11-23 by explicit user instruction after manual acceptance (Runbook E: all ten checks PASS, E3 after the Alt fix in `1b6012d`); see handover record 104.
- Decisions (user, 2026-11-23): joined corners move together (Alt detaches one wall);
  dragging works in every tool; paired portals can be dragged and keep their pairing.
- Status (original): open improvement, requested by the user on 2026-11-22. Not a bug.
- Request: in the wall editor, allow moving a wall endpoint by pressing the
  left mouse button on it, dragging, and releasing at the new position.

## Current behaviour (`static/js/admin_wall_editor.js`, 2026-11-22)

- Left click places walls with the Add tool (two clicks) or applies the
  Edit/Remove/retype tools to the nearest wall within 10 screen pixels.
- Endpoints can only be moved through the edit dialog's coordinate fields,
  opened by right-click or Ctrl+left-click.
- `PanZoom` handles drags, so a left-button drag currently pans the view;
  `onTap` only receives clicks.
- "Snap ends" snaps new points to existing endpoints within 10 screen pixels.
- Changes go through `mutate()`, giving undo/redo and the unsaved-changes state;
  points are clamped to the image by `imagePoint()`.

## Proposed behaviour

- A left-button press within 10 screen pixels of an endpoint starts an endpoint
  drag instead of a pan; a press anywhere else still pans. Show a hover/grab
  cursor on draggable endpoints.
- While dragging, render the wall live; on release, apply "Snap ends" and the
  image clamp, then record ONE undoable change (Ctrl+Z restores the original).
- Escape during a drag cancels and restores the original position. A drag that
  ends where it started records nothing.
- Reject a release that would make both endpoints of a wall equal, with the
  existing "endpoints must differ" message.
- Touch: consider a long-press to start an endpoint drag so one-finger panning
  keeps working.

## Open questions for the user

1. When several walls share the dragged endpoint (a corner), move all of them
   together, or only the nearest wall? Moving all keeps rooms closed; a modifier
   key (for example Alt) could detach one wall.
2. Should dragging work in every tool, or only in Add/Edit?
3. Portal elements: allow dragging, or require Portal configuration as for
   delete/retype of paired portals?

## Regression

- Browser tests (Playwright): drag an endpoint and save; the saved walls change
  only at that endpoint; undo/redo restores and reapplies it; Escape cancels;
  a drag starting away from endpoints still pans; snap-to-endpoint and image
  clamp apply on release; a zero-length result is rejected.
- Fog after save: rooms re-detect from the moved walls, matching an edit made
  through the coordinate dialog.
