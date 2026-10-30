## Explicit map-display reveal policy

`POST /api/campaigns/{id}/active` now requires `fog_action` whenever `map_id`
is non-null:

```json
{"map_id": 3, "fog_action": "restore"}
```

Use `"reset"` to delete the target map's fog-operation history before activating
it. Missing policy returns 400; unsupported values return validation error 422.
`{"map_id": null}` blanks the screen without requiring a policy. The HTML form
endpoint `/campaigns/{id}/active` accepts the same `fog_action` values. Existing
API clients must be updated; there is intentionally no silent default.

The update is transactional: checkpoint the outgoing map, restore/reset the
target, bump its fog version, checkpoint it, then activate it. Existing campaign
ownership and CSRF checks still apply. Display reset is not undoable.

Admin map JSON adds `cache_token`, an opaque unique map-incarnation identifier.
Viewer state `version` is opaque; use the supplied `image_url` rather than
constructing one. Versioned viewer image requests reject an obsolete `v` with
400 so a URL for an old state cannot receive the current map. Viewer composites,
admin raw images and admin masks use `Cache-Control: no-store`.

