## Fog-mode Double Reveal API reuse

No endpoints or fields are added. Ctrl-left-click reads GET
/api/maps/{map_id}/double-reveal/room?x=...&y=... and sends either the existing appearance
request with true_active=true or, after confirmation, travel. Requests use the fresh
cache_token, walls_version, fog_version, image_revision, area_key and room revision;
travel includes expected_active_map_id. The client rejects changed displayed state
before writing. Existing server permission, CSRF, geometry and travel checks remain
authoritative. The marker layer is admin-only markup, absent from viewer responses.
