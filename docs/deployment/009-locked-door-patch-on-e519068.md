## Locked-door patch on e519068

This patch targets the supplied `e519068f27ec3edef456e60e2557b9022c1d210e` source with the Center/Fit feature rolled back. Stop both application processes and back up SQLite (including live WAL contents as appropriate) plus application data. Extract the replacement/new files at repository root and restart normally. Startup applies reserved no-op migration 7, if needed, then locked-door migration 8. A database that already recorded the old viewer migration 7 is supported; leftover viewer columns remain unused. No Center/Fit feature is reintroduced and no new dependencies/config keys are required.

Reload admin browser tabs to load the versioned scripts/styles. Verify new design types, locked-arrow color on both displays, unlock-without-reveal, reveal-after-unlock, double-click-to-lock without reveal, Reset for originally locked AND originally unlocked doors, and existing Undo/reveal behavior. Viewers remain read-only; their JS/templates are unchanged. Use the [testing guide](testing.md) to validate behavior in the installed environment. Rollback requires matching previous code and database backup; no down-migration is supplied.


