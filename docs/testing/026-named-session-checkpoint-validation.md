## Named session checkpoint validation

From the repository root, run in the normal development environment:

```sh
PYTHONPATH=python pytest python/tests/test_session_checkpoints.py python/tests/test_session_checkpoints_templates.py python/tests/test_session_checkpoints_web.py python/tests/test_campaign_backup.py -q
```

Service coverage includes capture/preview without play-state changes, multi-map round trip,
last-displayed snapshot preservation/absence, door/entry overrides after hide-all triggers,
endpoint state, safety-checkpoint recovery, preservation of authored notes/names/appearance/
access, other-campaign isolation, monotonic versions, travel-cache clearing, incompatible
wall/calibration/image/map identity/map set/endpoint changes, changed engine configuration,
stale and duplicate forms (including empty campaigns), invalid cross-map runtime references,
transaction rollback on database failure, corrupt payload/fog, missing images, payload limit,
campaign deletion cascade, migration from schema 15 and schema-15 backup compatibility.
Template tests cover escaping and hidden restore controls when incompatible. HTTP tests
cover workflow, CSRF, confirmation/token handling, owner/superadmin access and other-admin/
viewer denial, read-only preview, deletion and stale restore resubmission. Missing FastAPI
skips HTTP coverage; skipped tests are not integration validation.

Manual acceptance before live use:
1. Create a named checkpoint with two maps, different fog and runtime passage states.
2. Continue play, then inspect the checkpoint; viewers must not change during preview.
3. Restore explicitly and verify active map/fog, locked/discovered passages and live refresh.
4. Restore the automatic safety checkpoint to recover the pre-restore state.
5. Confirm notes, authored walls/connections, owner and viewer assignments stay unchanged.
6. Edit geometry or replace an image and verify an older checkpoint is blocked.
7. Change play state in another tab after preview and verify the stale form is rejected.
8. Exercise pagination and typed-name deletion; confirm no automatic history pruning.
9. Test normal map switching after restore; existing map-display behavior is unchanged.

Keep item 7 (file-import busy feedback) deferred in TODO.md; it is not part of these tests.


