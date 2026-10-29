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

