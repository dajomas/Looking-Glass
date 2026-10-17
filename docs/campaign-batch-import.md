# Campaign batch map import and wall assignment

## Existing and new inputs

The existing **Import battle map** form still uploads one image, optional walls,
and an optional name exactly as before. Its wall label and both map-editor
wall-upload labels now explicitly say **UVTT (Universal VTT)** in addition to
Foundry VTT. Foundry scene/database formats and UVTT remain distinct formats.

The additional **Import multiple maps and assign walls** panel accepts:

- Multiple map images (PNG, JPEG, WEBP, or formats accepted by the image service).
- Multiple separate wall files: `.db`, `.json`, `.uvtt`, `.dd2vtt`, `.df2vtt`,
  and supported `.zip` packs.
- Only images, only wall files, or a mixture. Existing saved sources also work.

Map names default to their image filenames without the extension. Use the
existing campaign Rename control for custom names. Batch mode imports separate
artwork files: it deliberately does not substitute embedded pack artwork.

## Import, then explicitly assign

Uploads run sequentially, one request per file, reusing the existing validated
server endpoints and per-file size limits. Wall sources are saved first; map
images are imported separately. No files are matched by filename, selection
order, or scene position. Source deduplication remains the server's existing
byte-based, campaign-scoped policy; image imports always create new maps.

An assignment table contains existing campaign maps and maps just imported in
this tab. For each map, select a saved source and then an alphabetically sorted
wall set. Sorting is case-insensitive with natural numeric ordering. Original
scene indices are preserved; bracketed numbers are original source positions,
not the display order. Choose auto-alignment per map, then apply all selected
rows after reviewing the confirmation. The same wall file can provide different
sets to different maps, or the same set to several maps.

Rows with no selected set are untouched. Assignment replaces the target map's
walls, not other maps. Map artwork is always retained (`use_pack_image=false`).
Existing wall-type settings, fog history, authorization and notifications follow
the existing import endpoint. No campaign is activated by this panel. Blank the
player display first when changing walls: previous reveal coordinates will be
replayed against the new geometry. Check alignment in the fog editor afterward.

## Failures and retries

This is a per-file/per-map workflow, not an all-or-nothing batch transaction.
Successful uploads remain when another file fails; every upload gets a result.
File inputs are cleared after the queue finishes to discourage accidental
reimport of successful images. Reselect only failed files. A lost connection can
leave an uncertain result: check the campaign before retrying an image upload.
If the map was created and its redirect reached an editor returning an HTTP
error, the panel retains the map ID and reports the editor error as a warning
instead of encouraging a duplicate upload.

Successful wall assignments are deselected. Failed assignments retain their
choices and show a row error, so Apply retries only remaining selections. Source
changes clear stale wall-set choices. Canceling the confirmation sends no
assignment requests. Inputs are temporarily disabled while operations run.

Refresh saved wall sources fetches newly saved uploads from this or another tab.
Reload the campaign to refresh the original Battle maps table and discover maps
created in another tab. Reloading loses unsent choices. JavaScript is required
for the new panel; the original single-map form is still available without it.

## Deployment and API compatibility

No database/schema or backend API change is included. In particular, this patch
does not touch the prior cache-token migration repair. The new script reuses:

- `POST /campaigns/{id}/maps` (multipart image; follows the existing map-editor redirect).
- `GET/POST /api/campaigns/{id}/wall-sources` (saved source list/upload).
- `GET /api/maps/{map}/wall-sources/{source}` (map-specific inspection/calibration).
- `POST /api/maps/{map}/walls/from-source` (explicit source ID/scene index).

The map-upload form includes the existing CSRF form token and header; the JSON
wrapper supplies the header for source/assignment operations. Requests retain
session cookies and existing campaign ownership checks. File names and scene
names are rendered as text, not HTML. No new runtime dependencies are needed.
Deploy the templates and new static script together, then hard-reload the
campaign and map-editor pages. A reverse proxy's static cache may need purging.
