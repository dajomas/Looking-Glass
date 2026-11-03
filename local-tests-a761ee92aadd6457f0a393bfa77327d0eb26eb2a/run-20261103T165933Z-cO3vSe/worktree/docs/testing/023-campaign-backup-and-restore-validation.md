## Campaign backup and restore validation

Run the service tests from the repository root:

```sh
PYTHONPATH=python pytest python/tests/test_campaign_backup.py -q
```

Coverage: content round trip with linked endpoints and door/passage runtime states;
owner/viewer preservation and other-campaign isolation; absence of password hashes;
foreign-key integrity; transaction rollback after invalid campaign details; expanded
archive-size rejection. These service tests do not exercise HTTP authorization or UI.

In a development installation with requirements-dev installed, also run:

```sh
PYTHONPATH=python pytest python/tests/test_web.py -q
```

Manual checks before deployment:
1. Download, inspect and restore a campaign with maps, fog, room notes and linked endpoints.
2. Confirm active map, settings, runtime door states and notes survive.
3. Confirm current owner/viewers and other campaigns remain unchanged.
4. Reject wrong campaign confirmation, missing CSRF, other-admin and viewer access.
5. Reject corrupt ZIP, incompatible schema, missing image and upload-size overflow.
6. Confirm restore refreshes an already connected viewer.
7. Confirm cancelled confirmation sends no restore request.

Patch-specific executed results and limitations are recorded in
[Patch change notes](../Patch/campaign-backup-restore.md), not inferred from this guide.

