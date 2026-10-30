## Reusable wall sources (admin port only)

All routes below require manage permission for the campaign or map, including
read-only source inspection. Writes require CSRF. Raw source bytes are never
returned; these routes are not registered on the viewer application.

| Method | Path | Body | Result |
|---|---|---|---|
| GET | `/api/campaigns/{id}/wall-sources` | none | `{"ok":true,"sources":[...]}` |
| POST | `/api/campaigns/{id}/wall-sources` | multipart `file` | Validate and save; `{"ok":true,"source":{...}}` |
| GET | `/api/maps/{map_id}/wall-sources/{source_id}` | none | Source summary and `scenes[]`, with map-specific suggested calibration |
| POST | `/api/maps/{map_id}/walls/from-source` | JSON below | Existing map payload plus `imported`, `scene`, and `source_id` |
| DELETE | `/api/campaigns/{id}/wall-sources/{source_id}` | none | `{"ok":true}`; does not remove map walls |

```json
{"source_id": 1, "scene_index": 0, "use_scene_calibration": true}
```

`source_id` and `scene_index` are required. Source IDs are positive; scene indices
are zero-based, non-negative, and must be in range. `use_scene_calibration`
defaults to true. Missing/invalid fields use FastAPI validation errors (422);
unknown or cross-campaign sources and out-of-range indices return 400. Campaign
and map authorization follows the existing access helpers.

Source summaries contain `id`, `filename`, `scene_count`, and `created_at`.
Scene entries contain `index`, `name`, `format`, `walls`, `doors`, `scene_width`,
`scene_height`, and `calibration` (`offset_x/y`, `scale_x/y`). Empty scenes are
filtered by the existing parser; indices refer to this returned list. Duplicate
scene names remain separate choices, distinguished by index.

Uploads obey `storage.max_upload_mb`. Identical bytes in the same campaign
return the same source and retain its original filename. Sources are immutable:
uploading changed bytes creates a new source. Source inspection and saving do
not modify map walls, fog, or calibration. Applying copies walls to the target
map only, invalidates its fog cache, and notifies viewers. Existing fog actions
are preserved and replayed against the new geometry.

The existing one-off `/walls/inspect` and `/walls` APIs remain compatible and
do not save their files automatically. The HTML map upload saves valid wall
sources; a multi-set upload waits for selection instead of choosing index 0.

