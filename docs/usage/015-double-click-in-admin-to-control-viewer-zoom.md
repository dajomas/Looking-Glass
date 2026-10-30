## Double-click in admin to control viewer zoom

Double primary click/tap a revealed area of the admin fog map to send a camera command to all currently connected viewers for that campaign. Each viewer uses its existing behavior: if the selected room is already fitted and centered in that viewer, show the all-revealed overview; otherwise fit and center the room. The admin viewport never moves as part of this command. Different viewers may toggle differently if their current local camera poses differ.

Viewer-local double-click, Fit/F, drag, wheel, pinch and resize behavior remain available. A local viewer double-click still changes only that tab. A viewer fetches the current authorized area bounds before applying an admin command; stale, duplicate, wrong-map and superseded commands are ignored. Newer local navigation cancels a pending camera lookup.

To separate area double-clicks from fog actions, ordinary primary single-clicks now wait 400 ms. A nearby second click within that interval cancels the pending single and sends zoom instead—even in Hide mode—so the gesture does not reveal/hide a room first. The double-click tolerance is 12 screen pixels. Right-click inverse fog actions remain immediate. Another target, state/mode change, mutation, camera movement, drag, pinch, pointer cancellation, keyboard/resize or window blur cancels pending area work rather than allowing a delayed fog action.

Regular arrows and managed door/arrow gestures take priority and are not reinterpreted as area zoom: regular arrow reveal, locked-arrow double-click unlock and unlocked-arrow double-click lock remain unchanged. A hidden-area double-click sends no zoom and does not fall back to revealing it; use a single click to reveal normally. The selected map must already be active on viewers—this action never activates or switches maps automatically.

Commands use live WebSockets and are ephemeral, not stored camera preferences. The admin reports when no viewer screens are connected. Disconnected or not-yet-opened screens do not replay old zoom commands; issue the double-click again after reconnecting. The success toast counts subscribed screens, not confirmed camera acknowledgments. Reload both admin and viewer tabs after installing this update. Camera commands do not change fog operations, locks, checkpoints, versions, arrow visibility or the database.


