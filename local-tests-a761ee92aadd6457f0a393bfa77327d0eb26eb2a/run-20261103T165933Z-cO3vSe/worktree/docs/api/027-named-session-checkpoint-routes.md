## Named session checkpoint routes

Authenticated admin-portal form/HTML routes:

| Method | Route | Input / behavior |
|---|---|---|
| GET | `/campaigns/{campaign_id}/checkpoints` | `page` >=1; 50 entries/page |
| GET | `/campaigns/{campaign_id}/checkpoints/{checkpoint_id}` | Read-only restore preview |
| POST | `/campaigns/{campaign_id}/checkpoints` | `name` (1–120), optional `notes` (<=2000), CSRF |
| POST | `/campaigns/{campaign_id}/checkpoints/{checkpoint_id}/restore` | Preview `token`, `confirm` current campaign name, CSRF |
| POST | `/campaigns/{campaign_id}/checkpoints/{checkpoint_id}/delete` | `confirm` checkpoint name, CSRF |

All operations require campaign-management rights; checkpoint lookup is scoped by campaign.
Missing checkpoints return 404. GETs use query-only snapshots and no-store responses.
POSTs use write transactions and redirect with ok/err messages. Create/delete do not notify
viewers. Restore rechecks authored compatibility and current-state token while holding
`BEGIN IMMEDIATE`; it writes an automatic safety record and restored state atomically,
then invalidates caches and publishes a campaign refresh after commit. Expensive restore
work runs in a worker thread; it does not share a connection across threads.

The token is a stale-preview guard, not authorization; normal session/CSRF checks still
apply. There is no upload/import API for checkpoints or force-restore endpoint. Legacy
readiness and quick-navigation routes remain unchanged.

Campaign ZIP schema compatibility: this additive migration permits schema-15 portable
campaign ZIPs on schema 16, with existing exact table/column validation retained. This is
a narrow compatibility exception, not general support for arbitrary old schemas.

