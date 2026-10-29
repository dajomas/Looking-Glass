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

## Bug 6 implementation candidate: role-change socket revocation (2026-10-29)

Baseline: features/perplexity at aafa602fd1cae81f7157c57698f786e1b08c9ceb.
At this baseline bug 5 is delivered in 88c705eb98d42bbd39fef536b0515666ee298696,
with documentation in cbcf2b5bd2a8af87ec303b66388df338357ab0ea and TODO status in
aafa602fd1cae81f7157c57698f786e1b08c9ceb. Its earlier candidate/open wording above
is historical, not current TODO status. Bug 5 ASGI/deployment acceptance remains pending.

Re-read the live admin user routes, user repository, README and HANDOVER.
The unchanged users.py source matched Git blob
55b26049d1307aa73439dc48cee0d5450096e70e. Complete README/HANDOVER baselines were
recovered from the supplied bug 5 draft plus the existing final blank line,
then verified against current live blobs 7e4e92372428fb516965a716eafe86a1519f7285
and 5f59536dda1812c65f4e8d14b32ca30c6442f978 respectively. Preserve these exact
baselines as prefixes; do not substitute an older application snapshot.

Root cause: update_user already deleted all target sessions when the role changed
or active was false, but the post-transaction kick checked only active=false.
The sole runtime change computes revoke_sessions before updating the user and
uses that same predicate for transactional deletion and the post-commit kick.
All changed roles are covered, including promotions: this preserves the existing
session policy, rather than introducing a demotion-only policy. Unchanged-role,
active profile edits and existing reactivation behavior remain unchanged.
Self-revocation and last-superadmin guards, CSRF dependencies, password reset,
user deletion, the event hub, viewer routes and bug 5 are not modified. Bug 7
is not implemented. No migration, setting, dependency or new API is introduced.

Validation actually executed with Python 3.12.8 / pytest 8.3.5, plugin autoload off:
- New isolated route-body regressions against the verified baseline: 6 failed,
  14 passed. Every changed active-role pair missed its kick on the baseline.
- Candidate focused modules: 20 passed, 1 module skipped (0.19 seconds).
  The skipped module contains four ASGI/WebSocket cases; FastAPI is unavailable.
- The changed runtime file and both new test files compiled successfully.

The executable unit module loads update_user and _guard_last_superadmin from the
actual source via AST, strips routing decorators, and postpones annotations.
It does not rewrite their function bodies. Real temporary SQLite transactions
are used; role enum, repository facades, redirect and hub are test doubles.
Tests cover all nine active-role pairs, three deactivations, same-role reactivation,
unknown targets, self-revocation, last-superadmin protection, rollback after failed
session deletion and an injected commit-boundary failure. A fresh independent
SQLite connection inside the hub spy verifies the kick observes committed state;
unrelated actor/other-user sessions remain intact. These are isolated route-body
tests, not HTTP, real repository, dependency-injection or WebSocket execution.

The included ASGI module mounts the real admin/viewer apps on one TestClient loop.
Its four unexecuted cases cover two inherited-access demotions, unaffected viewer
isolation, unchanged-role profile saves and missing CSRF. The demotion cases
expect closure before another viewer event or idle timeout; a new valid session
also cannot recover the lost inherited campaign access. A three-second receive
bound prevents missing-frame regressions from hanging indefinitely.

Run in a normal checkout with runtime/development dependencies:
`PYTHONPATH=python python -m pytest -q python/tests/test_user_role_socket_revocation.py python/tests/test_user_role_socket_web.py`
No full suite, browser, live-server or Python 3.14 acceptance was executed. Run
both new modules without skips and verify role-change disconnection on the target
deployment before declaring the fix integration-validated. Existing in-process
hub/transport limitations still apply; already in-flight data cannot be recalled.

Implementation and documentation are prepared only; no bug 6 GitHub write has
occurred at preparation. TODO item 6 stays open until approved delivery, when
its actual SHA and pending integration acceptance must be recorded. The bug 5
two-commit exception applied only to bug 5 and is not reused for this candidate.
No archive or Patch/ material is included in the proposed repository write.

## Bug 7 implementation candidate: forced-password-change viewer gate (2026-10-29)

Baseline: features/perplexity at b95ac2123e5c11ee2e13d4d642c6986cc0340d65.
Bugs 5 and 6 are delivered; their earlier candidate/open wording above is historical.
Bug 6 implementation: 90fa8ba8b2a895d0a193b4aebfbe8f776f26a83e; documentation:
d1c6ee1ab9665611884d2d2028f724daf6e805c0; status: b95ac2123e5c11ee2e13d4d642c6986cc0340d65.
ASGI/deployment acceptance for both remains pending.

Re-read live viewer/api.py, deps.py, README and HANDOVER before preparing changes.
The unchanged viewer API matched blob a396f2714b34722f727d54e7e6f105c45e482ad8.
Full documentation recovered from the supplied bug 6 draft matched current live
blobs ff5cc083eb18693b6b887f189302f0f6165f5766 (README) and
659982bf5c47595fdbb21ab00e7822c0103f7304 (HANDOVER); retain those exact prefixes.
No old uploaded application snapshot substitutes for these live baselines.

Root cause: live() resolves a session without require_user()'s password-change
restriction, and bug 5's hashed-session checker also omitted the flag.
The sole runtime file changed is web/viewer/api.py: live() closes with 4403 before
accept/subscribe when its resolved user must change password; _session_allowed()
also rejects the flag on every subsequent check. Existing post-subscribe checks
cover flag changes during admission. Existing event/pong/report guards and idle
checks therefore inherit the restriction without changing the hub or timer.
All roles are covered. Missing/expired/inactive sessions and denied campaigns
retain their existing admission behavior. HTTP dependencies, auth/account/logout,
role-update routes, repositories, session revocation and bugs 5/6 are unchanged.
Account and logout remain available through their existing HTTP exceptions;
clearing the flag through successful password change permits normal reconnection.
No viewer mutation API, migration, configuration, dependency or JS change is added.

Validation actually executed on Python 3.12.8 / pytest 8.3.5, plugin autoload off:
- Final new regressions on verified baseline: 12 failed, 7 passed.
- Final new unit module on candidate: all 19 passed.
- Focused candidate run: 50 passed, 1 module skipped (0.30 seconds), comprising
  19 new cases, bug 5's existing 11 unit cases and bug 6's 20 isolated route cases.
  The skipped new module contains seven ASGI/WebSocket cases; FastAPI is absent.
- All three changed/new Python files compiled successfully.

The new unit loader extracts actual _session_allowed/live function bodies by AST,
removes decorators and postpones annotations; it does not rewrite their bodies.
Most sockets, repository/RBAC boundaries and hub operations are test doubles;
an additional case uses the real, unchanged EventHub to reject event delivery
through the new checker after the flag changes. New cases cover all three roles,
admission/recheck, valid ping/status, prior denial behavior, flag changes during
accept/receive, the timeout control path and reconnection after clearing the flag.
The timeout case injects TimeoutError, not a measured wall-clock timer. The new
unit module does not exercise real DB sessions, account password hashing, HTTP,
dependency injection or ASGI transport. Bug 5's retained unit tests use real SQLite.
Support security.py and viewer_sync.py matched their live blob hashes, and the
unchanged EventHub matched f5016149515921345c37d657485ad88862f59098. Previously
supplied bug 5/6 files were used only as focused test-tree support, not replacement
implementation files. No support files are included in the proposed commit.

The seven included ASGI cases remain unexecuted: admission denial for three roles,
a new flag blocking broadcast while another user stays connected, actual idle
closure, real account/password-change followed by reconnection, and logout while
a password change is required. These use normal application fixtures and bounded
three-second receive helpers; they are not browser or live-listener tests.

Run in a normal checkout with runtime/development dependencies:
`PYTHONPATH=python python -m pytest -q python/tests/test_viewer_password_gate.py python/tests/test_viewer_password_gate_web.py python/tests/test_viewer_session_lifetime.py python/tests/test_user_role_socket_revocation.py`
No full suite, browser, live-server or Python 3.14 acceptance was executed. Run the
new ASGI module without skips and verify required-change admission, password-change
recovery and existing-socket restriction on the deployment before declaring the
fix integration-validated. Idle checks retain the existing 15-second interval,
subject to scheduling/DB/transport delays; this adds no immediate flag-change kick.
Already in-flight data cannot be recalled and existing in-process hub limits apply.

Implementation/documentation are prepared only; no bug 7 repository write has
occurred at preparation. TODO item 7 stays open until approved delivery. Record
the delivered SHA and pending integration acceptance after delivery. Earlier
bug 5/6 split-delivery exceptions do not authorize splitting this candidate.
No archive or Patch/ material is included in the proposed repository write.

## Bug 8 implementation candidate: atomic account form validation (2026-10-29)

Baseline: features/perplexity at 960a142d0ce8e55ff661c1a5a9fa8fb5e28efe14.
Bug 7 is delivered in 07c5e8b9debad7c2fa7a3362e804c76d2cc30746, documented in
3c770fd4b90f375e5dac4c177cb85e674f7ce58a and recorded in TODO at this baseline.
Earlier candidate/open wording above is historical; HTTP/ASGI acceptance is still pending.

Re-read live auth_routes.py, db.py, users/sessions repositories, security/RBAC,
README and HANDOVER. Auth baseline blob: 7993723ffec510e819989ad21c0c35129c53dfb5.
Complete documentation recovered from the supplied bug 7 draft matched current
live blobs a71319556b61a170f8cf14780b701c7aa285b6dd and
144ca4717ead0c7e96c65905f9b0a96243193d89 respectively; preserve those exact prefixes.

Root cause: account_submit wrote display_name before password validation; returning
an error response normally caused Database.connect to commit that earlier write.
The sole runtime change moves users_repo.update(display_name=...) to the end of
the existing connection block. All existing password validations now precede every
write. Valid password/flag updates, other-session revocation and the profile write
remain in the same transaction, so write exceptions roll back the whole update.
Profile-only behavior, validation messages/order, current-session retention,
HTTP dependencies/CSRF, logout and bugs 5-7 are unchanged. No new API, migration,
configuration, dependency or frontend change is introduced. Deleted-user races
and unrelated account/session policy are not redesigned in this scoped fix.

Validation executed on Python 3.12.8 / pytest 8.3.5, plugin autoload disabled:
- New isolated tests on verified baseline: 18 failed, 14 passed (4.24 seconds).
- Candidate isolated tests: all 32 passed (4.27 seconds).
- Final focused modules: 32 passed, 1 module skipped (4.30 seconds).
  The skipped module contains 26 HTTP cases; FastAPI is unavailable.
- The changed runtime file and both new test files compiled successfully.

The isolated loader preserves the actual account_submit function body, removes its
routing decorator and postpones annotations. SQLite, user/session repository logic
and scrypt hashing/verification are real; the SQLite context wrapper models the
observed commit-on-return/rollback-on-error contract. Request/settings/render and
redirect boundaries are doubles. Tests use a minimal auth schema, not application
migrations or the actual Database wrapper. Verified live support modules are not
part of the proposed repository write. This is not HTTP/dependency-injection execution.

Both portal cookie identities are covered: four password validation errors with
required-change on/off, forced-change empty-password failure, valid profile-only
save, valid password/flag update, current-session retention, same/cross-portal
session revocation and unrelated-user isolation. Failure tests compare all user
and session rows; the four validation-error cases also assert no INSERT/UPDATE/DELETE.
Injected post-write errors in set_password, delete_for_user and profile update,
and an injected commit-boundary failure, verify rollback of all fields and sessions.

The 26 included HTTP cases remain unexecuted: failed password forms with/without
required-change, empty forced-change password, profile-only success, valid password
success and invalid CSRF behavior across both real application portals.
Run with normal runtime/development dependencies:
`PYTHONPATH=python python -m pytest -q python/tests/test_account_atomicity.py python/tests/test_account_atomicity_web.py`
No broader suite, browser, live-server or Python 3.14 acceptance was run. Execute
the HTTP module without skips and verify both portal workflows on deployment before
calling the change integration-validated. Existing bug 7 tests were not rerun here;
its viewer API, tests and runtime gate are excluded from all proposed replacements.

Implementation/documentation are prepared only; no bug 8 repository write has
occurred at preparation. TODO item 8 remains open until approved delivery; then
record the delivered SHA and pending HTTP/deployment acceptance. Earlier split-
delivery exceptions do not apply to bug 8. No archive or Patch/ material is proposed.


## Bug 9 candidate: bounded login-throttle retention (2026-10-29)

Baseline: features/perplexity at 978a16333d40137045b0480931cab45d8709da88.
Bug 8 is delivered in 35f749192272bdc3028b08a5f9493ba90160438f, documented in
704419d7a669fc55ae407090b4b7b79105b7a7d0, with TODO status at this baseline.
Earlier candidate/open wording records historical preparation, not delivery status.
Bug 8 HTTP/deployment acceptance remains pending. TODO's workflow summary and
remaining order still omit bug 8 delivery; those stale lines are not repaired here.

The user approved bounded, fail-closed capacity handling for bug 9. Live security.py
matched blob f5402c281b894921b4cfcfbb1f50b934d979eeb6. Complete uploaded README
and HANDOVER, after CRLF-to-LF normalization, matched current live blobs
cb0f241d53a8b83953a3219a448e6ae8e89e3b67 and
e06be3269ebef7e0a4064c10029f8f4a6de900f7. Preserve those exact normalized
contents as prefixes; do not substitute an older application snapshot.

Scope: only LoginThrottle in python/looking_glass/security.py changes runtime
behavior. MAX_KEYS=4096 limits retained IP/username entries; fail retains at most
max_failures newest timestamps per key. blocked never creates an entry. Checks
and failures prune all expired histories and delete empty keys under the existing
thread lock, sampling monotonic time after acquiring it. At capacity, blocked
rejects untracked keys without evicting active histories. Existing tracked keys
still follow the configured rolling window and threshold, and successful reset
releases its key. Lowercasing and existing key encoding remain unchanged. For
nonpositive thresholds, admission stays blocked without retaining failures; for
nonpositive windows and positive thresholds, failures are not retained and no
lockout is introduced. No constructor-validation/configuration-policy change.
Password hashing, session logic, account atomicity, roles, fog and bugs 1-8 are
not replaced. No schema, route, dependency, setting, file deletion or rename.

Validation actually executed on Python 3.12.8 using stdlib unittest in a temporary
focused package, with the real complete security.py module and an empty package
initializer. Only time.monotonic is replaced by a deterministic clock in unit
cases; no AST rewriting or throttle-body doubles. The test imports
looking_glass.security, matching normal repository package imports.
- Verified baseline: 17 tests ran; 15 failed and 2 passed.
- Candidate: all 17 passed (0.049 seconds), none skipped.
- Changed runtime and new regression file both compiled successfully.
- Additional real-default-cap probe: 4,200 distinct fail calls retained exactly
  4,096 keys/timestamps and blocked an overflow key. This is a bound assertion,
  not a performance/load acceptance benchmark.

Coverage includes check-only allocation, exact expiry, rolling-window behavior,
bounded newest histories, cleanup of abandoned keys, fail-closed saturation,
locked-history preservation, expiry/reset capacity recovery, case/IP isolation,
threaded failures and mixed reset/check/failure operations, nonpositive settings,
a deterministic capacity race and 1,000 seeded reference-model operations below
capacity. Thread tests exercise real threads, not all possible schedules.
The earlier 13-test preliminary standalone run is superseded by these final results.

Run without repository conftest/framework dependencies from the repository root:
PYTHONPATH=python python -m unittest discover -s python/tests -p test_login_throttle.py
Or use the normal development environment:
PYTHONPATH=python python -m pytest -q python/tests/test_login_throttle.py
The pytest invocation and project conftest were not executed in this preparation.
No full suite, HTTP application/DI, browser, live-server, multi-process or Python
3.14 deployment checks ran. Verify normal login failure/429/reset behavior and
capacity recovery on both portals with normal dependencies before calling this
HTTP/deployment accepted. No HTTP regression module is added in this scoped draft.

Limits/decisions: saturation intentionally trades availability for protecting
active histories; one failure each across 4,096 keys can deny new-key login until
capacity recovers. Existing tracked subthreshold keys can still authenticate.
blocked and fail remain separate calls: in-flight authentication is not cancelled
or rechecked if capacity fills in between. fail then drops a new-key record rather
than exceeding the bound/evicting another key; subsequent checks see saturation.
This does not provide atomic attempt reservation or a strict concurrent-attempt
limit. State is per instance/process and disappears on restart. Key strings keep
their existing encoding and arbitrary input lengths; the cap bounds entry and
timestamp counts, not a fixed byte budget. Cleanup is lazy/request-driven, not
time-driven release, and scans the bounded table while holding its lock. No
cross-process throttle, global rate limit or background maintenance is added.

Delivery exception explicitly approved by the user for bug 9 only: three separate
commits, documentation first (README, HANDOVER), then implementation plus tests.
README step 1 is delivered in dcd93fcee0d62508c541a13042e5874f5f50e28d; this
HANDOVER update is step 2. Runtime implementation and tests remain pending step 3
and their own exact-write approval. No tests were rerun during documentation delivery.
TODO item 9 remains open until approved implementation delivery; then record the
actual SHA and distinguish delivery from pending HTTP/deployment acceptance.
No archive or Patch/ material is part of the proposed repository writes.

## Bug 10 implementation candidate: ordered NeDB deletion replay (2026-10-29)

Baseline: features/perplexity at 4ab341e648013066f23a17e95480700315d3d949.
Bug 9 runtime is delivered in a0610c6b6a7af13b7b516a992364b4a38035ccd6 and its
TODO status in 6aade7df9fdf103f0b1096c0f86631a66fcbd177; earlier preparation
wording above is historical. README is a present-tense product guide at blob
20d0d3d3b1d897f576af842762f11133c48a9ab7: preserve its editorial policy without
patch references, bug/fix narratives or historical comparisons. It was reviewed
and needs no change for this parser implementation. Detailed NeDB semantics are
added to docs/foundry-import.md instead. HANDOVER baseline blob is
1dd7ec467f74e2c8df3b2d9e8f3ea0ac324c4135; its complete contents are preserved.

Only _parse_ndjson changes runtime behavior. Replay identified records in order:
replace a live _id, remove it on a truthy $$deleted record, and permit recreation
by a later document. Unknown/repeated deletions do nothing. IDs must be non-empty
strings, without coercion or trimming; malformed IDs raise WallImportError.
Anonymous live records remain independent; anonymous deletions and nonobjects are
ignored. Output is live identified records followed by anonymous records. Updates
keep their dictionary position; deletion/recreation inserts after surviving IDs.
Blank lines, JSON syntax errors, format auto-detection, JSON object/array semantics,
Foundry classification/alignment, UVTT and ZIP policies remain unchanged. The
existing No walls found error applies when direct replay leaves no usable geometry;
ZIP retains its skip-invalid-entry/no-supported-sets behavior. No schema, setting,
dependency, route, migration, deletion or rename. Bugs 2, 11 and 12 remain separate.

Live importer baseline matched f785fcc529fd9636a1e5ab1f74cde263072e7435.
Unchanged wall_model.py, pack_images.py, uvtt_export.py and test_foundry_import.py
were also reconstructed and verified against their live Git blobs before use as
test support. None of those unchanged files is proposed for replacement.

Validation actually executed on Python 3.12.8 / pytest 8.3.5 with plugin autoload
disabled in a temporary focused package:
- New pytest regressions on baseline: 15 failed, 9 passed (0.03 seconds).
- New candidate unittest module: 24 passed (0.003 seconds).
- Candidate focused pytest run: 32 passed, none skipped (0.05 seconds): 24 new
  cases and all eight unchanged existing importer cases.
- Changed importer and new regression module compiled successfully.
The preliminary baseline unittest report counted subtest failure/error events;
use the pytest 15-failed/9-passed result for method-level comparison.

Tests import the complete real parser, wall model, standard UVTT and ZIP helpers.
Empty package initializers and a minimal focused conftest containing the existing
two_room_scene helper avoid unrelated application fixture imports. Repository
conftest/configuration/application initialization was not executed. No AST rewriting,
fake parser, network or persistent DB was used. Coverage includes updates,
deletion/recreation, unknown/repeated deletion, ID case/order, anonymous documents,
truthy/false markers, malformed IDs, syntax errors, public walls/scenes/no-walls,
JSON-array compatibility, UTF-8 BOM and ZIP-contained histories. Existing cases
cover standard UVTT/classification/alignment, not extended portal graphs.

Normal-checkout commands:
PYTHONPATH=python python -m unittest discover -s python/tests -p test_nedb_replay.py
PYTHONPATH=python python -m pytest -q python/tests/test_nedb_replay.py python/tests/test_foundry_import.py
No saved-source DB, broader pack-image suite, full suite, HTTP, browser, live-server
or Python 3.14 deployment acceptance ran. Verify normal import and wall-set selection
with application dependencies before declaring integration/deployment acceptance.

Source bytes and walls already copied to maps are not automatically rewritten.
Explicit reapplication can change wall-set counts/indexes when deleted scenes are
omitted: review the selected set and blank viewers before applying geometry.
No automatic data repair is included; broad malformed-input and finite-value work
remain separate. The README and TODO.md are excluded from proposed changes.

The user explicitly approved two-commit delivery for bug 10 only: this HANDOVER
record first, followed by importer, regression module and import guide together.
Each write requires its own exact-content approval. Runtime implementation remains
pending step 2; TODO item 10 stays open until implementation delivery, when its
actual SHA and remaining acceptance must be recorded. No tests were rerun during
this documentation preparation. No archive or generated Patch/ material is included.

## Bug 11 implementation candidate: finite numeric imports and target transforms (2026-10-29)

Baseline: features/perplexity at 9713edf7bc4a9fc2c5c772207e330a8287b27fad.
Bug 10 runtime is delivered in be09fef50ea0a3bd1609b9850eab98b9a0061e41 and
its TODO status in this baseline; earlier preparation wording above is historical.
The current README is reviewed and remains a present-tense product guide without
patch references or bug/fix history. No README edit is required for this scoped
candidate; detailed numeric behavior belongs in docs/foundry-import.md. Preserve
the complete HANDOVER baseline d22a3c25e2c57e6710ecb728a8d73a7e34e0e68e.

Numeric helpers reject non-finite converted coordinates, origins and derived
geometry. Explicit dimensions, grids and UVTT scales/sizes must be positive;
padding must be non-negative. Omitted/null optional metadata retains defaults.
Explicit zero/negative required sizes and nonnumeric grid values are rejected.
Finite numeric strings and negative coordinates/offsets remain supported. Numeric
conversion/overflow failures use WallImportError, not a blanket exception handler.
Legacy omission of nonnumeric/zero-length wall coordinates remains unchanged;
structure/type and skip-policy work stays under bug 12. No arbitrary coordinate
cap, schema, dependency, configuration, deletion or rename is introduced.

validated_calibration checks actual target-map scales, offsets and transformed
endpoints. campaigns.apply_walls invokes it BEFORE walls_repo.replace for both
automatic and retained calibration. Direct and saved-source inspections translate
numeric calibration rejection to BadRequest. Complete route modules preserve
unrelated source, signatures, decorators and registration statements. Do not deploy
routes without the corresponding importer/helper implementation.

Measured validation on Python 3.12.8 / pytest 8.3.5 with plugin autoload disabled:
- Final 170 new baseline cases: 158 failed, 12 passed.
- Fresh combined candidate after restoring uploaded implementation and complete
  route artifacts: 202 passed, no failures/errors/skips (0.35 seconds).
- Counts: numeric/parser 154; isolated route-body 16; existing importer 8; NeDB 24.
- All six complete candidate Python files passed py_compile in the fresh rerun.
- Route assembly also verified unchanged source/AST outside the three targeted
  functions and preserved all 49 decorated-function definitions; 12 wiring checks
  passed. The earlier fragment run is not substituted for the combined rerun.
No application tests are claimed rerun merely for this documentation preparation.

The focused tree uses empty package initializers and a minimal conftest containing
the existing two_room_scene helper. Unchanged wall-model, UVTT/ZIP helpers and
existing tests matched pinned live Git blobs. Numeric parser/helper logic is real;
route tests AST-extract bodies from COMPLETE modules and remove annotations and
decorators. DB/repository, permission, request, response/fog and reconciliation
boundaries are doubles. Write-spy ordering is not persistent-DB rollback proof.
No full application imports/registration, HTTP/ASGI, authentication/CSRF, migrated
DB, full suite, extended portal graphs, browser, live listener or Python 3.14
acceptance was executed. No HTTP/DB regression module is included; that coverage
and acceptance remain unfinished and must not be described as passed.

Focused command in a normal checkout after complete delivery:
PYTHONPATH=python python -m pytest -q python/tests/test_import_numbers.py python/tests/test_import_numeric_routes.py python/tests/test_foundry_import.py python/tests/test_nedb_replay.py

Limits: ZIP keeps its per-entry skip policy; a numeric rejection can omit an entry
while accepting usable companions. Actual target/current calibration can make a
finite source unusable on one map. Source bytes, copied walls and bad legacy data
are not automatically repaired. Map-upload partial-wall/source-retention and file
lifecycle behavior are not redesigned. Broader malformed containers/doors are bug 12.

The user explicitly approved four-commit delivery for bug 11 only:
1. HANDOVER documentation.
2. Importer, numeric/parser regression module and import guide.
3. Complete campaigns.py and wall_sources.py replacements.
4. Complete api.py replacement and numeric route-body regression module.
Each write needs its own exact-content approval. The 202-pass result applies to
the COMPLETE final candidate, not separately to intermediate commits. Do not deploy
intermediate states as the completed fix. TODO item 11 remains open until step 4
succeeds; record actual delivered SHAs and pending integration/deployment acceptance
then. No unrelated README/TODO edit, archive or generated Patch/ folder is proposed.

## Bug 11 delivery completed; acceptance pending (2026-10-29)

All four approved delivery steps are committed to features/perplexity:
1. HANDOVER preparation: df9ad36b369b77aa2e896dd56dff95fb45d6fb7c.
2. Importer, numeric/parser tests and import guide: f03520b8ac76a2155a3af3eef4fc0c878acb71b6.
3. Apply/saved-source routes: 0f537c9b5b2e4881997da3ccb18e05543009b5f3.
4. Direct inspection and route-body tests: c21c0d1a299449eadf93ec8188afe6caf799654d.
TODO completion is committed in a024f61ac94126375831cae9b092fcd0e9959d86.
Historical candidate/open wording above describes preparation, not current delivery.

A fresh focused run immediately before step 4 approval passed all 202 cases,
none failed or skipped, in 0.26 seconds on Python 3.12.8: 154 numeric/parser,
16 isolated route-body, eight existing importer and 24 NeDB replay cases.
All six complete candidate Python files compiled successfully. The delivered
files are the exact tested candidates; no paired-dimension restriction was added.
No tests were rerun after the GitHub writes or for this documentation-only update.

The focused package used empty initializers and a minimal conftest with the
existing scene helper; unchanged support/test files matched live Git blobs.
Parser/calibration logic is real. Route tests load actual function bodies from
complete modules through AST, removing decorators and annotations; DB/repository,
permission, request/response, fog and reconciliation boundaries are doubles.
These checks prove isolated ordering, not persistent-DB rollback or HTTP acceptance.

Integration/deployment acceptance remains unfinished: run the four-module focused
command above in a normal checkout, add and execute real HTTP/DB inspection,
import and saved-source cases, and verify unchanged stored geometry on rejection
for automatic and retained calibration. Full application imports/registration,
authentication/CSRF, migrated DB, full suite, extended portal graphs, browser,
live-server and Python 3.14 acceptance were not executed. Retain the ZIP skip,
legacy-data and upload/file-lifecycle limitations documented above.

Five backlog implementations remain open: 12, 2, 13, 14, 15, in that suggested
order. Delivered implementations and pending acceptance are separate statuses.
README remains unchanged; this update adds no runtime code, tests or Patch/ material.
