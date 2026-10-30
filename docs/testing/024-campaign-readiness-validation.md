## Campaign readiness validation

Run from the repository root in the normal development environment:

```sh
PYTHONPATH=python pytest python/tests/test_campaign_readiness.py python/tests/test_campaign_readiness_templates.py python/tests/test_campaign_readiness_web.py python/tests/test_campaign_backup.py -q
```

Service coverage includes clean/empty campaigns, campaign isolation, missing/corrupt/unsafe
images, dimensions, informational missing walls, endpoint bounds, missing/arrival-only
links, wall-pixel arrival, same-map links, stale and valid room-note signatures, query-only
execution, unchanged database contents and map files, no fog cache output, and expanded
size matching real backup ZIP entries. Template tests cover escaping and the absence of
editor startup scripts. HTTP tests cover manager/superadmin access, other-admin/viewer
rejection, map membership, escaped names, marker clamping and unchanged database state.
HTTP tests are skipped when FastAPI is not installed; a skip is not successful HTTP coverage.

Manual browser acceptance:
1. Keep a player viewer open and record active map/fog state.
2. Run Check campaign and inspect a note/endpoint finding; confirm players do not change.
3. Confirm location markers, missing-image guidance and editor links are useful.
4. Fix an issue manually and re-run; confirm the finding disappears.
5. Confirm arrival-only endpoints and maps without walls are informational.
6. Confirm a non-owning admin cannot load report or inspection URLs.
7. Exercise large campaigns and concurrent file replacement to assess runtime/limitations.

