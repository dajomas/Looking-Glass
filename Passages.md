# Passages

Current contract after the portal-section editor follow-up to development commit
eb882f37308c624e4fe550ab6a05c0e3ec4fc14b. Runtime passage behavior is unchanged;
this follow-up changes authoring only. Viewer arrows remain display-only. No
cross-map portals, token movement or viewer passage mutation endpoints are added.

## Doors and secret doors

Doors work in both directions. Admin single-click on a usable arrow reveals the
adjacent destination even in Hide mode; the door remains a fog-area boundary.
Locked/unlocked doors can start in either state. Only admin arrow double-click
toggles state; it never also reveals/hides fog. Locked singles do nothing.

Secret doors have admin-only purple hints until discovered. Their post-discovery
type is configured in the wall editor: Door, Locked Door or Unlocked Door. Admin
arrow double-click discovers without revealing. A formerly secret door keeps
arrows after both areas are revealed, but each source area must itself be revealed.
Viewer locked/unlocked hints look ordinary; there is no learned-lock state.

## Portal sections, pairs and sides

- Each pair contains exactly two Portal wall elements on the same map.
- Each element has two sides: Entry, Exit, Both or None. At most one None per
  element is allowed in a complete configuration. Both has independent roles.
- Every Entry explicitly chooses one Exit-capable side of the other element.
  Self/same-element routing is prohibited. Shared Exits are allowed; every Exit
  needs at least one incoming Entry. A pair cannot route to a third element.
- Each Entry independently starts ordinary, locked, unlocked or secret. Secret
  Entries have authored post-discovery types. Discovery or locking affects only
  that Entry. Exit roles are always ordinary and invisible on viewers.
- Admin single-click on an ordinary/unlocked Entry reveals the area behind the
  remote Exit, not the locally adjacent area. Revealed destinations are no-ops.
- Only admin arrow double-click discovers/toggles state, without revealing.
- Portal Entry arrows persist after destination reveal, but their source area
  must be revealed. Admin-only Exit hints appear when an incoming Entry is shown,
  including secret/locked Entries. Exit hints may appear in fog and never act.
- Viewers never follow passages. They see Entry hints only; Both can show a
  double-headed Entry indicator. Undiscovered secret Entries are hidden.

## Portal configuration popup

1. Draw or convert Portal elements. Both sides start Unconfigured, not Entry/Exit.
2. Select one Portal section in the popup and edit only its two sides. All element
   dropdowns contain Portal elements only; ordinary walls/doors are excluded.
3. When configuring a side, the opposite side defaults to None if and only if it
   was still Unconfigured. Already configured sides are never overwritten by this
   default. Unconfigured is a temporary draft state, not a fifth saved role.
4. Entry/Both sides expose destination Portal-section and Exit-side selectors.
   Choose Exit/Both on the other element, or select an Unconfigured side whose
   label explicitly says it will become Exit on Apply. An untouched opposite side
   on that target defaults to None. Explicit None/Entry-only sides are not valid
   Exit targets; configure them first. Shared Exits remain allowed.
5. Switching selected section retains pending popup edits. Apply configuration to
   draft commits all edits atomically, including target initialization. Cancel or
   Escape changes nothing. No popup action autosaves to the server.
6. Apply may stage incomplete sections while the rest are configured. Save and
   Download require all portal sections/graphs to be complete, with valid pairs,
   destinations, incoming Entry coverage and the per-element None limit. Client
   preflight and existing server validation both enforce the complete contract.
7. Reset section / unpair resets a section and its partner together to two
   Unconfigured Portal elements. Coordinates and Portal type are preserved.
   Reset is pending until Apply and then undoable; re-pair or remove/retype afterward.

Side labels are wall-number.side-number. For directed endpoints, normal=(-dy,dx):
side 1 is minus normal, side 2 plus normal, in image coordinates with Y down.
Reversing endpoints swaps physical sides without changing side indices. Midpoint
sampling and narrow-room/gap limitations are unchanged; an unusable destination
open pixel yields no actionable arrow. Graph validity is not geometric room validity.

## Appearance

| Entity | Default color | Wall dashed | Admin arrow | Viewer arrow |
|---|---|---|---|---|
| Door | Blue #46c0ff | No | Toward passage | Ordinary door |
| Locked Door | Orange #ff9f43 | Yes | Locked color | Ordinary door |
| Unlocked Door | Orange #ff9f43 | No | Regular door color | Ordinary door |
| Undiscovered Secret Door | Purple #b07cff | Yes | Yes | No |
| Portal Entry / Exit | Silver #c0c0c0 | No | Toward / away | Entry only |
| Portal Both | Silver #c0c0c0 | No | Double-headed | Double-headed Entry |
| Locked Portal Entry | Brown #a66a3f | Yes | Yes | Ordinary silver Entry |
| Unlocked Portal Entry | Brown #a66a3f | No | Yes | Ordinary silver Entry |
| Undiscovered Secret Portal Entry | Red #ff5252 | No | Yes | No |

Existing per-map regular/locked door arrow color overrides and independent
admin/viewer arrow visibility preferences are preserved. Portal strokes remain
per-side over the silver segment; Unconfigured draft sides have no category stroke.

## Runtime, export and safety (unchanged)

Fog Undo changes reveal/hide history, not discovery/locks. Reset covers the map,
restores authored states and hides secrets; Show-map Reset does the same. Undoing
fog Reset does not restore discarded runtime overrides. Reload/restart/Restore
retains state. Replacing/saving walls clears state on replaced wall IDs.
UVTT extension v2 stores complete authored configuration only, never temporary
draft state or runtime overrides; ordinary v1 files remain supported. Standard
UVTT fallback represents teleport elements as opaque boundaries and loses routing.

Locks constrain passage controls, not the DM's manual reveal tools. Enabled and
Doors split areas control boundaries. Changing boundaries can merge areas and
expand existing reveals: blank viewers before editing, save, inspect the exact
viewer preview and reset fog if needed. Show controls affect wall overlays, not
passage-arrow visibility. Permission/CSRF/stale-save/runtime behavior is unchanged.

See docs/wall-editor.md for editing, docs/api.md and docs/architecture.md for the
unchanged saved schema, Patch/passages.md for the original passage migration and
Patch/portal-section-editor.md for this follow-up's installation and verification.
