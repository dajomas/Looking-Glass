# Looking Glass

Looking Glass is a fog-of-war tool for D&D battle maps. The DM imports map
artwork and wall geometry, then reveals or hides areas enclosed by those walls.
Players see a live, server-rendered fogged image on a separate viewer screen.
Raw map artwork, wall geometry and DM room notes are not sent to the viewer.

- Separate admin and player portals, with role-based access.
- Multiple campaigns, each containing multiple battle maps.
- SQLite storage and locally stored map images.
- Foundry VTT and Universal VTT wall imports, reusable wall sources and a wall editor.
- Room-based reveal/hide, undo, reveal all, reset, wall alignment and door controls.
- Same-map portals and DM-confirmed travel between campaign maps.
- Named rooms, Markdown notes and imported room-note libraries.
- Alternate room artwork, campaign backups, session checkpoints and clean duplication.
- Viewer room focus, DM-controlled viewer focus and synchronization status.

## Quick start

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Optional: create config.yaml only if it does not already exist.
cp config.example.yaml config.yaml
.venv/bin/python python/main.py
```

On first startup, the application creates a `superadmin` account and prints its
password in the log. Set `LG_SUPERADMIN_PASSWORD` before first startup to supply
that initial password. The account must change its password at first login.

| Portal | Default URL | Access |
|---|---|---|
| Admin (DM) | `http://<host>:5000` | Superadmins and admins |
| Viewer (players) | `http://<host>:5100` | Users authorized for the campaign |

Configuration is described in [the deployment guide](docs/deployment.md).
Back up the stopped application's configured database and map storage before
upgrades or other operations that can affect stored data.

## Repository layout

```text
/docs          Guides, examples and deployment resources
/python        Application package, entry point and tests
/static        CSS, JavaScript and images
/templates     Shared layouts, account and login templates, and partials
/web_html      Admin and viewer page templates
```

See [architecture](docs/architecture.md) for application structure.

## CLI

```bash
python python/main.py serve
python python/main.py create-user dm --role admin
python python/main.py reset-password superadmin
python python/main.py list-users
python python/main.py -c /etc/looking-glass/config.yaml serve
```

`serve` is the default command. Password reset also reactivates the account and
revokes its sessions.

## Tests

Install development requirements and run the Python suite:

```bash
.venv/bin/pip install -r requirements-dev.txt
cd python && ../.venv/bin/python -m pytest -q
```

The opt-in live end-to-end suite uses independent DM/player Chromium contexts,
real admin/viewer listeners, temporary application data and loopback ports:

```bash
bash runlive.sh
LG_RUN_LIVE_E2E=1 bash runtests.sh
```

The default runner excludes that opt-in suite. Browser tests require Playwright,
Chromium and the appropriate system libraries. See [testing](docs/testing.md)
for environment preparation, commands and suite scope.

The login helper also has an isolated regression check, runnable from the
repository root without Playwright: `python -m pytest -q python/tests/test_live_login_helper.py`.
It checks URL-string parsing and form actions with a page double; it does not
replace the live-browser suite. See the [validation record](docs/handover/025-ci-live-login-url-fix-2026-10-29.md).

## Documentation

- [Usage guide](docs/usage.md)
- [Architecture](docs/architecture.md)
- [Roles and permissions](docs/rbac.md)
- [Foundry VTT wall import](docs/foundry-import.md)
- [Wall editor](docs/wall-editor.md)
- [Doors and passages](docs/Passages.md)
- [Mouse controls](docs/mouse-controls.md)
- [Map controls](docs/map-controls.md)
- [HTTP API](docs/api.md)
- [Deployment](docs/deployment.md)
- [Testing](docs/testing.md)

## Accounts and access

- `superadmin`: manages users and has access to the admin portal.
- `admin`: manages owned campaigns and assigns viewers.
- `viewer`: views assigned campaigns through the player portal.

Users required to change their password can use account and logout routes but
cannot subscribe to viewer events. A successful password change clears that
requirement, revokes other sessions and retains the current session. Profile-only
saves are supported. Account-form validation finishes before account writes;
profile, password and session changes share one database transaction.

Viewer connections are associated with hashed session identities. Logout closes
connections for that session after session deletion. A changed user role or
account deactivation revokes sessions and disconnects that user's viewer sockets
after the database transaction commits. An active user's unchanged-role profile
save does not revoke sessions or disconnect sockets.

Session validity, active-user status, password-change requirements and campaign
access are checked before event/pong delivery and viewer status reports, and on
an idle recheck interval of 15 seconds. Scheduling, database and transport delays
can extend that interval. Immediate disconnect notifications are process-local;
other processes observe revocation through their checks. In-flight network data
cannot be recalled.

The process-local login throttle uses a rolling failure window and retains at
most 4,096 IP/username keys, with at most the configured failure-threshold
number of timestamps per key. Checks do not allocate entries. Checks and failures
reclaim expired histories under a lock; successful login resets its key.
At capacity, untracked keys are temporarily blocked without evicting active
histories. This can deny legitimate new-key logins until capacity recovers.
Checks do not reserve slots or cancel authentication already in progress.
Retention limits bound key/timestamp counts, not arbitrary key lengths or
traffic across processes. State resets on process restart.

## Campaigns, maps and wall sources

A campaign contains battle maps and viewer assignments. Import individual maps
or use **Import multiple maps and assign walls** to upload several images and
wall files, then explicitly assign a wall source and wall set to each map.
A source can serve multiple maps; filenames and selection order do not determine
pairing. See [batch imports](docs/campaign-batch-import.md).

Supported wall inputs include Foundry VTT scene exports (v9 to v13+), NeDB
`scenes.db`/`walls.db`, plain wall lists and Universal VTT `.dd2vtt`/`.uvtt` files.

Under **Walls → Saved wall sources**, save a source, choose a wall set and apply
it to a map. Each map has independent walls, alignment and fog operations.
Multi-set uploads alongside a map are saved for explicit selection; single-set
map uploads apply automatically and are saved for reuse. One-off editor imports
are also available without automatically creating a reusable source.

### Showing maps and exploration

When showing a map with effective saved reveals, choose **Restore**, **Reset** or
**Cancel**. A map without effective saved reveals is shown with reset reveals.
Saved display exploration belongs to that map instance; deleting a map and
importing another does not transfer it, even if the numeric map ID is reused.

Players receive fogged composite images. Fog edges soften inward, with reveal
coverage constrained so scaling and feathering do not expose hidden interiors.
Image and preview responses capture encoded bytes under the fog engine's per-map
lock. Each in-flight response holds those bytes in memory; this coordination
covers one engine instance, not external deletion or shared-cache processes.
Viewer image responses use `Cache-Control: no-store` and retain access/version
checks.

## Fog editor and map navigation

Left-click uses the selected Reveal/Hide mode. A stationary right-click applies
the inverse action without changing the selected mode; right-drag pans without
editing fog. The editor refreshes state after its first artwork load without
blanking the player screen or changing the active map.

The sidebar groups operational controls and collapsible help. **? Help** and its
topics start collapsed, open independently and support pointer and keyboard
interaction. Saved wall sources has nested help topics. The Map passages panel
and help topic are shown for campaigns with at least two maps; reload the editor
after changing the map count. Help surfaces are visually distinct from controls.

### Viewer room focus

Double-click a revealed room in the player screen to fit and center it.
Double-click that fitted room again to return to the revealed-area overview;
double-click another revealed room to focus it. Hidden areas do not respond.
The **Fit** button or **F** shortcut returns to the revealed-area overview.
These camera actions are local and read-only.

Double-click a revealed area in the admin fog editor to send the room-focus or
overview toggle to connected viewers without moving the admin camera. The map
must be shown to players. Ordinary admin area clicks wait 400 ms to distinguish
a single click from a double-click; door and arrow gestures have priority.

An additional revealed area returns focused viewers to the revealed-area
overview. Focus tracking uses area membership, so appearance-only changes and
repeated reveals of an already visible room do not clear focus unnecessarily.

### Viewer synchronization

Campaign pages and the editor's Players panel show recent viewer connections as
connected, loading, up to date, failed, or disconnected/reconnecting. Readiness
requires decoding and installing the current fogged image, or displaying the
waiting screen; a WebSocket connection alone is not proof of readiness.
The manager endpoint checks reports against the active map version, and the
viewer HUD shows local status. After a state error hides the image, a successful
response reloads and decodes the image before reporting readiness, even when
the image version is the same.

## Wall editor and UVTT export

Open **Walls → Open wall editor** from a map's fog editor. Add or remove segments,
choose among six wall types, change segment types and use Undo/Redo.
**Save wall set** applies geometry to the map and stores a reusable UVTT source.
**Download UVTT (current draft)** exports without saving and can include the
canonical map image. Original wall sources are immutable.

Blank the player screen before saving changed boundaries: replaying fog operations
against different geometry can reveal different areas. See
[wall editing](docs/wall-editor.md) and [the API](docs/api.md).

## Doors, portals and map passages

### Doors and visibility

An admin single-click on a usable passage arrow reveals its destination.
Door arrows reveal adjacent areas; same-map portal arrows reveal their configured
Exit. Viewer arrows are display-only. Secret passages stay hidden from viewers
until discovered.

Author locked/unlocked states in the wall editor. Admin arrow double-click toggles
locks; segment double-click does not. Secret doors and individual secret portal
Entries have authored post-discovery types, and their arrow double-click discovers
without revealing. Runtime states persist until Reset or wall replacement.
Secret-door and portal arrows persist after use.

Admin and viewer arrow visibility are independent. Disabling **Show door arrows
(viewer)** exposes separate portal and discovered-secret arrow options.
Still-secret entries remain hidden. Arrow visibility does not change walls,
runtime lock state or fog history.

### Same-map portals

Draw Portal elements, then configure each section's two compass-designated sides
(map-top is North). Entry/Both sides select a destination portal section and side.
Exit, Unconfigured and None sides are selectable; Unconfigured/None becomes Exit
in the popup and is committed on Apply. Both keeps its Entry role, shared exits
are supported, and every pair contains exactly two sections.

Apply commits one undoable draft transaction. Close/Escape confirms discarding
unapplied edits. Complete all sections before saving or exporting. The movable
popup supports dragging its title bar, keyboard movement and Center. Its read-only
Portal overview includes pending configuration without applying or saving it.

Visible enabled Entry-to-Exit routes can cycle through admin-only highlights.
Both arrows must be in the viewport and at least two routes must qualify.
The dwell-time slider ranges from 1 to 15 seconds, with 5 seconds as the default;
uncheck **Cycle visible Entry/Exit pairs** to pause. Preferences are local to the
browser and map. Highlights alternate yellow and blue phases; reduced-motion
presentation is steady. Section/compass labels use dark backing badges.

### Cross-map passages

Connect named stairway, ladder, hole/drop, portal, climb and custom endpoints
across maps in one campaign. Place and edit them under **Map passages** in the
fog editor, and inspect connections from the campaign overview.
Travel requires separate DM confirmation, preserves exploration and can reveal
an arrival area. Player markers are non-secret and clipped to visible fog.

The passage modal keeps actions visible while its form scrolls. **Inspect
destination** is admin-only and does not change the viewer or fog.
**Save configuration** and **Update session state** save separate groups while
preserving each other's pending edits. Close/Escape warns before discarding
unsaved changes; Travel uses saved values.

## Named rooms and DM notes

Enable **Select room (fog unchanged)** and click an interior to select it.
The right-hand Room notes panel displays its name and Markdown notes.
**Edit room** provides a formatting toolbar, Markdown-source paste and imported-note
selection. Selecting an unnamed room opens editing automatically and retains any
notes. Named rooms open in read mode. **Save room** or **Cancel** returns to the
read-only display. Revealing a room selects its notes; revealing it again does
not add a fog action. Room notes are DM-only.

An amber tint, outline and label identify the room being edited. Save/Cancel
removes that decoration without changing fog. **Show named / unnamed areas**
tints saved named areas green and unnamed areas red while selection mode is
enabled, including hidden areas in the admin view. Disabling selection mode
hides and resets this overlay.

### Importing and managing room notes

Import a UTF-8 Markdown file through **Import room notes**. The highest heading
level present defines room names; sections become Markdown notes. The library
is persistent and map-specific. Importing does not change fog or room content.
See [room-note examples](docs/examples/room-notes.md).

Choose an imported entry while editing a room, review the draft and save it.
Selection is a one-shot action. A confirmation appears when replacement would
discard a different unsaved draft; Cancel preserves that draft. Names already
saved on rooms in the same map are excluded from the picker, using trimmed,
case-insensitive matching. Unsaved drafts do not reserve names.

Clear a room's name, notes or both through **Edit room** and save the result.
Renaming or clearing the saved name releases it for another assignment without
deleting the imported library entry.

**List imported notes** shows names, Markdown and assignment status with persistent
heading and action controls while the entries scroll. Unassigned entries can be
deleted after confirmation; assigned entries are protected. **Unassign from rooms**
clears names and notes, including custom edits, from all matching rooms in that
map without deleting the library entry or changing fog. Save or cancel any
pending room draft before unassigning.

## Double-reveal room artwork

Upload an aligned alternate full-map image through **Double reveal**, select the
rooms that use it and reveal each room's true appearance explicitly. Visibility
and appearance are independent: hiding or resetting fog does not restore an
illusion. Optional DM-only destination-map links support discovered stairs
without automatic travel.

In fog mode, configured rooms have DM-only badges: amber **2** marks a room where
Ctrl-left-click reveals true artwork; cyan **↗** marks a subsequent Ctrl-left-click
that offers assigned-destination travel. Travel requires confirmation and a
visible source room on the current player map. Plain fog clicks use the selected
fog action. See [usage](docs/usage.md#double-reveal-rooms) and
[the API](docs/api.md#double-reveal-api).

## Campaign backup and restore

Use **Settings → Backup / Restore** to download a campaign-only ZIP or inspect
one before restoring it into the current campaign. Review compatibility, maps
and content counts, then select the identical ZIP and type the target name.
A validated pre-restore recovery ZIP is required and retained automatically.

Backups include map images, fog, walls, passages, connections and room notes.
Ownership and viewer assignments stay unchanged during restore. Accounts and
sessions are not exported. See [backup and restore](docs/usage.md#campaign-backup-and-restore).

## Campaign readiness

**Check campaign** produces a read-only preparation report covering map images,
missing walls, cross-map endpoints, room-note associations and expanded backup
capacity. DM-only inspection links do not make automatic repairs or change the
player screen. See [readiness checks](docs/usage.md#campaign-readiness-checks).

## Campaign-wide quick navigation

Use **Search campaign**, **Ctrl+K** or **⌘+K** to search maps, named rooms,
room-note text, passage endpoints and imported room-library entries.
Results open read-only DM inspection; they do not activate maps, reveal fog or
travel. A full search page works without JavaScript. See
[quick navigation](docs/usage.md#campaign-wide-quick-navigation).

## Named session checkpoints

**Session checkpoints** save named, campaign-wide play states. Restore includes
read-only compatibility and effects previews, campaign-name confirmation and an
automatic safety checkpoint. Authored maps, walls, connections, room notes and
permissions are not replaced. Checkpoints live in the installation database and
are not part of portable campaign ZIP backups. See
[session checkpoints](docs/usage.md#named-session-checkpoints).

## Clean map/campaign duplication

Use **Settings → Duplicate campaign** or a map's **Duplicate map** disclosure.
Copy names contain 1–120 non-whitespace characters. Copies preserve authored map
images as independent files, calibration, walls, passage definitions, display
settings, room names/notes and imported room libraries. Campaign copies also
preserve map order, descriptions and saved wall sources.

Passage endpoint IDs are regenerated. Connections within a copied campaign are
remapped; a single-map copy detaches links to endpoints outside that map, which
can be reconnected explicitly.

Copies start fully fogged, without reveal history, display fog snapshots,
runtime overrides, travel replay records or session checkpoints. A campaign copy
belongs to the requesting DM, has no viewer assignments and no active map.
A map copy is appended to its campaign and is not made active. The source
campaign and viewer state are not changed.

Duplication requires campaign-management permission and CSRF validation;
campaign copying also requires campaign-creation permission. Database writes
share an immediate transaction. Created images are removed after an error and
rollback. Large copies hold the write transaction while validating and copying
images, so allow disk space and avoid concurrent bulk writes. Process termination
can leave orphan image files even though database writes are transactional.

## Upload feedback and logging

Upload forms show an immediate busy status and prevent repeated submissions of
the same pending form. Batch, wall-source and room-note uploads have their own
completion and error handling.

Successful HTTP access records are suppressed by default; failed requests and
diagnostics are retained at the configured log level. Set
`server.access_log_success: true` for full HTTP access logging. See
[deployment](docs/deployment.md).

## GitHub Actions integration checks

The integration workflow is stored in
`.github/workflows/integration-tests.yml`. It defines four independent checks:

- `Python / HTTP`: Python 3.14 service and in-process HTTP/WebSocket tests,
  excluding the separate browser and live end-to-end directories.
- `JavaScript regressions`: every top-level `python/tests/test_*.js` script
  under Node.js 24, with per-script logs, exit inventory and JUnit reporting.
- `Browser / mocked HTTP`: the Playwright Chromium suite, including the
  existing standalone upload-busy regression through a pytest adapter.
- `Live Uvicorn`: the live end-to-end suite against real application listeners,
  using Python 3.14 and Playwright Chromium.

Browser jobs install Chromium/system dependencies and require the browser
preflight. All jobs retain evidence and reject missing, empty or failed JUnit
reports; reported skipped test cases also fail validation. JavaScript reports
count scripts rather than nested Node cases. The collector `getworkflow.sh`
automatically downloads and chunks all four artifact groups without changes.
A workflow definition is not evidence of a successful run, and merge gates
require separate repository settings. See [current CI details](docs/ci-tests.md)
for commands, artifacts, reporting scope, validation status and limitations.
