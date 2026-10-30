## Wall-type boundary request contract

`POST /api/maps/{id}/wall-types` accepts the required JSON field
`disabled_wall_types`, a list of `wall`, `door`, `locked_door`, `unlocked_door`,
`secret`, `portal`, `window`, `invisible` or `ethereal`. For example:

```json
{"disabled_wall_types": ["door", "window"]}
```

An empty list enables all types. The response is the updated map payload,
including `disabled_wall_types`. The shorter key `disabled` is not an alias:
a body containing only that key is missing the required field and returns 422.
Unknown type values, a missing field, null, or a scalar instead of a list also
return 422. Rejected validation requests do not update saved wall types or map
versions. This patch preserves the existing schema rather than adding a legacy
alias or changing validation to 400. Normal admin authentication, CSRF and map
management permissions still apply; this route is absent from the viewer app.


