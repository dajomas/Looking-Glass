# Map controls update

The update retains dropdown selections, implements independent wall-type overlay
and boundary controls, hardens editor image/state loading, warns on offline
reveals, and centers player display framing on the union of revealed pixels.

The production blank-editor symptom was not reproduced against a live backend.
Tests exercise complete rendered editor markup, real image decoding, real SVG
paths and pan/zoom; they also inject a metadata failure and verify artwork remains
visible and Retry recovers walls. Clear diagnostics replace a silent empty page.
A genuinely missing image, authorization error, unrepaired schema or server crash
still needs its underlying cause corrected. This is not a database reset script.

Schema 4 is a new separate per-map settings table. It does not renumber or rerun
migration 3. Fresh databases and version-3 upgrades are covered by focused tests.
The previous schema collision's cache-token/checkpoint repair remains a prerequisite
for deployments that encountered it. Legacy disabled_wall_types is not deleted;
its values are used until overwritten intentionally by Apply wall types.

Show is local/browser-scoped and never changes server boundaries. Enabled changes
boundaries only after Apply, persists server-side and leaves raw segments intact.
Ethereal remains non-blocking; door categories also honor Doors split areas.
Replaying old fog operations after disabling walls can expose more area, so blank
players first. The user-requested immediate Apply behavior is preserved.

Viewer bounds are based only on the revealed mask. They add no hidden wall data.
All visible regions are framed together; the last-clicked room is not privileged.
Automatic framing occurs on each new map/fog version, while pan/zoom remains usable
between updates. Fully hidden maps use full-map framing.


## Door arrow controls and clicking

The fog panel has **Show door arrows (admin)** and **Show door arrows (viewer)** immediately above the color selectors. Both persist independently per map and default on for new maps; existing maps inherit their old shared setting on both screens. Colors remain saved when hidden. Hiding admin walls is independent.

A primary click/tap on an arrow in the admin fog editor reveals the room on the other side of that door, overriding Hide mode only for that click. Ctrl+Z undoes it. Right-click still invokes the normal inverse mode; drags/pinches pan/zoom and do not follow arrows. Only visible arrow pixels are clickable. While fog/arrow images load or a mutation is pending, taps are ignored. Viewer arrows are display-only so players cannot change fog. See `usage.md` for details.


## Locked and unlocked doors

The fog panel adds Locked door arrow color next to the regular arrow color. It is shared per map, defaults to orange `#ff9f43`, and follows the existing arrow enable toggle. Unlocked arrows use the regular arrow picker; both wall types stay orange (locked dashed, unlocked solid). Legend Show/Enabled rows include both new types. Runtime boundary participation follows the authored kind to keep lock/unlock from revealing extra areas. Reset restores authored states. The rolled-back viewer Center/Fit controls are not part of this patch.


## Per-screen arrow visibility

Admin and viewer arrow visibility are independent; Show walls is unchanged. The admin toggle hides the DM arrow overlay/hit targets, while the viewer toggle hides hints in the server-rendered player image and exact image preview. Regular, locked and unlocked arrows follow their screen flag together. Both color pickers stay usable whenever either flag is on. Reset does not reset visibility preferences, and direct door wall interactions are unchanged.


## Viewer area zoom and overview

The viewer's double-click gesture focuses one revealed room, or toggles back to all revealed bounds if that room is already fitted/centered. Fit/F always selects overview. This is a local camera operation, not an admin Center/Fit toggle and not a reveal action. Viewer arrow visibility and admin arrow/door interaction controls remain independent and unchanged.


## Remote viewer camera from admin

Double-click a revealed area in the admin fog editor to toggle room focus/all-revealed overview in connected viewer screens, not in admin. Door/arrow gestures take priority. Ordinary primary area singles wait 400 ms; right-click mode inversion stays immediate. The map must already be live, and hidden areas do not send a camera command. Viewer-local double-click remains unchanged. No new Center/Fit toggles or persistent camera preferences are introduced.
