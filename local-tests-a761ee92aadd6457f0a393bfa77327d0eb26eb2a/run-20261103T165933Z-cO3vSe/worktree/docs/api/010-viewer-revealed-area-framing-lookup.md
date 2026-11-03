## Viewer revealed-area framing lookup

New read-only `GET /api/c/{campaign_id}/area-bounds?x=100&y=100&v=<viewer-version>` requires the existing viewer session and campaign-view authorization. Coordinates are source-map image pixels; `v` is the version returned with the currently displayed map. It returns no-store JSON:

```json
{"ok":true,"version":"1:token-1-2","bounds":{"x":10,"y":10,"width":190,"height":180}}
```

`bounds` is null for hidden/open pixels, fully hidden maps, invalid/out-of-map positions, or no eligible revealed area at that point. Visible boundary pixels can snap only to a revealed open component; unrevealed open labels are rejected even in a dilated wall fringe. Bounds cover the selected component's currently visible, wall-expanded mask. Responses contain no wall segments, component IDs, hidden room bounds or source artwork.

The endpoint checks active-map identity/version before and after its background framing computation, and rechecks campaign-view permission. A stale version/map change returns the existing 400 error path; blank maps return the existing not-found path. Normal authentication/forbidden behavior is retained. The client discards stale/out-of-order responses and refreshes state after stale/rejected lookups. This GET never adds fog operations, changes locks, checkpoints or versions, or broadcasts a map mutation. Existing state/image/WebSocket response shapes are unchanged.


