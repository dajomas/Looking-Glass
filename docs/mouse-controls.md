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
