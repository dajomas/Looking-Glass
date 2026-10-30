## Passage save-scope isolation

```sh
python -m pytest -q python/tests/test_passage_save_scopes.py
node python/tests/test_map_transitions.js
python -m pytest -q python/tests/test_map_transitions_web.py
python -m pytest -q python/tests/browser/test_passage_save_scopes.py
```

Stage edits in both groups; save each separately and verify only its own group is
persisted while the other remains pending. Test Close/Escape discard cancellation,
a new endpoint followed by a runtime update, server-normalized configuration values,
sequential revisions, failed/stale saves and Travel's saved-state warning. AST route
and Node mock tests do not replace real HTTP/CSRF and browser integration checks.


