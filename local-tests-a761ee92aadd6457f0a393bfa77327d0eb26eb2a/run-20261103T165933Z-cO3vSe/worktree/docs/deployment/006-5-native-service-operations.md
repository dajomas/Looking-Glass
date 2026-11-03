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

