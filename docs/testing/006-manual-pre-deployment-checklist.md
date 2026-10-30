## Manual pre-deployment checklist

Use a copied campaign and at least one connected viewer:

- Map activation and fog: verify restore/reset choices, current exploration,
  Undo, blanking, map switching and cache isolation after deletion/reimport.
- Doors and passages: verify locked/unlocked clicks, discovery without revealing,
  reveal after unlock/discovery, reset to authored state, independent admin/viewer
  arrow preferences, and the portal/discovered-secret viewer exceptions. Confirm
  that undiscovered secrets and admin-only portal Exit hints remain hidden.
- Wall editing: verify Edit/right-click shortcuts, coordinate limits, Cancel/Apply,
  Undo/Redo, stale-save rejection, source assignment and UVTT export/import. Blank
  players before saving changed boundaries because fog operations replay against
  the new geometry.
- Portal configuration: verify compass side names, routing, incomplete-graph
  rejection, the overview, Apply without closing, Close/Escape discard scope,
  readable labels, route highlights and reduced-motion presentation.
- Viewer zoom: verify local room focus/overview, Fit/F, hidden-area no-op, admin
  double-click commands without admin camera movement or fog mutation, new-reveal
  overview behavior, resize and late-response handling. Test multiple viewers if
  they will be used during play.
- Cross-map travel: create one-way and return connections, inspect the Travel
  confirmation without executing it, verify Inspect destination leaves
  viewers and fog unchanged without a reveal-choice prompt, preserve existing exploration, test area arrival and
  large-reveal approval, reject a wall/out-of-bounds arrival, discover/reset a
  secret endpoint, reject stale preflight after another tab edits it, and show a
  broken link after deleting a target. Check marker/label persistence after restart.
- Access control: verify an unrelated DM and unassigned viewer cannot access the
  campaign, viewer clients cannot invoke admin mutations, and writes reject missing
  CSRF tokens. Confirm private passage destinations and DM notes are not exposed
  in player state or marker data.

