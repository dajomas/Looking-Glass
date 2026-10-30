## Viewer diagnostics and disclosure-state fixture contracts

The read-only `/api/campaigns/{id}/viewer-status` mock uses the actual client
schema: `viewers: []` and `blank`, plus `ok: true`. This is explicit GET-only
coverage; unknown paths and all writes still fall through to the caller. The
standalone selection-persistence page must not call metadata helpers with a
nonexistent `data` variable. Helper tests protect both boundaries.

HTML base overrides get a UTF-8 declaration without altering the caller's
mapping. This prevents fixture-only mojibake; production base.html already has
UTF-8. Plain-text overrides are not rewritten.

Passage tests need at least two campaign maps: the real template deliberately
hides that section for single-map campaigns. The shared admin fixture now renders
two siblings and retains its explicit transitions handler. Independent auxiliary
mocks must not preempt that fixture's authored transition payload.

Sidebar tests must honor initial closed disclosure state. Open Fog before radio
input and Walls before native slider drag/focus. Peer panels use the real
accordion; Saved sources is a peer, while the legend remains independent. Test
closing and reopening explicitly rather than assuming a first click closes an
already-open panel. Do not add force=True, disable the accordion, or operate a
hidden control with synthetic callbacks to evade real input behavior.

Run focused fixtures first, then the complete browser suite:

```sh
python -m pytest -q python/tests/test_browser_fixture_support.py
python -m pytest -v python/tests/browser/test_editor_controls.py
python -m pytest -v python/tests/browser/test_secondary_click.py
python -m pytest -v python/tests/browser/test_map_transitions.py
python -m pytest -v python/tests/browser/test_wall_width_followup.py
python -m pytest -v python/tests/browser
```

This follow-up does not loosen the unresolved screenshot threshold or certify a
full-suite pass. Patch/ records measured execution results and outstanding items.


