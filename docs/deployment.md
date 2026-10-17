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

## Portable launchers

Use `./run.sh` (Bash), `run.bat` (Windows Command Prompt), or `./run.ps1`
(PowerShell). Bash users may first run `chmod +x run.sh`. Python 3.12+ must
already be installed (3.14 is recommended). `LG_PYTHON` can specify the full
path to an interpreter; it is an executable path, not a command with arguments.
All launchers change to the repository directory, create `.venv` if needed,
and install runtime requirements on first use or when requirements.txt changes.
First setup needs package-index access; later launches do not run pip unless needed.
Use `--install` to rerun pip, or `--no-install` to skip dependency setup for an
already provisioned venv. Setup failures stop startup and preserve the exit code.
No administrator privileges or global package installation are required.

Arguments are forwarded to the existing CLI, for example:

```bash
./run.sh --no-install -c config.yaml serve
./run.sh create-user dm --role admin
```

```powershell
./run.ps1 --no-install -c config.yaml serve
```

```bat
run.bat --no-install -c config.yaml serve
```

Defaults remain admin 5000 and viewer 5100. Config-file settings and
`LG_ADMIN_PORT` / `LG_VIEWER_PORT` overrides are respected; launchers do not
force ports. Ctrl+C stops the tool. PowerShell must permit local scripts under
your organization's execution policy; the launcher does not change that policy.
