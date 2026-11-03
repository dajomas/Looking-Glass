## Campaign readiness HTML routes

These authenticated admin-portal GET routes return HTML, not JSON:

| Route | Purpose |
|---|---|
| `/campaigns/{campaign_id}/readiness` | Run campaign-scoped checks and render the report |
| `/campaigns/{campaign_id}/readiness/maps/{map_id}` | Read-only DM map inspection |

Inspection accepts optional numeric `x` and `y` query parameters in image coordinates.
Finite coordinates are highlighted; out-of-bounds positions are clamped for display only.
Non-finite coordinates do not produce a marker; invalid numeric input is rejected by
FastAPI validation. Inspection verifies that the map belongs to the URL campaign.

Both routes require campaign-management permission and use `Cache-Control: no-store`.
They do not require CSRF because they perform no state changes. Database reads run in
an explicit snapshot with `PRAGMA query_only=ON`. There is no repair endpoint and no
viewer notification. Inspection image requests reuse the existing authenticated raw-map
image route; no new viewer route is exposed.

