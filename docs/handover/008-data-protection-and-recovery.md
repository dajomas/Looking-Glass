## Data protection and recovery

Read current docs/deployment.md before upgrades, schema changes or restores. The original layout uses data/looking_glass.db, data/maps/ and disposable rendered files in data/cache/; confirm current configuration and additional storage paths first.

Back up the stopped application's complete configured data storage before risky changes. Campaign ZIP backup, session checkpoints and full installation backup have different scopes: the README says campaign exports omit accounts/sessions, and checkpoints are local to the installation database rather than portable campaign ZIPs. Do not treat this handover or Git as a backup of runtime data.

Keep authorization, CSRF validation and DM-only notes intact. Inspection/search/navigation actions documented as read-only must not reveal fog, activate maps or travel. Do not accidentally expose hidden map content or secret passage state to viewers.

