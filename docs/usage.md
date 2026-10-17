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
