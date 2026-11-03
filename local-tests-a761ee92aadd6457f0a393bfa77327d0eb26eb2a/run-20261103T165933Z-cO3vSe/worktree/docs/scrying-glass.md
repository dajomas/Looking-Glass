# Scrying Glass automatic room/setup lookup

Patch base: Looking Glass 6a562321a5f0f35408b92fe79200c39cd5ad90f2.
Compatible Scrying Glass catalog API: f2f41a16c516a64095b048cd9ec6a60a07ba08bc.
No Scrying Glass update, schema migration, new dependency or configuration change is needed.

## Configuration and access
Keep the existing top-level config.yaml block:

```yaml
scrying_glass:
  enabled: true
  base_url: "https://scrying.example.net:8443"
  username: "integration-admin"
  password: ""
  password_env: LG_SCRYING_GLASS_PASSWORD
  timeout_seconds: 5
```

Set the password environment variable in the Looking Glass service/container and restart.
An environment password takes precedence over YAML. Protect secret files and never commit
credentials. The remote account must be an admin assigned to the matching campaign or a
superadmin; prefer least privilege. It is one server-configured identity, not per-DM remote
account mapping. The admin base URL must be an HTTP(S) origin without URL credentials,
paths, queries or fragments. HTTPS verification, no environment proxies, no redirects,
1..30-second per-request timeout and 2 MiB upstream catalog limit remain unchanged.
HTTP sends credentials without encryption and is suitable only on trusted local networks.
Private HTTPS requires a trusted CA. Reverse proxies must preserve /login, /api/campaigns
and the expected 303 login Location of / or /users. Invalid enabled configuration fails
startup; disabled lookup requires no credentials.

## Automatic lookup workflow
Select a room with a saved, nonblank name outside note edit/draft mode. There is no manual
check button. Enabled configuration, login/catalog access and one accessible same-name
campaign must be verified before the room check. Unnamed/dirty/editing selections initiate
no check; disabled integration remains hidden and does not contact Scrying Glass.

Successful matches now appear in a prominent green-bordered success panel with a checkmark,
singular/plural count heading and the complete list of matching setup names. Exact names
are additionally labelled Exact match. This is a distinct panel, not a subtle status line.
Long names wrap within the sidebar, and long lists scroll without removing items. The
heading/count and exact label communicate meaning independently of color; no flashing is
used. Missing results and access/connection problems use the separate status text, never
the success panel. Changing rooms, editing, a failed check or disabled access clears stale
success content. Cached results restore the full list and success styling.

The panel is DM-only. It lists possible battle setups but never chooses or loads one.
Suffixes are opaque: player counts, encounter stages and other variants are all supported.
No campaign, setup, fog, artwork, battle or player display state is activated or changed.
Lookup may create a remote login session when the catalog is refreshed.

## Campaign names and room prefixes
Campaign display names still compare exactly and case-sensitively after trimming surrounding
whitespace. IDs are independent between applications. Duplicate accessible same-name
campaigns remain ambiguous; missing/unassigned campaigns are not treated as definite proof
of nonexistence. All variants are confined to the one authorized matched campaign.

The room's saved name is normalized with Scrying Glass setup_slug rules: trim, lowercase,
replace runs outside ASCII a-z/0-9 with hyphens, strip edge hyphens, truncate to 80 characters
and strip a trailing hyphen. Existing saved-name and geometry/revision checks are unchanged.

A setup matches when its stored canonical name is either:
1. Exactly the normalized room name; or
2. The normalized room name followed by a hyphen and a nonempty suffix.

Example:

```text
Room: 04 - Silent room
Prefix: 04-silent-room

Matches, in display order:
04-silent-room                  (Exact match)
04-silent-room-1-4
04-silent-room-5-6
04-silent-room-reinforcements

Not matched:
04-silent-roommate
04-silent-room2
other-04-silent-room-1-4
```

An exact setup is not required: the two suffixed player-count variants alone count as two
matches. Suffix meaning is not parsed. Exact match sorts first, remaining variants sort
case-insensitively with a deterministic name tie-break, and duplicate names are removed.
Matching itself remains case-sensitive against Scrying Glass's canonical stored setup
names. Empty/invalid room prefixes cannot match the whole catalog. Distinct room names can
normalize to the same prefix; renames can break matches. Broader room prefixes may match
more variants than intended, so retain enough of the room name to disambiguate encounters.

## Verification, caching and failure behavior
Verification requires login/catalog access plus one accessible campaign with a valid setup
list, not just an open TCP port. The per-worker bounded catalog cache and automatic UI gates
are unchanged: success lasts up to 60 seconds, upstream failures back off for 30 seconds,
and configuration identity includes origin/account/secret/timeout. Up to eight identities
are retained per worker; a lock shares refreshes across concurrent callers. A temporary
cookie jar is cleared after each fetch; credentials/cookies never go to the browser.

The browser shares in-flight verification, caches at most 64 recent room results no longer
than verified access, and suppresses repeated checks at different points in one unchanged
room. Full result objects are now cached, including all setup names, not only a message.
Stale responses cannot overwrite a newly selected room. There is no background timer or
poll: reselect an eligible room after expiry to refresh/retry. Browser reload does not bypass
server backoff; server restart clears worker caches. Remote catalog/access changes can take
up to 60 seconds to become visible. Expired success is not reused after failed verification.

## API result additions
Admin-only POST /api/maps/{map_id}/scrying-glass/access and /check keep their existing
Looking Glass session, CSRF and map/campaign-ownership checks. /check validates coordinates,
geometry key and saved-note revision, derives campaign/name on the server, and closes the
DB snapshot before outbound HTTP. No client URL, credentials, arbitrary campaign or draft
name is accepted. Viewer apps have no lookup routes; responses are Cache-Control: no-store.

The /check request is unchanged:

```json
{"x":100,"y":100,"area_key":"<64-character geometry key>","revision":1}
```

Verified named-room results add setup_names, match_count and exact_match. setup_name remains
the normalized room prefix for compatibility; it is not a selected/loaded variant.
For example, omitting unchanged identity/TTL fields:

```json
{
  "matched": true,
  "status": "matched",
  "setup_name": "04-silent-room",
  "setup_names": ["04-silent-room-1-4", "04-silent-room-5-6"],
  "match_count": 2,
  "exact_match": false,
  "message": "2 matching battle setups found."
}
```

A valid campaign with no matching prefix yields matched=false, status=setup_not_found,
setup_names=[], match_count=0 and exact_match=false. Earlier disabled/unnamed/access-failure
responses may omit the list fields because no matching was performed. Missing/ambiguous
campaign statuses and access gates are preserved. Local stale geometry/revision still
returns 400; remote connection/auth/schema failures remain sanitized 502, not local 401.
Names and messages are rendered with DOM textContent, never inserted as HTML.

## Tests and manual validation

```sh
python -m pytest -q python/tests/test_scrying_glass_prefix.py python/tests/test_scrying_glass_prefix_templates.py
node python/tests/test_scrying_glass_room.js
```

New tests cover exact and multiple arbitrary suffixes, boundary false positives, duplicate
removal/order, missing results, empty names, canonical case, inaccessible/ambiguous campaign
outcomes and isolation from other campaigns. UI regression retains automatic gate/backoff/
TTL/stale-response checks and adds plural/singular headings, exact labels, full-list cache
restoration, safe name rendering and success-state clearing. Source checks verify the new
CSS/admin-only panel and unchanged access gate/cache constants.

Run existing matching, access-cache and HTTP tests in the target repository with its normal
dev dependencies as well. Manual browser/live checks remain necessary: two named variants
without an exact setup; exact plus variants; long names/narrow sidebar; many variants and
scrolling; missing/inaccessible results; room switches while checking; expired cache; disabled
lookup; note editing; player-screen absence; unchanged fog/Double Reveal/battle behavior.
