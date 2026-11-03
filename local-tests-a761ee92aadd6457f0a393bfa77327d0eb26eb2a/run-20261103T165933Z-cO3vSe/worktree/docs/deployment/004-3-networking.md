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

