## 2. systemd service

The supplied service runs both portals as `lookingglass`, using the virtual
environment directly. There is no need to activate the virtual environment
or use a shell wrapper.

### Prepare writable storage

For a new installation:

```bash
sudo install -d -m 0750 -o lookingglass -g lookingglass \
  /var/lib/looking-glass
```

If reusing an existing data directory, ensure that its existing files and
subdirectories are also owned appropriately. Creating the directory alone
does not repair ownership of existing contents.

The service account must be able to:

- Read the application, virtual environment and configuration.
- Write application state under `/var/lib/looking-glass`, including the database,
  map artwork and cache. Saved wall sources are stored in the database.

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
| Configuration | `/etc/looking-glass/config.yaml` |
| Writable directory | `/var/lib/looking-glass` |

The canonical unit is `docs/examples/looking-glass.service`; it is not
duplicated here.

`ProtectSystem=strict` makes the filesystem read-only for the service except
for locations permitted by `ReadWritePaths`.

If you move the checkout, adjust `WorkingDirectory` and the executable/script
paths in `ExecStart`. Keep the configuration and data paths independent.
The unit permits writes only under `/var/lib/looking-glass`; `/etc/looking-glass`
remains read-only to the service.

If `storage.data_dir` or the database is placed outside the documented data
directory, update `ReadWritePaths` and filesystem ownership before starting
the service.

