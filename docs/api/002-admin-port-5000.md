## Admin port (5000)

| Method | Path | Body | Purpose |
|---|---|---|---|
| GET | `/api/maps/{id}` | | Map info, calibration, walls (image coords), counts, live state |
| GET | `/api/maps/{id}/image` | | Raw battle map |
| GET | `/api/maps/{id}/fog.png` | | RGBA mask (alpha = revealed) at work resolution |
| GET | `/api/maps/{id}/viewer-preview` | | Exactly the image players receive |
| POST | `/api/maps/{id}/reveal` | `{"x":..,"y":..}` (image px) | Reveal the area at the point; returns `area_fraction`, `leak_warning` |
| POST | `/api/maps/{id}/hide` | `{"x":..,"y":..}` | Hide the area at the point |
| POST | `/api/maps/{id}/reveal-all` | | Reveal everything |
| POST | `/api/maps/{id}/reset` | | Fog everything (undoable) |
| POST | `/api/maps/{id}/undo` | | Undo the last fog operation |
| POST | `/api/maps/{id}/calibration` | `{"offset_x","offset_y","scale_x","scale_y","doors_block"}` | Wall alignment |
| POST | `/api/maps/{id}/walls/inspect` | multipart `file` | List scenes in a wall file |
| POST | `/api/maps/{id}/walls` | multipart `file`, `scene_index`, `use_scene_calibration` | Import / replace walls |
| DELETE | `/api/maps/{id}/walls` | | Remove walls |
| POST | `/api/campaigns/{id}/active` | `{"map_id": 3}` or `{"map_id": null}` | Show a map to players / blank the screen |

HTML form posts (redirect with `?ok=` / `?err=`) cover campaigns
(`/campaigns`, `/campaigns/{id}/update|delete|active`), viewers
(`/campaigns/{id}/viewers/add|create`, `/campaigns/{id}/viewers/{uid}/remove`),
maps (`/campaigns/{id}/maps`, `/maps/{id}/rename|move|image|delete`) and users
(`/users`, `/users/{id}/update|password|delete`, superadmin only).

### Manual calibration numeric validation

`POST /api/maps/{id}/calibration` requires map-management permission and a valid
CSRF token. Offsets and scales must be finite numbers; scales remain strictly
positive and no greater than 100. Negative finite offsets remain supported.
Non-finite or out-of-range fields return 422. Before any update, all stored wall
endpoints are checked using `(source - offset) * scale`; a non-finite result
returns 400, including overflow from individually finite inputs. Validation and
the update share one immediate transaction so a wall replacement cannot race
between those steps. Rejection does not change calibration, wall/fog versions,
notes or fog history, invalidate the fog cache, or send an update notification.

The endpoint URL and successful response contract are unchanged. Field checks
also apply to maps with no walls. This does not repair pre-existing invalid
stored values or impose additional finite coordinate-magnitude limits.
