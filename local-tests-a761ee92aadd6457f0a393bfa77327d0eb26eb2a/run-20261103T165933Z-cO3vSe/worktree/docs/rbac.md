# Roles and permissions

All checks live in `python/looking_glass/rbac.py`.

| Action | superadmin | admin | viewer |
|---|:-:|:-:|:-:|
| Log in on admin port (5000) | ✔ | ✔ | ✘ |
| Log in on viewer port (5100) | ✔ | ✔ | ✔ |
| Create / edit / disable / delete users, set roles, reset passwords | ✔ | ✘ | ✘ |
| Create campaigns | ✔ | ✔ | ✘ |
| Manage a campaign (maps, walls, fog, settings, delete) | all campaigns | own campaigns | ✘ |
| Transfer campaign ownership | ✔ | ✘ | ✘ |
| Assign / remove viewers on a campaign | all | own | ✘ |
| Create new **viewer** accounts from a campaign page | ✔ | ✔ (if `security.admins_can_create_viewers`) | ✘ |
| View a campaign on the viewer screen | all | own + assigned | assigned only |

Notes

- Any active user can be assigned to a campaign, so an admin can be a player in
  someone else's campaign.
- Sessions belong to one entry point (`lg_admin_session` / `lg_viewer_session`
  cookies). An admin-port session never authenticates on the viewer port, or
  the other way round.
- At least one active superadmin always remains. You cannot demote, disable
  or delete yourself.
- Changing a user's role, disabling them or resetting their password revokes
  their sessions and closes their live viewer sockets. So does removing them
  from a campaign.
- Users created by an admin (and, by default, by a superadmin) must change
  their password at first login.
- Unassigned viewers get **404** (not 403) for campaigns, so IDs can't be probed.
- Every state-changing request needs the session's CSRF token (hidden form
  field or `X-CSRF-Token` header). Cookies are `HttpOnly`, `SameSite=Lax`,
  and `Secure` when `security.secure_cookies: true`.


## Remote viewer camera control

Only a user allowed to manage the selected map's campaign may POST the new admin viewer-zoom command, with the existing admin session and CSRF token. The map must be the campaign's active map and the target must be currently revealed. Viewer accounts still have only their existing read-only local area-bounds navigation; no viewer-port mutation/control endpoint is added. Camera events are broadcast only to that campaign's subscribed sockets and revalidated through each viewer's authorized area lookup.

## Passage actions remain admin-only

Passage following, discovery and lock changes use the existing campaign-management
permission and admin CSRF session. Viewer arrows are display-only; no viewer write
route or hidden portal graph is exposed. Existing authorized read-only viewer
room zoom remains unchanged. See Passages.md.

## Portal overview and route highlighting

The wall-editor overview reads the current authorized authored draft only. New
portal_routes metadata is part of the existing manage-authorized admin map payload
and is never added to viewer state or the viewer compositor. Client-side highlighting
never calls a reveal, lock/discovery or save endpoint. Existing manager/CSRF checks
remain unchanged. Moving a modal or opening an overview does not mutate campaign
state. No new viewer permission or interactive viewer arrow action is introduced.


## Cross-map passages

Endpoint listings, previews and configuration require campaign management permission.
The DM owner and superadmins use the existing management policy; being an assigned
viewer is insufficient. All mutations/travel require CSRF. Source and destination
must belong to the managed campaign. Viewer application routes do not include the
admin transition API. Players receive server-composited discovered markers only,
not endpoint IDs, routes, destination names, private notes or admin-only labels.
A DM override can permit a particular secret/blocked/approval-required trip without
changing authored or session state. It is not a player permission bypass.


### Travel approval presentation

The travel modal uses I approve this trip for approval-required sources and Allow
this trip despite passage restrictions for secret/blocked sources, with the actual
saved-state reasons beneath the control. It hides the checkbox when approval is not
needed and clears it for every new preview. This is per-trip consent, not a saved
permission/state change. Authorization, stale-input validation and large-arrival
confirmation stay enforced. See [travel approval wording](travel-approval.md).

## Room notes

Room lookup/list/save uses map_for_manage and inherits campaign management
permissions. Admins cannot access another administrator's campaign merely by
knowing map/room identifiers. POST lookup and save require CSRF. Note HTML and
Markdown are not exposed through viewer routes, images or websocket messages.

## Imported room-note libraries

Library listing and import require management access to the map's campaign. Import
requires the existing CSRF protection and checks authorization before reading the
upload and again before persistence. Viewer endpoints do not expose library notes.
Libraries are scoped to a map, not shared globally or automatically across campaigns.

## Edit overlays and imported-note deletion

The edit-overlay POST and library-entry DELETE routes require CSRF and existing
map/campaign management permissions. DELETE checks current assignment on the server
under an immediate transaction; hiding a UI button is not the security boundary.
Wrong-map entry IDs cannot be deleted. Viewer APIs and images do not contain edit
markers or the imported-note manager. Existing admin read permissions apply to lists.

## Campaign backup and restore permissions

Both backup and restore use the campaign-management access check: the owning admin/DM
or a superadmin may act. Other admins cannot manage another owner's campaign, and
viewers cannot use admin-portal backup controls. Both routes require CSRF validation,
including backup downloads. Restore additionally requires the target's current name,
a valid signed inspection preview and the identical inspected ZIP. Inspection uses the
same management permission and CSRF guard. Recovery downloads are authenticated GETs
with the same management access check and exact campaign-prefixed filenames. They do
not require CSRF because they do not change state. Neither inspection nor recovery
download is exposed on the viewer portal.
Archive content cannot change owner or viewer assignments or create user accounts.
Fog-operation author references are cleared rather than linked to accounts by numeric ID.

## Campaign readiness permissions

Readiness and its DM inspection page require `campaign_for_manage`: owning admin or
superadmin. Other admins and viewers do not gain access. Map inspection verifies map
membership in the selected campaign. Destination lookups are campaign-scoped; missing
and out-of-campaign targets have the same message, without disclosing target details.
Reports may include secret endpoint/room names and must never be exposed on viewer routes.
Both new routes are read-only GETs protected by authentication and no-store response headers.

## Campaign search permissions

HTML search, JSON search and generic DM inspection all require the owning admin or a
superadmin via campaign-management checks. Neither viewer assignment nor another admin's
session authorizes searching that campaign. Every search table is filtered by campaign;
selected inspection objects must belong to the authorized map and URL campaign. A
superadmin still searches only the selected campaign. Secret passage names/notes can be
returned because this feature is exclusively DM-facing; no search UI appears on viewer
pages. Search and inspection use no-store responses and do not notify player clients.

## Session checkpoint permissions

Only the campaign owner/admin or a superadmin can list, inspect, create, restore or delete
its checkpoints. Lookup always includes the authorized campaign ID; checkpoint IDs alone
confer no access. Viewers receive no checkpoint routes, data or controls. GET previews are
query-only and do not notify viewers. Every POST requires CSRF. Restore additionally
requires the campaign name, a fresh preview token and compatible authored content; deletion
requires the saved checkpoint name. Restore may change what authorized viewers see but
never changes campaign ownership or viewer assignments. Safety records use the restoring
user as creator; deleting a creator account nulls its metadata reference.

## Viewer synchronization permissions (step 5)

The admin-only campaign viewer-status GET repeats campaign-management authorization for
every poll. Other admins and ordinary viewers cannot inspect another campaign's connection
list; the route is absent from the viewer app. Usernames come from authenticated viewer
sessions. Each viewer reports only through its already authorized campaign socket and its
server-bound record, never a client-selected username/record/campaign. Diagnostic reports
cannot change fog, active map, access assignments or checkpoints. JSON reports do not expose
arbitrary client errors, IP/user-agent, raw map images or wall data. Manager rendering uses
textContent. Existing session/access revocation socket cleanup remains in force.

## Clean map/campaign duplication (step 6)

On the campaign page, use Settings → Duplicate campaign to create an independently
owned clean campaign, or the Duplicate map disclosure beside a map to copy it into
the same campaign. Enter a copy name (1–120 non-whitespace characters).

Copies preserve authored map images (independent stored files), calibration, wall
and passage definitions, arrow/marker appearance settings, boundary settings,
room names/notes and imported room-library entries. Campaign copies also preserve
map order, description and saved wall sources. Passage endpoint IDs are regenerated;
connections among copied endpoints are remapped. A single-map copy detaches links
to endpoints outside that map; reconnect them explicitly if desired.

Copies start fully fogged, with no reveal history, last-display fog snapshots,
runtime door/passage/endpoint overrides, travel replay records, or session checkpoints.
A campaign copy belongs to the requesting DM, has no viewer assignments and no
active map. A map copy is appended in its existing campaign and never made active.
The source campaign, its viewer display and its runtime state are unchanged.

The operation requires campaign-management permission and CSRF validation; campaign
copy also requires campaign-creation permission. Database writes share one immediate
transaction. Images created before an error are removed after rollback. No migration,
new dependency, configuration change or port change is required. Large copies hold
the SQLite write transaction while validating and copying images; allow adequate disk
space and avoid concurrent bulk writes. Process termination can leave orphan image
files (as with other multi-resource operations); database commit is still transactional.

## Double-reveal authorization

Every double-reveal configuration, selection, preview, mutation and navigation request uses
`map_for_manage`. Campaign managers and authorized superadmins can operate it; other admins
cannot inspect the campaign's alternate artwork. Writes use the normal CSRF dependency and
reject stale version stamps. All routes are mounted exclusively on the admin application.
The viewer application has no raw alternate-image endpoint, room configuration response or
clickable navigation action. Same-campaign links are checked in services and enforced by
SQLite triggers. The data/maps directory must remain private rather than statically served.


## Scrying Glass lookup authorization

Only authenticated Looking Glass DMs who manage a map's campaign can check its saved
room-name match. The route is admin-only and CSRF-protected; geometry and note revision
are checked server-side. It is absent from viewer routing. The configured Scrying Glass
identity is shared server-side; remote campaign access still depends on that account's
ownership/role. Prefer an admin assigned only the relevant campaigns, rather than a
superadmin. Results distinguish no accessible campaign from a definite missing setup.
The browser never receives remote credentials or cookies. Checks do not activate or load
a campaign/setup. See [Scrying Glass integration](scrying-glass.md).

### Multiple setup variants

A verified room lookup now returns every exact or hyphen-boundary-prefixed setup name
within the already-authorized, uniquely matched campaign. It does not search other
campaigns or widen remote permissions. The success panel lists names only: no variant
is automatically selected, loaded or activated. Exact matches are labelled explicitly.
Names are rendered as text, not trusted HTML. Existing enabled/access gates, saved-name
checks, CSRF protection, geometry/revision checks and secret handling remain unchanged.
