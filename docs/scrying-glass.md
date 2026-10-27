# Scrying Glass automatic room/setup lookup

Looking Glass patch base: 972c293162946d90c088e122a5743ec9c07cbe5d.
Compatible Scrying Glass API: f2f41a16c516a64095b048cd9ec6a60a07ba08bc.
This replaces the manual-check workflow; no Scrying Glass, schema or dependency changes.

## Configuration
Keep the existing top-level config.yaml settings:

```yaml
scrying_glass:
  enabled: true
  base_url: "https://scrying.example.net:8443"
  username: "integration-admin"
  password: ""
  password_env: LG_SCRYING_GLASS_PASSWORD
  timeout_seconds: 5
```

Set LG_SCRYING_GLASS_PASSWORD in the Looking Glass service/container environment and restart.
A nonempty environment password takes precedence over YAML. Protect environment files and
never commit secrets. Use the final canonical admin origin including scheme/host/port, with
no path, URL credentials, query or fragment. The remote account must be an admin assigned
the matching campaign, or a superadmin. This identity is shared by authorized Looking Glass
DMs; it is not per-DM remote account mapping. Prefer the least-privileged assigned admin.

TLS verification remains enabled. HTTP is permitted for trusted local deployments but
sends credentials unencrypted. Configure trusted CAs for private HTTPS. Environment proxies
and redirects stay disabled; reverse proxies must preserve /login, /api/campaigns and the
expected 303 login Location of / or /users. Existing 1..30-second per-request timeouts and
2 MiB response limits remain. Invalid enabled configuration fails startup. Disabled lookup
requires no remote credentials.

## Automatic room workflow
There is no button. Select a room with a saved, nonblank name, outside note edit mode.
Looking Glass first asks its own server to verify the integration. Only when enabled and
verified does it automatically check for a matching saved battle setup. Verification means
successful login and catalog retrieval plus exactly one accessible campaign with the same
trimmed display name and a valid setup list, not merely an open TCP port.

- Unnamed areas, no selection and draft/edit state cause no access verification or room check.
- Saving a name or cancelling edits can make a room eligible and trigger its check.
- Disabled integration hides the status and makes no upstream request.
- Failed/unverified access shows a concise status, with no room-check request from the UI.
- Verified access permits automatic checks; matching or missing setup is shown in Room notes.
- Selecting another room invalidates late responses. Clicking another point inside the same
  area does not repeat an unchanged check. Returning to a recently checked room reuses its
  result within the verification TTL. No background polling or automatic battle loading.

Selecting the same named room after cache/backoff expiry refreshes or retries. Existing
room-note refresh hooks may also re-enter this flow; no timer is added. Reloading the page
clears UI state but does not bypass the server cache/backoff. Correct account/settings and
restart after changing YAML/environment, as before.

## Matching
Campaign display names compare exactly and case-sensitively after trimming surrounding
whitespace; IDs are independent between apps. Duplicate accessible campaign names are
ambiguous. Missing/unassigned campaigns are reported as not accessible, never as definite
proof that no remote campaign exists. The selected room's saved notes supply its name;
client-supplied campaign names, draft names or URLs are not accepted.

Setup names use Scrying Glass normalization: trim, lowercase, replace runs outside ASCII
a-z/0-9 with hyphens, strip edges, truncate at 80 and strip a trailing hyphen. For example,
Goblin Guardroom -> goblin-guardroom. Different names can map to the same slug; renames
can break matches. This is an existence check, not a permanent identity association.

## Cache and failure behavior
The new scrying_glass_access service caches verified catalog snapshots for 60 seconds,
and sanitized fetch/login failures for 30 seconds, using monotonic expiry. A bounded cache
holds at most eight configuration identities per worker. Its keys hash the origin, account,
secret and timeout; no plaintext secret appears in cache keys or responses. A lock shares
one refresh among concurrent callers and tabs. Credentials/cookies stay server-side; the
unchanged transport clears its temporary cookie jar after each catalog fetch.

Verification and room matching share the same cached catalog, avoiding a second login
for each room. Config/secret changes invalidate cache identity. Catalog/account access
changes may remain visible for at most 60 seconds. Each worker has its own cache, cleared
on restart. Expired success is not served as verified after a failed refresh. Failures
back off; they do not turn into rapid retries across room clicks.

The browser shares one in-flight verification, caches its gate only until the server TTL,
and retains at most 64 recent room results. UI/network errors back off 30 seconds.
Verification is enforced again server-side; clients cannot bypass it with a direct check.
No active campaign/setup, fog, artwork or battle state is changed. Remote login/session
creation can occur on a catalog refresh, as in the previous implementation.

## Looking Glass API and authorization
Both endpoints are admin-only POSTs under /api/maps/{map_id}/scrying-glass and require the
normal Looking Glass admin session, CSRF header and permission to manage the map campaign.
They are not mounted on the viewer app. Responses use Cache-Control: no-store.

POST /access with {} returns ok, enabled, verified, status, message and retry_after_seconds.
Disabled configuration returns enabled=false/verified=false without contacting Scrying
Glass. Missing or ambiguous campaigns return verified=false. Upstream/auth/schema problems
return a sanitized local 502, not a local 401 that would sign the DM out.

POST /check retains the existing request:

```json
{"x":100,"y":100,"area_key":"<64-character room geometry key>","revision":1}
```

The server validates ownership, room geometry and saved-name revision; it closes its DB
snapshot before network access. It then requires enabled configuration and verified campaign
access using the cache before matching. Normal results include matched, status and message;
verified results also carry the campaign/room/setup identifiers and remaining TTL. Disabled,
unnamed or unverified calls cannot trigger a room-name match. Stale geometry/revision still
returns a local 400. No raw upstream response, catalog, password or cookie is returned.

## Tests and deployment checklist

```sh
python -m pytest -q python/tests/test_scrying_glass_access.py python/tests/test_scrying_glass_templates.py python/tests/test_scrying_glass_web.py
node python/tests/test_scrying_glass_room.js
```

Cache tests cover enabled/disabled gates, unnamed areas, verified matching, inaccessible or
ambiguous campaigns, expiry, identity changes, bounded storage, concurrent refresh sharing,
negative-cache recovery and invalid responses. UI tests cover automatic request ordering,
no requests while unnamed/editing/dirty, duplicate suppression, caching, backoff and room
switches during verification/checking. The updated HTTP tests cover access/check CSRF,
login requirements, viewer exclusion, disabled results and stale revisions; runtime test
dependencies are required. Existing transport and matching unit tests remain applicable.

Manual browser/live-server checks: no check button, no disabled/unnamed activity, match after
selecting/saving a named room, bad-password/unreachable status with no retry storm, recovery
after 30 seconds and reselection, updated setup catalog after 60 seconds, rapid room changes,
and unchanged fog/Double Reveal/battle/player behavior. Browser timing/layout and live
Scrying Glass integration are not proven by mocked transport or source assertions.
