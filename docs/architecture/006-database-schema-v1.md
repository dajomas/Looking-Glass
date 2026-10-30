## Database schema (v1)

`users`, `sessions` (hashed tokens, per entry point, CSRF token),
`campaigns` (owner, active map), `campaign_viewers`, `maps` (image,
calibration, `doors_block`, `walls_version`, `fog_version`), `walls`,
`fog_ops`. Migrations are append-only in `db.MIGRATIONS`.

