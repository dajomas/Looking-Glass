# Deployment

Looking Glass provides two portals:

| Portal | Default port |
|---|---|
| Admin / DM | 5000 |
| Viewer / players | 5100 |

Choose one deployment method:

- Native installation with systemd: follow sections 1 and 2.
- Podman: follow section 4 instead.

Configure networking as appropriate for either method. Do not run native and
container instances against the same data directory simultaneously.

