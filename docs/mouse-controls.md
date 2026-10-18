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

The popup contains Endpoint 1 X/Y, Endpoint 2 X/Y, and all six wall types. Values
are map-image coordinates; mouse zoom and endpoint snapping do not rescale or
snap typed values. **Apply to draft** (or Enter in a coordinate field) makes one
undoable local edit; **Cancel** or Escape makes none. Tab and Shift+Tab stay
inside the modal, and viewport shortcuts do not run while it is open.

After applying, use Undo/Redo as usual. Save wall set persists changes; Download
UVTT includes unsaved draft edits without applying them to players. The existing
screen-pixel wall-width controls, fog controls and player display are unchanged.
See [wall-editor.md](wall-editor.md) for validation and save/boundary details.
