# Looking Glass - Project Handover

Last prepared: 2026-10-28 (Europe/Amsterdam).

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

First startup creates a superadmin and logs an initial password, unless LG_SUPERADMIN_PASSWORD was supplied before initialization. Change the initial password. Never commit credentials, local configuration containing secrets, database files, uploaded maps or session data.

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
