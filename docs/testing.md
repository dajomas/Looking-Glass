# Testing and upgrade validation

This guide describes reproducible checks using files stored in the repository.
It is not a record of results for a particular release, archive or platform. Run
and record the relevant checks against the version and environment you will deploy.
Do not interpret a skipped module or a documented command as a passing test.

## Environment

Run commands from the repository root in a development virtual environment using
the project's supported Python version (Python 3.14). Install the development
requirements; these include the runtime requirements, pytest and httpx:

```sh
python -m pip install -r requirements-dev.txt
```

Node.js is required for the standalone JavaScript regression scripts. These scripts
use Node's built-in modules and do not require a JavaScript package installation.
Keep automated tests isolated from live campaign data. Back up the complete stopped
application data directory before performing manual upgrade or rollback checks.

## Python service and HTTP tests

Run the top-level suite, including HTTP tests but excluding browser tests:

```sh
python -m pytest -q python/tests --ignore=python/tests/browser
```

The HTTP tests require FastAPI and the installed project test dependencies. They
exercise application authentication, authorization and CSRF behavior. If an optional
module is skipped because a dependency is missing, install that dependency and rerun
it before claiming coverage of that integration.

For a focused cross-map passage check:

```sh
python -m pytest -q python/tests/test_map_transitions.py python/tests/test_transition_templates.py
python -m pytest -q python/tests/test_map_transitions_web.py
```

Other top-level tests cover fog, wall import/export, lock/discovery state, arrow
visibility, map activation, viewer zoom, cache identity and permission checks. Use
the full suite when changes affect shared behavior rather than testing a single
feature in isolation.

## JavaScript regression scripts

A focused UI check:

```sh
node python/tests/test_map_transitions.js
```

Run every top-level JavaScript regression script in PowerShell:

```powershell
Get-ChildItem python/tests/test_*.js | ForEach-Object {
    node $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "JavaScript regression failed: $($_.Name)" }
}
```

Or in a POSIX shell:

```sh
for test in python/tests/test_*.js; do
    node "$test" || exit 1
done
```

These scripts exercise helpers and DOM/transport mocks; they do not substitute for
real-browser rendering, pointer behavior, modal focus or network timing tests.

## Browser tests

Install the additional browser-testing dependency and Chromium in the development
environment. Playwright is not included in requirements-dev.txt:

```sh
python -m pip install playwright
python -m playwright install chromium
python -m pytest -q python/tests/browser
```

The machine also needs the browser's platform libraries. Follow the locally
installed Playwright tooling's dependency diagnostics if Chromium cannot launch.
The included browser fixtures use mocked HTTP responses, not a live production
campaign. For a focused cross-map placement check:

```sh
python -m pytest -q python/tests/browser/test_map_transitions.py
```

## Manual pre-deployment checklist

Use a copied campaign and at least one connected viewer:

- Map activation and fog: verify restore/reset choices, current exploration,
  Undo, blanking, map switching and cache isolation after deletion/reimport.
- Doors and passages: verify locked/unlocked clicks, discovery without revealing,
  reveal after unlock/discovery, reset to authored state, independent admin/viewer
  arrow preferences, and the portal/discovered-secret viewer exceptions. Confirm
  that undiscovered secrets and admin-only portal Exit hints remain hidden.
- Wall editing: verify Edit/right-click shortcuts, coordinate limits, Cancel/Apply,
  Undo/Redo, stale-save rejection, source assignment and UVTT export/import. Blank
  players before saving changed boundaries because fog operations replay against
  the new geometry.
- Portal configuration: verify compass side names, routing, incomplete-graph
  rejection, the overview, Apply without closing, Close/Escape discard scope,
  readable labels, route highlights and reduced-motion presentation.
- Viewer zoom: verify local room focus/overview, Fit/F, hidden-area no-op, admin
  double-click commands without admin camera movement or fog mutation, new-reveal
  overview behavior, resize and late-response handling. Test multiple viewers if
  they will be used during play.
- Cross-map travel: create one-way and return connections, inspect the Travel
  confirmation without executing it, verify Inspect destination leaves
  viewers and fog unchanged without a reveal-choice prompt, preserve existing exploration, test area arrival and
  large-reveal approval, reject a wall/out-of-bounds arrival, discover/reset a
  secret endpoint, reject stale preflight after another tab edits it, and show a
  broken link after deleting a target. Check marker/label persistence after restart.
- Access control: verify an unrelated DM and unassigned viewer cannot access the
  campaign, viewer clients cannot invoke admin mutations, and writes reject missing
  CSRF tokens. Confirm private passage destinations and DM notes are not exposed
  in player state or marker data.

## Scope and limitations

Record source revision, Python/Node/browser versions, operating system, command exit
codes and any skipped or unexecuted checks with your validation results. Passing
service tests does not establish HTTP/CSRF, real-browser, Windows/Python 3.14,
font rendering, shutdown or multi-client timing coverage unless those checks were
actually performed. Do not transfer historical results to a different source version.

Fog and arrow geometry retain raster-resolution, wall-gap and tight-room limits.
Test unusual map geometry and imported wall calibration with your own campaign
assets. See [usage](usage.md), [map controls](map-controls.md),
[wall editing](wall-editor.md) and [deployment](deployment.md) for behavior,
upgrade precautions and matching-code/database rollback guidance.


## Passage modal/sidebar regressions

```sh
python -m pytest -q python/tests/test_destination_display_options.py python/tests/test_transition_templates.py python/tests/test_sidebar_appearance.py
node python/tests/test_map_transitions.js
node python/tests/test_sidebar_sections.js
node python/tests/test_viewer_refresh.js
python -m pytest -q python/tests/browser/test_passage_modal_layout.py
```

The route-body test checks current/saved reveal independence using stub dependencies;
it is not an HTTP authentication/CSRF test. The browser tests require local Playwright
Chromium. Manually verify footer visibility at your screen dimensions and zoom,
read-only inspection and popup-blocked fallback, and legend closure staying respected as peer panels
change. No passing browser or full-server result is implied by these commands.


## Passage save-scope isolation

```sh
python -m pytest -q python/tests/test_passage_save_scopes.py
node python/tests/test_map_transitions.js
python -m pytest -q python/tests/test_map_transitions_web.py
python -m pytest -q python/tests/browser/test_passage_save_scopes.py
```

Stage edits in both groups; save each separately and verify only its own group is
persisted while the other remains pending. Test Close/Escape discard cancellation,
a new endpoint followed by a runtime update, server-normalized configuration values,
sequential revisions, failed/stale saves and Travel's saved-state warning. AST route
and Node mock tests do not replace real HTTP/CSRF and browser integration checks.


## Portal Close, Reset and Travel-return regressions

```sh
node python/tests/test_portal_modal_actions.js
node python/tests/test_map_transitions.js
python -m pytest -q python/tests/test_modal_action_templates.py
python -m pytest -q python/tests/browser/test_portal_apply.py python/tests/browser/test_travel_return.py
```

Test a clean Close, declined and accepted dirty Close/Escape, Apply followed by new
pending edits, paired-reset cancel/accept, and both travel return actions with both
save groups dirty. Verify no writes on return and a fresh preflight next time.
Use another tab to change a source after opening it; travel cancellation must not
silently rebase that editor's saved revision. Check Reset fog and show map only on
copied data and confirm the scope warning matches its existing effects. Node mocks
and template assertions are not substitutes for real-browser/live-server checks.

## Collapsible sidebar help

```sh
python -m pytest python/tests/test_admin_sidebar_help.py -q
```

Seven regression cases render the real editor and help partial. They cover
single/multiple-map visibility, retained passage binding targets, eight main
help disclosures (seven for a single map), five nested source subsections,
initial closed state, absence of accordion names, revised wording and retained
live status/warning elements. Tests use the standard-library HTML parser and
existing Jinja/pytest dependencies; no new test package is required.

Browser smoke check: open Help, confirm all topics are initially closed, expand
several topics and nested source subsections independently, toggle control panels,
and verify Help stays open. Check pointer and Tab/Enter/Space interaction and a
narrow viewport. Reload to verify that every disclosure starts closed again.

## Help surface styling

```sh
python -m pytest python/tests/test_help_background_styles.py -q
```

Three focused checks verify progressively lighter help surfaces, help-only CSS
selector scope and default-theme text/focus contrast. These are source-level
regressions, not browser layout tests. No additional test dependencies are used.

Manual check after a hard refresh: the collapsed Help control should be lighter
than Players/Fog/Walls. Expand Help and main topics to check their card surfaces;
expand Saved wall sources and its nested subsections to check the lighter nested
cards. Verify hover, Tab focus outlines, narrow layouts and independent toggles.

## Room-note regression checks

Run `PYTHONPATH=python pytest python/tests/test_room_notes.py` and
`node python/tests/test_room_notes.js` from the repository root. Existing gesture
harnesses now stub the independent room-note component. Full validation should
also run the complete pytest suite and all JavaScript test scripts with installed
runtime/development requirements. See Patch/room-notes.md for the actual patch
validation results and manual acceptance checklist.

### Room editor follow-up

`node python/tests/test_room_notes.js` now covers mutually exclusive view/edit
containers, toolbar actions, multiline formatting, Markdown MIME preference,
clipboard-read denial, length limits, Cancel, save failure/success, dirty selection
protection and collapse persistence. Run from the repository root. See
Patch/room-editor.md for actual validation and browser acceptance checks.

## Markdown room-note import regression checks

`PYTHONPATH=python pytest python/tests/test_room_note_import.py` covers heading
levels, nested/code exclusions, section preservation, Setext/BOM/CRLF, invalid
input, duplicate titles, idempotent imports, map scope and cascading deletion.
`node python/tests/test_room_notes.js` also covers empty-room eligibility, duplicate
name labels, draft population, no implicit save and Cancel. HTTP coverage is in
python/tests/test_room_note_import_web.py and requires installed dev dependencies.
See Patch/room-note-import.md for which checks actually ran in the patch environment.

## Room controls follow-up coverage

Run the existing JS room-note tests for populated-room replacement, notes-only
replacement, default import collapse, draft clear/Cancel and failed/successful
clear saves. python/tests/test_room_notes_controls.py verifies a pre-upgrade schema
migration preserves text/revisions/library, allows empty name/notes, retains
length limits, and preserves cascading deletion. The HTTP import/assignment test
also covers clearing, stale revision rejection and notes-only saves; it requires
the project's installed FastAPI development dependencies.

## Replacement confirmation regression tests

Run `node python/tests/test_keep_select_values.js` and
`node python/tests/test_room_notes.js` from the repository root. The first test
seeds an old remembered imported choice, simulates observed mutations and checks
that it never dispatches a synthetic change while ordinary dropdown restoration
still works. With the pre-fix helper this test produced 10 replays before its
bounded drain stopped it; with the fix it passes without any replay.

Room tests cover saved replacement without warning, edit/undo clean state, a real
unsaved draft, one prompt on OK/Cancel, consumed/reentrant events, and identical
import selection. Existing paste/clear/save/import behavior is also covered.

## Edit-only imported-note picker

The room-note JS tests now open Edit room before importing and verify the picker
is hidden during reading and visible while editing, including after assignment.
Read-mode action attempts are ignored. Existing confirmation OK/Cancel, undo and
no-replay checks remain. python/tests/test_room_import_edit_layout.py asserts the
picker is structurally inside room-form, not the read view.

## Unnamed room auto-edit regression cases

node python/tests/test_room_notes.js now verifies explicit checked-mode selection
of hidden/empty and revealed/notes-only unnamed rooms auto-opens a clean editor
with the imported-note picker. Named rooms, unchecked mode and nonexplicit
selections remain in read mode. The test also checks Cancel, no extra writes or
warnings, existing draft protection and retention of panel collapse state.
