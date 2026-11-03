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

### Help text reference

#### Players

Show to players makes this map the active player display.
Blank replaces the player display with a waiting screen.
Open exact player image opens the player rendering in a separate tab so you can check what is visible.

#### Fog and navigation

Select Reveal area or Hide area, then single-click inside a room to change its fog. Single-click actions wait 400 ms so they can be distinguished from double-clicks.
Double-click a revealed area to toggle player zoom without changing its fog. Clicks on doors and arrows take priority over area clicks.
Navigate the DM map:
Right-drag or hold Space and drag to pan.
Use the mouse wheel to zoom.
Press F to fit the map.

Shortcuts:
R — Reveal mode.
H — Hide mode.
Ctrl+Z — Undo the last fog action.

#### Door arrows

Single-click a door arrow to reveal through that doorway.
Double-click a locked door arrow to unlock it without revealing. Double-click an unlocked door arrow to lock it.
Reset restores the designed door states. Ctrl+Z undoes fog reveals, not door locking or unlocking.

#### Wall alignment

Use Alignment when the wall overlay does not line up with the map image.
Offset X / Y adjusts the horizontal and vertical position of the source walls.
Scale X / Y adjusts their horizontal and vertical size.
Use the arrow buttons for small position adjustments. Hold Shift for a 10-pixel nudge.

Select Apply alignment to save the alignment settings.
Check the overlay against recognisable features, such as room corners and doorways. If the walls match in one part of the image but drift elsewhere, check the scale as well as the position.
Coordinate conversion:
image coordinate = (source wall coordinate − offset) × scale
The offset is subtracted before scaling. Increasing an offset therefore moves the walls in the opposite direction along that axis.

#### Wall types

Show and Enabled serve different purposes:
Show controls whether a wall type is visible in the DM’s wall overlay. It does not change the fog boundaries.
Enabled controls whether a wall type is used when calculating fog boundaries. Select Apply wall types to apply changes to these settings.

Disabling a wall type does not delete its wall segments. You can enable them again later.
Ethereal walls never form fog boundaries. Whether doors divide the map into separate areas also depends on Doors split areas.

#### Map passages

Map passages connect locations on different maps—for example, stairs between dungeon floors.
Select Add passage endpoint to create an endpoint on the current map. Click an existing passage marker to edit it.
Marker letters identify the passage type:
S — Stairs
L — Ladder
H — Hole
P — Portal
C — Climb
X — Custom

A passage endpoint defines one end of a connection. Configure its destination to connect it to an endpoint on another map.
Creating or editing a passage does not move the players. Travel is a separate DM action.

#### Saved wall sources

##### Sources and wall sets

A saved source is a Foundry VTT or Universal VTT file stored for reuse within this campaign.
A source can contain one or more scenes. Each scene provides a separate wall set containing its walls and doors. Choose the wall set that matches the current map image.

##### Save and apply walls

Choose a supported file and select Save source. This saves the file to the campaign library; it does not change the current map.
Select the file under Saved source.
Select the matching scene under Wall set. Use its name, wall and door counts, and position in the source file to distinguish similar entries.
Choose your alignment option:Checked: Auto-align for this map calculates alignment for the current map image.
Unchecked: the map keeps its current offset and scale.

Select Apply selected wall set to replace the current map’s walls.
Check the wall overlay and player preview. If necessary, adjust the alignment under Walls → Alignment.

Selecting a source or wall set does not apply it. The map changes only when you select Apply selected wall set.

##### What applying changes

Applying a wall set replaces the current map’s existing walls. It does not merge wall sets, change other maps or modify the saved source.
The map image, Doors split areas setting and existing fog history are retained.
During play, blank the player display before applying a different wall set. Existing fog actions may reveal different areas when replayed against the replacement walls. Check the player preview and reset fog if necessary.

##### Reuse, refresh and delete

Reuse: select the same saved source on another map in this campaign without uploading it again. Saved sources remain available after a restart.
Refresh sources: reload the list of saved sources.
Delete source: remove the source from the campaign library. Walls already applied to maps remain unchanged.

Editing a map’s walls does not update the saved source. To use the source in another campaign, save the file in that campaign separately.

##### Supported files

Supported sources include Foundry scene or adventure JSON, legacy Foundry NeDB .db files, and Universal VTT .dd2vtt, .uvtt and .df2vtt files.
Foundry LevelDB directories cannot be uploaded directly; export the scene as JSON instead. A .db extension alone does not mean a file is supported—arbitrary SQLite databases are not wall sources.


#### Replace map image

Use Replace map image to replace the artwork for the current map.
Choose an image file, then select Upload.
After uploading, check that the walls line up with the new image and inspect the player preview before continuing play.

