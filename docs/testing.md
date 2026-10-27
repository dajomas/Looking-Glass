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

## Imported-name availability tests

python/tests/test_room_note_availability.py covers pre-existing/manual matching
names, case/whitespace normalization, same-name variants, per-map scope, rename,
clear, duplicate saved names and retaining original library entries. The UI test
checks hiding assigned options, ignoring unavailable action IDs and disabling
an exhausted dropdown. HTTP integration coverage checks assigned flags after
save and clear; full FastAPI dependencies are required to run that file.

## Edit marker and imported-note manager coverage

python/tests/test_room_library_tools.py verifies an edit mask highlights only its
room without changing labels, deletion refuses assigned/wrong-map entries, names
remain protected when notes differ, and allowed deletion leaves map rooms/fog
untouched. node python/tests/test_room_edit_marker.js covers highlight lifecycle,
late responses, geometry invalidation and errors. node
python/tests/test_room_library_manager.js covers all-entry listing, safe source text,
assigned-button protection, deletion Cancel/success and changed-assignment errors.
The room-note harness checks edit-mode transition callbacks. HTTP integration tests
were extended for overlay invariance, stale geometry, deletion CSRF/access and
assigned protection, and require the full installed FastAPI dev dependencies.

## Name coverage overlay regression tests

python/tests/test_room_name_overlay.py verifies green/red classification, note-only
and whitespace-name handling, geometry-detached records, counts, transparent walls,
clear transitions and unchanged label data. The HTML placement test checks the
button immediately follows the checkbox and starts hidden/unpressed. node
python/tests/test_room_name_overlay.js exercises toggle show/hide, unchecking,
counts, geometry refresh, failures and stale-response suppression. Existing HTTP
coverage was extended for the GET overlay, permission refusal and fog invariance.

## Imported-room list fixed header and unassign regression

Run from the repository root:

```sh
node python/tests/test_room_library_manager.js
cd python
python -m pytest -q tests/test_room_library_unassign.py tests/test_room_library_layout.py
python -m pytest -q tests/test_room_library_unassign_web.py
```

Service tests cover normalized/all-matching names, duplicate imported names, revision
increments, idempotence, wrong-map/missing entries, import retention, other-map
isolation and rollback. JS tests cover confirmations, draft blocking, safe text,
selected-room/overlay refresh and errors. HTTP tests cover owner/CSRF checks, stale
save rejection and unchanged fog; they require installed web/dev dependencies.

Manual browser acceptance: import many notes, open the list, scroll to the bottom
and verify heading/Close/Refresh/status remain visible. Test keyboard scrolling,
a small viewport, and closed/reopened dialog visibility. Cancel unassign, then
confirm it; check the room is unnamed with empty notes, the library entry is
available, and player fog is identical. Try custom saved notes, duplicate names,
a selected room, dirty draft, and another map. Assigned entries must still resist
deletion until unassigned. Browser layout and HTTP checks were not run in the build
environment; service/static-layout and Node tests were run (see Patch notes).

## Campaign backup and restore validation

Run the service tests from the repository root:

```sh
PYTHONPATH=python pytest python/tests/test_campaign_backup.py -q
```

Coverage: content round trip with linked endpoints and door/passage runtime states;
owner/viewer preservation and other-campaign isolation; absence of password hashes;
foreign-key integrity; transaction rollback after invalid campaign details; expanded
archive-size rejection. These service tests do not exercise HTTP authorization or UI.

In a development installation with requirements-dev installed, also run:

```sh
PYTHONPATH=python pytest python/tests/test_web.py -q
```

Manual checks before deployment:
1. Download, inspect and restore a campaign with maps, fog, room notes and linked endpoints.
2. Confirm active map, settings, runtime door states and notes survive.
3. Confirm current owner/viewers and other campaigns remain unchanged.
4. Reject wrong campaign confirmation, missing CSRF, other-admin and viewer access.
5. Reject corrupt ZIP, incompatible schema, missing image and upload-size overflow.
6. Confirm restore refreshes an already connected viewer.
7. Confirm cancelled confirmation sends no restore request.

Patch-specific executed results and limitations are recorded in
[Patch change notes](../Patch/campaign-backup-restore.md), not inferred from this guide.

## Campaign readiness validation

Run from the repository root in the normal development environment:

```sh
PYTHONPATH=python pytest python/tests/test_campaign_readiness.py python/tests/test_campaign_readiness_templates.py python/tests/test_campaign_readiness_web.py python/tests/test_campaign_backup.py -q
```

Service coverage includes clean/empty campaigns, campaign isolation, missing/corrupt/unsafe
images, dimensions, informational missing walls, endpoint bounds, missing/arrival-only
links, wall-pixel arrival, same-map links, stale and valid room-note signatures, query-only
execution, unchanged database contents and map files, no fog cache output, and expanded
size matching real backup ZIP entries. Template tests cover escaping and the absence of
editor startup scripts. HTTP tests cover manager/superadmin access, other-admin/viewer
rejection, map membership, escaped names, marker clamping and unchanged database state.
HTTP tests are skipped when FastAPI is not installed; a skip is not successful HTTP coverage.

Manual browser acceptance:
1. Keep a player viewer open and record active map/fog state.
2. Run Check campaign and inspect a note/endpoint finding; confirm players do not change.
3. Confirm location markers, missing-image guidance and editor links are useful.
4. Fix an issue manually and re-run; confirm the finding disappears.
5. Confirm arrival-only endpoints and maps without walls are informational.
6. Confirm a non-owning admin cannot load report or inspection URLs.
7. Exercise large campaigns and concurrent file replacement to assess runtime/limitations.

## Campaign quick-navigation validation

From the repository root:

```sh
PYTHONPATH=python pytest python/tests/test_campaign_search.py python/tests/test_campaign_search_templates.py python/tests/test_campaign_search_web.py python/tests/test_campaign_readiness.py python/tests/test_campaign_readiness_templates.py python/tests/test_campaign_backup.py -q
node python/tests/test_campaign_quick_nav.js
```

Search service coverage includes category filters, unnamed notes, imported library,
Unicode casefold matching, multiword matching, literal SQL/wildcard punctuation, campaign
isolation, ranking/truncation, query/type limits, bounded snippets, URL escaping, deleted/
wrong-map target resolution and unchanged database state under query-only operation.
Template checks cover escaping, admin/viewer context gating and plain-text selected notes.
The Node DOM-stub regression covers request supersession/cancellation, stale responses,
text insertion, keyboard movement/Enter, shortcut input protection and focus restoration.
It is not a real-browser accessibility/layout test. HTTP tests verify manager/superadmin
access, viewer/other-admin rejection, JSON/HTML responses, validation, no-store, generic
inspection and unchanged campaign data. Missing FastAPI skips HTTP coverage.

Manual acceptance:
1. Keep a viewer open. Search and inspect results on several maps; ensure it never moves.
2. Test campaign, fog editor, wall editor, readiness and inspection contexts; confirm each
   search stays scoped to its campaign.
3. Exercise Ctrl/Command+K, arrows, Tab, Enter, Escape and focus restoration with a keyboard.
4. Confirm other modal dialogs and active text inputs are not interrupted.
5. Try network failure, rapid typing and changing result filters while requests are pending.
6. Confirm long results/snippets fit on narrow screens and full search works without JS.
7. Save pending editor drafts before following results; normal navigation may discard drafts.
8. Delete a result after searching and verify its old target is rejected rather than remapped.

## Named session checkpoint validation

From the repository root, run in the normal development environment:

```sh
PYTHONPATH=python pytest python/tests/test_session_checkpoints.py python/tests/test_session_checkpoints_templates.py python/tests/test_session_checkpoints_web.py python/tests/test_campaign_backup.py -q
```

Service coverage includes capture/preview without play-state changes, multi-map round trip,
last-displayed snapshot preservation/absence, door/entry overrides after hide-all triggers,
endpoint state, safety-checkpoint recovery, preservation of authored notes/names/appearance/
access, other-campaign isolation, monotonic versions, travel-cache clearing, incompatible
wall/calibration/image/map identity/map set/endpoint changes, changed engine configuration,
stale and duplicate forms (including empty campaigns), invalid cross-map runtime references,
transaction rollback on database failure, corrupt payload/fog, missing images, payload limit,
campaign deletion cascade, migration from schema 15 and schema-15 backup compatibility.
Template tests cover escaping and hidden restore controls when incompatible. HTTP tests
cover workflow, CSRF, confirmation/token handling, owner/superadmin access and other-admin/
viewer denial, read-only preview, deletion and stale restore resubmission. Missing FastAPI
skips HTTP coverage; skipped tests are not integration validation.

Manual acceptance before live use:
1. Create a named checkpoint with two maps, different fog and runtime passage states.
2. Continue play, then inspect the checkpoint; viewers must not change during preview.
3. Restore explicitly and verify active map/fog, locked/discovered passages and live refresh.
4. Restore the automatic safety checkpoint to recover the pre-restore state.
5. Confirm notes, authored walls/connections, owner and viewer assignments stay unchanged.
6. Edit geometry or replace an image and verify an older checkpoint is blocked.
7. Change play state in another tab after preview and verify the stale form is rejected.
8. Exercise pagination and typed-name deletion; confirm no automatic history pruning.
9. Test normal map switching after restore; existing map-display behavior is unchanged.

Keep item 7 (file-import busy feedback) deferred in TODO.md; it is not part of these tests.


## Step 4 backup inspection and recovery

From the repository root, with development dependencies installed:

```sh
PYTHONPATH=python python -m pytest -q python/tests/test_campaign_backup.py python/tests/test_campaign_backup_inspection.py python/tests/test_campaign_backup_inspection_templates.py python/tests/test_campaign_backup_inspection_web.py
```

Patch build results: 18 tests passed; the HTTP module was skipped because FastAPI is
not installed in the build environment. Tests ran with Python 3.12; source compilation is
also checked using Python 3.14. These are not claims of browser or HTTP acceptance.
Service checks cover original round trips and schema compatibility, read-only inspection,
archive/user/target/expiry/restart binding, restorable recovery, corrupt images, missing,
unexpected and duplicate entries, incompatible schema, and recovery failure/limit blocking.
Template checks cover escaped archive text, preview/CSRF fields and the inspection-first UI.
The added HTTP regression covers management/CSRF boundaries, preview requirement,
successful restore, authenticated recovery downloads and preview replay rejection.

Manual acceptance before deployment:
1. Inspect a nonempty campaign ZIP with notes, linked passages and active map; verify
   names/dimensions/counts/schema/size match. Cancel and verify all live state is unchanged.
2. Reject incompatible schema, corrupt JSON/images, missing/duplicate/extra ZIP entries,
   compressed/expanded overflow and foreign-key inconsistencies without replacement.
3. Reject other-admin/viewer access, missing CSRF, wrong typed name, missing preview,
   a different ZIP, expired preview, server restart, target edits and replay after success.
4. Restore a valid backup; check owner/viewers/other campaigns are unchanged, linked
   destinations and runtime states are restored and connected players refresh.
5. Download recovery from success and settings pages. Inspect and restore it; verify
   the original portable state returns, including original active map/fog/notes.
6. Make recovery storage unwritable/full or remove a current image; restore must be
   blocked before live replacement. Restore service permissions afterward.
7. Check an empty campaign round trip and token replay rejection. Check recovery links
   reject nonmanagers and invalid/cross-campaign filenames.
8. Confirm retained ZIPs survive restart and require explicit operator cleanup. Verify
   the temporary directory is cleaned after normal inspection failure/success.
9. Exercise large campaigns on the actual deployment, observing memory/temp/disk use,
   request latency, proxy limits and viewer reconnect behavior.

No automatic recovery retention or full installation rollback is provided. Local named
checkpoint history is excluded from ZIPs and older checkpoints may become incompatible.

## Step 5 viewer synchronization status

Run from the repository root:

```sh
PYTHONPATH=python python -m pytest -q python/tests/test_viewer_sync.py python/tests/test_viewer_sync_web.py
node --test python/tests/test_viewer_sync.js python/tests/test_viewer_refresh.js
```

Executed in the patch build: six Python service tests passed; the HTTP module skipped
because FastAPI is unavailable. Twelve JavaScript tests passed (seven new synchronization
checks plus five existing refresh/display-prompt regressions). Changed Python sources
compiled using Python 3.14; changed JavaScript passed node --check. Python service tests
ran on Python 3.12. These results do not imply real HTTP/WebSocket/browser acceptance.

Service coverage: connected/loading/ready/current-version comparison and blank targets;
failed/timeout freshness; disconnect expiry and bounded history; per-tab/campaign isolation;
untrusted/malformed reports; legacy ping contact without false readiness. JavaScript checks:
decode-before-ready, stale completion/failure guards, blank invalidation, failed decode and
recovery, request failure/timeout, reconnect HUD, text-only manager rendering and failed-poll
clearing. The HTTP regression checks manager/superadmin access, other-admin and viewer
isolation, no-store output and absence of database changes.

Before deployment, run HTTP tests with existing development dependencies installed and
perform these browser checks:

1. Open two viewer tabs for the same user plus a second user's tab. Verify distinct rows
   and username labels in campaign and editor Players panels; counts are connections.
2. Reveal, hide, undo, switch maps, restore a session checkpoint and blank the campaign.
   Confirm Loading until the latest image installs, then Up to date; blank is acknowledged.
3. Throttle image transfer, force decode/image/state failures and verify Failed appears;
   restore connectivity and confirm periodic refresh recovers without changing play state.
4. Race several reveals and a blank/switch while an old image decode is pending. Old success
   or failure must not overwrite the latest image/status or acknowledge the wrong version.
5. Drop the network/WebSocket, suspend the tab, and block pongs. Check reconnect/backoff,
   stale detection after roughly 65 seconds plus polling, and old-row expiry after close.
6. Confirm manager poll failure clears stale success, and revoked/other-admin/viewer users
   cannot obtain connection diagnostics. Verify legacy ping-only clients stay Connected.
7. Test proxy upgrade/idle timeout handling and a cache-reloaded viewer. Confirm current
   read-only diagnostics do not expose raw maps, walls or notes on the viewer port.
8. Restart the service: history must clear and viewer reconnects must repopulate it. Review
   CPU/request rates with many open manager pages. Sleep/background timing is best effort.

## Step 6: duplication

Run `PYTHONPATH=python python -m unittest discover -s python/tests -p test_duplication.py -v`.
Service regressions cover campaign link remapping and reset, internal single-map
links, external link detachment, independent image storage, invalid inputs,
missing-image rollback and partial-copy file cleanup.

Target-installation acceptance (not executed in patch environment):
1. Duplicate a live campaign with revealed rooms, runtime doors, checkpoints,
   notes, imported library entries, wall sources and linked maps. Verify authored
   content survives and all play state/access assignments reset in the copy.
2. Confirm the original player screen does not change and the copy is not live.
3. Duplicate a map with internal and external links; verify only internal links survive.
4. Change/delete copied images/walls/notes and verify source content is independent.
5. Exercise anonymous, viewer, foreign-DM and missing/invalid-CSRF POSTs; ensure denied.
6. Test missing/corrupt images and storage errors, checking no database partial copy
   or referenced partial image remains. Test a large campaign under the target runtime.

FastAPI is unavailable in the patch environment, so HTTP authorization/CSRF routing,
real browsers and Python 3.14 runtime acceptance remain outstanding.

## Items 7 and 8: import busy feedback / access logging

Commands:

```sh
PYTHONPATH=python python -m unittest discover -s python/tests -p test_access_logging.py -v
node --test python/tests/test_*.js
python python/tests/check_upload_busy_browser.py
```

The optional browser regression requires Playwright and an installed Chromium;
neither is a runtime application dependency. It intercepts a delayed real native
multipart POST and checks duplicate suppression, preserved file/CSRF/submitter
fields, visible feedback, validation/confirmation cancellation, JS-managed form
exclusion and back-forward restoration. Logging tests cover success filtering,
4xx/5xx retention, warning retention, unknown formats, opt-in and idempotent setup.
Room-note DOM regressions now check busy feedback and repeat-upload blocking.

Patch-environment results: seven logging unittests, 33 Node test-runner cases and
seven browser checks passed. Changed Python syntax, JavaScript syntax, Jinja
compilation and archive integrity/hash checks also passed. FastAPI and Uvicorn
are unavailable here, so full application integration and live Uvicorn log output
were not exercised. Target Python 3.14 and cross-browser acceptance remain open.

Installation acceptance:
1. With network throttling, import a large map and click/press Enter repeatedly.
   Verify one import, immediate busy feedback and normal success/error redirects.
2. Repeat for image replacement, backup inspection/restore, saved wall sources,
   batch maps/walls and room-note imports. Check error recovery and Back navigation.
3. Confirm the full-width duplication panel layout remains unchanged.
4. Verify normal 200/303/304 HTTP requests are quiet; intentional 404/422 failures
   are logged at INFO, and application/server failures retain their diagnostics.
5. Set access_log_success true, restart and verify successful access lines return.

## Double-reveal regression checks

`python/tests/test_double_reveal.py` exercises room-only compositing, fog independence,
geometry invalidation, optimistic room revisions, navigation prerequisites and state preservation,
SQLite persistence, deleted destinations, portable backups, schema-15/16 compatibility,
duplication, checkpoint compatibility and history recovery. The file contains 15 cases including
parameterized legacy versions. `python/tests/test_double_reveal.js` exercises the real controller
with mocked DOM/transport plus the production selection interceptor. Existing click-handler
mocks now declare the new controller; browser render fixtures include its partial.

`python/tests/test_double_reveal_web.py` adds HTTP ownership/CSRF, image dimensions/previews,
stale-write and navigation checks. It skips when FastAPI is unavailable; a skip is not a pass.
Browser execution requires an installed Playwright Chromium. Run browser tests separately from
unit tests because several test module basenames overlap in the existing repository.

```sh
PYTHONPATH=python python -m pytest -q --ignore=python/tests/browser
for test in python/tests/test_*.js; do node "$test" || exit 1; done
PYTHONPATH=python python -m pytest -q python/tests/browser
python -m compileall -q python
```

The delivery-specific results, exact scope and unrun checks are recorded in
`Patch/VALIDATION.md`. No HTTP, browser, live deployment or Python 3.14 result should be inferred
from source compilation or mocked JavaScript tests. Migration expectations use `len(MIGRATIONS)`
rather than obsolete literals; the help CSS test is restricted to its intended six-rule block.

## Admin artwork response regression

A reported HTTP failure (`test_image_choice_and_type_permissions`, `KeyError: image_url`)
identified a missing key in shared admin map responses. The pack-artwork HTTP regression now
asserts the returned URL, consistency with GET map metadata, a successful artwork response,
and the existing no-store, pixel and permission checks. It does not remove or bypass assertions.

```sh
python -m pytest -ra python/tests/test_admin_image_url_contract.py
python -m pytest -v python/tests/test_pack_images_web.py::test_image_choice_and_type_permissions
python -m pytest -ra python/tests --ignore=python/tests/browser
```

`test_admin_image_url_contract.py` is dependency-light source-contract coverage: it evaluates
the production payload URL expression, checks shared payload use in the import route, and
checks that the original-image route retains authorization and no-store headers. It is not an
HTTP test. `Patch/IMAGE_URL_FIX_VALIDATION.md` records the checks actually run for this hotfix;
previous double-reveal validation results must not be counted as reruns of this correction.
The Starlette/httpx deprecation warning is separate; this patch changes no dependency pins.


## Rocky Linux 10 / WSL browser preflight

Playwright's automatic dependency installer does not support Rocky Linux 10.
Do not run `install-deps` or `install --with-deps` there: the fallback calls
Ubuntu's apt-get. On supported Ubuntu/Debian hosts, the --with-deps installer
can be used. On Rocky, provision dependencies with DNF and download Chromium
as the normal test user, in the test virtual environment:

```sh
sudo dnf install -y nspr nss fontconfig dejavu-sans-fonts
python -m playwright install chromium
fc-match sans-serif
python -u python/tests/check_browser_environment.py
```

This is a starting dependency set, not a full native compatibility guarantee.
Rocky is not an officially supported Playwright browser host. Resolve any
remaining missing shared library using `dnf provides '*/NAME.so'` and inspect
the trusted downloaded executable with ldd. Do not install Ubuntu packages or
create arbitrary library symlinks on Rocky.

### Fontconfig and rendered-text failures

The supplied eee89c4 run reports 521 Python passes. Its browser preflight reaches
page creation, HTTP navigation and set_content, but fails the rendered text
assertion. Browser stderr includes “Fontconfig error: Cannot load default config
file” and Vulkan/EGL errors; the browser is then closed normally in the cleanup
block. This is not the original missing-libnspr4 launch failure. The exact value
returned by inner_text was not recorded in that old run, so do not infer it.

The updated preflight records both DOM text_content and rendered inner_text,
FONTCONFIG_FILE/FONTCONFIG_PATH overrides, and bounded fc-match output. It keeps
both DOM and rendered-text checks strict: replacing inner_text with text_content
alone would mask a rendering problem. A mismatch still fails the preflight.
Fontconfig warnings are evidence to investigate, not proof of the only cause.

Verify installed configuration, font availability and environment overrides:

```sh
rpm -q fontconfig dejavu-sans-fonts
rpm -V fontconfig
ls -l /etc/fonts/fonts.conf
fc-match sans-serif
printenv FONTCONFIG_FILE FONTCONFIG_PATH
```

If configuration files are missing from an installed Fontconfig package, restore
them with `sudo dnf reinstall fontconfig`. Investigate custom environment paths
before changing them. If overrides are accidental, compare a one-command run
using system defaults without changing the parent shell:

```sh
env -u FONTCONFIG_FILE -u FONTCONFIG_PATH fc-match sans-serif
env -u FONTCONFIG_FILE -u FONTCONFIG_PATH python -u python/tests/check_browser_environment.py
```

Do not disable SELinux or change GPU flags based solely on warning text. The
Vulkan/GPU messages are not proven to cause this failure. Use pw:browser process
logs and the explicit DOM/rendered values to diagnose further if font setup is
healthy. Native Rocky compatibility remains best-effort; a supported container
userland is an alternative, with matching Playwright image/package versions and
a Python runtime meeting the project's requirements.

### Running and interpreting the checks

```sh
python -u python/tests/check_browser_environment.py
bash runtests.sh
```

The preflight starts a temporary loopback HTTP server; it needs no production
server or campaign data. It uses the current fixtures' headless/no-sandbox test
settings, not a production sandbox policy. Its parent imposes a 45-second timeout;
use --timeout to adjust. Font diagnostics have a separate five-second timeout.

runtests.sh logs preflight output to test-results/browser-preflight.log. If it
fails, browser.log says NOT RUN and the entire run returns nonzero even after
log packaging. No blocked browser tests are counted as passing. Direct pytest
commands bypass this preflight. A passing smoke test is not a passing full suite.
After successful preflight, run `python -m pytest -ra python/tests/browser`.

Source guidance: https://playwright.dev/python/docs/browsers . Patch/ contains
release-specific measured validation results; these instructions are not results.


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


## Confirmation spy initialization

Install browser instrumentation using an explicit initializer callback:

```python
page.evaluate("() => { window.confirmCalls = 0; window.confirm = () => { window.confirmCalls++; return false; }; }")
assert page.evaluate("window.confirmCalls") == 0
```

The initializer returns no function. The previous multi-statement string ended
with a function-valued assignment; evaluating it incremented the counter before
Apply. Check the counter baseline before the action, then verify the expected
request and check the counter again after completion. This fixes test
instrumentation rather than adding/removing a production confirmation dialog.
Exact payload assertions prevent a no-op Apply from incorrectly passing.

Run from the repository root in the test virtual environment:

```sh
python -m pytest -q python/tests/browser/test_campaign_batch_import.py::test_empty_upload_is_noop_and_apply_does_not_confirm
python -m pytest -q python/tests/browser/test_campaign_batch_import.py
```

The focused test also checks that empty submission performs no map uploads,
source uploads or assignments. The completed Apply payload must contain the
selected source ID, original scene index, alignment choice and use_pack_image=false.

Scope: this correction does not repair all failures in the supplied 2b81e59 run.
That run reports 529 Python passes, and browser results of 109 passed, 32 failed,
13 setup errors. Other failures include missing sidebar-help partials in mocked
Jinja loaders, editor image waits, modal pointer interception, saved-source status
expectations, progress timing and geometry/width assertions. Those remain outside
this focused patch. Do not interpret a batch-module pass as a full-suite pass.
See Patch/VALIDATION_BATCH_CONFIRM.md for the recorded execution and limitations.


## Fixture repair and UI follow-up for 9f3be8f

`python/tests/browser/browser_support.py` provides an override-first Jinja
ChoiceLoader with real web_html/templates fallback. Shared partials must not
be replaced with empty strings merely to hide missing-template errors. The
auxiliary GET helper handles only named independent room-note, double-reveal
and transition endpoints; it never swallows writes or unknown requests.

Gesture fixtures now render the actual map-editor template instead of a drifting
minimal DOM. This preserves production prerequisite order, controls and real
PanZoom/editor behavior. The viewer-centering fixture explicitly includes
viewer_area_zoom.js before viewer_display.js. Optional independent API responses
have bounded empty schemas; the tested metadata/actions remain fixture-controlled.

The source busy assertion uses the intended Uploading / processing message,
retaining original scene-index and exact assignment-payload checks. Empty sources
must show No wall sets found and keep Apply disabled. Production inspect() now
distinguishes that empty state.

Batch clock tests install and pause virtual time before loading the application,
then use run_for(3999) and run_for(1). No real setup/polling time is allowed to
consume the four-second deadline. Geometry tests pan the image edge into the
viewport and assert hit-testing reaches it before using a real pointer click.
Do not replace pointer tests with synthetic callbacks or force=True.

Floating-dialog content growth is observed with ResizeObserver; reflow preserves
the current/user-dragged position when possible and clamps it when necessary.
A regression adds secret controls and checks bounds plus ordinary Apply/Close
clicks. Browser-free Node coverage checks dynamic growth and cleanup.

The zoom-2.5 label screenshot assertion remains strict. On failure it saves the
screenshot and coordinates under pytest's tmp_path. Its threshold was not relaxed;
that visual issue may remain platform-specific and requires target-host review.

Focused commands from repository root:

```sh
python -m pytest -q python/tests/test_browser_fixture_support.py
node python/tests/test_floating_dialog_reflow.js
python -m pytest -v python/tests/browser/test_saved_wall_sources.py
python -m pytest -v python/tests/browser/test_ui_refinement.py
python -m pytest -v python/tests/browser/test_secondary_click.py
python -m pytest -v python/tests/browser/test_portal_tools.py
python -m pytest -v python/tests/browser
```

The supplied baseline has 31 failures and 13 setup errors, often grouped behind
one fixture defect. A repaired fixture can expose additional assertions; do not
count those earlier setup failures as validated features. Patch/ contains exact
new execution results and distinguishes them from target-host baseline evidence.


## Viewer diagnostics and disclosure-state fixture contracts

The read-only `/api/campaigns/{id}/viewer-status` mock uses the actual client
schema: `viewers: []` and `blank`, plus `ok: true`. This is explicit GET-only
coverage; unknown paths and all writes still fall through to the caller. The
standalone selection-persistence page must not call metadata helpers with a
nonexistent `data` variable. Helper tests protect both boundaries.

HTML base overrides get a UTF-8 declaration without altering the caller's
mapping. This prevents fixture-only mojibake; production base.html already has
UTF-8. Plain-text overrides are not rewritten.

Passage tests need at least two campaign maps: the real template deliberately
hides that section for single-map campaigns. The shared admin fixture now renders
two siblings and retains its explicit transitions handler. Independent auxiliary
mocks must not preempt that fixture's authored transition payload.

Sidebar tests must honor initial closed disclosure state. Open Fog before radio
input and Walls before native slider drag/focus. Peer panels use the real
accordion; Saved sources is a peer, while the legend remains independent. Test
closing and reopening explicitly rather than assuming a first click closes an
already-open panel. Do not add force=True, disable the accordion, or operate a
hidden control with synthetic callbacks to evade real input behavior.

Run focused fixtures first, then the complete browser suite:

```sh
python -m pytest -q python/tests/test_browser_fixture_support.py
python -m pytest -v python/tests/browser/test_editor_controls.py
python -m pytest -v python/tests/browser/test_secondary_click.py
python -m pytest -v python/tests/browser/test_map_transitions.py
python -m pytest -v python/tests/browser/test_wall_width_followup.py
python -m pytest -v python/tests/browser
```

This follow-up does not loosen the unresolved screenshot threshold or certify a
full-suite pass. Patch/ records measured execution results and outstanding items.


## Arrow-image and new-window inspection mock contracts

The real editor fetches door-arrows.png even when an isolated scenario has no
arrows. Raising an unexpected-route assertion there breaks pending requests and
can cause both test failures and teardown errors. The auxiliary helper now
handles exactly `/api/maps/{id}/door-arrows.png` for the current fixture map,
GET only, only when neither authored door arrows nor portal routes are present.
It returns a decodable transparent RGBA PNG at work resolution, falling back to
image resolution only when work dimensions are absent. Invalid dimensions,
other maps, writes, unrelated paths and authored imagery are not intercepted.
PNG bytes are cached for repeated identical dimensions. Tests decode the image
and verify dimensions/alpha, not merely its content-type header.

Inspect destination opens a new tab. Parent page.route handlers do not provide
a mock document for that new page's initial navigation. The regression now
registers a context route for the exact expected destination, checks its title
and URL, preserves parent dialog/no-write assertions, and closes/unroutes in
finally. The stub tests navigation/isolation, not destination editor rendering.
Unexpected destination URLs remain unmatched instead of silently succeeding.

Focused commands from repository root in the test environment:

```sh
python -m pytest -q python/tests/test_browser_fixture_support.py python/tests/test_inspection_fixture_contract.py
python -m pytest -v python/tests/browser/test_editor_controls.py
python -m pytest -v python/tests/browser/test_secondary_click.py
python -m pytest -v python/tests/browser/test_passage_modal_layout.py::test_inspection_does_not_activate_viewer
```

The zoom-2.5 screenshot threshold and its diagnostic capture are unchanged.
Neither this focused fix nor a focused test pass certifies the complete suite.
Patch/ distinguishes measured patch validation from supplied baseline results.

## Browser regressions and isolated label paint checks (f4d60c3)

The existing secondary-click fixture separates read-only room-at POSTs from fog
mutations and still rejects unexpected mutation requests. The supplied local run
confirms those tests and both wall-width parameters pass; these fixes are already
in f4d60c3 and are not duplicated in this follow-up archive.

The portal-label test retains visible-text bounds, exact screen-relative padding,
font size, layer order, CSS fill, pointer behavior and non-scaling border checks.
A pixel two screen pixels from a rounded border is not an isolated measurement
of fill: glyph and edge rasterization may contribute. The exact source of the
reported (139,141,145) pixel has not been established from the supplied log.

`background_paint_sample` hides label text only during screenshot capture via
Playwright's screenshot `style` option. It samples a central 3x3 region of each
of four backgrounds away from their borders; every channel must remain <110.
It does not inject a replacement background in the positive test. Visible-text
geometry is measured before screenshot capture. This tests fill paint, not the
unmodified final composition at the former edge pixel; it is deliberately a
measurement-contract change rather than a production rendering fix.

Six negative-control cases set the screenshot-only fill to `none` or `#fff` at
zooms 0.5, 1 and 2.5. Every sampled pixel must fail the darkness criterion.
Tests verify normal text visibility and original fill return after capture.
Failure diagnostics include the isolated screenshot, sample values and an
unmodified screenshot. No pixel threshold or geometry tolerance is relaxed.

Validation: 13 portal-visibility tests passed in 7.14s under Python 3.12.8 and
pytest 8.3.5 in the assistant environment. This does not certify the full suite
or reproduce your Rocky Linux/Python 3.14 font/compositor setup.

Run from the configured test environment:

```bash
python -m pytest -v -ra python/tests/browser/test_portal_visibility.py
python -m pytest -v -ra python/tests/browser
bash runtests.sh
```

The module now contains 13 cases (7 existing + 6 negative controls); an otherwise
unchanged full browser collection should therefore grow from 155 to 161 cases.
See `Patch/VALIDATION.md` for supplied results and remaining limitations.
