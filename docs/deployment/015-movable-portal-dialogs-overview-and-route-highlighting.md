## Movable portal dialogs, overview and route highlighting

This follow-up targets c745166b56319901be8b609d120a9ee3b4cf9817. Stop both
processes, preserve local edits and normal data backups, extract replacements at
repository root and restart/reload editor tabs. The admin API includes an additive
read-only presentation field, so update backend and assets together. Modified
assets use portal-tools-4. No new migration/dependency/port is required.

The 5-second default/1–15 second per-pair slider and pause flag are stored in the
admin browser per map, not in the database. Reduced-motion settings are respected.
Rollback this follow-up by restoring its replaced code/assets from the base; no
database rollback is necessary. Earlier migration-10 passage rollback requirements
remain separate. Run the checks in [testing](testing.md) against the installed
version before live deployment.


