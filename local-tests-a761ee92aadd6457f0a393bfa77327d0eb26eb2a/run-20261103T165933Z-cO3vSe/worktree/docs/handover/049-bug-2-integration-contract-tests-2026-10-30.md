## Bug 2: regression-first integration contracts (2026-10-30)

Prepared against features/perplexity HEAD
61aa38b73c3b51f1514745c3ba5af96f308373df. The user requested pushing the
integration tests before the implementation. This is an intentionally red,
tests-only baseline, not delivery of the bug-2 fix.

The two new top-level HTTP test modules specify 41 parameterized cases: 28
archive/recovery cases and 13 backup/restore/duplication cases. They use the
existing test_web environment, real sessions/CSRF, uploaded PNGs, Foundry walls
and SQLite. Read-triggered reconciliation stages real geometry directly to
isolate the admin GET path. The event publication spy forwards to the real hub;
it is not connected-browser/WebSocket delivery coverage. Storage failures use
SQLite triggers; they are not actual disk exhaustion or crash tests.

At preparation, live source ended at migration 17. The fixture deliberately
fails when room_note_archives is absent. No skips, exclusions, xfail markers,
workflow changes or runtime implementation are included. All cases must be
revisited after migration/archive/recovery implementation; a failed setup is
not execution of the underlying HTTP assertions.

Contract: archive GET returns {ok,archives} with no-store; explicit recovery
POST accepts target coordinates, area_key, revision, cache_token, walls_version,
room_notes_version and overwrite. Conflict/stale context is 400; wrong-map
archive is 404; missing required save context is 422; injected storage errors
are 500 with complete rollback. These are test-defined implementation targets,
not installed endpoint guarantees. Archives are retained after recovery and
replacement archives preserve overwritten content. No automatic reattachment,
purge or note-triggered fog/viewer changes are permitted.

The final review layout consolidates helpers and formatting from the earlier
downloadable draft while retaining its 41 cases. The earlier draft passed AST
parsing/compilation only. The final commit contents received static review;
no application tests, imports or pytest collection were executed here. There
is no verified Actions run/tested SHA for this change at preparation.

Run from the repository root:

```bash
PYTHONPATH=python python -m pytest -v \
  python/tests/test_room_note_archive_web.py \
  python/tests/test_room_note_archive_portability_web.py
```

Remaining: migration 18, lossless transactional archive/detach, revision-safe
saves and recovery, recovery UI, portability implementation and execution of
these tests. Earlier drafted migration/service tests are not included in this
commit. Browser, live listeners, restart and container acceptance remain outside
these modules. Keep bug 2 open. README.md was reviewed and remains unchanged
because no user-facing feature is installed. The split handover records and
both historical reconstruction manifests are unchanged; only an index link is
added. No Patch/ delivery material is included.
