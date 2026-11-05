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
hostnames and certificate paths before using it. Configure a default virtual
host to reject unrecognized hostnames rather than forwarding arbitrary hosts.

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

        proxy_set_header Host $http_host;
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

        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 1h;
    }
}
```

`$http_host` preserves the supplied external authority, including a nondefault
port. For example, https://dm.example.lan:8443 must reach the application with
Host dm.example.lan:8443, not dm.example.lan or 127.0.0.1:5000. Change the listen,
firewall and certificate configuration to match the actual endpoint. Hostless
requests are not a supported login path; do not synthesize a trusted origin for
them. See [nginx proxy headers](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header).

Set the following in `config.yaml` when serving the application over HTTPS:

```yaml
security:
  secure_cookies: true
```

With separate portal hostnames, bookmark the viewer hostname directly.
Admin UI links that assume the viewer is on port 5100 of the same host may
not match a separate-hostname proxy arrangement.

### Login-origin protection and proxy trust

POST /login on either portal requires a same-origin source: Origin takes
precedence, with Referer used only when Origin is absent. Comparison includes
scheme, hostname and effective port (HTTP 80 / HTTPS 443 by default). Missing,
opaque/null, malformed, duplicate or cross-origin source headers return 403.
A mismatching Origin is not rescued by a matching Referer. Existing sessions do
not exempt a login submission. Login return targets are separately checked to
remain local; authentication and authenticated-mutation CSRF rules still apply.

Preserve the browser's Origin and Referer. Do not strip them, overwrite them
with the application's origin or enable a headerless bypass. Browser/privacy
settings that remove both prevent login by design. CORS configuration is not a
substitute for this form-submission protection.

The login policy compares against the ASGI request URL; it does not itself trust
Forwarded or X-Forwarded-* headers. The normal launcher enables Uvicorn proxy
header handling. Uvicorn restricts this to trusted connecting peers via
FORWARDED_ALLOW_IPS (default 127.0.0.1 when unset). For the same-host example,
ensure the actual backend peer is loopback and the environment has not expanded
trust. For a remote/container proxy, restrict backend access and explicitly list
only the actual proxy peer addresses/networks in the service environment. Never
set FORWARDED_ALLOW_IPS=* merely to fix login. This is a server environment
setting, not a new Looking Glass config.yaml key. Restart the service after
changing its environment. Consult [Uvicorn settings](https://www.uvicorn.org/settings/#http)
and verify behavior for the installed server version.

The example terminates TLS at nginx and overwrites X-Forwarded-Proto with its
own scheme; do not forward a client-supplied scheme as trusted input. Multi-hop
TLS/load-balancer arrangements require their own explicit trust design. A
browser at https://dm.example.lan must appear to the application as that origin,
not the HTTP backend. Validate admin and viewer separately; their different
hostnames or ports are different origins.

Automation posting credentials must send the receiving endpoint's exact Origin,
without a path or trailing slash, for example https://dm.example.lan:8443.
Send it only for the intended login request; do not add defaults that mask
negative security tests. Use HTTPS and avoid passwords in shell history, process
arguments or diagnostic logs.

### Deployment verification checklist

These are checks to perform on the actual deployment, not claims that a real
nginx/TLS configuration has already passed the application suites.

1. Check nginx configuration with nginx -t and reload through the site's normal
   service procedure. Verify recognized hosts and restricted backend access.
2. Sign in through each external portal in a fresh browser context, including
   the actual nondefault port if used. Confirm normal redirect/account behavior
   and appropriate secure session cookies over HTTPS.
3. Using disposable credentials, verify a matching Origin reaches normal
   authentication, while a foreign or null Origin returns 403 and creates no
   session. With Origin absent, matching Referer may authorize the request;
   with both absent it must be rejected. Keep valid-password checks separate
   from throttle/invalid-credential errors and do not record passwords.
4. Confirm that a slash/backslash external login return target stays local,
   including an already-authenticated visit to the login page.
5. If legitimate login receives 'Login requires a same-origin request', compare
   the external scheme/host/port to what the trusted ASGI request sees. Check
   Host preservation, actual proxy peer trust, TLS scheme and stripped source
   headers. Correct the deployment; do not disable the guard or fabricate Origin.
6. Recheck viewer WebSocket connectivity through the proxy's existing Upgrade
   forwarding. Record the endpoint/topology and outcomes without credentials.

### SELinux and nginx

If SELinux is enforcing and prevents nginx from connecting to the backend,
enable the appropriate network-connect permission:

```bash
sudo setsebool -P httpd_can_network_connect 1
```

This is conditional proxy configuration, not a required step for every
installation.

