## Viewer synchronization diagnostics (step 5)

`GET /api/campaigns/{campaign_id}/viewer-status` is mounted on the admin portal only.
It requires authenticated campaign management permission (owner/admin or superadmin),
is read-only, and returns `Cache-Control: no-store`. It uses the usual 401/403/404 access
handling. No CSRF token is required for this GET. It cannot be called on the viewer portal.

Response fields: `viewers` (connection records), `counts` by status, `blank` (whether the
current target is the waiting screen), `stale_after_seconds` (65), `retained_for_seconds`
(90). Each record has `id` (ephemeral short connection identifier), `username`, `status`,
`last_report_seconds` (seconds since valid report or ping; UI labels this last contact),
and `connected` (socket not yet closed; freshness is evaluated separately). Status values
are `connected`, `loading`, `up-to-date`, `failed`, `reconnecting`. Retained disconnected
rows are included in counts, so totals are not unique users or strictly live socket counts.
No raw acknowledged/expected map versions or image details are returned by this endpoint.

The existing authenticated `/ws/c/{campaign_id}` viewer socket additionally accepts:

```json
{"type":"viewer-status","state":"ready","version":"1:cache-token-2-3"}
```

Allowed states are `loading`, `ready`, `failed`; version is 1–200 characters. `blank`
identifies a successfully displayed waiting screen. Normal map versions use the unchanged
`id:cache_token-walls_version-fog_version` format already supplied by viewer state. Text
frames larger than 2048 characters close with 1009; malformed/unknown reports are ignored.
Client-supplied identities, campaign IDs and error strings are never trusted or displayed.
Existing `ping`/`pong`, refresh and remote-zoom messages remain supported.

`ready` becomes Up to date only when its version equals the server's current active target.
Changed target versions become Loading without needing a successful refresh broadcast.
Failed reports remain Failed even when the target changed; stale/closed transport overrides
all display states. Legacy pings update contact freshness but do not imply readiness.
Reports affect ephemeral diagnostics only; they cannot mutate campaign or user data.

