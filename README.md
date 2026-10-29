# Looking Glass

A fog of war tool for D&D battle maps. The DM imports a battle map plus its
**Foundry VTT walls**, then clicks a room in the admin screen. The whole area
enclosed by walls is revealed on the players' viewer screen, live.

- **Two entry points**: admin portal on port **5000**, viewer (player) screen on port **5100**
- **RBAC**: `superadmin` (manages users), `admin` (manages own campaigns and assigns viewers), `viewer` (views assigned campaigns only)
- **SQLite3** storage, no external services
- Multiple **campaigns**, each with multiple **battle maps**
- Imports **Foundry VTT** scene exports (v9 to v13+), NeDB `scenes.db`/`walls.db`, plain wall lists, and Universal VTT (`.dd2vtt` / `.uvtt`)
- Reusable campaign-scoped wall sources: save one database and choose a wall set independently for each battle map
- **Area reveal / hide**, undo, reveal all, reset, a door toggle, and wall alignment tools
- Players only ever receive a **server-rendered, fogged image**. The raw map and walls never reach the viewer port.

## Quick start

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp config.example.yaml config.yaml          # optional
.venv/bin/python python/main.py             # starts both portals
```

The first start creates a `superadmin` account and prints its password in the
log. You must change it at first login. Alternatively set
`LG_SUPERADMIN_PASSWORD=...` before the first start.

| Portal | URL | Who |
|---|---|---|
| Admin (DM) | `http://<host>:5000` | superadmin, admin |
| Viewer (players) | `http://<host>:5100` | anyone assigned to a campaign |

## Repository layout

```
/repo-root
|-/docs          documentation, examples (demo map + Foundry scene, systemd unit)
|-/python        application code (package: looking_glass) + tests
|-/static        CSS, JavaScript, images served at /static on both ports
|-/templates     shared Jinja2 layouts and partials (base, nav, login, account, error)
|-/web_html      page templates per entry point: admin/*.html and viewer/*.html
```

More detail in [docs/architecture.md](docs/architecture.md).

## CLI

```bash
python python/main.py serve                      # default
python python/main.py create-user dm --role admin
python python/main.py reset-password superadmin  # also reactivates and revokes sessions
python python/main.py list-users
python python/main.py -c /etc/looking-glass/config.yaml serve
```

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
cd python && ../.venv/bin/python -m pytest -q
```

## Documentation

- [Usage guide](docs/usage.md)
- [Architecture](docs/architecture.md)
- [RBAC](docs/rbac.md)
- [Foundry VTT wall import](docs/foundry-import.md)
- [HTTP API](docs/api.md)
- [Deployment (Podman, systemd, reverse proxy)](docs/deployment.md)

## Reusing a walls database

In the map editor, open **Walls → Saved wall sources**, save the Foundry database,
choose the saved source and wall set, and press **Apply selected wall set**. On a
second map in the same campaign, choose that saved source without uploading it
again. Each map keeps independent walls, alignment, and fog operations.

Uploading a multi-set source alongside a map saves it for explicit selection in
the editor instead of silently applying the first set. Single-set map uploads
continue to apply automatically and are also saved for reuse. One-off editor
imports remain available and are not automatically saved.

Schema migration 2 adds source uploads to the existing application database.
Back up the stopped application's data directory before upgrading. No new
runtime dependencies or configuration keys are required. See
[wall import](docs/foundry-import.md) and [deployment](docs/deployment.md).

## Showing maps: reveal choice and cache isolation

Show controls check whether effective saved reveals exist. When they do, choose
Restore / Reset / Cancel; otherwise the target is shown with reset reveals. Saved checkpoints belong to one map instance;
deleting and importing a map starts a new instance, even when SQLite reuses
its numeric ID. See [the usage guide](docs/usage.md#choosing-reveals-when-showing-a-map)
and [deployment](docs/deployment.md).

## Batch campaign imports and wall assignment

The campaign page retains its single-map import and adds a separate **Import
multiple maps and assign walls** section. Select multiple map images and/or
Foundry VTT / UVTT (Universal VTT) wall files, then explicitly assign a saved
wall source and wall set to each new or existing campaign map. One wall source
can be reused for many maps. No filename or selection-order pairing is assumed.
See [the workflow](docs/campaign-batch-import.md).

## Quick inverse mouse action

In the admin map editor, a stationary right-click temporarily inverts the
selected Reveal/Hide mode. Reveal mode + right-click hides; Hide mode + right-click
reveals. The selected mode does not change. Left-click uses the selected mode.
Right-drag still pans and never edits fog. See [mouse controls](docs/mouse-controls.md).

The editor also performs a non-mutating state refresh after the first artwork
load. This provides the refresh previously obtained through the reported Blank
workaround without blanking the player screen or changing the active map.

## Separate wall editor and UVTT export

Open **Walls → Open wall editor** from a map's fog editor. Add or remove segments,
choose all six supported wall types, change an existing segment's type and use
Undo/Redo. **Save wall set** applies the geometry to this map and stores a reusable
UVTT source. **Download UVTT (current draft)** exports without saving, optionally
including the canonical map image. Original sources remain immutable.

See [the wall editor guide](docs/wall-editor.md), [usage](docs/usage.md#separate-wall-editor-and-uvtt-saving),
[API](docs/api.md#dedicated-wall-editor-and-uvtt-export-admin-only) and
[deployment](docs/deployment.md). No new migration, runtime dependency
or configuration key is introduced. Blank players before saving changed boundaries:
existing fog operations are replayed and can reveal different areas.


## Door arrows and click-to-reveal

Admin single-click on a usable passage arrow reveals its destination. Ordinary
doors reveal the adjacent area; portals reveal a configured remote Exit on the
same map. Viewer arrows remain display-only. Independent admin/viewer visibility
settings are retained. Secret passages are hidden from viewers until discovered.
See `docs/Passages.md` for the current contract.

## Locked and unlocked doors

Author initial locked/unlocked states in the wall editor. Only admin arrow
double-click toggles locks; segment double-click does not. Secret doors and
individual secret portal Entries have authored post-discovery types. Their admin
arrow double-click discovers without revealing. Runtime changes persist until
Reset or wall replacement. Secret-door and portal arrows persist after use.

## Independent arrow visibility

Show door arrows (admin) controls the DM overlay/click targets; Show door arrows (viewer) controls the player image and exact viewer-image preview. Either screen can show arrows while the other hides them. Wall visibility, runtime lock state and fog history are unaffected. Migration 9 preserves each map's previous shared setting on both screens. The rolled-back Center/Fit controls remain excluded.


## Viewer double-click room zoom

In the player viewer, double-click a revealed room to fit and center that room. Double-click it again while it is already fitted and centered to return to the overview of all revealed areas. A double-click on another room focuses that room instead. Hidden areas do nothing. The Fit button/F shortcut always returns to the revealed-area overview. This is local read-only camera navigation: it never reveals fog or changes doors. See [usage](docs/usage.md) and [testing](docs/testing.md).


## Admin-controlled viewer zoom

Double-click a revealed area in the admin fog editor to send the existing room-focus/overview toggle to connected viewer screens, without moving the admin camera. Ordinary area single-clicks wait 400 ms so the first click cannot reveal/hide fog before a double-click is recognized. Door and arrow gestures keep priority. Double-clicking directly in the viewer remains unchanged. The map must already be shown to players; hidden areas do not send commands. See [usage](docs/usage.md) and [testing](docs/testing.md).


## New reveals return focused viewers to overview

Whenever an additional revealed area appears, viewers focused on a specific room automatically leave that focus and fit/center all currently visible areas. This applies to focus chosen locally or from an admin double-click. Detection uses revealed-area membership, not just image versions, counts or the overall rectangle, so arrow/color/lock-only changes and repeated reveals of an already visible room do not unnecessarily clear focus. No database migration or new controls are added.

## Same-map portals

Draw Portal elements, then use Portal configuration to select one section and
edit its two compass-designated sides (map-top is North). Entry/Both sides select
a destination Portal section and compass side. Exit, Unconfigured and None sides
are selectable; Unconfigured/None becomes Exit in the popup, committed on Apply.
Both remains usable without losing its Entry role. Shared exits are supported;
every pair still contains exactly two sections. Close/Escape confirm discard of unapplied popup edits;
Apply is one undoable draft transaction. Complete all sections before Save/export.
See [passages](docs/Passages.md) and [wall editing](docs/wall-editor.md).

## Portal editor overview and pair highlighting

The wall editor's portal popup is movable: drag its title bar, use arrow keys on
the focused title bar (Shift moves farther), or choose Center. A lighter modal
backdrop keeps the map visible without allowing accidental background edits.
Portal overview opens a read-only grid of compass sides, roles, counterpart
connections, authored initial states and secret outcomes. Inside the popup it
includes pending edits; it never applies or saves them.

On the admin fog page, enabled visible Entry→Exit routes are highlighted in turn,
5 seconds per route by default. The 1–15 second slider changes dwell time; uncheck
Cycle visible Entry/Exit pairs to pause. Both arrows must be in the viewport and
at least two routes must qualify. Preferences are local to this browser/map. The
gold pulse is admin-only; arrow clicking, viewer images and fog state do not change.
See [deployment](docs/deployment.md) and [testing](docs/testing.md) for installation and validation guidance.

## Portal overlay readability

Wall-editor section/compass labels have semi-transparent dark backing badges with
white text and a light border. Admin route highlights now alternate full-opacity
yellow/black-outline and blue/white-outline phases, making the selected pair more
distinct from the artwork. Reduced-motion remains steady; viewer images, route
selection, hit targets and data are unchanged. See [wall editing](docs/wall-editor.md) and [map controls](docs/map-controls.md).


### Viewer arrow exceptions

Disable Show door arrows (viewer) to expose independent, indented portal and discovered-secret arrow options. Still-secret entries remain hidden. See [usage](docs/usage.md) and [deployment](docs/deployment.md) for behavior and installation.


### Cross-map passages

Connect named stairway, ladder, hole/drop, portal, climb and custom endpoints across
maps in one campaign. Place/edit them under Map passages in the admin fog editor;
travel is a separate DM confirmation, with preserved exploration, optional arrival
area reveal and non-secret fog-clipped player markers. The campaign page includes
a connection overview. See [usage](docs/usage.md), [deployment](docs/deployment.md)
and [testing](docs/testing.md). Requires
automatic schema migration 12; back up the database before installation.


### Passage modal and sidebar workflow

The Map passage modal keeps its main actions visible in a bottom footer while the
form scrolls. Inspect destination is admin-only, with no viewer/fog mutation or
Restore/Reset prompt. Save configuration and Update session state save separate
groups, keep the modal open and preserve each other's pending edits. Close/Escape
warn before discarding unsaved changes; Travel still uses saved values.
Map passages is above Walls in the fog-editor sidebar. Peer sections start closed
and open exclusively; Wall legend and types starts open and remains independently
manually closable. See [usage](docs/usage.md) and [testing](docs/testing.md).

## Collapsible map-editor help

The left sidebar’s `? Help` control contains eight independent help topics:
Players; Fog and navigation; Door arrows; Wall alignment; Wall types; Map
passages; Saved wall sources; and Replace map image. Help and every topic start
collapsed on each page load. Expand a heading with a pointer or Tab followed by
Enter/Space. Multiple topics can remain open, independently of the editor’s
control-panel accordion. Expansion state is not persisted across reloads.

Saved wall sources contains five further collapsed subsections: Sources and
wall sets; Save and apply walls; What applying changes; Reuse, refresh and
delete; Supported files. Closing a parent hides its children without resetting
their open state until the page is reloaded.

For a campaign with one map, Map passages and its help topic are hidden; the
other seven help topics remain available. With two or more maps, all eight are
shown. Reload the editor after changing the campaign’s map count. This changes
presentation only, not saved endpoints or passage APIs.

Static sidebar instructions live in Help. Live errors, warnings, counts and
statuses stay beside their controls; action-specific modal guidance is unchanged.

## Help background styling

Help uses lighter blue-grey surfaces than the regular sidebar so instructions
are visually distinct from operational controls. The outer `? Help` container is
`#263143`, main topic cards are `#303e53`, and nested Saved wall sources cards
are `#3a4a61`. Hover and keyboard focus use `#435570`; keyboard focus also keeps
an accent outline. The regular sidebar remains `var(--bg-2)` (`#1a202c` in the
default theme). Help text retains `var(--text)`.

These styles apply only inside `#editor-help`. They affect both collapsed
headings and expanded content without changing disclosure behavior: all help
topics/subtopics still start closed and open independently. Regular feature
panels, dialogs, map and viewer are unchanged.

After deploying this CSS-only follow-up, hard-refresh the admin page to bypass
cached `admin.css`. No template, JavaScript or database changes are required.

## Named rooms and DM notes

The admin map editor includes a collapsible right-hand Room notes panel. Select
“Select room (fog unchanged)”, click an interior, then click Edit room to enter
a name and Markdown. Save room or Cancel returns to the read-only display.
A formatting toolbar and Markdown-source paste support are provided. Switch selection mode off for normal fog gestures. Revealing a room
shows its notes; revealing it again selects the notes without adding a fog action.
Notes are never sent to the viewer app. See docs/usage.md and Patch/room-notes.md.

## Markdown room-note import

Import room notes in the admin editor from a UTF-8 Markdown file (the import section starts collapsed). The highest
heading level present defines room names; sections become Markdown notes. For any
selected room, click Edit room, choose an imported entry in the dropdown, review the replacement
draft and Save room. Libraries are persistent and map-specific; importing never changes fog or
existing rooms. See docs/usage.md and docs/examples/room-notes.md.

Room metadata can be removed with Edit room → Clear name and notes → Save room.
Names and notes may also be cleared individually. Cancel restores the saved values.

## Room import confirmation fix

Imported-room selection is a one-shot action, excluded from remembered dropdown
restoration. Selecting a replacement for saved content does not prompt. The
replacement warning appears only when it would discard a different unsaved draft;
OK applies once and Cancel preserves the draft. Undoing edits back to saved values
clears the unsaved state. See Patch/room-confirmation.md for the cause and tests.

## Automatic editing for unnamed room selection

With Select room (fog unchanged) enabled, explicitly selecting an unnamed room
opens Room notes edit mode automatically, including the imported-note picker.
Existing notes are retained. Named rooms still open in read mode.

## Available imported room names

The edit-mode imported-note dropdown hides names already saved on rooms in the
same map. Save a rename or clear the name to release it for another assignment.
Matching trims surrounding whitespace and ignores case; unsaved drafts do not
reserve names. Imported records are retained, not deleted.

## Room edit marker and imported-note management

While editing room notes, an amber tint/outline and Editing room notes label mark
the selected room on the admin map. Save/Cancel removes only this decoration;
fog is never temporarily changed. In Import room notes, List imported notes opens
all names/Markdown with assignment status. Confirm deletion of unassigned entries;
assigned entries are protected by both UI and server validation.

## Named / unnamed area overview

Enable Select room (fog unchanged), then use Show named / unnamed areas beneath
it to tint saved named areas green and unnamed areas red. The same button hides
the colours; unchecking selection mode hides/resets them too. Admin-only coverage
includes hidden areas without changing fog. The amber edit marker stays above it.

## Imported room list: fixed controls and unassign

The imported-note dialog keeps its heading, Close/Refresh controls, instructions
and status visible while entries scroll. Assigned entries offer **Unassign from
rooms** with confirmation. This clears the saved name and notes from every
matching room in this map, including custom note edits, without deleting the
imported library entry or changing fog. The imported name becomes available again.
Save/cancel a pending room draft before unassigning. See docs/usage.md and
Patch/imported-room-list.md for details and validation.

## Campaign backup and restore

Campaign Settings now includes **Backup / Restore**. Download a campaign-only ZIP
or inspect one before restoring it into the current campaign. Preview compatibility, map
list and content counts, then select the identical ZIP and type the target name. A validated
pre-restore recovery ZIP is required and retained automatically. Includes map images,
fog, walls, passages, connections and room notes. Ownership and viewer assignments
stay unchanged; accounts and sessions are never exported. See [usage](docs/usage.md#campaign-backup-and-restore)
and [step 4 patch notes](Patch/step-4-backup-inspection.md). No database migration or new dependency is required.

## Campaign readiness

Use **Check campaign** on a campaign page for a read-only preparation report with
DM-only inspection links. Checks cover map images, missing walls, cross-map endpoints,
room-note associations and expanded backup capacity. No automatic repairs or player-screen
changes are made. See [the usage guide](docs/usage.md#campaign-readiness-checks).

## Campaign-wide quick navigation

On campaign-context admin screens, select **Search campaign** or press **Ctrl+K**
(**⌘+K** on macOS) to search maps, named rooms, room-note text, passage endpoints
and imported room-library entries. Results open read-only DM inspection; they never
activate a map, reveal fog or travel. A full search page works without JavaScript.
See [usage](docs/usage.md#campaign-wide-quick-navigation).

## Named session checkpoints

Use **Session checkpoints** on campaign-context admin pages to save and restore named,
campaign-wide play states. Restore includes a read-only compatibility/effects preview,
campaign-name confirmation and an automatic safety checkpoint. Authored maps, walls,
connections, room notes and permissions are not replaced. Checkpoint history is local
to the installation database, not portable campaign ZIP backups. See
[usage](docs/usage.md#named-session-checkpoints) and migration notes in deployment.

## Viewer synchronization status

Campaign pages and the fog editor's Players panel now show each recent viewer connection
as connected, loading, up to date, failed, or disconnected/reconnecting. A WebSocket alone
is not proof that the map loaded: readiness is reported only after the viewer decodes and
installs the current fogged image (or shows the waiting screen). The manager endpoint checks
that report against the currently active map version. The viewer HUD also shows its local
status. See [usage](docs/usage.md#viewer-synchronization-status) and
[step 5 patch notes](Patch/step-5-viewer-sync.md). No migration or dependency is added.

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

## Import feedback and quieter logs

File-upload forms display an immediate busy status and prevent repeated submits
in the same pending form. Batch, wall-source and room-note uploads retain their
own completion/error handling. See docs/usage.md for scope and retry guidance.
Successful HTTP access records are suppressed by default; failed HTTP requests
and diagnostics are retained at the configured log level. Set
`server.access_log_success: true` to restore full HTTP access logging for debugging.
See docs/deployment.md. No migration or new runtime dependency is needed.

## Double-reveal room artwork

The fog editor now has a **Double reveal** panel. Upload an aligned alternate full-map image,
select the rooms that use it, and reveal each room's true appearance explicitly. Fog visibility
and appearance are independent: hiding/resetting fog never restores an illusion. Optional
DM-only destination-map links support newly discovered stairs without automatic travel.

See [Usage](docs/usage.md#double-reveal-rooms), [API](docs/api.md#double-reveal-api),
and the delivery notes in `Patch/DOUBLE_REVEAL_CHANGES.md`. This feature adds schema
migration 17; back up the database and map storage before upgrading.


## Test-result follow-up for 6ea80e0

The follow-up patch clarifies saved-source upload and passive-wall labels and
aligns wall-type HTTP regression tests with the existing `disabled_wall_types`
request schema (422 on invalid input). It does not add a `disabled` alias or
change runtime wall/fog behavior. See [the API contract](docs/api.md#wall-type-boundary-request-contract)
and [browser-test host setup](docs/testing.md#rocky-linux-10--wsl-browser-preflight).
Patch/ contains change notes, measured validation results and a commit message.


## Rocky browser preflight follow-up (eee89c4)

The browser preflight now distinguishes DOM content from rendered text and logs
font configuration, font matching and both observed text values. Rendering
failures remain failures; they are not bypassed by checking DOM content alone.
See [Rocky/WSL test-host setup](docs/testing.md#rocky-linux-10--wsl-browser-preflight)
for native Fontconfig/fonts installation, configuration recovery and rerunning
`python -u python/tests/check_browser_environment.py` before `bash runtests.sh`.
No application behavior, browser flags, database schema or production dependencies
are changed by this follow-up. Patch/ records scope and measured validation.


## Browser harness follow-up (a24b7d0)

Browser tests share one session-scoped synchronous Playwright/browser lifecycle
from python/tests/browser/conftest.py. Do not re-export browser from test modules
or start overlapping drivers. Function cleanup closes leftover contexts after
failed setup; the batch fixture closes its page and local HTTP server in finally.
Batch readiness uses initialized controls with aria-busy=false, not a Ready
message. Result checks use separate map/source/failure/editor-warning counts
and verify Apply never calls window.confirm. Production behavior is unchanged.

Run python -m pytest --setup-plan -q python/tests/browser to check fixture
resolution (not UI execution), then python -m pytest -ra python/tests/browser.
Measured results and limitations are recorded in Patch/.


## Batch confirmation regression correction (2b81e59)

The empty-upload/no-confirm browser regression initializes its confirmation spy
through an explicit page.evaluate callback. It checks zero calls before Apply,
no writes on empty submission, and the exact selected assignment afterward.
This is a test-only correction: production behavior, shared browser lifecycle,
dependencies and schema are unchanged. See docs/testing.md for focused commands
and Patch/ for change notes, prior measured validation and remaining limitations.


## Browser regression repairs (9f3be8f follow-up)

Browser fixtures now fall back to real project partials behind explicit test
layout overrides. Minimal gesture and viewer tests load current script
prerequisites; exact timer tests use frozen virtual time and image-edge tests
ensure their click is inside the viewport. Production floating portal dialogs
are clamped again when their content changes size, and empty saved wall sources
show an explicit empty-state message. Normal clicks, payload assertions and
pixel thresholds are retained. See docs/testing.md and Patch/ for measured
validation, scope and remaining visual-test limitations.


## Browser fixture contract follow-up (bd7bf83)

The mocked editor harness now supplies the read-only viewer-status endpoint,
keeps metadata helpers out of the standalone dropdown test, and declares UTF-8
in HTML layout overrides. Passage fixtures provide two maps, matching the UI's
multi-map prerequisite. Native sidebar controls are exercised after opening their
actual disclosures, not by assuming they start open. Production code is unchanged
in this follow-up. See docs/testing.md and Patch/ for validation and limitations.


## Arrow-mask and inspection fixture follow-up (a83394c)

Mocked editor pages now return a correctly sized, fully transparent door-arrow
PNG only for their own map when they declare no authored arrows or portal routes.
Authored-arrow fixtures retain their own renderers. Destination-inspection tests
mock the new tab's document on the browser context, not just its parent page,
and remove that route afterward. These corrections change test coverage only;
no production rendering, security, fog or database behavior changes.
See docs/testing.md and Patch/ for validation and remaining limitations.

## Browser-regression validation and portal paint probe (base f4d60c3)

The supplied f4d60c3 local run confirms that the secondary-click and both
wall-width cases pass. Its remaining browser failure is the portal-label
zoom-2.5 single-pixel check. This follow-up changes only that test's paint probe:
geometry is checked with text visible; background fill is sampled independently
using screenshot-only text hiding and a central 3x3 region on all four labels.
The <110 darkness threshold is unchanged. Six negative controls reject missing
and white fills at all three zoom levels.

The updated portal module passed 13 tests in 7.14s in the assistant environment.
The complete post-follow-up browser suite has not been rerun on your host.
See `Patch/CHANGES.md` and `Patch/VALIDATION.md` for scope and verification.

## Live end-to-end tests (batch 1, base 58dd6a1)

A separate opt-in suite connects independent DM/player Chromium contexts to real
admin/viewer Uvicorn listeners, with no HTTP interception or WebSocket mocks.
Four scenarios cover room reveal/privacy, hide/undo propagation, switching maps,
and offline preparation. Each test uses temporary SQLite/images/cache and
OS-assigned loopback ports. It does not use your running campaign or config.

```bash
source .venv-test/bin/activate
bash runlive.sh
# Include this additional group in the normal runner:
LG_RUN_LIVE_E2E=1 bash runtests.sh
```

The existing default runner explicitly excludes this additional suite. A default
suite pass is not a live-E2E pass. Prerequisites: existing development/runtime
requirements, Playwright and installed Chromium/system libraries. See
`docs/testing.md` and `Patch/VALIDATION.md`; live execution is pending in this
patch, since the assistant environment lacks FastAPI and Uvicorn.


## Double Reveal directly from fog mode

Configured rooms now show DM-only badges: amber `2` means Ctrl-left-click reveals true
artwork, then cyan `↗` means a later Ctrl-left-click offers assigned-destination travel.
Travel keeps confirmation and requires a visible source room on the current player map.
Plain fog clicks retain their meaning. Wrapping checkboxes and Done — return to fog are
included; the redundant fog-mode paragraph stays removed. See docs/usage.md and
Patch/DOUBLE_REVEAL_FOG_CHANGES.md.


## Bug-fix backlog

[TODO.md](TODO.md) tracks the 15 bug-hunt findings, proposed solutions and
acceptance checks. Fix them one at a time on `features/perplexity`, with an
individually reviewed implementation and recorded validation. All entries start
open; the earlier combined draft was not committed. See [HANDOVER.md](HANDOVER.md)
for the current recovery context and delivery workflow.

## Fog-edge privacy (bug 1)

Viewer fog softens inward only: neither scaling the reveal mask nor feathering
may expose a hidden room interior. Wall coverage is retained, but dilation is
clipped before it can enter another hidden open component. A new fog-cache
identity prevents reuse of composites generated by the previous renderer.
No migration, dependency, configuration key or port change is introduced.

Run `python -m pytest -q python/tests/test_fog.py python/tests/test_fog_privacy.py`
from the repository root. Tests use lossless PNG output for exact pixel checks;
see HANDOVER.md for measured validation and outstanding integration checks.

## Viewer state recovery (bug 3)

A successful same-version state response can skip image loading only while the
previous decoded image is still displayed. If a state error hid the stage, the
viewer decodes and installs the current image again before reporting Up to date.
Already visible maps keep the fast path; blank states and stale-response guards
retain their existing behavior. Reload viewer tabs after deployment to load the
updated script URL. No backend, migration or dependency change is required.

Run `node --test python/tests/test_viewer_refresh.js` from the repository root;
see HANDOVER.md for measured regression results and integration limitations.

## Composite response lifetime (bug 4)

Viewer image and admin viewer-preview routes capture encoded composite bytes
under the fog engine's existing per-map reentrant lock before returning an HTTP
response. Managed cache invalidation or a newer render can then delete the cache
file without breaking response delivery. Rendering and reading remain off the
event loop via `asyncio.to_thread`. Viewer access/version rechecks, image media
types and `Cache-Control: no-store` are retained; raw-map routes are unchanged.

The bug 1 inward-only fog protections and bug 3 viewer-recovery implementation
are preserved. No schema, configuration or dependency change is required. This
lock coordinates one FogEngine instance, not external deletion or multiple
processes sharing a cache. Each in-flight response holds its encoded image bytes.

Regression commands and measured limitations are recorded in HANDOVER.md.

## Viewer socket session lifetime (bug 5)

Viewer sockets are bound to hashed session identities. Logout closes sockets for
that session after deleting it, without disconnecting other sessions of the same
user. Session validity and current campaign access are checked before each event
and pong, before accepting status reports, and at most every 15 seconds while
idle. Invalid sockets close with code 4403 and leave the synchronization tracker.
A socket admitted just as logout occurs is rechecked after subscription.

The event hub and explicit kicks serialize each socket's delivery and closure;
already in-flight network data cannot be recalled. Immediate logout notification
is local to the shared in-process hub; other processes observe revocation through
their checks. The 15-second idle interval excludes event-loop/DB/transport delays.
No schema, configuration or dependency change is required. Bugs 6 (explicit role
change kicks) and 7 (forced-password-change admission) remain separate TODO items.
See HANDOVER.md for regression commands, measured results and integration limits.

## Role-change socket revocation (bug 6)

Saving a changed user role now disconnects that user's viewer sockets after the
user/session transaction commits, matching the existing session-revocation rule.
This applies to promotions as well as demotions because both already invalidate
sessions. Deactivation keeps its existing disconnect behavior. An active user's
unchanged-role/profile save does not revoke sessions or disconnect sockets.
Other users are unaffected; rejected or rolled-back updates do not trigger kicks.
The bug 5 session checks remain unchanged. No schema, configuration or dependency
change is required. See HANDOVER.md for measured tests and ASGI acceptance limits.

## Forced-password-change viewer gate (bug 7)

A user required to change their password cannot accept a viewer WebSocket or
subscribe to campaign events, regardless of role. After a connection is admitted,
the existing session checks also reject a newly required password change before
event/pong delivery or status reports, and during the bounded idle recheck.
The close code is 4403. Existing account/password-change and logout routes remain
available; after a successful password change the user can reconnect normally.
No viewer mutation API, schema, configuration or dependency change is introduced.
Bugs 5 and 6 remain otherwise unchanged. See HANDOVER.md for measured validation
and outstanding ASGI/deployment acceptance.

## Atomic account form validation (bug 8)

Failed password-change forms no longer save a submitted display name. Current
password, minimum length, confirmation and different-password checks finish before
any account write. Valid profile-only saves remain supported; valid password
changes still clear the required-change flag and revoke other sessions while
retaining the current session. Profile/password/session writes share one database
transaction. Both portals use the same handler. No schema, dependency or setting
change is required. See HANDOVER.md for measured validation and HTTP acceptance limits.

## Bounded login-throttle retention (bug 9)

The in-process login throttle retains at most 4,096 active IP/username keys and
only the newest configured failure-threshold timestamps per key. Check-only
requests do not create entries; subsequent checks or failures also reclaim
expired histories for abandoned keys. Existing rolling-window expiry, username
case handling and successful-login reset remain unchanged.

At capacity, untracked keys are temporarily blocked rather than evicting active
histories. This can deny legitimate new-key logins until histories expire or a
tracked successful login resets its key. Already-started authentication is not
cancelled and checks do not reserve slots. The cap bounds key/timestamp counts,
not total bytes of arbitrary-length keys or deployment-wide request traffic.
State remains process-local and resets on restart. Cleanup is request-driven,
not a background timer, and scans the bounded table under its existing lock.
No migration, configuration key or dependency is added. See HANDOVER.md for
measured tests, the capacity-race limitation and pending HTTP/deployment acceptance.
