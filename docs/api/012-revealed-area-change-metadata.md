## Revealed-area change metadata

Authorized `GET /api/c/{campaign_id}/state` map payloads add `revealed_area_signatures`, a sorted array of opaque SHA-256 strings for currently revealed components only. Hidden/empty maps produce an empty array (or existing map:null when blanked). No numeric component labels, hidden-area signatures, room count for hidden geometry, wall coordinates or additional bounds are exposed.

Signatures depend on each visible component's source/work dimensions, location and binary footprint, not on its numeric label, fog operation ID, wall/fog version, arrow preferences/colors or lock kind. They stay stable across cache invalidation/restart when raster geometry is unchanged. This field is snapshot metadata, not a persistent reveal-event log. Existing version/image/area-bounds and remote camera command protocols remain unchanged.

The viewer compares the newly displayed map's signatures to the previously displayed set. A new member clears room focus and uses current `revealed_bounds` for overview. Subsets/reordering/unchanged sets do not trigger a new-area reset. Missing metadata is tolerated for compatibility and retains previous focus behavior. No mutation endpoint or database change is added; normal campaign-view authorization still applies.

