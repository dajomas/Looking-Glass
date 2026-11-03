## Live integration-test boundary (batch 1)

The optional live_e2e suite starts two actual Uvicorn listeners over one AppContext
and one asyncio loop, as required by the in-process EventHub. This exercises the
browser/HTTP/SQLite/image-generation/WebSocket boundary absent from intercepted
browser fixtures. It uses the production app factories and _Server signal-handling
adapter, but bypasses interactive bootstrap with synthetic test account seeding.
It therefore does not certify the CLI bootstrap or production process supervisor.

Every test starts with default-derived isolated settings and tmp_path storage;
no project/user config is loaded. Real authenticated setup requests and DM UI fog
actions drive an independent player browser context. Polling assertions sample the
img installed by production viewer JS. Final-state map consistency is covered;
transient frame atomicity and exhaustive privacy checks are future batches.

There are no production code, schema, API or dependency changes in this batch.


