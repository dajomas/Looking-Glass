## Double Reveal fog shortcuts and badges

The admin template mounts a pointer-transparent marker layer and a compact legend.
double_reveal_markers.js draws amber 2 / cyan ↗ badges at saved image-space room points,
excludes invalid geometry and true rooms without destinations, and compensates for zoom
scale. It never performs hit tests or mounts in viewer templates.

The fog click router reserves Ctrl-primary before doors, transitions and delayed fog/zoom
dispatch, cancelling both gesture queues without fallthrough. Explicit selection modes
keep priority. PanZoom still filters drags and multi-pointer input. quickAction executes
inside the editor run() busy lock, without nested run/mutate. It reads the room endpoint,
checks displayed revision/stamps against fresh state and performs exactly one existing
appearance or travel request. A 600 ms post-reveal guard prevents accidental rapid travel.
Travel keeps confirmation, visibility/active-map checks, authorization and optimistic
concurrency. No schema, API or dependency changes are introduced.

The cumulative usability fixes include native wrapping checkboxes, Done, panel/tool exit
paths and room-note change events, with no redundant fog-mode description.
