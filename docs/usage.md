# Usage guide

## First run

1. Start the server and read the generated `superadmin` password from the log.
2. Log in on `http://<host>:5000` and change the password.
3. **Users**: create an `admin` account for each DM and `viewer` accounts
   for players. DMs can also create viewer accounts from a campaign page.

## Preparing a session (DM)

1. **Campaigns → New campaign**.
2. **Import battle map**: choose the image and, optionally, the Foundry wall
   file in the same form. You land in the fog editor.
3. Check the walls overlay: magenta = wall, blue = door, purple dashed =
   secret door, green = window, yellow dashed = invisible. If needed, fix the
   **Alignment**.
4. Add players under **Viewers** on the campaign page.

## Reuse one wall source across battle maps

1. In a map editor, expand **Walls → Saved wall sources**.
2. Choose your `.db`, `.json`, or Universal VTT file and press **Save source**.
   If you already uploaded it alongside a map, it is already saved.
3. Choose **Saved source**, then explicitly choose **Wall set**. The dropdown
   shows each scene's name, wall count, door count, and position in the source.
   Selecting a source or wall set alone does not change the map.
4. Leave **Auto-align for this map** enabled to derive offset and scale from
   that scene and the current map image. Disable it to retain current alignment.
5. Press **Apply selected wall set** and confirm replacement. The editor reloads
   with the selected walls. Verify alignment before showing the map to players.
6. Open or import another map in the same campaign. Choose the same saved source
   and either the same or a different wall set; no second source upload is needed.

A file uploaded with a map is automatically saved. For multiple wall sets,
application waits for your explicit selection in the editor; for a single set,
application remains automatic. The separate one-off import form does not save
its file to the library.

Sources persist across server restarts and are private to their campaign's
managers. To use a file in another campaign, save it in that campaign too.
Identical bytes uploaded twice in one campaign reuse the original source; a
changed file is a new source. **Refresh sources** picks up changes from another
tab. **Delete source** removes the reusable upload, not walls copied to maps.

Replacing walls preserves existing fog actions and replays them against the new
geometry. This can change what is visible. Blank the player screen first, then
check the exact player preview and reset fog if appropriate.

## At the table

- Open the viewer screen (`http://<host>:6000`) on the TV / table PC and log
  in. With exactly one campaign it opens straight away. It shows a waiting
  screen until the DM shows a map.
- In the editor, press **Show to players**. The map starts fully fogged.
- **Click a room** in *Reveal* mode to reveal the whole area enclosed by
  walls. *Hide* mode (H) fogs an area again. **Undo** (Ctrl+Z),
  **Reveal all** and **Reset** are available.
- **Doors split areas** (under Alignment) controls whether opening a door
  matters. Turn it off to treat rooms joined by doors as one area.
- **Player preview** shows the fog fully opaque. *Open exact player image*
  shows the actual composite.
- **Blank** shows the waiting screen, e.g. while switching maps.
- Viewers update live. They can pan (drag), zoom (wheel / pinch), fit (F) and
  go fullscreen. The HUD hides itself after 3 s.
