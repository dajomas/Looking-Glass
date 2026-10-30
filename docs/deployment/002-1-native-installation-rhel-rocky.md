## 1. Native installation (RHEL / Rocky)

The deployment layout separates read-only application code, configuration and
writable state:

| Purpose | Location |
|---|---|
| Application and virtual environment | `/opt/looking-glass` |
| Configuration | `/etc/looking-glass/config.yaml` |
| Persistent data | `/var/lib/looking-glass` |
| SQLite database (with the settings below) | `/var/lib/looking-glass/looking_glass.db` |

These instructions assume a Python 3.14 executable named `python3.14`.
The application does not automatically discover the `/etc` configuration:
pass `--config /etc/looking-glass/config.yaml` or set `LG_CONFIG` explicitly.
The developer defaults remain unchanged; set `storage.data_dir` as shown below.

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
sudo install -d -o root -g lookingglass -m 0750 /etc/looking-glass
sudo install -o root -g lookingglass -m 0640 \
  docs/examples/config.production.yaml /etc/looking-glass/config.yaml
```

Do not repeat this command during upgrades: it would overwrite the existing
configuration.

Review the configuration before starting the application:

```bash
sudoedit /etc/looking-glass/config.yaml
```

Keep the viewer port set to 5100 and set the absolute data directory. Merge
these keys into the existing sections rather than adding duplicate YAML keys:

```yaml
server:
  host: 0.0.0.0
  admin_port: 5000
  viewer_port: 5100

storage:
  data_dir: /var/lib/looking-glass
  database: looking_glass.db
```

Use `host: 127.0.0.1` instead if both portals should be reachable only through
a reverse proxy running on the same machine.

Continue with the systemd setup below.

