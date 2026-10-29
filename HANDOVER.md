# Looking Glass - Project Handover

Last prepared: 2026-10-29 (Europe/Amsterdam).

## Purpose and authority

This file preserves enough context to resume development if the Perplexity project or conversation is lost. It is a recovery guide, not a backup of application data or the complete conversation.

The live Git repository, checked-out branch, source code and tests are authoritative. Uploaded archives and Project Files in Perplexity can be older. In particular, the uploaded snapshot documented viewer port 6000; the live branch README documents 5100. Read current configuration before deployment.

## Repository and agreed working branch

- Owner/repository: dajomas/Looking-Glass
- Clone URL: https://github.com/dajomas/Looking-Glass.git
- Assistant working branch: features/perplexity
- Other branches observed: main and features/development.
- The user created features/perplexity locally and pushed it. Do not recreate or overwrite it.
- A remote check on 2026-10-28 showed all three branches at 1206a4bd7b223041f44d8aa59ebb6df59558d932. This is a historical observation, not a permanent baseline.
- That check reported features/perplexity as unprotected. Recheck access and rules when needed; read access does not prove write access.
- Do not merge to main, force-push, reset branches or change other branches without explicit user approval.

## Project purpose

Looking Glass is a D&D battle-map fog-of-war application. The DM manages maps and wall boundaries and reveals areas; players see a live, server-rendered fogged image.

Core documented characteristics include separate admin and viewer portals, SQLite storage, multiple campaigns/maps, Foundry VTT and Universal VTT wall imports, and superadmin/admin/viewer roles. Raw map artwork and wall geometry must not be exposed through the player-facing application.

## Current live README highlights

The branch README describes considerably more than the original uploaded snapshot:

- Admin port 5000 and viewer port 5100.
- Reusable campaign wall sources, batch imports and independent per-map alignment/fog.
- A dedicated wall editor, UVTT export, door states, secret passages and same-map portals.
- Cross-map passages with explicit DM travel confirmation.
- Viewer room focus, admin-controlled viewer focus and viewer synchronization status.
- Named rooms, DM-only Markdown notes and imported room-note libraries.
- Campaign backup/restore, readiness checks, campaign search, named session checkpoints and clean duplication.
- Alternate room artwork via Double reveal, documented as adding schema migration 17.
- Extensive browser-test harness and regression follow-ups documented in README, docs/testing.md and Patch/.

These are documentation observations, not an independent functional audit. Do not infer that migration 17 is the latest schema version; inspect db.py and current deployment notes. No application tests were run while preparing this handover.

## Architecture orientation

The uploaded architecture guide describes two FastAPI applications served by uvicorn in one process, sharing an AppContext, SQLite storage, a fog engine and an in-process WebSocket event hub. Revalidate details against the current source.

Useful paths:

- python/main.py: application entry point.
- python/looking_glass/: application package.
- config.py, cli.py, server.py: configuration and startup.
- db.py: schema and ordered migrations.
- rbac.py and security.py: authorization and authentication.
- repositories/: persistence operations.
- services/: fog, image, wall/import and related domain logic.
- web/: application factories, auth, admin and viewer routes.
- static/: browser JavaScript, CSS and images.
- templates/ and web_html/: shared and portal-specific templates.
- python/tests/: automated tests, including browser tests in the live repository.
- docs/: user, architecture, API, deployment and testing documentation.
- Patch/: feature/change notes referenced by the live README; inspect existence and contents at the current revision.

The original fog design labels areas enclosed by blocking walls, stores reveal/hide operations and renders fogged composites. Boundary changes can alter the areas affected when operations are replayed. Preserve this distinction between authored geometry, runtime state, fog history and viewer camera state.

## Resume locally

```bash
git clone https://github.com/dajomas/Looking-Glass.git
cd Looking-Glass
git switch features/perplexity
git status --short --branch
git log -5 --oneline
```

For an existing checkout, inspect status and local commits before fetching/integrating remote changes. Do not discard uncommitted work.

The live README documents this basic setup:

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Optional: copy only if config.yaml does not already exist.
cp config.example.yaml config.yaml
.venv/bin/python python/main.py
```

First startup creates a superadmin and logs an initial password, unless LG_SUPERADMIN_PASSWORD was supplied for initialization. Change the initial password. Never commit credentials, local configuration containing secrets, database files, uploaded maps or session data.

The live README documents this basic test invocation:

```bash
.venv/bin/pip install -r requirements-dev.txt
cd python
../.venv/bin/python -m pytest -q
```

Read docs/testing.md before browser tests. The live README references Playwright lifecycle constraints, Rocky Linux/WSL font/rendering preflight and python/tests/check_browser_environment.py. Inspect runtests.sh and other launcher scripts before relying on their behavior. Record actual commands, results and limitations; do not describe collection or setup-plan checks as passing browser execution.

## Data protection and recovery

Read current docs/deployment.md before upgrades, schema changes or restores. The original layout uses data/looking_glass.db, data/maps/ and disposable rendered files in data/cache/; confirm current configuration and additional storage paths first.

Back up the stopped application's complete configured data storage before risky changes. Campaign ZIP backup, session checkpoints and full installation backup have different scopes: the README says campaign exports omit accounts/sessions, and checkpoints are local to the installation database rather than portable campaign ZIPs. Do not treat this handover or Git as a backup of runtime data.

Keep authorization, CSRF validation and DM-only notes intact. Inspection/search/navigation actions documented as read-only must not reveal fog, activate maps or travel. Do not accidentally expose hidden map content or secret passage state to viewers.

## Assistant workflow and user preferences

The user prefers direct technical explanations, complete working changes, reproducible commands, incremental validation and candid limitations. Use the live features/perplexity branch as the target unless the user changes that instruction.

In this Perplexity environment the GitHub connector exposed file reads, single-file create/update and multi-file commits. Tool availability and authentication can change in a new session; rediscover them rather than assuming access.

Before an external write, resolve the repository, branch and current file contents, prepare exact file contents and commit message, and obtain the required action confirmation. For an existing single-file update, obtain its blob SHA from the target branch. Execute only the approved write. Do not assume a general branch instruction authorizes arbitrary future changes.

After a successful commit, report its actual SHA and changed paths. Do not claim a push succeeded merely because a draft or confirmation was prepared. Test code changes where execution is available; otherwise explicitly distinguish review from execution.

## Status at preparation

- Remote branch visibility and repository root access were verified through the GitHub connector.
- No HANDOVER.md existed in the root listing before this proposed addition.
- The live README was read; its connector response was truncated near the end.
- Architecture orientation also used older uploaded documentation and is explicitly marked for revalidation.
- No write permission test or application test had been performed before this file's proposed commit.
- The immediate user request was to create this handover and commit it to features/perplexity. No additional feature work was specified in this exchange.

## Suggested first message in a replacement assistant session

Read HANDOVER.md and the current README on dajomas/Looking-Glass, branch features/perplexity. Verify the branch head, inspect relevant source and current docs, and summarize the verified state before proposing changes. Do not rely on old uploaded snapshots, alter other branches or claim unexecuted tests passed. Ask for the specific development task if none is supplied.

## Bug-hunt backlog and one-at-a-time workflow (2026-10-28)

The user superseded the combined-fix approach: keep the 15 findings and proposed
solutions in root TODO.md and tackle them individually. All 15 entries are open;
this documentation change does not deliver fixes, tests, migrations or assets.
The live branch was observed at 3d34a4f8d2c5f184d5e667aa4e47de2a22ee3c10 before
preparing this backlog. No earlier combined implementation was committed.

Treat earlier replacement snippets, local candidate files and candidate test
results as uncommitted exploratory work, not branch state. Re-read live source,
reproduce each issue, agree a minimal compatible solution, add regression tests,
record actual results, update relevant docs and obtain exact-write approval for
each delivered change. Never apply the earlier combined draft wholesale.

TODO.md preserves audit corrections: imported-name release is intentional and
must remain lossless for custom notes; the originally alleged double-reveal
rendering crash was not established. Archive/recovery models and retirement
queues are design proposals, not an installed or approved migration 18.

The uploaded base64 source ZIP names the audit revision and matched checked blob
hashes, including README.md and this handover. Prefer future live branch state.
No application tests were run for this documentation-only backlog change. Prior
candidate testing does not validate the unchanged implementation on the branch.
A pre-existing scrying-auto-2 template assertion failure was reproduced on the
untouched baseline; keep it separate from these 15 items.

## Bug 1 implementation candidate: inward fog feathering (2026-10-28)

Prepared against features/perplexity at ee9a0fa9d7f4a4fa4930d7217cd951dfbf899742.
Only services/fog.py and the new python/tests/test_fog_privacy.py change runtime
code/test coverage; README.md and this handover describe the same scoped fix.
The other 14 backlog items, database migrations, routes, assets and configuration
are unchanged. TODO item 1 remains open until approved GitHub delivery; record the
actual delivered SHA then. No GitHub implementation write has occurred at preparation.

The boolean mask now clips dilation to revealed interiors or wall pixels. Viewer
mask scaling uses nearest-neighbour support; Gaussian feathering is clipped to
that support so it softens inward only. The cache identity changes from
fog-cache-v2 to fog-cache-v3-inward-feather. Existing work-resolution/raster limits
remain; no whole-map source-image resampling redesign is included.

Validation executed with Python 3.14.4, using existing pure-Python pytest 8.3.5
sources through a temporary support path with plugin autoload disabled:
- New regressions on unchanged renderer: 13 failed, 2 passed (expected red run).
- New plus existing fog tests after the fix: 25 passed.
- Focused fog/doors/arrows/regions/double-reveal/passages/transitions suite:
  246 passed in the final run (3.62 seconds).
- Broader 64-module non-HTTP suite: 574 passed, 2 failed. Failures are the stale
  scrying-auto-2 template assertion and viewer-sync equal-timestamp history eviction.
  Both were reproduced from untouched baseline sources; neither is fixed here.
- All 192 Python sources compiled with Python 3.14.4.

Exact pixel assertions use PNG and cover default feather radius 2, radii 0/5,
mask upscaling/viewer downscaling and odd dimensions, wall dilation, full reveal,
full hide and restart isolation from old disk caches. JPEG/WebP visual output,
HTTP endpoints, browsers and live multi-viewer behavior were not executed.
FastAPI/Uvicorn remain unavailable; compilation/service tests do not substitute
for those checks. Do not claim the broad suite passed or relax unrelated tests.

## Bug 3 implementation candidate: same-version viewer recovery (2026-10-29)

Prepared against features/perplexity at 685fff20ebd63c6cb8abf4f36731ca72b327d682.
Bug 1 was delivered in 253b33ddae49d403a3985bf99135ce07226e95e4 and its TODO
completion was recorded in 685fff20ebd63c6cb8abf4f36731ca72b327d682. Earlier
candidate/open wording above records historical preparation, not current status.
Bug 3 remains open pending approved GitHub delivery; record its actual SHA then.

Scope: static/js/viewer_display.js adds a visible-stage condition to the
same-version fast path. An error-hidden stage reuses the normal decode/install
path instead of falsely reporting ready. Existing generation guards, blanking,
remote/local navigation, permissions and server play state are unchanged.
web_html/viewer/display.html bumps the display-script query token to
viewer-state-recovery-1. The existing viewer-refresh Node harness adds HTTP-error
injection and captured status reports; its original five tests are retained.
No changes to Python runtime code, migrations, routes or other backlog items.

Validation executed with Node v20.20.1:
- Expanded viewer-refresh suite before the fix: 3 failed, 7 passed (expected red).
- The same suite after the fix: all 10 passed, none skipped/cancelled.
- All 27 top-level JavaScript regression scripts passed after supplying their
  unmodified template fixtures; an earlier partial extraction lacked fixtures.
- node --check passed for the changed controller and regression script.
- The modified viewer template parsed with Jinja2; this is not browser rendering.

New coverage: HTTP 500/404 followed by same-version recovery; failed/loading/ready
status ordering and stage visibility; a still-visible same-version fast path;
blank response after an error; and a late recovery decode superseded by a newer
map. HTTP responses and WebSocket reports in these tests are mocks. No Python,
real HTTP/WebSocket, browser or live multi-viewer tests were run for this change.
The recovery logic adds no mutation calls; its final image/version checks still
come from the existing server endpoints. No implementation was pushed at preparation.

## Bug 4 corrected archive candidate (2026-10-29)

Explicit baseline: 54cae125d996ceccff6cc61d3942edea88209c4e. All five existing replacement files
(fog service, viewer/admin APIs, README and HANDOVER) were verified byte-for-byte
against GitHub blob hashes at that revision before modification. The supplied
older source bundle was used only as a reconstruction starting point; it was
not accepted as the baseline for those replacements. Existing documentation is
preserved as an exact prefix, including the bug backlog and bug 1/3 records.
Bug 1 and bug 3 implementations are present at this baseline; historical
candidate/open wording above must not be read as their current TODO status.

The entire fog.py implementation change is the addition of viewer_bytes(),
which holds the existing per-map RLock across viewer_image() and read_bytes().
The viewer image and admin preview routes use that helper via asyncio.to_thread
and return Response bytes instead of a deferred FileResponse path. The viewer
post-render access and version checks, media type and no-store header remain.
Bug 1's clipped dilation, nearest-neighbour support, inward-only feathering and
fog-cache-v3-inward-feather identity are unchanged. No bug 3 JS/template files,
TODO status, migrations, configuration or unrelated implementation is replaced.

Validation actually run on Python 3.14.4: focused new service regressions plus
existing fog, bug 1 privacy, door-arrow and viewer-area tests: 73 passed, 1 skipped.
The skipped module contains five HTTP cases; FastAPI is unavailable in this
execution environment. No ASGI integration, full suite, browser or live-server
checks were performed. New service coverage includes PNG/JPEG/WebP bytes after
cleanup, cold/warm map locking against invalidation/new renders, read-failure
lock release and independent map locks. Bug 3 was not retested in this delivery;
its JS/template files are excluded from the overlay and therefore preserved.

Implementation complete as an archive candidate; HTTP and deployment acceptance
remain pending. No GitHub writes or pushes were attempted. Corrected archive
supersedes the earlier stale-baseline bug 4 archive. Do not use that earlier ZIP.
The commit edd5c121f3ee292a6cf3d75dfa8f991c464595c8 contains a bug 1 rollback and
documentation loss; this corrected overlay restores the chosen baseline content
in its replacements while retaining bug 4. Review any other local later edits.

Limitations: per-instance/per-process cleanup coordination only; external file
deletion and shared-cache multi-process locking are outside this fix. Encoded
response bytes consume memory for each concurrent response. No files are deleted
or renamed. Newly generated Patch/ material is archive-only and must be excluded
from git staging; do not remove unrelated pre-existing tracked Patch/ contents.

## Bug 5 implementation candidate: viewer socket session lifetime (2026-10-29)

Baseline: features/perplexity at 10c5d4af419b08d7639d2e3867e49fe518798b47.
Reconstructed existing code replacements and HANDOVER were verified against live
Git blob hashes. The supplied README matched live blob
9b08f1618d55ba27a9c5fb303c9376e1fd8e26c4 after CRLF-to-LF normalization;
its complete previous contents and this handover are preserved as exact prefixes.
No earlier uploaded application snapshot is used for code replacements.

Scope: sessions.lookup_hash resolves the existing DB identity without retaining
raw tokens in socket indexes/checker closures. Viewer sockets record that hash
and an access checker for session expiry/deletion, active user, viewer portal and
current campaign access. The hub validates before each event/pong, the live loop
validates before reports and on an idle timeout of 15 seconds, and a post-subscribe
check covers logout during admission. Logout becomes async and, after committed
session deletion, kicks only that hashed session's sockets across campaigns.
Per-socket delivery locks serialize sends with explicit session/user kicks;
existing kick_user behavior is retained. Failed checks fail closed. Empty hub
subscription sets are removed, and sync records are disconnected on retirement.

No fog rendering, JS, templates, schema, settings, dependencies or other backlog
implementations change. Bug 6's explicit role-update kick and bug 7's forced
password-change restriction are deliberately not implemented here. Session checks
can observe role-related session deletions, but this is not bug 6's completion.

Validation executed on Python 3.12.8 with installed pytest 8.3.5, plugin autoload
disabled, and a focused source tree containing verified live support modules:
- New unit regressions against baseline: 9 failed, 2 passed. Baseline's FastAPI
  WebSocket annotation import alone was shimmed with object because FastAPI is
  unavailable; no baseline hub/repository logic was changed. One failure directly
  reproduces all three events being sent despite access being revoked.
- Candidate focused modules: 11 passed, 1 module skipped (0.04 seconds). The
  skipped module contains seven ASGI/WebSocket tests; FastAPI/Starlette are absent.
- All six changed/new Python files compiled successfully.

Unit coverage uses real SQLite for hash/raw lookup equivalence, portal separation,
expiry boundary and deletion, plus mocked sockets for session/campaign isolation,
event/pong/idle guard behavior, failed authorization/transport cleanup, existing
user kicks, idempotent removal and serialization with an in-flight send. This does
not execute routing, middleware, ASGI transport or the actual live-loop timer.
The seven included integration cases cover logout isolation/tabs, expiry before
broadcast, timer-driven idle closure, assignment removal, rejected status reports,
admission/logout races and unauthenticated admission; they remain unexecuted.

Run from a normal repository checkout with development/runtime dependencies:
`PYTHONPATH=python python -m pytest -q python/tests/test_viewer_session_lifetime.py python/tests/test_viewer_session_web.py`
No full suite, browser or live-server test was run. Python 3.14 deployment acceptance
also remains pending; do not describe the skipped integration module as passing.

Limits: hub/kicks are in-process; revocations from another process are observed by
DB checks rather than direct cross-process notification. Short synchronous DB
checks run on the application loop, consistent with existing access checks. The
15-second idle interval excludes scheduling/DB/transport delays. An already
in-flight frame cannot be recalled; after closure no new sends are authorized.
No files are deleted/renamed and no Patch/ material is added to the repository.
Implementation is prepared, not delivered at preparation. TODO item 5 remains
open until approved GitHub delivery; record the delivered SHA and distinguish
implementation delivery from pending ASGI/deployment acceptance then.

