## Passages upgrade (schema 10)

This incremental patch targets a055343a921c0e6e234025744ea1269f2e4240fb.
Stop both processes and back up the complete data directory/database before
extracting replacement files at repository root. Restart normally to apply
migration 10, then reload admin/viewer tabs. No new dependency or port is needed.
Do not deploy mixed code versions against the migrating database. Rollback requires
restoring the matching old code and pre-upgrade data/database backup; no down
migration is supplied.

