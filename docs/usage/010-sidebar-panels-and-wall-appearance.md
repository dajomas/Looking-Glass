## Sidebar panels and wall appearance

On the battle map screen, Players, Fog, Map passages, Walls, Saved wall sources
and Replace map image start closed. Map passages appears immediately above Walls.
These peer sections form an accordion: opening one closes any other open peer.
Wall legend and types starts open, is excluded from the accordion, and stays in
its manually selected open/closed state while other sections change. Alignment
starts closed inside Walls and is independent of the peer accordion; opening it
does not close Walls. These defaults are reapplied on page reload.
In the wall editor, Save and export below the tools is also collapsible and
starts expanded. Collapsing panels does not reset controls or discard edits.

Both editors have a Wall width slider (0.5–10 screen pixels), defaulting to the
battle map's existing 2-pixel base width. The preference is saved per map in
this browser and reused when opening either editor. Width stays constant while
zooming. Battle-map doors and secret doors retain their double-width styling.
This changes only the DM overlay, not fog boundary thickness, wall coordinates,
UVTT exports, or the player image. Sidebar open/closed state resets on reload.


