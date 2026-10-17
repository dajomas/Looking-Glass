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
sudo firewall-cmd --permanent --add-port=5000/tcp --add-port=6000/tcp && sudo firewall-cmd --reload
```

With SELinux enforcing on non-standard ports behind nginx:
`sudo setsebool -P httpd_can_network_connect 1`.

## Podman

```bash
podman build -t looking-glass -f Containerfile .
podman run -d --name looking-glass -p 5000:5000 -p 6000:6000 \
  -e LG_SUPERADMIN_PASSWORD='change-me-now' \
  -v lg-data:/app/data:Z looking-glass
podman logs looking-glass
```

Mount a config with `-v ./config.yaml:/app/config.yaml:ro,Z`.
`podman generate systemd` or a Quadlet `.container` file makes it a service.

## Port 6000 and browsers

Chrome, Edge and Firefox refuse to open port **6000** (reserved for X11) and
show `ERR_UNSAFE_PORT` / "This address is restricted". The app warns about this
at startup. Options:

1. **Reverse proxy (recommended)**: expose the viewer on 443/80 or another port
   and proxy to `127.0.0.1:6000`. Keep 6000 internal.
2. **Change the port**: `server.viewer_port: 6001` in `config.yaml`, or `LG_VIEWER_PORT=6001`.
3. **Allow it in the browser** on the table PC:
   - Chrome/Edge: start with `--explicitly-allowed-ports=6000`
   - Firefox: `about:config` → add string `network.security.ports.banned.override` = `6000`

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
    location / { proxy_pass http://127.0.0.1:6000; proxy_set_header Host $host;
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
