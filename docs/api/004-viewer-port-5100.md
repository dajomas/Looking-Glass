## Viewer port (5100)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/c/{campaign}/state` | Active map name, size, version and versioned `image_url` (or `map: null`) |
| GET | `/api/c/{campaign}/image` | Fogged composite of the active map |
| WS | `/ws/c/{campaign}` | Pushes `{"type":"refresh","reason":...}`; send `ping` to keep alive |

Both ports also serve `GET /healthz`.

