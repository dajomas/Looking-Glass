## Read-only campaign readiness

`services/campaign_readiness.py` owns campaign-scoped checks and structured findings
(severity, stable code, message, map identity and inspection URL). The admin pages router
checks authorization first, enables SQLite query-only mode, begins a read snapshot and
passes the campaign to the service. Filesystem checks are best-effort, not an atomic
snapshot with SQLite. No results are persisted and no viewer notifications are emitted.

Room-note validation compares anchor pixels and `area_key` signatures using the current
effective topology. It calls `build_area_map` directly, not reconciliation, fog replay or
viewer rendering. This uses transient memory but creates no fog cache files or changes
to saved notes. Only maps with notes/endpoints need topology construction. Each map is
processed separately; large campaigns may still take time and use image/geometry memory.

`campaign_backup.campaign_payload` is shared by export and readiness so JSON serialization
matches the backup format. Expanded size is the serialized JSON length plus stored image
sizes; no ZIP is generated. Backup exports retain their existing read transaction and
archive format. Compressed size and infrastructure limits are not calculated.

Inspection deliberately uses a separate page without the editor JavaScript or metadata
API, because the existing editor metadata loader reconciles stale room notes. It shows
the authenticated raw image, a report-position marker and stored anchor lists. Editors
are explicit onward links. Image paths outside storage are not embedded by inspection.
No schema migration, runtime dependency or port change is introduced.

