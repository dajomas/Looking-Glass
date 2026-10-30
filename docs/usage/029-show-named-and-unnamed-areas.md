## Show named and unnamed areas

With Select room (fog unchanged) checked, a Show named / unnamed areas button
appears directly below it. Click to show a translucent green tint for areas with
saved names and red for unnamed areas, plus a text legend/counts. Click again to
hide the overlay. It starts off on page load. Unchecking Select room removes the
colours and hides the button; rechecking reveals the button with the overlay off.
The checkbox and its button remain accessible during note editing so the overview
can be toggled while the amber edit marker remains on top.

Classification uses saved names only: whitespace-only or missing names count as
unnamed, even if notes exist. A saved name turns its current matching area green;
saving a cleared name turns it red. Draft text does not change colours until saved.
Colours cover both hidden and revealed areas, are local to the admin page, and do
not alter fog, player images, undo history or metadata. Map pan/zoom moves the
colours with the artwork. Wall pixels stay transparent.

Areas follow the fog engine's connected-region boundaries, including exterior
open regions if present. Counts are detected areas, not imported-note entries.
A detached old room record whose saved geometry no longer matches does not name
a different current area. The overlay reloads after successful room saves and
geometry changes. To see another admin session's metadata changes, hide/show the
overview again. Removing the overview leaves the original map/fog display intact.

