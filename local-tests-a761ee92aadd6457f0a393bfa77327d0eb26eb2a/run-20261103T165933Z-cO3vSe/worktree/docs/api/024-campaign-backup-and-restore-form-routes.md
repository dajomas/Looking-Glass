## Campaign backup and restore form routes

These are admin-portal form routes, not JSON API routes. POST routes require an authenticated
campaign manager (owning admin or superadmin) and valid CSRF token, supplied as
`csrf_token` or `X-CSRF-Token`.

| Method / route | Form fields | Success |
|---|---|---|
| `POST /campaigns/{campaign_id}/backup` | `csrf_token` | ZIP attachment, `application/zip`, `Cache-Control: no-store` |
| `POST /campaigns/{campaign_id}/restore/inspect` | multipart `backup` ZIP, `csrf_token` | HTML preview; `Cache-Control: no-store`; no live campaign changes |
| `POST /campaigns/{campaign_id}/restore` | multipart identical `backup` ZIP, signed `preview`, `confirm` current campaign name, `csrf_token` | HTML success page with recovery download link; `Cache-Control: no-store` |
| `GET /campaigns/{campaign_id}/recovery/{name}` | authenticated campaign manager; exact retained filename | ZIP attachment; `Cache-Control: no-store` |

Backup uses filename `campaign-{campaign_id}-backup.zip`. Restore replaces campaign
content but preserves target ownership and viewer assignments. Validation failures
redirect with `err`; missing/invalid CSRF is forbidden. Oversized uploads use the
existing upload error handler. Missing or inaccessible campaigns use existing access checks.
The archive includes `campaign.json` (format `looking-glass-campaign`, version 1,
current schema version, campaign details and allowlisted table rows) plus `images/{id}.png`.
Raw wall source BLOBs use base64. No accounts, sessions or SQL are accepted from archives.

Restore now requires a preview issued by the same running process within 900 seconds,
bound to the user, target campaign state and archive SHA-256. Direct legacy restore POSTs
without a preview are rejected. A changed target or ZIP requires inspection again. Restore
rechecks under `BEGIN IMMEDIATE`, validates/saves a recovery ZIP, increments the campaign
session version, and checks foreign keys before commit. Recovery GETs recheck management
permissions; viewer routes do not expose these endpoints. Invalid recovery names/missing
files return 404. Recovery files are retained until an operator removes them.

