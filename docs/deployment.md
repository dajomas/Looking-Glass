# Deployment

## Bare metal (RHEL / Rocky)

```bash
sudo dnf install python3.14            # or build / use uv: uv python install 3.14
sudo useradd --system --home /opt/looking-glass lookingglass
sudo git clone <repo> /opt/looking-glass && cd /opt/looking-glass
sudo python3.14 -m venv .venv && sudo .venv/bin/pip install -r requirements.txt
sudo cp config.example.yaml config.yaml
sudo install -d -o lookingglass data
sudo cp docs/examples/looking-glass.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now looking-glass
sudo journalctl -u looking-glass | grep -A3 "initial superadmin"   # first password
sudo firewall-cmd --permanent --add-port=5000/tcp --add-port=5100/tcp && sudo firewall-cmd --reload
```

With SELinux enforcing on non-standard ports behind nginx:
`sudo setsebool -P httpd_can_network_connect 1`.

## systemd service

After the bare-metal installation above, the supplied unit runs both portals as
`lookingglass`, with admin port 5000 and viewer port 5100. The following paths
assume the checkout and virtual environment are in `/opt/looking-glass`.

### Install and start

Review `/opt/looking-glass/config.yaml` before starting. Keep
`server.viewer_port: 5100`. The service uses the virtual environment directly;
there is no need to activate it or use a shell wrapper.

```bash
cd /opt/looking-glass
sudo install -d -m 0750 -o lookingglass -g lookingglass /opt/looking-glass/data
sudo chown root:lookingglass /opt/looking-glass/config.yaml
sudo chmod 0640 /opt/looking-glass/config.yaml
sudo install -m 0644 docs/examples/looking-glass.service /etc/systemd/system/looking-glass.service
sudo systemctl daemon-reload
sudo systemctl enable --now looking-glass.service
sudo systemctl status looking-glass.service --no-pager
```

The unit is provided in `docs/examples/looking-glass.service`:

```ini
# /etc/systemd/system/looking-glass.service
[Unit]
Description=Looking Glass - D&D fog of war
After=network-online.target

[Service]
Type=simple
User=lookingglass
WorkingDirectory=/opt/looking-glass
ExecStart=/opt/looking-glass/.venv/bin/python python/main.py --config /opt/looking-glass/config.yaml serve
Restart=on-failure
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/opt/looking-glass/data
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

`ProtectSystem=strict` makes the filesystem read-only for the service except
for `/opt/looking-glass/data`, where SQLite, maps, saved sources and cache live.
The service account must be able to read the application, its virtual
environment and config, and write the entire data directory. If reusing an
existing installation, correct the ownership of existing data files too.
If you move `storage.data_dir` or the database outside this directory, update
`ReadWritePaths` in a systemd override and grant ownership there before starting.
Changing the checkout location also requires updating `WorkingDirectory`,
`ExecStart`, and `ReadWritePaths`.

### Logs, credentials and maintenance

```bash
sudo journalctl -u looking-glass.service -b --no-pager
sudo journalctl -u looking-glass.service -f
sudo journalctl -u looking-glass.service --no-pager | grep -A3 "initial superadmin"
sudo systemctl restart looking-glass.service
sudo systemctl stop looking-glass.service
```

On the first run with an empty database, the application logs the generated
superadmin credentials. Change that password at first login and restrict access
to the journal. Credentials are not generated again for an existing superadmin.

After changing only `config.yaml`, restart the service. After changing the unit
or a drop-in, run `sudo systemctl daemon-reload` before restarting. For updates,
stop the service, back up the complete data directory, update the code and
virtual-environment dependencies, then start the service and check the journal.
Do not run a second instance manually against the same data directory while the
service is active.

## Podman

```bash
podman build -t looking-glass -f Containerfile .
podman run -d --name looking-glass -p 5000:5000 -p 5100:5100 \
  -e LG_SUPERADMIN_PASSWORD='change-me-now' \
  -v lg-data:/app/data:Z looking-glass
podman logs looking-glass
```

Mount a config with `-v ./config.yaml:/app/config.yaml:ro,Z`.
`podman generate systemd` or a Quadlet `.container` file makes it a service.

### nginx example

```nginx
map $http_upgrade $connection_upgrade { default upgrade; '' close; }

server {                         # DM portal
    listen 443 ssl; server_name dm.example.lan;
    client_max_body_size 200m;
    location / { proxy_pass http://127.0.0.1:5000; proxy_set_header Host $host;
                 proxy_set_header X-Forwarded-For $remote_addr; proxy_set_header X-Forwarded-Proto $scheme; }
}
server {                         # player screen
    listen 443 ssl; server_name table.example.lan;
    location / { proxy_pass http://127.0.0.1:5100; proxy_set_header Host $host;
                 proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade;
                 proxy_set_header Connection $connection_upgrade; proxy_read_timeout 1h; }
}
```

Set `security.secure_cookies: true` when serving over HTTPS. If you use one
hostname for both portals, the "Viewer screen" links in the admin UI assume
the viewer runs on `viewer_port` of the same host. With separate hostnames,
just bookmark the viewer URL.

## Backups

All state is in `data/`: `looking_glass.db` (SQLite, WAL mode) plus
`data/maps/`. `data/cache/` can be deleted at any time. For a consistent hot
backup: `sqlite3 data/looking_glass.db ".backup backup.db"`.

## Reveal-state update (schema v3)

Stop the service and back up the entire data directory before applying the
fog-display patch. Start the service to apply migration 3 automatically. Do not
run old and new application versions concurrently against the same database.
Rollback of the migration means restoring the pre-update backup with the old
application, not decrementing `schema_version` by hand.

Reload existing DM and viewer tabs after deployment to load the new prompt and
viewer race guard. Old composite cache files are ignored by the new cache-key
format; clearing the render cache while stopped is optional. No existing saved
wall sources are removed by this migration.
