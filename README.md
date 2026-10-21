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
[wall import](docs/foundry-import.md) and [patch notes](Patch/wall-source-library.md).

## Showing maps: reveal choice and cache isolation

Show controls check whether effective saved reveals exist. When they do, choose
Restore / Reset / Cancel; otherwise the target is shown with reset reveals. Saved checkpoints belong to one map instance;
deleting and importing a map starts a new instance, even when SQLite reuses
its numeric ID. See [the usage guide](docs/usage.md#choosing-reveals-when-showing-a-map)
and [the patch notes](Patch/fog-display-state.md).

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
[patch notes](Patch/wall-editor-uvtt.md). No new migration, runtime dependency
or configuration key is introduced. Blank players before saving changed boundaries:
existing fog operations are replayed and can reveal different areas.


## Door arrows and click-to-reveal

Admin single-click on a usable passage arrow reveals its destination. Ordinary
doors reveal the adjacent area; portals reveal a configured remote Exit on the
same map. Viewer arrows remain display-only. Independent admin/viewer visibility
settings are retained. Secret passages are hidden from viewers until discovered.
See `Passages.md` for the current contract and `Patch/passages.md` for deployment.

## Locked and unlocked doors

Author initial locked/unlocked states in the wall editor. Only admin arrow
double-click toggles locks; segment double-click does not. Secret doors and
individual secret portal Entries have authored post-discovery types. Their admin
arrow double-click discovers without revealing. Runtime changes persist until
Reset or wall replacement. Secret-door and portal arrows persist after use.

## Independent arrow visibility

Show door arrows (admin) controls the DM overlay/click targets; Show door arrows (viewer) controls the player image and exact viewer-image preview. Either screen can show arrows while the other hides them. Wall visibility, runtime lock state and fog history are unaffected. Migration 9 preserves each map's previous shared setting on both screens. The rolled-back Center/Fit controls remain excluded.


## Viewer double-click room zoom

In the player viewer, double-click a revealed room to fit and center that room. Double-click it again while it is already fitted and centered to return to the overview of all revealed areas. A double-click on another room focuses that room instead. Hidden areas do nothing. The Fit button/F shortcut always returns to the revealed-area overview. This is local read-only camera navigation: it never reveals fog or changes doors. See `docs/usage.md` and `Patch/viewer-room-zoom.md`.


## Admin-controlled viewer zoom

Double-click a revealed area in the admin fog editor to send the existing room-focus/overview toggle to connected viewer screens, without moving the admin camera. Ordinary area single-clicks wait 400 ms so the first click cannot reveal/hide fog before a double-click is recognized. Door and arrow gestures keep priority. Double-clicking directly in the viewer remains unchanged. The map must already be shown to players; hidden areas do not send commands. See `docs/usage.md` and `Patch/admin-viewer-zoom.md`.


## New reveals return focused viewers to overview

Whenever an additional revealed area appears, viewers focused on a specific room automatically leave that focus and fit/center all currently visible areas. This applies to focus chosen locally or from an admin double-click. Detection uses revealed-area membership, not just image versions, counts or the overall rectangle, so arrow/color/lock-only changes and repeated reveals of an already visible room do not unnecessarily clear focus. No database migration or new controls are added.

## Same-map portals

Draw Portal elements, then use Portal configuration to select one section and
edit its two compass-designated sides (map-top is North). Entry/Both sides select
a destination Portal section and compass side. Exit, Unconfigured and None sides
are selectable; Unconfigured/None becomes Exit in the popup, committed on Apply.
Both remains usable without losing its Entry role. Shared exits are supported;
every pair still contains exactly two sections. Cancel discards popup edits;
Apply is one undoable draft transaction. Complete all sections before Save/export.
See Passages.md and Patch/portal-compass-exits.md.

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
See Patch/portal-tools.md for installation and verification limits.
