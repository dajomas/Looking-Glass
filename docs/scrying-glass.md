# Scrying Glass room/setup lookup

Target Looking Glass: 855df04db1c5a177d5972166835ed6db8e8b0a46.
Compatible catalog API inspected at Scrying Glass f2f41a16c516a64095b048cd9ec6a60a07ba08bc.
No Scrying Glass changes, schema migration or extra Python dependencies are required.

## Configuration
Add this top-level block to your existing config.yaml (do not replace your other settings):

```yaml
scrying_glass:
  enabled: true
  base_url: "https://scrying.example.net:8443"
  username: "integration-admin"
  password: ""
  password_env: LG_SCRYING_GLASS_PASSWORD
  timeout_seconds: 5
```

Set LG_SCRYING_GLASS_PASSWORD in the environment of the Looking Glass server process,
including its systemd EnvironmentFile or container environment. If using systemd, protect
the environment file with mode 0600 and restart the service. A nonempty environment secret
wins over the optional YAML password. Never commit a real password. The account must be a
Scrying Glass admin with matching campaigns assigned, or a superadmin. Prefer the least
privileged account. This is one server-configured identity shared by authorized Looking
Glass DMs; it is not automatic per-DM Scrying Glass account mapping.

base_url is the admin HTTP(S) origin, including an explicit port when required. No path,
query, URL credentials or fragment is accepted. HTTPS certificate verification stays on;
HTTP is supported for trusted local deployments but sends credentials without encryption.
Configure a trusted CA for private HTTPS deployments. Server environment proxies and all
redirects are disabled to avoid credential forwarding; configure the final canonical admin
origin. Reverse proxies must preserve the /login and /api/campaigns paths and login's 303
Location of / or /users. Restart Looking Glass after configuration changes. Invalid enabled
configuration fails startup; the default disabled configuration requires no credentials.

## Room notes workflow
Select a room normally or using room-note selection. Save its name, leave note edit mode,
and press Check Scrying Glass in the Room notes panel. The button is disabled for unnamed
rooms, while editing, or without a selected room. It checks saved names, never draft text.
There is no automatic lookup on every fog click. Repeat the button to refresh the result.
Switching rooms or changing notes invalidates an in-flight response so it cannot overwrite
the new room's status. Errors stay in the integration status and do not break fog controls.

## Matching
The server authenticates using POST /login and retains the returned cookie only for that
lookup, then requests GET /api/campaigns. It neither follows the login redirect nor calls
activation, setup-load, save, battle or display endpoints. Each explicit check signs in;
there is no background polling, catalog cache, or persisted session/password in a browser.

Campaign names are compared exactly and case-sensitively after trimming surrounding
whitespace. IDs are not shared between apps. Multiple accessible same-name campaigns are
reported as ambiguous. No visible matching campaign is reported as missing OR inaccessible,
not as proof of nonexistence, because Scrying Glass filters campaigns by ownership.

The room name comes from the selected map's saved room_notes row. The integration uses
Scrying Glass setup_slug rules: trim, lowercase, replace runs outside ASCII a-z/0-9 with
hyphens, strip edge hyphens, truncate at 80 and strip a trailing hyphen. Example:
Goblin Guardroom -> goblin-guardroom; The King's Chamber -> the-king-s-chamber.
The resulting name must appear in the matched campaign's setups list. Different names
can collapse to the same slug; this is an existence check, not a permanent identity link.
Renaming a room or setup can break a match. No state is loaded or activated by the lookup.

## Looking Glass endpoint and security
POST /api/maps/{map_id}/scrying-glass/check, with the normal admin session and CSRF header:

```json
{"x":100,"y":100,"area_key":"<64-character room geometry key>","revision":1}
```

The server checks map/campaign ownership, room geometry and saved-note revision, derives
the campaign/name itself, then closes its DB snapshot before outbound HTTP. No client URL,
remote credentials or arbitrary campaign/name are accepted. The route exists only on the
admin app, not the viewer app. Responses use Cache-Control: no-store.

A successful check returns ok, matched, status and message; enabled checks also include
campaign_name, room_name and setup_name, plus campaign_id when accessible. Statuses include
matched, setup_not_found, campaign_not_accessible, ambiguous_campaign, invalid_room_name,
unnamed_room and disabled. Stale room geometry/revision produces a local 400. Upstream
connection/auth/permission/schema/size failures return a sanitized local 502, not a local
401 that could incorrectly log the DM out. No remote bodies, cookies or passwords are
returned. Upstream catalog bodies are limited to 2 MiB; timeouts are 1..30 seconds per
upstream request. There are no retries. The configured remote address is trusted operator
configuration, not a user-supplied URL. Real Scrying Glass login/session creation can
occur, but no campaign, encounter or battle state is changed.

## Testing
From the repository root:

```sh
python -m pytest -q python/tests/test_scrying_glass.py python/tests/test_scrying_glass_templates.py python/tests/test_scrying_glass_web.py
node python/tests/test_scrying_glass_room.js
```

Unit tests cover normalization, exact matching, duplicate names, inaccessible campaigns,
disabled/unnamed paths, URL/secret/timeout settings, startup validation, mock login/cookie
flow, bounded catalogs, redirect refusal and sanitized failures. UI tests cover selection,
editing guards, duplicate requests and late-result rejection. HTTP tests cover route auth,
CSRF, disabled operation, cache headers, stale revision and viewer-route exclusion; they
require the normal application dependencies. Browser layout and a live Scrying Glass
server still require manual validation.

Before deployment, test a matching setup, missing setup, wrong-case campaign, inaccessible
campaign, bad password, unreachable host, expired/restarted remote sessions and a renamed
room. Confirm no active campaign/setup or player state changes in either application.
