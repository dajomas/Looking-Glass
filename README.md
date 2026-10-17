# Looking Glass

A fog of war tool for D&D battle maps. The DM imports a battle map plus its
**Foundry VTT walls**, then clicks a room in the admin screen. The whole area
enclosed by walls is revealed on the players' viewer screen, live.

- **Two entry points**: admin portal on port **5000**, viewer (player) screen on port **5100**
- **RBAC**: `superadmin` (manages users), `admin` (manages own campaigns and assigns viewers), `viewer` (views assigned campaigns only)
- **SQLite3** storage, no external services
- Multiple **campaigns**, each with multiple **battle maps**
- Imports **Foundry VTT** scene exports (v9 to v13+), NeDB `scenes.db`/`walls.db`, plain wall lists, and Universal VTT (`.dd2vtt` / `.uvtt`)
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
