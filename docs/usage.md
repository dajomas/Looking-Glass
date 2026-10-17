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

- Open the viewer screen (`http://<host>:5100`) on the TV / table PC and log
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

## Pack artwork and consistent screens

In Saved wall sources, save a `.db`, JSON, Universal VTT, or `.zip` pack,
select its wall set, and optionally tick **Use image from this wall set on BOTH
screens** before applying. Unticked (the default) retains your current artwork.
Selection is reset when changing wall sets, preventing accidental reuse of a
previous image choice. Applying replaces this map's walls; it does not alter
other maps using the saved source.

Supported artwork is a Foundry `background.src` or legacy `img` data URI,
a Universal VTT base64 `image`, or a referenced file included in a ZIP alongside
scene exports. ZIP references are matched by their full pack-root path or a
path relative to the scene file. Paths are case-sensitive. Nested archives,
absolute/traversal paths and duplicate normalized archive paths are rejected.
ZIPs are limited to 2,000 entries and 150 MiB total expanded content; individual
uploads and decoded images also obey `storage.max_upload_mb`. Unsupported
metadata JSON is skipped. Supported images are validated using the normal
image-import path and pixel limits.

Foundry exports commonly contain only an external path and a small embedded
`thumb`. When only that thumbnail is embedded, it is explicitly labelled as low
resolution and never selected automatically. Upload the full-resolution art or
include it in a ZIP for best results. URLs and local Foundry module paths are
not fetched or read from the server filesystem. Existing databases are reusable
without being uploaded again, because image metadata is parsed from saved bytes.

There is one canonical `maps.image_file` per map, not separate DM/player images.
Every newly imported image is normalized to an oriented, static RGB PNG (first
frame for animated inputs). Both admin artwork and viewer fog compositing use
that file. The viewer may downscale/re-encode it and adds fog; it never receives
an alternate scene image, the raw image endpoint, or wall data. Replacing artwork
updates image dimensions, wall/fog versions and cache keys; admin refreshes its
versioned image URL and viewers receive the existing refresh notification.
The currently selected active map must be the map being compared: another map
can still be edited while the viewer displays the campaign's active map.

Auto-align uses the selected image dimensions. Disable auto-align to preserve
manual offsets/scales. Applying artwork or changing boundaries retains fog
history and replays it against the new geometry; blank the viewer first and
reset fog if old reveals are inappropriate. Source deletion leaves copied map
artwork and walls intact.

## Wall legend and type controls

| Type | Overlay | Boundary behavior when enabled |
|---|---|---|
| Normal wall | Magenta solid | Blocks areas |
| Door | Blue solid | Blocks when Doors split areas is on |
| Secret door | Purple dashed | Blocks when Doors split areas is on |
| Window / terrain | Green solid | Blocks areas |
| Invisible wall | Yellow dashed | Blocks areas |
| Ethereal | Grey dashed | Never blocks (source semantics) |

Each legend row has **Show** (DM overlay only, page-local) and **Enabled**
(persistent per-map boundary participation). Press **Apply wall types** to save
the Enabled switches and recalculate fog on the server. Disabled categories
remain stored and visible at reduced opacity unless Show is unticked, so they
can be re-enabled without re-import. Ethereal can be toggled but remains
non-blocking even when enabled. The global Show walls checkbox still hides all
overlays. The existing Doors split areas toggle is an additional gate for both
door categories. Filters are independent of source selection and survive
re-import. Disabling boundaries can merge rooms and expand prior reveals;
confirmation warns to blank the viewer before recalculating.
