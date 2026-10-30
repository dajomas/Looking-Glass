## Admin map artwork URL contract

Shared admin map responses from `_map_payload` include:

- `image_url`: `/api/maps/{map_id}/image`, a relative URL for the original/current base map
  artwork through the authenticated admin image route.
- `image_version`: the artwork identity used for detecting replacement.
- `double_reveal_image`: whether an alternate double-reveal image is configured.

This applies to `GET /api/maps/{map_id}` and responses that reuse the same payload, including
`POST /api/maps/{map_id}/walls/from-source`. Importing embedded pack artwork must not omit
`image_url`. The endpoint retains map-management authorization and `Cache-Control: no-store`;
no filesystem path, public file serving, or raw viewer image access is introduced.

`image_url` intentionally continues to mean base artwork, not the current per-room appearance
composite. Double-reveal DM previews use `/double-reveal/artwork`; player-facing rendering
continues using the fogged viewer image routes. No schema migration or dependency change is
needed for this response-field correction.


