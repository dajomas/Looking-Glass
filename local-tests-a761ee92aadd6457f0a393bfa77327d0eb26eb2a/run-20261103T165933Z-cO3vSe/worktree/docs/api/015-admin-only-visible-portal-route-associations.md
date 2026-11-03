## Admin-only visible portal route associations

The existing authorized admin map payload additionally returns portal_routes:

```json
{"id":"8:0>10:1","state":"locked_door","entry":{"wall_id":8,"section":3,"side":0,"compass":"E","polygon":[[1,2],[3,2],[2,4]]},"exit":{"wall_id":10,"section":5,"side":1,"compass":"W","polygon":[[8,2],[10,2],[9,4]]}}
```

This is presentation metadata, one item per actual visible Entry with a displayed
paired Exit polygon. Polygons use the existing work-pixel coordinate space.
section is the 1-based position in the current map wall list, matching editor
labels; wall_id and side identify the actual endpoint. state is the effective
Entry kind. Shared Exits can occur in multiple route items. Both can supply an
existing double-headed arrow polygon instead of an Exit-only hint. No guessed
or client-selected target point is supplied.

This field is produced only by the manage-authorized admin map payload. It is not
added to viewer state, image responses or websocket messages. Viewer rendering,
permissions, CSRF and all mutation endpoints are unchanged. Dwell/pause preferences
are browser-local, not an API or database setting. No migration is introduced.
See [testing](testing.md) for validation guidance and environment requirements.


