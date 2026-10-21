# Admin map mouse controls

| Selected mode | Left click/tap | Stationary right-click |
|---|---|---|
| Reveal area | Reveal area | Hide area |
| Hide area | Hide area | Reveal area |

A right-click uses the opposite action for that click only. The mode radio button
is not changed. The action targets the same wall-bounded room and uses the same
server endpoint, fog history, Undo, active-map warning and viewer notification
paths as the equivalent left-click action.

## Pan versus edit

Right-drag still pans. Movement beyond the existing 5-pixel pointer threshold
cancels the click action, so releasing a right-drag does not reveal/hide a room.
Space-drag and middle-button panning remain available. A tiny movement within the
click tolerance is still a click. Pointer cancellation and multi-pointer gestures
do not edit fog. Primary touch taps retain the selected mode.

The browser context menu is suppressed within the map viewport, as before.
Secondary taps are opt-in to the admin editor's PanZoom instance; the shared
viewer PanZoom retains its previous behavior and does not emit right-click taps.
No Apply confirmation, map selection policy or boundary settings are changed.

## Startup refresh after artwork

The reported Blank workaround is useful evidence: Blank changes active display
state and then fetches/renders the admin map payload again. That observation
alone does not establish a precise cache, rendering or backend failure.

The editor now schedules one additional metadata/render refresh after its first
artwork load, waiting for an existing UI operation to finish. This uses the same
non-mutating state GET/render path without requesting Blank or any activation
change. It can also recover from a failed initial metadata request. It does not
loop on every image update or automatically reset reveals. Existing explicit
load errors and Retry loading map remain available for persistent failures.

Deployment changes JavaScript and documentation only. No schema migration or
server route is added. Hard-reload the admin page after deploying both changed
scripts together. If artwork/state still fail, retain the visible error and
inspect the server log; the exact production cause has not been proven.

## Dedicated wall editor: Edit tool

These controls apply to the separate wall editor, not to fog Reveal/Hide modes.
Choose **Edit** in the Tool menu, then left-click/tap within 10 screen pixels of
an existing segment to open its endpoint/type dialog. Alternatively, a stationary
**right-click** or **Ctrl+left-click** within the same tolerance opens that dialog
from any tool, without
changing the selected tool or running Add/Remove/Change-type. The nearest segment
wins; zoom in to distinguish overlapping lines. Right-drag still pans rather
than opening the dialog; Ctrl+left-drag also pans rather than opening it. Browser
context menus are suppressed in both the map viewport and the endpoint/type
popup, including contextmenu events delivered after the popup has opened. Browser
menus outside those areas are not disabled. Opening the dialog cancels a pending
Add-wall start; either shortcut on empty space preserves it. Unmodified primary
clicks and touch taps retain the selected tool's behavior.

The popup contains Endpoint 1 X/Y, Endpoint 2 X/Y, and all nine wall types. Values
are map-image coordinates; mouse zoom and endpoint snapping do not rescale or
snap typed values. Coordinates outside the image are clamped to its edge when
applying; existing outside endpoints are shown at the edge when opening Edit. **Apply to draft** (or Enter in a coordinate field) makes one
undoable local edit; **Cancel** or Escape makes none. Tab and Shift+Tab stay
inside the modal, and viewport shortcuts do not run while it is open.

After applying, use Undo/Redo as usual. Save wall set persists changes; Download
UVTT includes unsaved draft edits without applying them to players. The existing
screen-pixel wall-width controls, fog controls and player display are unchanged.
See [wall-editor.md](wall-editor.md) for validation and save/boundary details.

## Dedicated wall editor: clicks outside the artwork

In Add wall mode, clicking outside the image (within the viewport) places the
pending dot at the nearest image edge/corner. Both endpoints are clamped to
X = 0..image width and Y = 0..image height, including when endpoint snapping is
on. Panning or zooming never changes these bounds into browser-window bounds.

Edit, right-click and Ctrl+left-click may select a visible imported wall outside
the image. The dialog shows bounded coordinates, but Apply is still required to
change the draft. Typed outside values are also clamped on Apply. Cancel/Escape
leaves the original coordinates unchanged; Undo restores a corrected wall.
If clamping would make both endpoints coincide, no edit is applied.


## Clicking door arrows

On the admin fog editor, left-click or tap a visible enabled door arrow to reveal its adjacent hidden room. The pointer cursor indicates a hit. This takes precedence over the current Hide mode without changing the selected mode; Ctrl+Z undoes it as an ordinary reveal. Right-click remains the inverse of the selected fog mode. Pan/zoom drags, Space-drag and pinch gestures retain their existing behavior. Transparent arrow-image pixels are not clickable. Viewer screens remain read-only.


## Locked and unlocked doors

Admin arrow single-click reveals an ordinary/unlocked passage destination.
Locked/secret singles do nothing. Arrow double-click toggles a locked/unlocked
passage or discovers a secret using its authored outcome. Segment double-click
does not change passage state. Portal targets are remote configured Exits; their
source must be revealed. Exit-only hints are not actionable. Managed singles wait
400 ms; side IDs distinguish portal Entries. Viewer arrows have no passage
click/double-click action; existing room-focus navigation remains. See ../Passages.md.

## Viewer double-click area focus

Viewer only: double primary click a revealed room/area to fit and center it; double-click again at its fitted/centered pose to return to all revealed areas. A different room becomes the new focus. The decision uses actual camera position/zoom, not just a remembered focus flag, so manually achieved matching poses toggle out too. Fit/F always returns to overview. Hidden areas do not respond. Two stationary touch taps use a 400-ms/12-screen-pixel pairing window; drag, Space-drag, pinch/multitouch, wheel, non-primary clicks and cancellation/blur invalidate pending gestures. No fog/door state is modified.


## Admin area double-click -> viewer camera

Admin ordinary area single primary click/tap: selected reveal/hide action after 400 ms. Two nearby clicks/taps within that time: cancel that single and toggle room focus/overview in connected viewers instead; no admin camera movement or fog change. Hidden areas are ignored for double-click zoom. Right-click inverse fog mode is still immediate. Door/arrow gestures keep their existing priority and meaning. Pan, Space-drag, pinch/multitouch, wheel/zoom, cancellations, mode/state changes and blur cancel pending area singles. Viewer-local double-click behavior remains unchanged.
