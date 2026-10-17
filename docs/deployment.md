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
