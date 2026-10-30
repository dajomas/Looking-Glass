## 4. Podman deployment

This is an alternative to the native installation and its systemd unit.

The host uses the same configuration and data locations as the native
installation. Inside the unchanged image, data remains mounted at `/app/data`.
The image sets `LG_DATA_DIR=/app/data`, overriding the host-oriented YAML data
path. Do not remove that override unless you also change the container mount.

The examples below use rootless Podman as the current login user, not the native
`lookingglass` service account. For a NEW container-only installation:

```bash
sudo install -d -o root -g "$(id -g)" -m 0750 /etc/looking-glass
sudo install -o root -g "$(id -g)" -m 0640 \
  docs/examples/config.production.yaml /etc/looking-glass/config.yaml
sudo install -d -o "$(id -u)" -g "$(id -g)" -m 0750 /var/lib/looking-glass
sudoedit /etc/looking-glass/config.yaml
```

Set `storage.data_dir: /var/lib/looking-glass` and keep the database filename
relative as in the native example. Do not overwrite an existing configuration
or change ownership of a native installation's data using these setup commands.
For existing data, stop the old instance, back up and plan ownership/SELinux
label changes for the chosen deployment user before switching methods.

From the repository root:

```bash
podman build -t looking-glass -f Containerfile .
```

For direct access on ports 5000 and 5100:

```bash
podman run -d --name looking-glass \
  --userns=keep-id --user "$(id -u):$(id -g)" \
  -e LG_CONFIG=/etc/looking-glass/config.yaml \
  -e LG_DATA_DIR=/app/data \
  -p 5000:5000 \
  -p 5100:5100 \
  -v /etc/looking-glass/config.yaml:/etc/looking-glass/config.yaml:ro,Z \
  -v /var/lib/looking-glass:/app/data:Z \
  looking-glass
```

For a reverse proxy running on the host, use the same command but replace the
port publications with `-p 127.0.0.1:5000:5000 -p 127.0.0.1:5100:5100`.
Run only one instance. `:Z` privately relabels the mounted paths on SELinux hosts;
use dedicated paths and do not share them with a running native instance.
The configuration mount is read-only; data is writable by the mapped login user.

View startup logs:

```bash
podman logs looking-glass
```

The first start with an empty database generates and logs the initial
superadmin credentials.

For persistent container startup, configure a Podman Quadlet service. The
native `looking-glass.service` supplied with the repository runs a checkout
and virtual environment; it does not manage this container.

