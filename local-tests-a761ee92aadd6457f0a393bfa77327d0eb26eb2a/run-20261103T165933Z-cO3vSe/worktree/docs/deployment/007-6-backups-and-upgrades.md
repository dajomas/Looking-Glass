## 6. Backups and upgrades

### Backups

With the deployment configuration above, application state is under:

```text
/var/lib/looking-glass/
```

This includes:

- `looking_glass.db`: SQLite database.
- `maps/`: map artwork. Reusable wall sources are stored in the SQLite database.
- Render cache files.

For a straightforward consistent backup:

1. Stop the service.
2. Back up `/var/lib/looking-glass` and `/etc/looking-glass/config.yaml`.
3. Store the backup securely outside the application directory.
4. Start the service again.

If storage paths were customized, include those locations too.

For an online SQLite database backup, use SQLite's backup command rather
than copying only the live database file. Back up map files as well;
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

### Move an existing native installation to the new paths

Updating these documentation files does not move a running installation's data.
Before installing the updated unit, stop the service and take a verified backup
of its current configuration and complete data directory. The example below
assumes the old locations were `/opt/looking-glass/config.yaml` and
`/opt/looking-glass/data`; substitute your actual paths if different.
Do not merge into a destination that already contains another installation.

```bash
sudo systemctl stop looking-glass.service
sudo install -d -o root -g lookingglass -m 0750 /etc/looking-glass
sudo install -o root -g lookingglass -m 0640 \
  /opt/looking-glass/config.yaml /etc/looking-glass/config.yaml
sudo install -d -o lookingglass -g lookingglass -m 0750 /var/lib/looking-glass
sudo cp -a /opt/looking-glass/data/. /var/lib/looking-glass/
sudo chown -R lookingglass:lookingglass /var/lib/looking-glass
sudoedit /etc/looking-glass/config.yaml
```

Only copy the configuration above if the destination file does not already
exist. In the editor, set `storage.data_dir: /var/lib/looking-glass` and use
`storage.database: looking_glass.db` unless intentionally using another database
path. Check for stale `LG_DATA_DIR`/`LG_CONFIG` environment variables and systemd
drop-ins that could override the new configuration or write permissions.
Preserve all stopped SQLite files, including any WAL/SHM sidecars, in the copy.

Install the updated example unit as described in section 2, then:

```bash
sudo -u lookingglass test -r /etc/looking-glass/config.yaml
sudo -u lookingglass test -w /var/lib/looking-glass
sudo systemctl daemon-reload
sudo systemctl start looking-glass.service
sudo systemctl status looking-glass.service --no-pager
sudo journalctl -u looking-glass.service -b --no-pager
```

Confirm your existing campaigns/users/maps are present. A new initial-superadmin
message may indicate that the service opened an empty database at the wrong
path. Keep the old files until the migrated installation and backups have been
verified. For rollback, stop the service and restore the previous unit/config
and the matching data backup; do not run both copies against shared storage.
For containers, stop the container rather than the native unit and copy from
the actual old bind mount or named volume, not necessarily the old checkout.

### Administrative CLI commands

Use the deployment configuration explicitly for maintenance commands, otherwise
they can open a different database using developer defaults:

```bash
cd /opt/looking-glass
sudo -u lookingglass .venv/bin/python python/main.py \
  --config /etc/looking-glass/config.yaml list-users
```

### Historical reveal-state upgrade

The earlier fog-display update introduced schema migration 3, explicit
reveal-state handling and revised composite-cache keys.

For installations upgrading across that change:

- Preserve a complete pre-upgrade backup.
- Reload DM and viewer tabs after deployment.
- Old composite-cache files are ignored by the revised cache-key format.
- Clearing the render cache while stopped is optional.
- Existing saved wall sources are retained.

