# Passages

This is the current passage contract, including the clarified requirements for
commit a055343a921c0e6e234025744ea1269f2e4240fb. Viewer arrows are display-only:
there are no viewer passage click/double-click actions. Existing local viewer
room zoom is unchanged. Cross-map portals are out of scope.

## Doors and secret doors

- Doors work in both directions: an admin arrow single click reveals the adjacent
  area, even in Hide mode. The segment remains an area boundary.
- Locked/unlocked doors may start in either state. Admin double-click on an arrow
  toggles the state without revealing or hiding an area. Double-click on a wall
  segment does not change passage state. A locked arrow single click does nothing.
- Secret doors initially have admin-only purple arrows. Configure their
  post-discovery type (Door, Locked Door, Unlocked Door) in the wall editor's Edit
  dialog. Admin double-click on the arrow discovers without revealing an area.
- After discovery, a formerly secret door retains arrows, even when both adjacent
  areas are revealed. Each arrow still requires its own source area to be revealed.
- Viewer locked/unlocked arrows look like ordinary doors. No learned-lock state
  is implemented because viewer passage interaction is explicitly deferred.

## Portal pairs and sides

- A pair contains exactly two wall elements on one map: A and B.
- Each element has two sides, independently Entry, Exit, Both or None.
- At most one None side is allowed per element, not per pair.
- Both provides one independently routable Entry and one targetable Exit.
- Each Entry explicitly targets exactly one Exit-capable side of the other
  element. Same-element and self-routing are impossible. Multiple Entries may
  share an Exit. Every Exit requires at least one incoming Entry.
- Exit roles are ordinary, carry no lock/discovery state and are invisible on
  viewers. A Both side may display its Entry arrow on viewers.
- Entry state is independently normal, locked, unlocked or secret. A secret Entry
  has an authored post-discovery state. Discovering/locking one Entry never changes
  another Entry, including the other side of the same element.
- Admin single click on a usable Entry reveals the area behind the configured
  remote Exit, not the locally adjacent area. A revealed destination is a no-op.
- Admin arrow double-click discovers a secret Entry, or toggles a locked/unlocked
  Entry. It never also follows the portal.
- Entry arrows persist after destination reveal but require a revealed source.
  Admin Exit hints appear when an incoming Entry is shown, including locked and
  secret Entries; they may be drawn in fog and are not actionable.

## Appearance

| Entity | Default color | Wall dashed | Admin arrow | Viewer arrow |
|---|---|---|---|---|
| Door | Blue #46c0ff | No | Toward passage | Ordinary door |
| Locked Door | Orange #ff9f43 | Yes | Locked color | Ordinary door |
| Unlocked Door | Orange #ff9f43 | No | Regular door color | Ordinary door |
| Undiscovered Secret Door | Purple #b07cff | Yes | Yes | No |
| Portal Entry / Exit | Silver #c0c0c0 | No | Toward / away | Entry only |
| Portal Both | Silver #c0c0c0 | No | Double-headed | Double-headed Entry indicator |
| Locked Portal Entry | Brown #a66a3f | Yes | Yes | Ordinary silver Entry |
| Unlocked Portal Entry | Brown #a66a3f | No | Yes | Ordinary silver Entry |
| Undiscovered Secret Portal Entry | Red #ff5252 | No | Yes | No |

Existing per-map regular and locked door arrow color overrides are preserved.
Portal and secret arrow colors use the defaults above. Independent admin/viewer
arrow visibility settings continue to apply to all passage arrows.
Portal wall styling uses separate offset strokes for the two independently typed
sides, over a silver base segment.

## Authoring workflow

1. Draw two elements, or choose existing segments. The Portal element type may
   be used while drafting; an unpaired Portal cannot be saved/exported.
2. Choose Portal configuration. Select A and B, assign side roles, initial Entry
   states, secret post-discovery states and destination side numbers.
3. Apply pair to draft, then Save wall set. Configuration, removal and Undo/Redo
   operate atomically on the pair. Cancel/Escape makes no changes.
4. To change partners or delete/retype a paired element, use Remove pair first.
   Both elements become normal walls in one undoable operation. Coordinates stay.

Side labels are wall-number.side-number. For directed endpoints (x1,y1) to
(x2,y2), side 1 is minus the normal (-dy,dx), side 2 plus that normal, in image
coordinates (Y down). Reversing endpoints swaps their physical sides; routing
remains attached to the side number. Drawn labels make this visible. Geometric
sampling uses the midpoint; narrow rooms/gaps inherit the fog engine's raster
limitations. An unavailable source/destination open pixel produces no usable arrow.

## Runtime and safety

- Fog Undo undoes reveals/hides, not discovery or locks.
- Reset covers the map, restores authored lock states and makes secrets
  undiscovered again. Show-map Reset does the same. Undoing fog Reset does not
  restore discarded runtime states.
- Reloads, restarts and map switches using Restore retain runtime state.
- Saving/replacing walls clears state attached to replaced walls. Export/reuse
  stores authored configuration and pair routing only, never runtime state.
- Locks constrain passage controls, not a DM's manual reveal tools.
- Enabled/Doors split areas still control boundary participation. Disabling or
  altering boundaries may merge areas and expand existing reveals: blank players
  before boundary edits, save, inspect the exact viewer preview, then reset fog
  if needed. Show controls affect wall overlays, not passage arrow visibility.

Implementation/storage/API details: docs/api.md and docs/architecture.md.
Installation, rollback and verification: Patch/passages.md.
