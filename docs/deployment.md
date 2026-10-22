# Deployment

Looking Glass provides two portals:

| Portal | Default port |
|---|---|
| Admin / DM | 5000 |
| Viewer / players | 5100 |

Choose one deployment method:

- Native installation with systemd: follow sections 1 and 2.
- Podman: follow section 4 instead.

Configure networking as appropriate for either method. Do not run native and
container instances against the same data directory simultaneously.

## 1. Native installation (RHEL / Rocky)

These instructions assume installation under `/opt/looking-glass` and a
Python 3.14 executable named `python3.14`.

Install Python using an appropriate repository or your preferred installation
method. Where the packages are available:

```bash
sudo dnf install git python3.14
```

### Create the service account

For a new installation:

```bash
sudo useradd --system --user-group \
  --home-dir /opt/looking-glass \
  --no-create-home lookingglass
```

If the account already exists, do not recreate it. Ensure that the
`lookingglass` group also exists.

### Install the application

```bash
sudo git clone https://github.com/dajomas/Looking-Glass.git /opt/looking-glass
cd /opt/looking-glass
```

Check out the branch, tag or commit you intend to deploy before installing
dependencies.

```bash
sudo python3.14 -m venv .venv
sudo .venv/bin/pip install -r requirements.txt
```

The service account needs read and directory-traversal access to the checkout
and virtual environment. Application code does not need to be writable by the
service account.

### Create and review the configuration

For the first installation only:

```bash
sudo install -o root -g lookingglass -m 0640 \
  config.example.yaml config.yaml
```

Do not repeat this command during upgrades: it would overwrite the existing
configuration.

Review the configuration before starting the application:

```bash
sudoedit /opt/looking-glass/config.yaml
```

Keep the viewer port set to 5100:

```yaml
server:
  host: 0.0.0.0
  admin_port: 5000
  viewer_port: 5100
```

Use `host: 127.0.0.1` instead if both portals should be reachable only through
a reverse proxy running on the same machine.

Continue with the systemd setup below.

## 2. systemd service

The supplied service runs both portals as `lookingglass`, using the virtual
environment directly. There is no need to activate the virtual environment
or use a shell wrapper.

### Prepare writable storage

For a new installation:

```bash
sudo install -d -m 0750 -o lookingglass -g lookingglass \
  /opt/looking-glass/data
```

If reusing an existing data directory, ensure that its existing files and
subdirectories are also owned appropriately. Creating the directory alone
does not repair ownership of existing contents.

The service account must be able to:

- Read the application, virtual environment and configuration.
- Write the database, map files, saved wall sources and cache under `data/`.

### Install and start the service

Install the supplied unit once:

```bash
sudo install -m 0644 \
  /opt/looking-glass/docs/examples/looking-glass.service \
  /etc/systemd/system/looking-glass.service
```

Load the unit and enable/start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now looking-glass.service
```

Check startup:

```bash
sudo systemctl status looking-glass.service --no-pager
```

### Service paths and filesystem protection

The supplied unit uses:

| Setting | Value |
|---|---|
| User | `lookingglass` |
| Working directory | `/opt/looking-glass` |
| Python executable | `/opt/looking-glass/.venv/bin/python` |
| Configuration | `/opt/looking-glass/config.yaml` |
| Writable directory | `/opt/looking-glass/data` |

The canonical unit is `docs/examples/looking-glass.service`; it is not
duplicated here.

`ProtectSystem=strict` makes the filesystem read-only for the service except
for locations permitted by `ReadWritePaths`.

If you move the checkout, adjust `WorkingDirectory`, `ExecStart` and
`ReadWritePaths` in the unit or an appropriate override.

If `storage.data_dir` or the database is placed outside the default data
directory, update `ReadWritePaths` and filesystem ownership before starting
the service.

## 3. Networking

### Direct LAN access

For clients connecting directly to the application:

- Keep `server.host: 0.0.0.0`, or use the appropriate listening address.
- Allow access to admin port 5000 only from trusted DM devices.
- Allow access to viewer port 5100 from the player devices that need it.

If using firewalld, the following opens both ports in its default zone:

```bash
sudo firewall-cmd --permanent \
  --add-port=5000/tcp \
  --add-port=5100/tcp
```

Choose the appropriate zone and restrict access further where required.

### Reverse proxy

When nginx runs on the same host as the native application, use
`server.host: 127.0.0.1` if direct access to the backend ports is not needed.

Expose the proxy's HTTP/HTTPS ports rather than opening 5000 and 5100 to
clients.

For HTTPS access through firewalld:

```bash
sudo firewall-cmd --permanent --add-service=https
```

The direct-access and reverse-proxy rules above are alternatives. Apply only
the rules required by your deployment.

After making permanent firewalld changes, load them into the runtime
configuration:

```bash
sudo firewall-cmd --reload
```

Do not run firewalld commands on systems that use another firewall manager.

### nginx example

The following is an HTTPS configuration outline. Replace the example
hostnames and certificate paths before using it.

Place the `map` and `server` directives in nginx's HTTP configuration context:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 443 ssl;
    server_name dm.example.lan;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    client_max_body_size 200m;

    location / {
        proxy_pass http://127.0.0.1:5000;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl;
    server_name table.example.lan;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5100;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 1h;
    }
}
```

Set the following in `config.yaml` when serving the application over HTTPS:

```yaml
security:
  secure_cookies: true
```

With separate portal hostnames, bookmark the viewer hostname directly.
Admin UI links that assume the viewer is on port 5100 of the same host may
not match a separate-hostname proxy arrangement.

### SELinux and nginx

If SELinux is enforcing and prevents nginx from connecting to the backend,
enable the appropriate network-connect permission:

```bash
sudo setsebool -P httpd_can_network_connect 1
```

This is conditional proxy configuration, not a required step for every
installation.

## 4. Podman deployment

This is an alternative to the native installation and its systemd unit.

From the repository root:

```bash
podman build -t looking-glass -f Containerfile .
```

For direct access on ports 5000 and 5100:

```bash
podman run -d --name looking-glass \
  -p 5000:5000 \
  -p 5100:5100 \
  -v lg-data:/app/data:Z \
  looking-glass
```

For a reverse proxy running on the host, publish the backend ports on loopback
instead:

```bash
podman run -d --name looking-glass \
  -p 127.0.0.1:5000:5000 \
  -p 127.0.0.1:5100:5100 \
  -v lg-data:/app/data:Z \
  looking-glass
```

Run only one of these container examples.

View startup logs:

```bash
podman logs looking-glass
```

The first start with an empty database generates and logs the initial
superadmin credentials.

An optional configuration file can be mounted with:

```text
-v ./config.yaml:/app/config.yaml:ro,Z
```

Ensure that the container's application user can read the mounted file.

For persistent container startup, configure a Podman Quadlet service. The
native `looking-glass.service` supplied with the repository runs a checkout
and virtual environment; it does not manage this container.

## 5. Native-service operations

The following are independent operations, not a sequence to run together.

### View recent logs

```bash
sudo journalctl -u looking-glass.service -b --no-pager
```

### Follow logs continuously

```bash
sudo journalctl -u looking-glass.service -f
```

Press Ctrl+C to stop following the logs. This does not stop Looking Glass.

### Retrieve initial credentials

On the first run with an empty database:

```bash
sudo journalctl -u looking-glass.service --no-pager \
  | grep -A3 "initial superadmin"
```

Change the generated password at first login and restrict access to the
journal. Credentials are not generated again when the superadmin already
exists.

If `LG_SUPERADMIN_PASSWORD` was supplied for initial creation, the generated
password message is not used.

### Restart the service

After changing application configuration:

```bash
sudo systemctl restart looking-glass.service
```

A change to `config.yaml` does not require `daemon-reload`.

After changing a systemd unit or drop-in, run `systemctl daemon-reload` before
restarting the service.

### Stop the service

```bash
sudo systemctl stop looking-glass.service
```

### Start a stopped service

```bash
sudo systemctl start looking-glass.service
```

## 6. Backups and upgrades

### Backups

With the default configuration, application state is under:

```text
/opt/looking-glass/data/
```

This includes:

- `looking_glass.db`: SQLite database.
- Map artwork and reusable wall sources.
- Render cache files.

For a straightforward consistent backup:

1. Stop the service.
2. Back up the complete data directory and the configuration file.
3. Store the backup securely outside the application directory.
4. Start the service again.

If storage paths were customized, include those locations too.

For an online SQLite database backup, use SQLite's backup command rather
than copying only the live database file. Back up map/source files as well;
a database-only backup is not a complete application backup.

Render-cache contents can be regenerated. Clear them only when the
application is stopped.

### Upgrades

For a native installation:

1. Stop the service.
2. Back up all application data and configuration.
3. Update the checkout to the intended revision.
4. Update virtual-environment dependencies if required.
5. Review configuration and unit-file changes.
6. Run `systemctl daemon-reload` only if the unit or a drop-in changed.
7. Start the service and inspect the journal.
8. Reload existing DM and viewer tabs to load updated JavaScript and CSS.

Do not run old and new application versions concurrently against the same
database.

Startup applies the pending database migrations for the installed revision.
Rollback after a schema change may require restoring the pre-upgrade data
backup together with the corresponding application version. Do not manually
decrement `schema_version`.

### Historical reveal-state upgrade

The earlier fog-display update introduced schema migration 3, explicit
reveal-state handling and revised composite-cache keys.

For installations upgrading across that change:

- Preserve a complete pre-upgrade backup.
- Reload DM and viewer tabs after deployment.
- Old composite-cache files are ignored by the revised cache-key format.
- Clearing the render cache while stopped is optional.
- Existing saved wall sources are retained.

## Door-arrow and clickable-arrow upgrade

This cumulative patch supports baseline schema 4, the color-only arrow schema 5 and the toggle schema 6. Stop both processes and back up the database/data. Extract the repository-root-relative replacement files, restart normally and reload admin pages. Startup applies migrations 5 and 6 only if needed. Existing colors and enabled/disabled settings survive the upgrade. Clicking requires no new migration, dependencies or configuration keys. New versioned admin script URLs load the click helper before the map editor.

Verify a room-to-hidden-room arrow on both screens; click it on the admin screen while Hide mode is selected, confirm the opposite room is revealed and Undo restores the prior fog. Check drag/pinch behavior, disabled arrows, retained color and stale clicks. The viewer remains read-only. Render cache identities change automatically; manual cache cleanup is optional. For rollback restore matching previous code and database backup; no down-migration is supplied.


## Locked-door patch on e519068

This patch targets the supplied `e519068f27ec3edef456e60e2557b9022c1d210e` source with the Center/Fit feature rolled back. Stop both application processes and back up SQLite (including live WAL contents as appropriate) plus application data. Extract the replacement/new files at repository root and restart normally. Startup applies reserved no-op migration 7, if needed, then locked-door migration 8. A database that already recorded the old viewer migration 7 is supported; leftover viewer columns remain unused. No Center/Fit feature is reintroduced and no new dependencies/config keys are required.

Reload admin browser tabs to load the versioned scripts/styles. Verify new design types, locked-arrow color on both displays, unlock-without-reveal, reveal-after-unlock, double-click-to-lock without reveal, Reset for originally locked AND originally unlocked doors, and existing Undo/reveal behavior. Viewers remain read-only; their JS/templates are unchanged. Use the [testing guide](testing.md) to validate behavior in the installed environment. Rollback requires matching previous code and database backup; no down-migration is supplied.


## Independent arrow visibility upgrade

Apply this changed-file archive to the supplied d457b93 source containing the locked-door patch. Stop both application processes, back up SQLite/data, extract at repository root, restart normally and reload admin tabs for the versioned script. Startup applies migration 9, copying every map's existing shared preference to both screen flags. Existing colors, lock state and fog history are preserved. No dependencies/configuration keys or Center/Fit features are added.

Verify all four admin/viewer combinations, including exact viewer-image preview, admin arrow clicks and locked-arrow double-click behavior. Admin-only toggles should not refresh the viewer; changing viewer visibility must update active viewer images. A viewer browser reload is not needed for new JavaScript because viewer scripts are unchanged. Rollback requires previous code and matching database backup; no down-migration is included. See [map controls](map-controls.md) for visibility behavior and [testing](testing.md) for validation.


## Viewer room-zoom upgrade

Apply the changed/new files to the supplied 1618eef source containing split arrow visibility and locked doors. Stop the application processes, back up code/data normally, extract at repository root and restart both processes so the new read-only endpoint is available. Reload viewer tabs to load the versioned zoom helper/display script. No database migration, new dependency or configuration setting is required; the existing schema remains unchanged.

Verify focus/toggle on two revealed rooms, hidden-area no-op, manual pan then refit, Fit/F overview, resize, live hide/reset while focused, map switching/blanking, and drag/pinch suppression. Admin arrow visibility, viewer arrow visibility, lock/unlock and fog operations should be unchanged. See [testing](testing.md) for validation guidance. Rollback is the prior code version; this patch does not alter database contents/schema.


## Admin-controlled viewer zoom upgrade

Apply this changed-file archive to the supplied 13d62ae source (viewer room zoom already installed). Stop both processes, back up normally, extract at repository root, restart both processes and reload BOTH admin and viewer browser tabs. This is important: older viewer scripts ignore the new camera event type. No database migration, new dependency or configuration key is required. No rolled-back Center/Fit preferences are added.

With a live viewer connected, double-click a revealed admin area in Reveal and Hide modes; verify room focus/overview in the viewer, no admin camera movement, and no fog action. Verify ordinary delayed singles, immediate right-click inverse mode, regular arrows, locked/unlocked double-clicks, viewer-local double-click/F, multi-viewer behavior, inactive-map rejection, hidden-area no-op, disconnected screens and stale map changes. See [testing](testing.md) for automated checks and environment requirements. Roll back to prior code; this increment does not change database schema/data.


## New-reveal overview reset upgrade

Apply the changed/new files to the supplied f1d837f source, which includes admin remote zoom. Stop both processes and back up code/data normally, extract at repository root, restart and reload viewer tabs so the versioned helper/display scripts and new state metadata are used together. No database migration, dependency or configuration change is required; admin tabs need no new gesture code.

Focus a viewer room locally and from admin, then reveal a second room: verify all visible areas are fitted/centered. Test a room inside unchanged overview bounds; hide/reveal exchange; Reveal all; Undo hide; repeated Reveal; colors, arrow flags and lock/unlock changes; and an old pending zoom response arriving after a reveal. Style/lock-only updates should preserve focus. See [testing](testing.md) for automated and manual checks. Rollback is the prior code version; there are no database changes to undo.

## Passages upgrade (schema 10)

This incremental patch targets a055343a921c0e6e234025744ea1269f2e4240fb.
Stop both processes and back up the complete data directory/database before
extracting replacement files at repository root. Restart normally to apply
migration 10, then reload admin/viewer tabs. No new dependency or port is needed.
Do not deploy mixed code versions against the migrating database. Rollback requires
restoring the matching old code and pre-upgrade data/database backup; no down
migration is supplied.

## Movable portal dialogs, overview and route highlighting

This follow-up targets c745166b56319901be8b609d120a9ee3b4cf9817. Stop both
processes, preserve local edits and normal data backups, extract replacements at
repository root and restart/reload editor tabs. The admin API includes an additive
read-only presentation field, so update backend and assets together. Modified
assets use portal-tools-4. No new migration/dependency/port is required.

The 5-second default/1–15 second per-pair slider and pause flag are stored in the
admin browser per map, not in the database. Reduced-motion settings are respected.
Rollback this follow-up by restoring its replaced code/assets from the base; no
database rollback is necessary. Earlier migration-10 passage rollback requirements
remain separate. Run the checks in [testing](testing.md) against the installed
version before live deployment.


## Installing the viewer arrow exceptions patch

Stop Looking Glass and back up its SQLite database before updating. Extract the patch
archive into the repository root, preserving relative paths and replacing supplied files.
Restart normally; the existing migration runner applies schema migration 11 automatically.
Hard-refresh admin and viewer pages after updating. No new dependencies or config keys
are needed. New exception flags default off and existing visibility settings are preserved.
For a complete rollback, stop the application and restore both pre-patch code and the
pre-patch database backup. Do not manually modify schema_version.


## Installing cross-map passages (schema migration 12)

This incremental patch targets commit cbaf4890d5aba22dd50b42445b1c7109ef5fb8ee.
Stop both portals before installing. Back up the entire data directory, SQLite
file and any present WAL/SHM sidecars while stopped, along with your working tree.
Extract the archive at the repository root, preserving relative paths and replacing
only its listed files. Do not apply over an unrelated source snapshot or a schema
with a different migration 12. Review the changed files against the target source
version before replacing local modifications.

Restart through your normal launcher. The existing migration runner applies schema
12 automatically. Hard-refresh admin and viewer tabs. There are no new packages,
ports or config keys; the viewer default remains 5100. Marker/label settings default
on but no existing maps acquire endpoints automatically. Migration preserves the
prior map, arrow and fog data. Server-side marker labels try Windows Arial or Linux
DejaVu Sans and fall back to Pillow's built-in font; unsupported glyphs in the fallback
may not render. No fonts or other assets are downloaded.

Test on a copy of a campaign before live play, including one-way/return connections,
a secret endpoint, preserve/reveal arrival, stale-tab rejection and a deleted target.
Run HTTP/CSRF and real-browser tests in the installed project environment before
live use. See [testing](testing.md) for commands, prerequisites and manual checks;
a test command documented here is not a claim that it passed on every platform.

For rollback, stop both portals and restore the matching pre-patch code and complete
pre-upgrade data/database backup together. There is no down-migration. Do not lower
schema_version manually. Preserve the post-upgrade backup too if you may need to
recover newly authored endpoint links; wall exports do not carry these links.


## Passage modal and sidebar updates

The map-passage main-action footer and exclusive sidebar peers remain unchanged.
Inspect destination is admin-only and does not activate viewers or prompt for fog.

### Independent configuration and session saving

Restart both portals after installing the updated save handler so create/update
responses include saved_endpoint_id. Reload the admin page to load the versioned
controller and renamed controls. No migration, dependency, port or configuration
change is required. Verify configuration/session draft isolation in both directions,
new-endpoint creation followed by session update, repeated revision-safe saves,
failed-save retention, Close/Escape warnings and inspection without viewer changes.
Full-server/browser checks should be run in your installed environment; see
[testing](testing.md). Rollback restores matching previous code/assets; this increment
requires no database rollback. Previously saved configuration/session edits remain
real data changes and are not undone by rolling back the UI.


## Portal Close, Travel return and Reset labels

Reload the admin wall/map editor pages after deploying updated templates and
versioned portal/travel scripts. No migration, backend behavior change, dependency
or configuration change is required. If your running template loader caches HTML,
restart the portals to ensure the new markup is loaded. Verify dirty portal Close/
Escape confirmation, clean Close without a question, paired-reset scope, Back to
passage/Escape retaining pending fields, and the clearer Show battle map labels.
The destructive activation reset has the same existing effects; test it on a copy,
not a live campaign. Rollback restores prior code/assets, not databases. Saved
changes or resets performed during use are not undone by a UI rollback.
