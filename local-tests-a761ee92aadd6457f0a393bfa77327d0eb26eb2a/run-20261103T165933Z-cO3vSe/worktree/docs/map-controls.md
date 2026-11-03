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


## Automatic overview after new reveals

A newly visible area clears viewer room focus and returns to the all-revealed overview, whether focus was chosen in admin or viewer. No extra toggle is needed. This checks actual revealed-area membership, so color, arrow visibility and lock changes alone do not reset focus. Double-click can focus again after the reset; Fit/F and all admin door gestures retain their behavior.

## Passage controls

Portal configuration lives in the wall editor, separate from coordinate Edit.
The fog-editor legend includes Portal Show/Enabled controls. Portal type strokes
are silver, brown for locked/unlocked Entries, red for undiscovered secret Entries;
secret door strokes remain purple dashed. Only arrow double-click changes runtime
locks/discovery. Hiding admin arrows disables those actions; segment double-click
is not a substitute. Viewers remain read-only and see no Exit-only or undiscovered
secret hints. See [passages](Passages.md) for current behavior and
[deployment](deployment.md) for upgrade instructions; this supersedes earlier
segment-double-click descriptions.

## Admin portal pair highlighting

Cycle visible Entry/Exit pairs enables admin-only highlights over the two arrows
of each qualifying directed route. A complete 1.2-second cycle alternates bright
yellow (#ffea00) with black outlines and deep blue (#1538d0) with white outlines.
Both phases are full opacity, with 4-screen-pixel outlines and a light/dark halo.
The slider sets 1–15 seconds per route (default 5); it does not change color cadence. Both endpoint polygons must intersect
the viewport and at least two routes must qualify. Pan/zoom updates the set. Each
incoming Entry gets a turn even when several share an Exit; Both uses its displayed
arrow polygon. The status line names the current sections and compass sides.

Uncheck to pause. Dwell/enabled settings are browser-local per map, not server
settings. Loading/mutations, hidden tabs, disabled arrows or an insufficient visible
route set clear the highlight and cancel its timer. Exact raster arrow alpha clips
the presentation overlay; it has pointer-events:none. Normal arrows remain present
and clickable throughout, and the viewer image is never animated. Reduced motion
uses a steady full-opacity yellow/black-outline highlight. Route selection still
advances at the chosen dwell. See [passages](Passages.md) for route selection and
[wall editing](wall-editor.md) for label and highlight presentation.


## Viewer portal and discovered-secret arrow exceptions

When **Show door arrows (viewer)** is unchecked, two indented controls appear:

- **Show portal arrows (viewer)**: show eligible portal entry/Both arrows, including discovered secret portal entries.
- **Show secret arrows (viewer)**: show eligible arrows with a secret origin after discovery, including secret-origin portal entries.

The categories form a union: either matching option is sufficient. An entry whose current state is `secret` is always hidden from players, regardless of all three toggles. Ordinary doors remain hidden when the main toggle is off. Existing revealed-area, blocking-wall, source-side, and doors-split-areas rules still apply; these options never reveal fog or display admin-only exit hints.

The main viewer toggle retains its previous all-eligible-arrows behavior when enabled. Exception choices are saved per map, retained while the main toggle is on, and default to off for both existing and new maps. The admin arrow toggle is independent. Changes are saved immediately and notify connected viewers.


## Cross-map passage controls

Map passages is a separate sidebar panel, not a wall type. Add passage endpoint arms
placement; the next left-click opens the endpoint dialog. Escape cancels. Click a
marker/sidebar entry to edit. Pick / move location on map preserves the dialog draft
until Save; coordinates refer to the original image. Ordinary marker clicks do not
perform fog actions or travel. Right-drag and zoom remain map navigation controls.

Travel… uses saved configuration and requires the source map to be
active. Inspect destination opens the saved destination in admin only and does
not activate viewers, change fog or show Restore/Reset. Travel remains the separate
passage action.
Create destination endpoint opens the selected map in a new tab; save there, then
Reload destinations in the source dialog. Reverse links are explicit and independent.
Show map passage markers (viewer) and Show passage labels (viewer) are unrelated to
door/portal arrow toggles. Reset passage session states is independent of fog reset.
See docs/usage.md for the complete workflow, secrecy and arrival-reveal rules.


### Sidebar section defaults

Map passages is immediately above Walls. Players, Fog, Map passages, Walls, Saved
wall sources and Replace map image start closed and act as a peer accordion. The
wall legend starts open but is never automatically closed/reopened by other panels;
manual closing is respected until page reload. Nested Alignment is not a peer and
can open while Walls stays open. Wall-editor panels on the separate wall-editor
page are unaffected. Passage main actions stay in a fixed modal footer while only
the form body scrolls.


### Independent passage saves

The pinned footer's Save configuration and Update session state actions save only
their corresponding field groups. Both keep the modal open and preserve pending
edits in the other group. Each group has its own unsaved-status indicator. Save a
new endpoint before updating its session state. Close/Escape confirm discard if
needed; already saved changes remain saved. Travel asks when it would use saved
values instead of pending edits. See [usage](usage.md) for full scope semantics.


### Travel return and reset scope

Travel… opens a confirmation with a destination-specific final Travel label.
Back to passage or Escape returns to the original passage form with its pending
configuration/session edits, dirty statuses and scroll intact. It sends no trip or
fog mutation. Cancellation is disabled during an in-flight trip request. The normal
Show battle map dialog labels its destructive choice Reset fog and show map and
explains permanent history removal plus wall-door/wall-passage state reset; it does
not reset independent cross-map endpoint overrides. This activation reset is not the
same operation as the fog panel's existing Reset or the endpoint session reset.

## Collapsible map-editor help

The left sidebar’s `? Help` control contains eight independent help topics:
Players; Fog and navigation; Door arrows; Wall alignment; Wall types; Map
passages; Saved wall sources; and Replace map image. Help and every topic start
collapsed on each page load. Expand a heading with a pointer or Tab followed by
Enter/Space. Multiple topics can remain open, independently of the editor’s
control-panel accordion. Expansion state is not persisted across reloads.

Saved wall sources contains five further collapsed subsections: Sources and
wall sets; Save and apply walls; What applying changes; Reuse, refresh and
delete; Supported files. Closing a parent hides its children without resetting
their open state until the page is reloaded.

For a campaign with one map, Map passages and its help topic are hidden; the
other seven help topics remain available. With two or more maps, all eight are
shown. Reload the editor after changing the campaign’s map count. This changes
presentation only, not saved endpoints or passage APIs.

Static sidebar instructions live in Help. Live errors, warnings, counts and
statuses stay beside their controls; action-specific modal guidance is unchanged.

## Help background styling

Help uses lighter blue-grey surfaces than the regular sidebar so instructions
are visually distinct from operational controls. The outer `? Help` container is
`#263143`, main topic cards are `#303e53`, and nested Saved wall sources cards
are `#3a4a61`. Hover and keyboard focus use `#435570`; keyboard focus also keeps
an accent outline. The regular sidebar remains `var(--bg-2)` (`#1a202c` in the
default theme). Help text retains `var(--text)`.

These styles apply only inside `#editor-help`. They affect both collapsed
headings and expanded content without changing disclosure behavior: all help
topics/subtopics still start closed and open independently. Regular feature
panels, dialogs, map and viewer are unchanged.

After deploying this CSS-only follow-up, hard-refresh the admin page to bypass
cached `admin.css`. No template, JavaScript or database changes are required.

## Double-reveal controls

The fog editor's **Double reveal** disclosure contains alternate-image upload and DM-only
preview links, a non-mutating room-selection mode, per-room enable/destination settings,
explicit true/initial appearance actions, and independent appearance Undo. The selected
room is highlighted; configured rooms are listed with their current appearance. Invalidated
geometry is marked inactive and can be removed before reconfiguration.

The normal Reveal/Hide modes and fog Undo/Ctrl+Z retain their behavior. Turn double-reveal
selection off to use normal fog and door clicks. With selection enabled, clicking a room
selects it only; it never automatically reveals truth or switches maps. A separate confirmed
**Open destination map** action is available only for a visible true room on the active map.
No player-facing travel control is added.


## Double Reveal markers

Amber 2 marks configured rooms awaiting true artwork; cyan ↗ marks true rooms with an
assigned destination. Ctrl-left-click anywhere inside the room performs the marked
action. The second reveal does not automatically travel. A later click asks for travel
confirmation, requiring visible source fog and the active player map. Badges stay
screen-sized on zoom, use the saved selection point, and never appear on player screens.
Invalid geometry has no badge. Hidden-room artwork may be prepared without revealing fog.
See docs/usage.md for stale-state handling and the 600 ms rapid-tap guard.
