## Current live README highlights

The branch README describes considerably more than the original uploaded snapshot:

- Admin port 5000 and viewer port 5100.
- Reusable campaign wall sources, batch imports and independent per-map alignment/fog.
- A dedicated wall editor, UVTT export, door states, secret passages and same-map portals.
- Cross-map passages with explicit DM travel confirmation.
- Viewer room focus, admin-controlled viewer focus and viewer synchronization status.
- Named rooms, DM-only Markdown notes and imported room-note libraries.
- Campaign backup/restore, readiness checks, campaign search, named session checkpoints and clean duplication.
- Alternate room artwork via Double reveal, documented as adding schema migration 17.
- Extensive browser-test harness and regression follow-ups documented in README, docs/testing.md and Patch/.

These are documentation observations, not an independent functional audit. Do not infer that migration 17 is the latest schema version; inspect db.py and current deployment notes. No application tests were run while preparing this handover.

