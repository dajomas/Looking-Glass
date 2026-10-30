## Ordered fog snapshot initialization (2026-10-30)

CI run 41011195909 against fe357602aa918ecc7dfa25b02178fd9775a237d9
reported reversed snapshot operation order during a version-2 upgrade.
Historical migration SQL and schema version count remain unchanged. The runner
now delegates pending migrations to `migration_hooks.apply_migration`. Only
while applying version 3, it leaves the script transaction open, initializes
its newly created snapshots from `fog_ops ORDER BY map_id,id` using Python JSON,
and records version 3 before committing. Any failure rolls back this migration's
schema, snapshot data and version record. Other migration execution is unchanged.
This avoids dependence on aggregate ORDER BY syntax or JSON subtype behavior.
Maps with no history still have no snapshot. Raw history and cache-token behavior
are retained. The hook only runs for a pending version 3; already migrated
snapshots are not rebuilt, including ones that differ from offline edit history.
No automatic repair of previously misordered snapshots is attempted: recovering
those requires an explicit, backed-up decision rather than overwriting saved
last-displayed state from potentially different current history.

Seven isolated candidate-hook SQLite checks passed in the assistant environment
(Python 3.12.8, SQLite 3.46.1): ordering/coordinates across interleaved maps,
empty maps, committed version, initialization rollback/retry, version-insert
rollback, later-migration preservation, and in-transaction hook execution.
These used a focused schema and migration-3 fixture, not the full checkout.
New repository tests in `python/tests/test_fog_snapshot_migration.py` cover real
migration integration, idempotency, saved-state preservation and rollback.
Those tests, the existing `test_map_display.py` suite and full Python/live suites
have not been executed by the assistant; Python 3.14 CI acceptance is pending.
The original migration regression is unchanged. The separate Scrying Glass asset
token assertion failure is out of scope and remains unresolved.
README.md was reviewed; existing upgrade/backup and test guidance stays accurate.

