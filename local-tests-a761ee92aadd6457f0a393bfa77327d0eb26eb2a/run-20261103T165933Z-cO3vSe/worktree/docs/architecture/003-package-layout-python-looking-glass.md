## Package layout (`python/looking_glass/`)

| Module | Responsibility |
|---|---|
| `config.py` | Defaults, then `config.yaml`, then env vars (`LG_ADMIN_PORT`, `LG_VIEWER_PORT`, `LG_HOST`, `LG_DATA_DIR`, `LG_CONFIG`) |
| `db.py` | SQLite connection helper (connection per unit of work, WAL) + ordered migrations |
| `rbac.py` | Roles and **every** permission decision |
| `security.py` | scrypt password hashing, session tokens, login throttle |
| `bootstrap.py` | Creates the first superadmin |
| `cli.py`, `server.py`, `__main__.py` | Entry points |
| `repositories/` | All SQL: `users`, `sessions`, `campaigns`, `maps`, `walls`, `fog_ops` |
| `services/wall_model.py` | Dataclasses: `WallSegment`, `Calibration`, `FogOp`, `WallSet` |
| `services/foundry_import.py` | Foundry / UVTT parsers → `WallSet` |
| `services/fog.py` | Area detection, fog masks, viewer image compositing (storage-agnostic) |
| `services/images.py` | Image validation and storage |
| `services/events.py` | In-process WebSocket pub/sub |
| `web/context.py` | `AppContext` shared by both apps |
| `web/app_factory.py` | Builds the admin and viewer apps |
| `web/deps.py` | Auth dependencies (session cookie per portal, CSRF) |
| `web/access.py` | Load-and-authorise helpers (`campaign_for_manage`, `campaign_for_view`, …) |
| `web/auth_routes.py` | Login / logout / account (mounted on both ports) |
| `web/admin/*` | Admin pages, form posts, users, JSON API for the fog editor |
| `web/viewer/*` | Campaign picker, display page, state/image API, WebSocket |

Dependencies point one way: `web → services/repositories → db/rbac`. Services
take plain data (no DB, no FastAPI), so they are easy to test and reuse.

