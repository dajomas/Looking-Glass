## Cross-map passage API (admin portal only)

All paths below are under `/api`. Reads require authenticated campaign-management
permission, not just campaign viewing. Writes additionally require the existing
`X-CSRF-Token`. All writes serialize with BEGIN IMMEDIATE. Unknown body fields are
rejected; boolean flags are strict booleans. Service validation/stale state is a
400 BadRequest; permission/CSRF failures use existing 401/403 behavior, and invalid
request schemas use FastAPI's 422 response. These routes do not exist on the viewer
application (404).

| Method | Path | Purpose |
|---|---|---|
| GET | `/campaigns/{cid}/transitions` | Admin-only endpoints and campaign maps/settings |
| POST | `/campaigns/{cid}/transitions` | Create endpoint |
| POST | `/campaigns/{cid}/transitions/{id}` | Update full authored record, with revision |
| DELETE | `/campaigns/{cid}/transitions/{id}?revision=N` | Delete with stale check |
| POST | `/campaigns/{cid}/transitions/{id}/runtime` | Set/clear session overrides |
| GET | `/campaigns/{cid}/transitions/{id}/preview` | Read-only saved arrival preflight |
| POST | `/campaigns/{cid}/travel` | Atomic reveal/checkpoint/switch |
| POST | `/maps/{mid}/transitions/reset` | Clear this map's endpoint runtime overrides |
| POST | `/maps/{mid}/transition-markers` | Save viewer marker/label booleans |

Create/update body:

```json
{
  "map_id": 12, "name": "West stairs", "player_label": "Up",
  "kind": "stairs", "x": 100, "y": 120,
  "visibility": "discovered", "availability": "usable",
  "destination_id": null, "arrival": "area", "notes": "DM-only notes",
  "revision": null, "return_link": false
}
```

Required: map_id, name, x, y. Other fields use the illustrated defaults except
player_label/notes (empty). Name/label max 120 chars; notes max 2000. Coordinates
must be finite and inside the referenced image. Update requires the current revision
and immutable map_id. It replaces authored configuration, rather than applying a
partial patch. `destination_id` is an endpoint UUID, not a map ID; null unlinks it.
`return_link` creates an explicit reverse link without overwriting an existing
outgoing destination. Kind: stairs/ladder/hole/portal/climb/custom; visibility:
secret/discovered/admin; availability: usable/blocked/approval; arrival: area/preserve.

Runtime body: `{"revision": 1, "visibility": "discovered", "availability": null}`.
Both override fields are replaced on each runtime request; omitted/null clears the
corresponding override. Null means inherit authored value. Reset uses an empty body.
Marker body: `{"enabled": true, "labels": true}`; both fields are required.

Configuration mutations return the same listing shape as GET: ok, active_map_id,
endpoints, maps. Endpoint listing fields include current_visibility,
current_availability, broken and admin-only destination metadata. Never forward this
payload to players. Endpoint edits preserve runtime overrides.

Preview response includes source_revision, destination_revision, destination_id,
destination_map_id/name, destination_name, destination_version (three-element array),
arrival, source_state/visibility, needs_override, fraction and warning. For preserve,
fraction=0 and warning=false. Area fraction is the full component, not the incremental
reveal. Preview does not change fog or active map.

```json
{
  "source_endpoint_id": "SOURCE_UUID", "expected_active_map_id": 12,
  "source_revision": 3, "destination_revision": 2,
  "destination_version": ["DESTINATION_CACHE_TOKEN", 4, 9],
  "request_id": "unique-client-travel-request",
  "override": false, "allow_large_reveal": false
}
```

Populate revision/version fields from a fresh preview, and expected_active_map_id
from the listing. The source must be the active map. Use a new request_id for a new
trip; retry exactly the same payload after a transport failure. A successful retry
never reapplies the trip. Success returns `{ok:true,active_map_id:N,admin_url:"/maps/N"}`.
Explicit override is required for a source that is secret, blocked or approval-only;
it does not modify that state. Destination visibility/availability is not an arrival
gate. A large/leaking arrival requires allow_large_reveal=true as a separate consent.
An endpoint on a wall cannot use area reveal. No small-zone/radius arrival policy
exists in this version.


### Destination display availability

The existing admin `GET /api/maps/{map_id}/display-options` response now adds
`has_current_reveals`, a boolean evaluated from live fog operations. Existing
`can_restore` retains its meaning: effective active-map operations or, for an
inactive map, its saved checkpoint. Inspect destination does not consume these flags or show a reveal-choice prompt;
it uses authorized reads and admin navigation only. Existing display-option callers
retain their default behavior.
The existing CSRF-protected `POST /api/campaigns/{campaign_id}/active` performs
activation with map_id and fog_action (restore/reset); the endpoint, permissions
and response contract are unchanged. A cancelled choice issues no mutation request.
No new passage-travel operation or schema migration is introduced by this UI change.


### Passage save identity and independent scopes

Successful `POST /api/campaigns/{cid}/transitions` and
`POST /api/campaigns/{cid}/transitions/{id}` responses now include
`saved_endpoint_id` alongside the existing listing fields. It identifies the saved
endpoint, especially on create when several admins might add endpoints concurrently.
This is an additive response field; the request schema is unchanged.

The configuration request replaces authored configuration and preserves runtime
overrides. The runtime request replaces its two override fields only and preserves
configuration. Null/omitted override fields inherit authored settings. Clients must
use the returned endpoint revision for subsequent writes in either scope. UI dirty
tracking does not change server permissions, CSRF or stale-write validation.


### Modal-action clarification (no API changes)

The single portal Close/discard confirmation and Reset pairing confirmation are
client-side popup/draft operations. Back to passage and Escape from travel send no
mutation request. Entering travel preflight no longer replaces the source editor's
saved revision/baselines: cancelling cannot silently acknowledge another tab's
configuration changes. A later save still undergoes the existing stale-write check.
Travel and active-map request schemas, action values (restore/reset/cancel) and
backend effects are unchanged; only user-facing labels and return behavior change.

