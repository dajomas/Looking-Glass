## Double-reveal rooms

### Prepare the artwork

1. Open a map's fog editor and expand **Double reveal**.
2. Upload an alternate full-map image. Its normalized pixel dimensions must exactly match
   the original, with the same scale, alignment and room boundaries. Alignment itself is a
   preparation responsibility; matching dimensions cannot prove artwork alignment.
3. Use **Preview initial** and **Preview true** to inspect the two complete artworks in
   separate DM-only tabs. These reads never change fog, appearance, or the player display.
4. Enable **Select double-reveal room (fog unchanged)** and click inside a room. The selected
   room is highlighted. Enable double reveal, optionally choose another map in this campaign,
   and save. Repeat only for rooms that should have a second appearance.
5. Press **Done — return to fog** to stop selection, remove its highlight and open Fog
   with the previous tool focused. This also disables room-note selection. Unchecking
   selection, closing Double reveal, choosing a fog tool or R/H outside form fields
   also exits Double Reveal selection. Selecting room notes turns off double-reveal
   selection, and vice versa. Use Save room configuration to save configuration edits.
   Checkbox labels wrap inside their frame; no extra fog-mode description is shown.

### Run the reveal

A normal room reveal shows the initial artwork unless that room was previously changed.
In normal fog mode, an amber **2** badge marks a configured room awaiting true artwork.
Hold **Ctrl** and left-click anywhere inside the room to perform its second reveal
without opening Double reveal. If a destination is assigned, the badge then becomes
cyan **↗**: a later Ctrl-left-click asks for confirmation before showing the destination
to players and opening its DM editor. A 600 ms post-reveal guard prevents accidentally
revealing and travelling with a rapid Ctrl double-click. The first action never travels.
Badges are DM-only and stay screen-sized while zooming; their position is the saved
room-selection point, not necessarily the room's center. True rooms without a destination
have no badge. The existing sidebar buttons remain available as an alternative.
Select the configured room and press **Reveal true appearance** to replace only that room's
interior with its corresponding alternate artwork. This does not remove fog; an appearance
can be prepared while hidden. Other rooms and all wall/door boundaries remain unchanged.

**Restore initial appearance** explicitly restores the original room artwork.
**Undo appearance change** reverses the latest appearance action on this map, independently
of fog Undo/Ctrl+Z. Reveal all, Hide/Reset, hiding and revisiting rooms do not reset appearance.
Reloads and restarts preserve the state and its undo history.

### Use a destination link

For a configured destination, **Open destination map** becomes available when the source
room is visible, its true appearance is active, and the source map is currently shown to
players. Confirming the action switches the campaign's player map and opens its DM editor.
It preserves the destination's current fog, doors and appearances; it neither reveals an
arrival room nor invokes the ordinary Restore/Reset map-display dialog. Discovering stairs
does not automatically use them. Players have no clickable travel control. Configure a
return link separately if wanted; same-map and cross-campaign links are not accepted.
Deleting a destination map clears its links.

### Maintenance and limitations

- Replacing the original image while alternate artwork exists requires the original's
  current normalized pixel dimensions, even if no double-reveal rooms are enabled.
  A dimension mismatch returns an error without changing the saved original, alternate
  artwork, room configuration, notes or play state; the rejected upload is removed.
  Resize the replacement to match before retrying. Same-size original replacement stays
  supported, but matching dimensions do not prove alignment. Without alternate artwork,
  original-image dimension changes remain supported; check wall calibration afterwards.
- Replacement alternate images preserve appearance states: already-true rooms immediately
  use replacement artwork. The UI asks for confirmation. Use the same aligned dimensions.
- Disabling a room removes its configuration and appearance history and restores its initial
  artwork. The alternate image remains available for other rooms.
- Changed room geometry makes the old configuration inactive. Remove the listed stale
  configuration and select/configure the intended room again. Geometry identities are
  conservative; calibration, wall type and fog work-resolution changes can invalidate them.
- Artwork is clipped to room interiors without dilation into adjacent rooms. Keep bounding
  wall artwork unchanged; this version does not transform walls or room connectivity.
- Campaign backups contain alternate assets and state. Named checkpoints restore play state
  and appearance history only when their authored image/configuration fingerprints match;
  checkpoints are not image-file backups.


